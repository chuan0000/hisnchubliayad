with open('app/routers/evidence.py', 'r', encoding='utf-8') as f:
    text = f.read()

f95_code = '''
# ==============================================================================
# 【功能 95】分團行事曆與個人 Google Calendar 雙向匯出與 WebCal 自動同步 API
# ==============================================================================
@router.get("/calendar/webcal-feed")
def get_webcal_live_feed(db: Session = Depends(get_db)):
    """【功能 95】產製專業級 WebCal 即時訂閱流 (RFC 5545)，支援即時雙向排程同步"""
    from datetime import datetime
    items = db.query(EvidenceItem).filter(EvidenceItem.is_published == True).all()
    now_utc = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//BLIA Hsinchu Youth Subgroup//Universal Calendar Feed//ZH",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:國際佛光會新竹青年分團年度弘法行事曆",
        "X-WR-TIMEZONE:Asia/Taipei",
        "REFRESH-INTERVAL;VALUE=DURATION:P1D",
        "X-PUBLISHED-TTL:P1D"
    ]

    for item in items:
        try:
            d_str = item.event_date.replace("-", "").strip()
            lines.extend([
                "BEGIN:VEVENT",
                f"UID:blia-hcy-webcal-{item.id}@hsinchuyouth.fgs.org.tw",
                f"DTSTAMP:{now_utc}",
                f"DTSTART;VALUE=DATE:{d_str}",
                f"DTEND;VALUE=DATE:{d_str}",
                f"SUMMARY:【佛光青年】{item.title}",
                f"DESCRIPTION:{item.description or ''} | 評鑑代碼: {item.evaluation_code or ''}",
                f"LOCATION:佛光山新竹法寶寺 ({item.venue or '新竹市東區民族路241號'})",
                "STATUS:CONFIRMED",
                "BEGIN:VALARM",
                "TRIGGER:-P1D",
                "ACTION:DISPLAY",
                f"DESCRIPTION:提醒：明日佛光青年活動【{item.title}】",
                "END:VALARM",
                "END:VEVENT"
            ])
        except Exception:
            continue

    lines.append("END:VCALENDAR")
    return Response(content="\\r\\n".join(lines), media_type="text/calendar")

@router.get("/calendar/sync-guide")
def get_calendar_sync_guide():
    """【功能 95】取得手機與 Google Calendar 一鍵訂閱教學與引導網址"""
    return {
        "status": "success",
        "calendar_name": "國際佛光會新竹青年分團年度弘法行事曆",
        "webcal_url": "webcal://127.0.0.1:8000/api/evidence/calendar/webcal-feed",
        "ics_url": "http://127.0.0.1:8000/api/evidence/calendar.ics",
        "google_cal_import_guide": "至 Google 日曆網頁版 -> 其他日曆 -> 透過網址新增 -> 貼上上述 webcal/ics 網址即可每日自動同步。",
        "apple_cal_guide": "iPhone / Mac 點擊 webcal 連結即可自動加入訂閱行事曆。"
    }
'''

if 'calendar/webcal-feed' not in text:
    target = '@router.get(\"/calendar.ics\"'
    text = text.replace(target, f95_code + '\n' + target)
    with open('app/routers/evidence.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('Feature 95 added to evidence.py!')
else:
    print('Feature 95 already exists in evidence.py')
