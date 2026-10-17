import base64
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
try:
    from sqlalchemy.orm import Session
except ImportError:
    Session = object

from app.config import SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES
from app.database import get_db
from app.models import User

# HTTP Bearer Scheme
security = HTTPBearer()

# ----------------- Password Hashing (PBKDF2-HMAC-SHA256) -----------------
def hash_password(password: str) -> str:
    """密碼安全雜湊，採用標準 PBKDF2-HMAC-SHA256 與隨機鹽值，無外部 C 編譯依賴，跨平台極致穩定"""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    return f"{salt}${key.hex()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """驗證明文密碼是否與雜湊值相符"""
    try:
        salt, stored_hash = hashed_password.split('$')
        computed_hash = hashlib.pbkdf2_hmac(
            'sha256',
            plain_password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        ).hex()
        return hmac.compare_digest(computed_hash, stored_hash)
    except Exception:
        return False

# ----------------- JWT Token (HMAC-SHA256) -----------------
def base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')

def base64url_decode(data: str) -> bytes:
    padding = '=' * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """生成標準 JWT Token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": int(expire.timestamp())})

    header = {"alg": "HS256", "typ": "JWT"}
    header_bytes = base64url_encode(json.dumps(header).encode('utf-8'))
    payload_bytes = base64url_encode(json.dumps(to_encode).encode('utf-8'))

    signing_input = f"{header_bytes}.{payload_bytes}".encode('utf-8')
    signature = hmac.new(SECRET_KEY.encode('utf-8'), signing_input, hashlib.sha256).digest()
    signature_bytes = base64url_encode(signature)

    return f"{header_bytes}.{payload_bytes}.{signature_bytes}"

def decode_access_token(token: str) -> Dict[str, Any]:
    """解析並驗證 JWT Token"""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token 格式無效")
        
        header_b64, payload_b64, sig_b64 = parts
        signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
        expected_sig = base64url_encode(hmac.new(SECRET_KEY.encode('utf-8'), signing_input, hashlib.sha256).digest())

        if not hmac.compare_digest(sig_b64, expected_sig):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token 簽章驗證失敗")

        payload = json.loads(base64url_decode(payload_b64).decode('utf-8'))
        exp = payload.get("exp")
        if exp and datetime.utcnow().timestamp() > exp:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token 已過期，請重新登入")

        return payload
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Token 解析失敗: {str(e)}")

# ----------------- RBAC 權限依賴注入 -----------------
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """提取當前登入者"""
    token = credentials.credentials
    payload = decode_access_token(token)
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="認證憑證無效")

    user = db.query(User).filter(User.username == username, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="使用者不存在或已被停用")
    return user

def require_cadre(current_user: User = Depends(get_current_user)) -> User:
    """幹部層級權限（包含活動幹部與超級管理員）"""
    if current_user.role not in ["cadre", "super_admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="權限不足，僅幹部與管理員可操作")
    return current_user

def require_super_admin(current_user: User = Depends(get_current_user)) -> User:
    """最高權限（僅團長 / 評鑑秘書等超級管理員）"""
    if current_user.role != "super_admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="權限不足，需要超級管理員權限")
    return current_user
