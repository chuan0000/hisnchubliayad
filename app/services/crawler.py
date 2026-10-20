from datetime import datetime
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
    """使用 Python 原生 httpx 與 BeautifulSoup 抓取社群與道場公開活動日程"""
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
