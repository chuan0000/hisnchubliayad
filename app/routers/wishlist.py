from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
try:
    from sqlalchemy.orm import Session
except ImportError:
    Session = object

from app.database import get_db
from app.models import YouthWish, User
from app.schemas import (
    YouthWishCreate,
    YouthWishStatusUpdate,
    YouthWishResponse,
    YouthWishSummary
)
from app.auth import require_cadre

router = APIRouter(prefix="/api/wishlist", tags=["青年心願許願牆 (Youth Wishlist Wall)"])

@router.get("", response_model=List[YouthWishResponse])
def list_wishes(
    category: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """【公開前台/後台】取得青年心願卡片清單（支援分類與圓滿狀態篩選）"""
    all_wishes = db.query(YouthWish).all()
    filtered = all_wishes
    if category:
        filtered = [w for w in filtered if getattr(w, 'category', '') == category]
    if status:
        filtered = [w for w in filtered if getattr(w, 'status', '') == status]
    filtered.sort(key=lambda x: getattr(x, 'id', 0), reverse=True)
    return filtered[:limit]


@router.post("", response_model=YouthWishResponse)
def create_wish(
    wish_in: YouthWishCreate,
    db: Session = Depends(get_db)
):
    """【青年許願】發布新青年心願（運動裝備、數位3C、身心靈成長、生活文創）"""
    new_wish = YouthWish(
        title=wish_in.title,
        category=wish_in.category or "sports_gear",
        description=wish_in.description or "",
        estimated_budget=wish_in.estimated_budget or 0.0,
        created_by=wish_in.created_by or "青年同修",
        likes_count=0,
        status="open",
        sponsor_note=""
    )
    db.add(new_wish)
    db.commit()
    db.refresh(new_wish)
    return new_wish


@router.post("/{wish_id}/like", response_model=YouthWishResponse)
def like_wish(
    wish_id: int,
    db: Session = Depends(get_db)
):
    """【公開前台】為青年心願點讚集氣 (+1)"""
    wish = db.query(YouthWish).filter(YouthWish.id == wish_id).first()
    if not wish:
        raise HTTPException(status_code=404, detail="找不到此心願卡片")
    
    wish.likes_count = (getattr(wish, 'likes_count', 0) or 0) + 1
    db.commit()
    db.refresh(wish)
    return wish


@router.put("/{wish_id}/status", response_model=YouthWishResponse)
def update_wish_status(
    wish_id: int,
    status_in: YouthWishStatusUpdate,
    db: Session = Depends(get_db)
):
    """【幹部認領/更新】更新青年心願進度（open 許願中, in_progress 籌備中, fulfilled 已圓滿）"""
    wish = db.query(YouthWish).filter(YouthWish.id == wish_id).first()
    if not wish:
        raise HTTPException(status_code=404, detail="找不到此心願卡片")
    
    wish.status = status_in.status
    if status_in.sponsor_note is not None:
        wish.sponsor_note = status_in.sponsor_note
        
    db.commit()
    db.refresh(wish)
    return wish


@router.get("/summary", response_model=YouthWishSummary)
def get_wishlist_summary(db: Session = Depends(get_db)):
    """【心願牆儀表板】統計總許願數、已圓滿心願數、總按讚集氣數與類別分佈"""
    all_wishes = db.query(YouthWish).all()
    total_wishes = len(all_wishes)
    fulfilled = sum(1 for w in all_wishes if getattr(w, 'status', '') == 'fulfilled')
    total_likes = sum(getattr(w, 'likes_count', 0) or 0 for w in all_wishes)
    
    cat_dist = {}
    for w in all_wishes:
        cat = getattr(w, 'category', 'other') or 'other'
        cat_dist[cat] = cat_dist.get(cat, 0) + 1
        
    return YouthWishSummary(
        total_wishes=total_wishes,
        fulfilled_wishes=fulfilled,
        total_likes=total_likes,
        category_distribution=cat_dist
    )


@router.delete("/{wish_id}")
def delete_wish(
    wish_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_cadre)
):
    """【幹部/管理員】刪除青年心願"""
    wish = db.query(YouthWish).filter(YouthWish.id == wish_id).first()
    if not wish:
        raise HTTPException(status_code=404, detail="找不到此心願卡片")
    db.delete(wish)
    db.commit()
    return {"message": "心願卡片已成功移除"}
