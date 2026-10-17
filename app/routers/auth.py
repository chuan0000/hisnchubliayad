import secrets
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
try:
    from sqlalchemy.orm import Session
except ImportError:
    Session = object

from app.database import get_db
from app.models import User, ReviewerToken
from app.schemas import (
    Token, UserLogin, UserCreate, UserUpdate, UserResponse,
    ReviewerTokenCreate, ReviewerTokenResponse
)
from app.auth import (
    verify_password,
    hash_password,
    create_access_token,
    get_current_user,
    require_super_admin
)

router = APIRouter(prefix="/api/auth", tags=["使用者與認證 (Auth)"])

@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """登入並取得 JWT 授權憑證"""
    user = db.query(User).filter(User.username == login_data.username).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="帳號或密碼錯誤"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="此帳號已被停用，請洽分團長或評鑑秘書"
        )

    token = create_access_token({"sub": user.username, "role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
        "username": user.username,
        "full_name": user.full_name
    }

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """取得當前登入者資訊"""
    return current_user

@router.get("/users", response_model=List[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    admin: User = Depends(require_super_admin)
):
    """【超級管理員】列出所有幹部帳號"""
    return db.query(User).order_by(User.id.asc()).all()

@router.post("/users", response_model=UserResponse)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_super_admin)
):
    """【超級管理員】新增幹部帳號"""
    existing = db.query(User).filter(User.username == user_in.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="此使用者帳號已存在")

    new_user = User(
        username=user_in.username,
        hashed_password=hash_password(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_super_admin)
):
    """【超級管理員】修改幹部資訊或重設密碼"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="找不到此使用者")

    if user_update.full_name is not None:
        user.full_name = user_update.full_name
    if user_update.role is not None:
        user.role = user_update.role
    if user_update.is_active is not None:
        user.is_active = user_update.is_active
    if user_update.password:
        user.hashed_password = hash_password(user_update.password)

    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_super_admin)
):
    """【超級管理員】刪除幹部帳號"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="找不到此使用者")
    if user.username == admin.username:
        raise HTTPException(status_code=400, detail="不可刪除當前登入的超級管理員帳號")

    db.delete(user)
    db.commit()
    return {"message": f"帳號 {user.username} 已成功刪除"}

# ==============================================================================
# 【功能 9】評審委員專用免登入唯讀通行證 API
# ==============================================================================
@router.post("/reviewer-tokens", response_model=ReviewerTokenResponse)
def create_reviewer_token(
    token_in: ReviewerTokenCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_super_admin)
):
    """【超級管理員】生成評審委員專屬免登入安全存取 Token 連結"""
    safe_token = secrets.token_urlsafe(32)
    exp_date = (datetime.now() + timedelta(days=token_in.expiry_days or 30)).strftime("%Y-%m-%d")

    rev_token = ReviewerToken(
        token=safe_token,
        name=token_in.name,
        expires_at=exp_date,
        is_active=True
    )
    db.add(rev_token)
    db.commit()
    db.refresh(rev_token)
    return rev_token

@router.get("/reviewer-tokens", response_model=List[ReviewerTokenResponse])
def list_reviewer_tokens(
    db: Session = Depends(get_db),
    admin: User = Depends(require_super_admin)
):
    """【超級管理員】列出所有已發行之評審專屬通行證"""
    return db.query(ReviewerToken).order_by(ReviewerToken.id.desc()).all()

@router.delete("/reviewer-tokens/{token_id}")
def revoke_reviewer_token(
    token_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_super_admin)
):
    """【超級管理員】撤銷或作廢評審通行證"""
    tok = db.query(ReviewerToken).filter(ReviewerToken.id == token_id).first()
    if not tok:
        raise HTTPException(status_code=404, detail="找不到此評審憑證")
    db.delete(tok)
    db.commit()
    return {"message": "評審憑證已撤銷"}

@router.get("/verify-reviewer-token/{token}")
def verify_token(token: str, db: Session = Depends(get_db)):
    """驗證評審 Token 是否有效"""
    tok = db.query(ReviewerToken).filter(ReviewerToken.token == token, ReviewerToken.is_active == True).first()
    if not tok:
        raise HTTPException(status_code=401, detail="無效或已被撤銷的評審通行證")
    if tok.expires_at:
        today = datetime.now().strftime("%Y-%m-%d")
        if today > tok.expires_at:
            raise HTTPException(status_code=401, detail="此評審通行證已過期，請洽新竹青年分團秘書處")
    return {
        "status": "valid",
        "reviewer_name": tok.name,
        "expires_at": tok.expires_at
    }
