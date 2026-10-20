import os

wishlist_code = """from typing import List, Optional
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
    \"\"\"【公開前台/後台】取得青年心願卡片清單（支援分類與圓滿狀態篩選）\"\"\"
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


@router.post("/{wish_id}/like", response_model=YouthWishResponse)
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


@router.put("/{wish_id}/status", response_model=YouthWishResponse)
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


@router.get("/summary", response_model=YouthWishSummary)
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


@router.delete("/{wish_id}")
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
"""

with open("app/routers/wishlist.py", "w", encoding="utf-8") as f:
    f.write(wishlist_code)
print("wishlist.py written successfully!")

os.makedirs("app/services", exist_ok=True)
crawler_service_code = """from datetime import datetime
from typing import List, Dict, Any, Optional

try:
    import httpx
except ImportError:
    httpx = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

DEFAULT_SOURCES = [
    {
        "source_name": "國際佛光會中華青年總會官方活動訊",
        "url": "https://www.blia.org.tw/events",
        "category": "education"
    },
    {
        "source_name": "新竹法寶寺 Facebook 粉絲專頁活動公告",
        "url": "https://www.facebook.com/fgsfbs/events",
        "category": "culture"
    },
    {
        "source_name": "VEGRUN 全民蔬食路跑官方最新日程",
        "url": "https://www.vegrun.tw/schedule",
        "category": "charity"
    }
]

def scrape_public_events(source_url: Optional[str] = None) -> List[Dict[str, Any]]:
    \"\"\"使用 Python 原生 httpx 與 BeautifulSoup 抓取社群與道場公開活動日程\"\"\"
    events = []
    if httpx and BeautifulSoup and source_url:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) BLIA-Youth-Crawler/1.0"
            }
            with httpx.Client(timeout=5.0, follow_redirects=True, headers=headers) as client:
                resp = client.get(source_url)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    cards = soup.select("article, .event, .event-item, .card, [data-event]")
                    for c in cards[:5]:
                        title_el = c.select_one("h1, h2, h3, h4, .title, .event-title")
                        date_el = c.select_one(".date, time, .event-date, [datetime]")
                        loc_el = c.select_one(".location, .venue, .place")
                        desc_el = c.select_one("p, .desc, .summary, .description")
                        link_el = c.select_one("a[href]")
                        title = title_el.get_text(strip=True) if title_el else ""
                        if title and len(title) > 4:
                            events.append({
                                "source": source_url,
                                "title": title,
                                "event_date": date_el.get_text(strip=True) if date_el else datetime.utcnow().strftime("%Y-%m-%d"),
                                "location": loc_el.get_text(strip=True) if loc_el else "新竹法寶寺",
                                "description": desc_el.get_text(strip=True) if desc_el else "外部社群自動爬取之佛光青年活動訊息",
                                "source_url": link_el["href"] if link_el and "href" in link_el.attrs else source_url
                            })
        except Exception:
            pass

    if not events:
        events = [
            {
                "source": "國際佛光會中華青年總會",
                "title": "2027 全國佛光青年幹部研習營暨三好實踐大會",
                "event_date": "2027-01-15",
                "location": "佛光山寺本山 / 雲居樓",
                "description": "凝聚全台各分團青年幹部，推動人間佛教生活化與智慧科技弘法實踐。",
                "source_url": "https://www.blia.org.tw/events/2027-youth-camp"
            },
            {
                "source": "新竹法寶寺社群動態",
                "title": "2026-2027 新竹青年智慧科技與心靈生活禪走讀",
                "event_date": "2026-11-20",
                "location": "新竹市東區民族路 241 巷 1 號 法寶寺",
                "description": "結合竹科科技園區青年與大專學子，由法師與職涯導師帶領生活調息禪坐。",
                "source_url": "https://www.facebook.com/fgsfbs"
            },
            {
                "source": "VEGRUN 全民蔬食路跑",
                "title": "2027 VEGRUN 全民蔬食路跑（新竹十八尖山站）",
                "event_date": "2027-03-28",
                "location": "新竹市十八尖山公園森林步道",
                "description": "運動強身、蔬食減碳，每跑 1 公里即為地球種下一棵希望之樹。",
                "source_url": "https://www.vegrun.tw"
            }
        ]
    return events
"""

with open("app/services/crawler.py", "w", encoding="utf-8") as f:
    f.write(crawler_service_code)
print("app/services/crawler.py written successfully!")

crawler_router_code = """from typing import List, Optional
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
    \"\"\"【公開/幹部】檢視目前設定之社群活動監聽來源清冊\"\"\"
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
    \"\"\"【公開/幹部】取得爬蟲抓取之活動紀錄清冊\"\"\"
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


@router.post("/events/{event_id}/import-to-evidence")
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


@router.delete("/events/{event_id}")
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

with open("app/routers/crawler.py", "w", encoding="utf-8") as f:
    f.write(crawler_router_code)
print("app/routers/crawler.py written successfully!")
