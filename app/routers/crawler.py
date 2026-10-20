from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
try:
    from sqlalchemy.orm import Session
except ImportError:
    Session = object

from app.database import get_db
from app.models import CrawledEvent, EvidenceItem, User
from app.schemas import CrawledEventCreate, CrawledEventResponse
from app.services.crawler import scrape_public_events, DEFAULT_SOURCES
from app.auth import require_cadre

router = APIRouter(prefix="/api/crawler", tags=["社群與活動自動爬蟲服務 (Event Crawler Service)"])

@router.get("/sources")
def get_crawler_sources():
    """【公開/幹部】檢視目前設定之社群活動監聽來源清冊"""
    return {
        "status": "active",
        "service": "Python httpx + BeautifulSoup4 Event Crawler",
        "sources": DEFAULT_SOURCES
    }


@router.get("/events", response_model=List[CrawledEventResponse])
def list_crawled_events(
    sync_status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """【公開/幹部】取得爬蟲抓取之活動紀錄清冊"""
    all_events = db.query(CrawledEvent).all()
    filtered = all_events
    if sync_status:
        filtered = [e for e in filtered if getattr(e, 'sync_status', '') == sync_status]
    filtered.sort(key=lambda x: getattr(x, 'id', 0), reverse=True)
    return filtered[:limit]


@router.post("/fetch-external-events", response_model=List[CrawledEventResponse])
def trigger_event_crawler(
    source_url: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """【觸發爬蟲】即時執行 Python 爬蟲抓取外部公開社群或活動日程，寫入資料庫"""
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


@router.post("/events/{event_id}/import-to-evidence")
def import_crawled_event_to_evidence(
    event_id: int,
    category: Optional[str] = "culture",
    db: Session = Depends(get_db),
    user: User = Depends(require_cadre)
):
    """【一鍵匯入】將爬蟲抓到的公開活動轉存至四大宗旨成果佐證庫（草稿待審）"""
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
        summary=f"【外部社群自動爬蟲匯入】\n{c_ev.description}\n來源連結：{c_ev.source_url}",
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


@router.delete("/events/{event_id}")
def delete_crawled_event(
    event_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_cadre)
):
    """【幹部管理】刪除抓取的活動紀錄"""
    ev = db.query(CrawledEvent).filter(CrawledEvent.id == event_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail="找不到此抓取活動")
    db.delete(ev)
    db.commit()
    return {"message": "活動抓取紀錄已成功刪除"}
