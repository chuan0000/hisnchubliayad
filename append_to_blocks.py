with open("app/routers/blocks.py", "r", encoding="utf-8") as f:
    content = f.read()

wishlist_and_crawler_code = """

# ==============================================================================
# 【青年心願許願牆】Router (Youth Wishlist Wall)
# ==============================================================================
from app.models import YouthWish, CrawledEvent
from app.schemas import (
    YouthWishCreate,
    YouthWishStatusUpdate,
    YouthWishResponse,
    YouthWishSummary,
    CrawledEventCreate,
    CrawledEventResponse
)
from app.services.crawler import scrape_public_events, DEFAULT_SOURCES

wishlist_router = APIRouter(prefix="/api/wishlist", tags=["青年心願許願牆 (Youth Wishlist Wall)"])

@wishlist_router.get("", response_model=List[YouthWishResponse])
def list_wishes(
    category: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    \"\"\"【公開前台/後台】取得青年心願卡片清單（支援分類與圓滿狀態篩選）\"\"\"
    all_wishes = db.query(YouthWish).all()
    filtered = all_wishes
    if category:
        filtered = [w for w in filtered if getattr(w, 'category', '') == category]
    if status:
        filtered = [w for w in filtered if getattr(w, 'status', '') == status]
    filtered.sort(key=lambda x: getattr(x, 'id', 0), reverse=True)
    return filtered[:limit]


@wishlist_router.post("", response_model=YouthWishResponse)
def create_wish(
    wish_in: YouthWishCreate,
    db: Session = Depends(get_db)
):
    \"\"\"【青年許願】發布新青年心願（運動裝備、數位3C、身心靈成長、生活文創）\"\"\"
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


@wishlist_router.post("/{wish_id}/like", response_model=YouthWishResponse)
def like_wish(
    wish_id: int,
    db: Session = Depends(get_db)
):
    \"\"\"【公開前台】為青年心願點讚集氣 (+1)\"\"\"
    wish = db.query(YouthWish).filter(YouthWish.id == wish_id).first()
    if not wish:
        raise HTTPException(status_code=404, detail="找不到此心願卡片")
    
    wish.likes_count = (getattr(wish, 'likes_count', 0) or 0) + 1
    db.commit()
    db.refresh(wish)
    return wish


@wishlist_router.put("/{wish_id}/status", response_model=YouthWishResponse)
def update_wish_status(
    wish_id: int,
    status_in: YouthWishStatusUpdate,
    db: Session = Depends(get_db)
):
    \"\"\"【幹部認領/更新】更新青年心願進度（open 許願中, in_progress 籌備中, fulfilled 已圓滿）\"\"\"
    wish = db.query(YouthWish).filter(YouthWish.id == wish_id).first()
    if not wish:
        raise HTTPException(status_code=404, detail="找不到此心願卡片")
    
    wish.status = status_in.status
    if status_in.sponsor_note is not None:
        wish.sponsor_note = status_in.sponsor_note
        
    db.commit()
    db.refresh(wish)
    return wish


@wishlist_router.get("/summary", response_model=YouthWishSummary)
def get_wishlist_summary(db: Session = Depends(get_db)):
    \"\"\"【心願牆儀表板】統計總許願數、已圓滿心願數、總按讚集氣數與類別分佈\"\"\"
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


@wishlist_router.delete("/{wish_id}")
def delete_wish(
    wish_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_cadre)
):
    \"\"\"【幹部/管理員】刪除青年心願\"\"\"
    wish = db.query(YouthWish).filter(YouthWish.id == wish_id).first()
    if not wish:
        raise HTTPException(status_code=404, detail="找不到此心願卡片")
    db.delete(wish)
    db.commit()
    return {"message": "心願卡片已成功移除"}


# ==============================================================================
# 【社群與活動自動爬蟲服務】Router (Event Crawler Service)
# ==============================================================================
crawler_router = APIRouter(prefix="/api/crawler", tags=["社群與活動自動爬蟲服務 (Event Crawler Service)"])

@crawler_router.get("/sources")
def get_crawler_sources():
    \"\"\"【公開/幹部】檢視目前設定之社群活動監聽來源清冊\"\"\"
    return {
        "status": "active",
        "service": "Python httpx + BeautifulSoup4 Event Crawler",
        "sources": DEFAULT_SOURCES
    }


@crawler_router.get("/events", response_model=List[CrawledEventResponse])
def list_crawled_events(
    sync_status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    \"\"\"【公開/幹部】取得爬蟲抓取之活動紀錄清冊\"\"\"
    all_events = db.query(CrawledEvent).all()
    filtered = all_events
    if sync_status:
        filtered = [e for e in filtered if getattr(e, 'sync_status', '') == sync_status]
    filtered.sort(key=lambda x: getattr(x, 'id', 0), reverse=True)
    return filtered[:limit]


@crawler_router.post("/fetch-external-events", response_model=List[CrawledEventResponse])
def trigger_event_crawler(
    source_url: Optional[str] = None,
    db: Session = Depends(get_db)
):
    \"\"\"【觸發爬蟲】即時執行 Python 爬蟲抓取外部公開社群或活動日程，寫入資料庫\"\"\"
    raw_events = scrape_public_events(source_url)
    saved_items = []
    
    for item in raw_events:
        existing = db.query(CrawledEvent).filter(CrawledEvent.title == item["title"]).first()
        if not existing:
            ev = CrawledEvent(
                source=item.get("source", "Web/Social"),
                title=item["title"],
                event_date=item.get("event_date", ""),
                location=item.get("location", ""),
                description=item.get("description", ""),
                source_url=item.get("source_url", ""),
                sync_status="synced"
            )
            db.add(ev)
            db.commit()
            db.refresh(ev)
            saved_items.append(ev)
        else:
            saved_items.append(existing)
            
    return saved_items


@crawler_router.post("/events/{event_id}/import-to-evidence")
def import_crawled_event_to_evidence(
    event_id: int,
    category: Optional[str] = "culture",
    db: Session = Depends(get_db),
    user: User = Depends(require_cadre)
):
    \"\"\"【一鍵匯入】將爬蟲抓到的公開活動轉存至四大宗旨成果佐證庫（草稿待審）\"\"\"
    c_ev = db.query(CrawledEvent).filter(CrawledEvent.id == event_id).first()
    if not c_ev:
        raise HTTPException(status_code=404, detail="找不到此抓取活動")
        
    year = c_ev.event_date[:4] if c_ev.event_date and len(c_ev.event_date) >= 4 else "2026"
    
    evidence = EvidenceItem(
        category=category or "culture",
        year=year,
        evaluation_code="EXT-CRAWL",
        title=c_ev.title,
        event_date=c_ev.event_date or "2026-10-17",
        location=c_ev.location or "新竹法寶寺",
        summary=f"【外部社群自動爬蟲匯入】\\n{c_ev.description}\\n來源連結：{c_ev.source_url}",
        created_by="自動爬蟲機器人",
        participants_count=0,
        volunteers_count=0,
        service_hours=0.0,
        is_published=False
    )
    db.add(evidence)
    c_ev.sync_status = "imported_to_evidence"
    db.commit()
    db.refresh(evidence)
    
    return {
        "status": "success",
        "message": f"活動「{c_ev.title}」已成功轉入四大宗旨佐證資料庫！",
        "evidence_id": evidence.id,
        "is_published": evidence.is_published
    }


@crawler_router.delete("/events/{event_id}")
def delete_crawled_event(
    event_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_cadre)
):
    \"\"\"【幹部管理】刪除抓取的活動紀錄\"\"\"
    ev = db.query(CrawledEvent).filter(CrawledEvent.id == event_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail="找不到此抓取活動")
    db.delete(ev)
    db.commit()
    return {"message": "活動抓取紀錄已成功刪除"}
"""

if "wishlist_router = APIRouter" not in content:
    content += wishlist_and_crawler_code
    with open("app/routers/blocks.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("blocks.py updated with wishlist and crawler routers!")
else:
    print("blocks.py already has wishlist_router")
