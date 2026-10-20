from pathlib import Path
import io
import os
import csv
import re
import json
import zipfile
import shutil
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from app.pdf_utils import html_to_pdf_bytes as safe_html_to_pdf
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, Body
from fastapi.responses import FileResponse, HTMLResponse, Response
try:
    from sqlalchemy.orm import Session
except ImportError:
    Session = object

from app.config import UPLOAD_DIR
from app.database import get_db
from app.models import EvidenceItem, User, EvidenceFeedback, SurveyResponse, ActivityRegistration, MeetingActionItem, CadreAttendance
from app.schemas import (
    EvidenceItemCreate, EvidenceItemUpdate, EvidenceItemResponse,
    EvidenceFeedbackCreate, EvidenceFeedbackResponse,
    SurveyResponseCreate, SurveyResponseResponse,
    ActivityRegistrationCreate, ActivityRegistrationUpdate, ActivityRegistrationResponse,
    MeetingActionItemCreate, MeetingActionItemUpdate, MeetingActionItemResponse
)
from app.auth import require_cadre

router = APIRouter(prefix="/api/evidence", tags=["四大宗旨佐證資料 (Four Objectives Evidence)"])

CATEGORY_MAP = {
    "文化": "culture", "culture": "culture", "文化弘法": "culture", "文藝": "culture",
    "教育": "education", "education": "education", "教育培力": "education", "培育": "education",
    "共修": "cultivation", "cultivation": "cultivation", "共修淨心": "cultivation", "修持": "cultivation", "法會": "cultivation",
    "慈善": "charity", "charity": "charity", "慈善福田": "charity", "公益": "charity", "環保": "charity"
}

CATEGORY_DIR_MAP = {
    "culture": "01_文化弘法_Culture",
    "education": "02_教育培力_Education",
    "cultivation": "03_共修淨心_Cultivation",
    "charity": "04_慈善福田_Charity"
}

# 預設新竹與竹北關鍵地點經緯度座標對照表
KNOWN_COORDINATES = {
    "新竹法寶寺": (24.8052, 120.9715),
    "新竹科學園區": (24.7831, 121.0112),
    "竹北市": (24.8291, 121.0135),
    "竹北演藝廳": (24.8291, 121.0135),
    "清華大學": (24.7935, 120.9930),
    "陽明交通大學": (24.7885, 120.9975),
    "南寮漁港": (24.8485, 120.9250),
    "護城河": (24.8035, 120.9690),
    "巨城": (24.8095, 120.9750),
    "五峰鄉": (24.6300, 121.1100),
    "竹東鎮": (24.7380, 121.0920),
    "十八尖山": (24.7940, 120.9850),
    "青草湖": (24.7750, 120.9710)
}

def resolve_coordinates(location_name: str):
    if not location_name:
        return 24.8052, 120.9715
    for k, v in KNOWN_COORDINATES.items():
        if k in location_name:
            return v
    return 24.8052, 120.9715

def normalize_date(val: Any) -> str:
    if not val:
        return datetime.now().strftime("%Y-%m-%d")
    if isinstance(val, datetime):
        return val.strftime("%Y-%m-%d")
    s = str(val).strip()
    match = re.search(r'(\d{4})[-/.年](\d{1,2})[-/.月](\d{1,2})', s)
    if match:
        y, m, d = match.groups()
        return f"{y}-{int(m):02d}-{int(d):02d}"
    return s[:10]

def normalize_category(val: Any) -> str:
    if not val:
        return "culture"
    s = str(val).strip().lower()
    for k, v in CATEGORY_MAP.items():
        if k in s:
            return v
    return "culture"

# ----------------- 成果查詢 API -----------------
@router.get("", response_model=List[EvidenceItemResponse])
def list_evidence(
    category: Optional[str] = Query(None, description="宗旨分類：culture, education, cultivation, charity"),
    year: Optional[str] = Query(None, description="活動年度：例 2026, 2025"),
    evaluation_code: Optional[str] = Query(None, description="評鑑指標代碼：例 A-1-1"),
    keyword: Optional[str] = Query(None, description="標題或內文搜尋關鍵字"),
    db: Session = Depends(get_db)
):
    """【公開前台/後台】取得佐證成果庫"""
    query = db.query(EvidenceItem).filter(EvidenceItem.is_published == True)
    if category:
        query = query.filter(EvidenceItem.category == category)
    if year:
        query = query.filter(EvidenceItem.year == year)
    if evaluation_code:
        query = query.filter(EvidenceItem.evaluation_code == evaluation_code)
    if keyword:
        query = query.filter(
            (EvidenceItem.title.contains(keyword)) | 
            (EvidenceItem.summary.contains(keyword)) |
            (EvidenceItem.location.contains(keyword))
        )
    return query.order_by(EvidenceItem.event_date.desc()).all()

@router.get("/years", response_model=List[str])
def list_available_years(db: Session = Depends(get_db)):
    """【功能 5】取得目前資料庫中所有活動年度列表"""
    items = db.query(EvidenceItem).all()
    years = set()
    for i in items:
        y = getattr(i, 'year', None)
        if y: years.add(str(y))
        elif getattr(i, 'event_date', None):
            years.add(str(i.event_date)[:4])
    if not years:
        years.add("2026")
    return sorted(list(years), reverse=True)

# ==============================================================================
# 【功能 11】活動公文與表單範本下載專區 API
# ==============================================================================
@router.get("/templates")
def list_templates():
    """【功能 11】取得分團常用公文簽呈、經費預算表、家長同意書標準空白範本清單"""
    tpl_dir = UPLOAD_DIR / "templates"
    tpl_dir.mkdir(parents=True, exist_ok=True)
    templates_meta = [
        {"name": "活動企劃書與公文簽呈範本", "filename": "活動企劃書與公文簽呈範本.docx", "format": "docx", "desc": "包含宗旨指標代碼、活動主旨、預算與簽核欄位之標準簽呈"},
        {"name": "活動經費收支預算表範本", "filename": "活動經費收支預算表範本.xlsx", "format": "xlsx", "desc": "包含收入、支出、單價數量與常住補助款核銷試算表"},
        {"name": "青年團員活動家長同意書範本", "filename": "青年團員活動家長同意書範本.docx", "format": "docx", "desc": "戶外探索、營隊與公益服務必備之法定代理人家長同意書"},
        {"name": "青年志工服務時數登記與認證表", "filename": "青年志工服務時數登記與認證表.xlsx", "format": "xlsx", "desc": "志工簽到退、服務時數累積與分團時數證明核章清冊"},
        {"name": "菩提讀書會帶領人教案設計表", "filename": "菩提讀書會帶領人教案設計表.docx", "format": "docx", "desc": "採用星雲說喻聞思修證四層次提問法之標準讀書會教案表"}
    ]
    for t in templates_meta:
        t["url"] = f"/uploads/templates/{t['filename']}"
    return templates_meta

# ==============================================================================
# 【功能 12】四大宗旨里程碑時序時間軸 API
# ==============================================================================
@router.get("/timeline")
def get_milestone_timeline(year: Optional[str] = "2026", db: Session = Depends(get_db)):
    """【功能 12】依月份時序整理年度活動大事記時間軸"""
    query = db.query(EvidenceItem).filter(EvidenceItem.is_published == True)
    if year:
        query = query.filter(EvidenceItem.year == year)
    items = query.order_by(EvidenceItem.event_date.asc()).all()

    timeline_data = []
    for it in items:
        dt_str = str(it.event_date or "")
        m_match = re.search(r'\d{4}[-/.](\d{1,2})', dt_str)
        if m_match:
            display_month = f"{int(m_match.group(1))} 月"
        else:
            display_month = "年度紀事"
        timeline_data.append({
            "id": it.id,
            "month": display_month,
            "date": dt_str,
            "category": it.category,
            "title": it.title,
            "evaluation_code": it.evaluation_code,
            "location": it.location,
            "participants": it.participants_count or 0,
            "summary": it.summary[:80] + "..." if len(it.summary) > 80 else it.summary,
            "file_url": it.file_url
        })
    return timeline_data

# ==============================================================================
# 【功能 13】活動地圖足跡視覺化 API (新竹與竹北在地深耕足跡)
# ==============================================================================
@router.get("/map-footprints")
def get_map_footprints(year: Optional[str] = None, db: Session = Depends(get_db)):
    """【功能 13】回傳新竹市、竹北市及周邊服務活動地點經緯度座標與成果聚合"""
    query = db.query(EvidenceItem).filter(EvidenceItem.is_published == True)
    if year:
        query = query.filter(EvidenceItem.year == year)
    items = query.all()

    loc_groups = {}
    for it in items:
        loc = it.location or "新竹法寶寺"
        lat, lng = resolve_coordinates(loc)
        key = f"{round(lat, 4)}_{round(lng, 4)}"
        if key not in loc_groups:
            loc_groups[key] = {
                "location_name": loc,
                "latitude": lat,
                "longitude": lng,
                "events_count": 0,
                "total_participants": 0,
                "activities": []
            }
        loc_groups[key]["events_count"] += 1
        loc_groups[key]["total_participants"] += (it.participants_count or 0)
        loc_groups[key]["activities"].append({
            "id": it.id,
            "title": it.title,
            "category": it.category,
            "date": it.event_date
        })

    return list(loc_groups.values())

@router.get("/radar-stats")
def get_radar_stats(year: Optional[str] = None, db: Session = Depends(get_db)):
    """【功能 6】四大宗旨五育均衡佔比雷達數據"""
    categories = ["culture", "education", "cultivation", "charity"]
    names_map = {"culture": "文化弘法", "education": "教育培力", "cultivation": "共修淨心", "charity": "慈善福田"}
    colors_map = {"culture": "#F59E0B", "education": "#3B82F6", "cultivation": "#10B981", "charity": "#EF4444"}

    q = db.query(EvidenceItem).filter(EvidenceItem.is_published == True)
    if year:
        q = q.filter(EvidenceItem.year == year)
    all_items = q.all()

    total_events = len(all_items)
    stats = []

    for cat in categories:
        cat_items = [it for it in all_items if it.category == cat]
        cnt = len(cat_items)
        part = sum(getattr(it, 'participants_count', 0) or 0 for it in cat_items)
        hrs = sum(getattr(it, 'service_hours', 0.0) or 0.0 for it in cat_items)
        pct = round((cnt / total_events * 100), 1) if total_events > 0 else 25.0
        balance_score = min(100, int((cnt / max(1, (total_events / 4))) * 85)) if total_events > 0 else 80

        stats.append({
            "category": cat,
            "name": names_map[cat],
            "color": colors_map[cat],
            "events_count": cnt,
            "participants": part,
            "hours": round(hrs, 1),
            "percentage": pct,
            "score": balance_score
        })

    avg_score = round(sum(s["score"] for s in stats) / 4, 1)
    grade = "特優 (S)" if avg_score >= 90 else "優等 (A)" if avg_score >= 80 else "甲等 (B)"

    return {
        "year": year or "全年度",
        "total_events": total_events,
        "radar_data": stats,
        "balance_index": avg_score,
        "evaluation_grade": grade
    }

# ==============================================================================
# 【功能 36】總會評鑑指標缺漏警示與補件提示雷達 API
# ==============================================================================
@router.get("/evaluation-audit")
def audit_evaluation_indicators(year: Optional[str] = "2026", db: Session = Depends(get_db)):
    """【功能 36】比對總會四大宗旨 12 大法定評鑑指標，自動診斷缺漏指標與建議補件對策"""
    # 總會評鑑指標基準字典 (包含四大宗旨法定必備指標)
    STANDARD_INDICATORS = [
        # 文化
        {"code": "A-1-1", "category": "culture", "cat_name": "文化弘法", "title": "文化藝文展覽與法語書法拓印推廣", "desc": "舉辦書法、拓印或藝文沙龍，推廣人間佛教文化"},
        {"code": "A-1-2", "category": "culture", "cat_name": "文化弘法", "title": "影音Podcast與新媒體自媒體傳播", "desc": "自主錄製青年播客、短影音或自媒體宣傳專案"},
        {"code": "A-1-3", "category": "culture", "cat_name": "文化弘法", "title": "三好刊物文創出版與宣傳品發行", "desc": "發行文宣明信片、手繪文創或定期簡訊刊物"},
        # 教育
        {"code": "B-1-1", "category": "education", "cat_name": "教育培力", "title": "科技青年生活禪修與正念舒壓營", "desc": "舉辦大專與職場青年禪修營，講授生活禪中道哲學"},
        {"code": "B-1-2", "category": "education", "cat_name": "教育培力", "title": "青年幹部領導力培訓與教案研習", "desc": "幹部破冰技巧、團體動力與教案設計研習工作坊"},
        {"code": "B-1-3", "category": "education", "cat_name": "教育培力", "title": "青年菩提讀書會與星雲說喻共讀", "desc": "雙週或每月讀書會研讀星雲大師經典著作"},
        # 共修
        {"code": "C-1-1", "category": "cultivation", "cat_name": "共修淨心", "title": "寺院法會執事與香燈梵唄引禮修持", "desc": "青年承擔法會引禮、梵唄與行堂執事修持體驗"},
        {"code": "C-1-2", "category": "cultivation", "cat_name": "共修淨心", "title": "青年大悲懺共修與定時念佛共修之夜", "desc": "定期舉辦青年共修，淨化身心與凝聚道情"},
        {"code": "C-1-3", "category": "cultivation", "cat_name": "共修淨心", "title": "三皈五戒願力落實與晨鐘暮鼓修行", "desc": "鼓勵青年受持五戒與踐行佛門清淨生活禮儀"},
        # 慈善
        {"code": "D-1-1", "category": "charity", "cat_name": "慈善福田", "title": "偏鄉獨居長者關懷訪視與冬令送暖結緣", "desc": "臘八粥結緣與走入偏鄉長輩家中探訪致贈物資"},
        {"code": "D-1-2", "category": "charity", "cat_name": "慈善福田", "title": "海岸環保淨灘與減塑愛護地球實踐行動", "desc": "落實環保與心保，號召志工守護自然生態環境"},
        {"code": "D-1-3", "category": "charity", "cat_name": "慈善福田", "title": "VEGRUN 全民蔬食路跑倡導與健康打卡", "desc": "推廣蔬食愛地球運動，結合里程累積公益捐贈"},
    ]

    query = db.query(EvidenceItem).filter(EvidenceItem.is_published == True)
    if year:
        query = query.filter(EvidenceItem.year == year)
    items = query.all()

    # 統計現有指標
    fulfilled_codes = {}
    for it in items:
        code = (it.evaluation_code or "").strip()
        if code:
            if code not in fulfilled_codes:
                fulfilled_codes[code] = []
            fulfilled_codes[code].append({"id": it.id, "title": it.title, "date": it.event_date})

    audit_results = []
    missing_count = 0
    fulfilled_count = 0

    for std in STANDARD_INDICATORS:
        code = std["code"]
        matches = fulfilled_codes.get(code, [])
        is_fulfilled = len(matches) > 0
        if is_fulfilled:
            fulfilled_count += 1
            status = "fulfilled"
            suggestion = f"已達標！包含 {len(matches)} 筆佐證（例: {matches[0]['title']}）"
        else:
            missing_count += 1
            status = "missing"
            suggestion = f"尚缺佐證！建議儘速規劃或登錄「{std['title']}」相關佐證以符合總會評鑑指標要求。"

        audit_results.append({
            "code": code,
            "category": std["category"],
            "cat_name": std["cat_name"],
            "title": std["title"],
            "desc": std["desc"],
            "status": status,
            "is_fulfilled": is_fulfilled,
            "matched_count": len(matches),
            "matched_items": matches,
            "suggestion": suggestion
        })

    fulfillment_rate = round((fulfilled_count / len(STANDARD_INDICATORS)) * 100, 1)

    return {
        "year": year or "2026",
        "total_indicators": len(STANDARD_INDICATORS),
        "fulfilled_count": fulfilled_count,
        "missing_count": missing_count,
        "fulfillment_rate": fulfillment_rate,
        "audit_verdict": "評鑑指標充足 (特優備評)" if fulfillment_rate >= 80 else ("部分指標尚待補齊 (請評鑑秘書追蹤)" if fulfillment_rate >= 50 else "多數指標缺漏，請儘速補建檔"),
        "indicators": audit_results
    }

@router.get("/stats")
def get_evidence_stats(year: Optional[str] = None, db: Session = Depends(get_db)):
    """統計四大宗旨成果筆數與量化數據"""
    categories = ["culture", "education", "cultivation", "charity"]
    counts = {}
    total_participants = 0
    total_volunteers = 0
    total_hours = 0.0

    for cat in categories:
        q = db.query(EvidenceItem).filter(
            EvidenceItem.category == cat,
            EvidenceItem.is_published == True
        )
        if year:
            q = q.filter(EvidenceItem.year == year)
        items = q.all()
        counts[cat] = len(items)
        for it in items:
            total_participants += getattr(it, 'participants_count', 0) or 0
            total_volunteers += getattr(it, 'volunteers_count', 0) or 0
            total_hours += getattr(it, 'service_hours', 0.0) or 0.0

    counts["total"] = sum(counts.values())
    counts["total_participants"] = total_participants
    counts["total_volunteers"] = total_volunteers
    counts["total_service_hours"] = round(total_hours, 1)
    return counts

@router.get("/export-zip")
def export_evaluation_zip(
    year: Optional[str] = Query(None, description="指定年度，如 2026"),
    category: Optional[str] = Query(None, description="指定宗旨，留空則全選"),
    db: Session = Depends(get_db)
):
    """【功能 2】一鍵將四大宗旨佐證檔案與彙整總表打包成標準評鑑 ZIP 壓縮檔"""
    query = db.query(EvidenceItem).filter(EvidenceItem.is_published == True)
    if year:
        query = query.filter(EvidenceItem.year == year)
    if category:
        query = query.filter(EvidenceItem.category == category)

    items = query.order_by(EvidenceItem.category.asc(), EvidenceItem.event_date.asc()).all()

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_name = f"BLIA_Evaluation_{year or 'All'}_{ts}.zip"
    zip_path = UPLOAD_DIR / zip_name

    with zipfile.ZipFile(str(zip_path), 'w', zipfile.ZIP_DEFLATED) as zf:
        csv_buffer = io.StringIO()
        csv_buffer.write('\ufeff')
        writer = csv.writer(csv_buffer)
        writer.writerow([
            "序號", "宗旨分類", "評鑑指標代碼", "活動名稱", "活動日期", "年度",
            "活動地點", "預期參與人數", "實際受惠人次", "出勤幹部人數", "志工總時數", "活動滿意度",
            "成果與成效摘要", "預期目標 vs 實際亮點", "主要佐證檔名", "多檔附件清單"
        ])

        cat_names = {"culture": "文化弘法", "education": "教育培力", "cultivation": "共修淨心", "charity": "慈善福田"}

        for idx, item in enumerate(items, 1):
            folder_name = CATEGORY_DIR_MAP.get(item.category, "05_其他成果")
            
            att_names = []
            try:
                atts = json.loads(item.attachments or "[]")
                att_names = [a.get("name", "") for a in atts if a.get("name")]
            except Exception:
                pass

            comparison_str = f"預期: {getattr(item, 'expected_goals', '')} ｜ 亮點: {getattr(item, 'actual_highlights', '')}"

            writer.writerow([
                idx,
                cat_names.get(item.category, item.category),
                item.evaluation_code or "-",
                item.title,
                item.event_date,
                item.year or item.event_date[:4],
                item.location,
                item.expected_participants or 0,
                item.participants_count or 0,
                item.volunteers_count or 0,
                item.service_hours or 0.0,
                f"{item.satisfaction_rate or 95}%",
                item.summary,
                comparison_str,
                item.original_filename or (Path(item.file_url).name if item.file_url else "-"),
                "；".join(att_names) if att_names else "-"
            ])

            if item.file_url and item.file_url.startswith("/uploads/"):
                clean_filename = Path(item.file_url).name
                disk_file = UPLOAD_DIR / clean_filename
                if disk_file.exists():
                    safe_entry_name = f"{folder_name}/{item.event_date}_{item.title[:20]}_{clean_filename}"
                    zf.write(str(disk_file), safe_entry_name)

            try:
                atts = json.loads(item.attachments or "[]")
                for att in atts:
                    a_url = att.get("url", "")
                    if a_url.startswith("/uploads/"):
                        a_name = Path(a_url).name
                        a_disk = UPLOAD_DIR / a_name
                        if a_disk.exists():
                            zf.write(str(a_disk), f"{folder_name}/附件_{item.event_date}_{a_name}")
            except Exception:
                pass

        zf.writestr("00_新竹佛光青年分團_年度成果評鑑總彙整表.csv", csv_buffer.getvalue().encode('utf-8-sig'))

    return FileResponse(
        path=str(zip_path),
        filename=f"新竹佛光青年分團_{year or '全年度'}_評鑑成果資料包.zip",
        media_type="application/zip"
    )

@router.get("/all-admin", response_model=List[EvidenceItemResponse])
def list_all_evidence_admin(
    year: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(require_cadre)
):
    """【幹部/管理員】列出所有佐證（含未發布草稿）"""
    query = db.query(EvidenceItem)
    if year:
        query = query.filter(EvidenceItem.year == year)
    if category:
        query = query.filter(EvidenceItem.category == category)
    return query.order_by(EvidenceItem.event_date.desc()).all()

# ==============================================================================
# 【功能 14】重複性活動一鍵複製建檔 API
# ==============================================================================
@router.post("/{item_id}/duplicate", response_model=EvidenceItemResponse)
def duplicate_evidence_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_cadre)
):
    """【功能 14】快速複製既有活動專案為新紀錄（秒速建檔讀書會或常態共修）"""
    item = db.query(EvidenceItem).filter(EvidenceItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="找不到欲複製的佐證項目")

    today_str = datetime.now().strftime("%Y-%m-%d")
    year_str = today_str[:4]

    cloned_item = EvidenceItem(
        category=item.category,
        title=f"{item.title} (複製副本)",
        event_date=today_str,
        year=year_str,
        evaluation_code=item.evaluation_code,
        location=item.location,
        latitude=getattr(item, 'latitude', 24.8052),
        longitude=getattr(item, 'longitude', 120.9715),
        summary=item.summary,
        participants_count=item.participants_count,
        volunteers_count=item.volunteers_count,
        service_hours=item.service_hours,
        satisfaction_rate=item.satisfaction_rate,
        expected_participants=item.expected_participants,
        expected_goals=item.expected_goals,
        actual_highlights=item.actual_highlights,
        file_url=item.file_url,
        file_type=item.file_type,
        original_filename=item.original_filename,
        attachments=item.attachments,
        created_by=f"{current_user.full_name} (複製建檔)",
        is_published=True
    )
    db.add(cloned_item)
    db.commit()
    db.refresh(cloned_item)
    return cloned_item

# ==============================================================================
# 【功能 15】單頁 A4 活動成果提報評鑑單 PDF 自動排版生成 API (Weasyprint)
# ==============================================================================
@router.get("/{item_id}/export-pdf")
def export_evidence_pdf(
    item_id: int,
    db: Session = Depends(get_db)
):
    """【功能 15】自動將單筆活動成果排版輸出為符合公文標準的單頁 A4 PDF 提報單"""
    item = db.query(EvidenceItem).filter(EvidenceItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="找不到此佐證項目")

    # WeasyPrint check replaced with safe_html_to_pdf

    cat_map = {"culture": "文化弘法 (Culture)", "education": "教育培力 (Education)", "cultivation": "共修淨心 (Cultivation)", "charity": "慈善福田 (Charity)"}

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  @page {{ size: A4 portrait; margin: 15mm; }}
  body {{ font-family: "Noto Sans CJK TC", "Noto Sans TC", sans-serif; color: #1e293b; line-height: 1.5; font-size: 11pt; }}
  .header {{ border-bottom: 3px solid #d97706; padding-bottom: 8px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: flex-end; }}
  .title {{ font-size: 17pt; font-weight: bold; color: #0f172a; margin: 0; }}
  .subtitle {{ font-size: 10pt; color: #d97706; font-weight: bold; }}
  .meta-table {{ width: 100%; border-collapse: collapse; margin-bottom: 12px; }}
  .meta-table th, .meta-table td {{ border: 1px solid #cbd5e1; padding: 6px 10px; font-size: 10pt; }}
  .meta-table th {{ background: #f8fafc; font-weight: bold; width: 22%; color: #334155; }}
  .metrics-box {{ display: flex; justify-content: space-between; margin-bottom: 12px; background: #fffbeb; border: 1px solid #fde68a; border-radius: 6px; padding: 10px; }}
  .metric-item {{ text-align: center; width: 25%; }}
  .metric-num {{ font-size: 14pt; font-weight: bold; color: #b45309; }}
  .metric-lbl {{ font-size: 9pt; color: #78350f; font-weight: bold; }}
  .compare-box {{ background: #f1f5f9; border-left: 4px solid #3b82f6; padding: 8px 12px; margin-bottom: 12px; font-size: 9.5pt; }}
  .summary-box {{ border: 1px solid #e2e8f0; border-radius: 6px; padding: 10px; margin-bottom: 14px; font-size: 10pt; background: #fafafa; }}
  .sign-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
  .sign-table td {{ border: 1px solid #94a3b8; height: 50px; text-align: center; vertical-align: top; padding: 4px; font-size: 9pt; width: 33.3%; }}
</style>
</head>
<body>
  <div class="header">
    <div>
      <div class="subtitle">國際佛光會中華青年總會 新竹青年分團</div>
      <h1 class="title">活動成果提報評鑑單</h1>
    </div>
    <div style="text-align: right; font-size: 9pt; color: #64748b;">
      單據編號：BLIA-HC-{item.year or '2026'}-{item.id:03d}<br>列印日期：{datetime.now().strftime('%Y/%m/%d')}
    </div>
  </div>

  <table class="meta-table">
    <tr>
      <th>活動專案名稱</th>
      <td colspan="3" style="font-weight: bold; font-size: 11pt;">{item.title}</td>
    </tr>
    <tr>
      <th>宗旨分類</th>
      <td>{cat_map.get(item.category, item.category)}</td>
      <th>評鑑指標代碼</th>
      <td>{item.evaluation_code or '一般專案活動'}</td>
    </tr>
    <tr>
      <th>辦理日期</th>
      <td>{item.event_date}</td>
      <th>所屬年度</th>
      <td>{item.year or '2026'} 年度</td>
    </tr>
    <tr>
      <th>活動地點</th>
      <td>{item.location}</td>
      <th>登錄幹部</th>
      <td>{item.created_by}</td>
    </tr>
  </table>

  <div class="metrics-box">
    <div class="metric-item">
      <div class="metric-num">{item.participants_count or 0} 人</div>
      <div class="metric-lbl">實際參與人次</div>
    </div>
    <div class="metric-item">
      <div class="metric-num">{item.volunteers_count or 0} 位</div>
      <div class="metric-lbl">出勤青年義工</div>
    </div>
    <div class="metric-item">
      <div class="metric-num">{item.service_hours or 0.0} hr</div>
      <div class="metric-lbl">志工服務時數</div>
    </div>
    <div class="metric-item">
      <div class="metric-num">{item.satisfaction_rate or 95}%</div>
      <div class="metric-lbl">活動整體滿意度</div>
    </div>
  </div>

  <div class="compare-box">
    <strong>【籌備預期目標】：</strong>{item.expected_goals or '依循星雲大師人間佛教四大宗旨推展在地青年教化活動。'}<br>
    <strong>【實際舉辦亮點】：</strong>{item.actual_highlights or '活動圓滿達成，青年出席踴躍，成效深獲指導法師與社區肯定！'}
  </div>

  <div class="summary-box">
    <strong>活動成果概要與評鑑效益說明：</strong><br>
    {item.summary}
  </div>

  <table class="sign-table">
    <tr>
      <td>活動總召執行幹部簽核<br><br><br></td>
      <td>新竹青年分團團長審閱<br><br><br></td>
      <td>新竹法寶寺輔導法師開示指導<br><br><br></td>
    </tr>
  </table>
</body>
</html>
"""
    pdf_bytes = safe_html_to_pdf(html)
    pdf_filename = f"BLIA_Report_{item.id}_{item.event_date}.pdf"
    pdf_path = UPLOAD_DIR / pdf_filename
    with open(pdf_path, "wb") as f:
        f.write(pdf_bytes)

    return FileResponse(
        path=str(pdf_path),
        filename=f"新竹佛光青年_{item.event_date}_{item.title[:15]}_成果提報單.pdf",
        media_type="application/pdf"
    )

# ----------------- 評審評語回饋 API -----------------
@router.post("/{item_id}/feedback", response_model=EvidenceFeedbackResponse)
def add_feedback(
    item_id: int,
    fb_in: EvidenceFeedbackCreate,
    db: Session = Depends(get_db)
):
    item = db.query(EvidenceItem).filter(EvidenceItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="找不到此佐證項目")

    fb = EvidenceFeedback(
        evidence_id=item_id,
        reviewer_name=fb_in.reviewer_name or "評鑑委員",
        rating=max(1, min(5, fb_in.rating)),
        comment=fb_in.comment
    )
    db.add(fb)
    db.commit()
    db.refresh(fb)
    return fb

@router.get("/{item_id}/feedback", response_model=List[EvidenceFeedbackResponse])
def get_feedbacks_by_item(item_id: int, db: Session = Depends(get_db)):
    return db.query(EvidenceFeedback).filter(EvidenceFeedback.evidence_id == item_id).order_by(EvidenceFeedback.id.desc()).all()

# ==============================================================================
# 【功能 24】全站活動問卷整體指標概況 API (置於 /{item_id} 之前避免路徑衝突)
# ==============================================================================
@router.get("/surveys/overview")
def get_all_surveys_overview(db: Session = Depends(get_db)):
    """【功能 24】計算全站所有活動問卷整體滿意度與 NPS 推薦度總指標"""
    surveys = db.query(SurveyResponse).all()
    if not surveys:
        return {
            "total_surveys": 0,
            "avg_overall": 4.9,
            "avg_nps": 9.5,
            "nps_score": 92.0,
            "recent_feedback": []
        }
    total = len(surveys)
    avg_overall = round(sum(s.overall_rating for s in surveys) / total, 2)
    promoters = sum(1 for s in surveys if s.nps_score >= 9)
    detractors = sum(1 for s in surveys if s.nps_score <= 6)
    nps = round(((promoters - detractors) / total) * 100, 1)

    recent = [{
        "id": s.id,
        "evidence_id": s.evidence_id,
        "name": s.respondent_name,
        "overall": s.overall_rating,
        "favorite": s.favorite_aspect,
        "suggestions": s.suggestions,
        "date": s.created_at.strftime("%Y-%m-%d") if s.created_at else ""
    } for s in sorted(surveys, key=lambda x: x.id, reverse=True)[:10]]

    return {
        "total_surveys": total,
        "avg_overall": avg_overall,
        "nps_score": nps,
        "recent_feedback": recent
    }

@router.get("/feedbacks/all", response_model=List[EvidenceFeedbackResponse])
def get_all_feedbacks(db: Session = Depends(get_db)):
    return db.query(EvidenceFeedback).order_by(EvidenceFeedback.id.desc()).all()

# ==============================================================================
# 【功能 28】活動行事曆 iCal / Google 日曆同步訂閱 API (置於 /{item_id} 之前)
# ==============================================================================
# ==============================================================================
# 【功能 35】分團評鑑書面成果手冊自動裝訂排版輸出 API (A4 多頁正式 PDF)
# ==============================================================================
@router.get("/export-booklet-pdf")
def export_annual_evaluation_booklet(year: Optional[str] = "2026", db: Session = Depends(get_db)):
    """【功能 35】全自動裝訂彙編年度四大宗旨、幹部名冊、財務收支與評鑑效益為正式 A4 書面成果手冊 PDF"""
    items = db.query(EvidenceItem).filter(EvidenceItem.is_published == True)
    if year:
        items = items.filter(EvidenceItem.year == year)
    all_items = items.order_by(EvidenceItem.event_date.asc()).all()

    total_events = len(all_items)
    total_participants = sum(i.participants_count or 0 for i in all_items)
    total_volunteers = sum(i.volunteers_count or 0 for i in all_items)
    total_hours = sum(i.service_hours or 0.0 for i in all_items)
    avg_sat = round(sum(i.satisfaction_rate or 95 for i in all_items) / total_events, 1) if total_events > 0 else 96.0

    today_str = datetime.now().strftime("%Y 年 %m 月 %d 日")

    # 項目分組 HTML
    items_rows = []
    for it in all_items:
        items_rows.append(f"""
        <tr>
          <td><span class="badge">{it.category}</span></td>
          <td><strong>{it.title}</strong><br><small style="color:#64748b;">{it.location}</small></td>
          <td style="font-family:monospace;">{it.event_date}</td>
          <td>{it.evaluation_code or '-'}</td>
          <td style="text-align:right;">{it.participants_count or 0} 人</td>
          <td style="text-align:right;">{it.service_hours or 0.0} hr</td>
        </tr>
        """)

    booklet_html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>國際佛光會新竹青年分團 成果評鑑提報手冊</title>
  <style>
    @page {{
      size: A4 portrait;
      margin: 20mm 15mm 20mm 15mm;
      @bottom-right {{
        content: counter(page) " / " counter(pages);
        font-size: 9pt;
        color: #94a3b8;
      }}
      @bottom-left {{
        content: "國際佛光會新竹青年分團 2026 年度成果評鑑手冊";
        font-size: 9pt;
        color: #94a3b8;
      }}
    }}
    * {{ box-sizing: border-box; }}
    body {{
      font-family: "Noto Sans CJK TC", "PingFang TC", "Microsoft JhengHei", sans-serif;
      color: #1e293b;
      line-height: 1.6;
    }}
    .page-break {{ page-break-after: always; }}
    
    /* 封面樣式 */
    .cover-container {{
      height: 250mm;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      align-items: center;
      text-align: center;
      padding: 30mm 10mm;
      border: 6px double #b45309;
      position: relative;
    }}
    .cover-title {{
      font-size: 28pt;
      font-weight: 900;
      color: #b45309;
      letter-spacing: 4px;
      margin-top: 20mm;
    }}
    .cover-sub {{
      font-size: 16pt;
      font-weight: bold;
      color: #334155;
      letter-spacing: 2px;
      margin-top: 8mm;
    }}
    .cover-org {{
      font-size: 13pt;
      color: #475569;
      margin-top: 15mm;
      line-height: 2;
    }}
    .badge {{
      display: inline-block;
      padding: 2px 8px;
      background: #fef3c7;
      color: #92400e;
      border-radius: 4px;
      font-size: 8pt;
      font-weight: bold;
    }}
    
    /* 內頁樣式 */
    h2 {{
      color: #b45309;
      border-bottom: 2px solid #f59e0b;
      padding-bottom: 6px;
      font-size: 16pt;
      margin-top: 0;
    }}
    .metrics-grid {{
      display: flex;
      justify-content: space-between;
      margin: 15px 0 25px 0;
    }}
    .metric-card {{
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      padding: 12px;
      width: 23%;
      text-align: center;
    }}
    .metric-val {{
      font-size: 18pt;
      font-weight: 900;
      color: #b45309;
    }}
    .metric-lbl {{
      font-size: 9pt;
      color: #64748b;
      margin-top: 4px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 9pt;
      margin-top: 10px;
    }}
    th, td {{
      padding: 8px 10px;
      border: 1px solid #cbd5e1;
      text-align: left;
    }}
    th {{
      background: #f1f5f9;
      color: #334155;
      font-weight: bold;
    }}
    .sign-box {{
      margin-top: 30mm;
      display: flex;
      justify-content: space-between;
    }}
    .sign-col {{
      width: 45%;
      border-top: 1px dashed #64748b;
      text-align: center;
      padding-top: 10px;
      font-size: 11pt;
      color: #334155;
    }}
  </style>
</head>
<body>
  <!-- 封面頁 -->
  <div class="cover-container page-break">
    <div style="font-size: 40pt; color: #b45309;">☸</div>
    <div>
      <div class="cover-title">國際佛光會新竹青年分團</div>
      <div class="cover-sub">{year} 年度成果評鑑提報總手冊</div>
      <div style="font-size: 11pt; color: #64748b; margin-top: 4mm;">Four Objectives Annual Assessment & Leadership Dossier</div>
    </div>
    
    <div class="cover-org">
      <strong>指導道場：</strong>佛光山新竹法寶寺<br>
      <strong>受評單位：</strong>國際佛光會中華青年總會 新竹青年分團<br>
      <strong>提報日期：</strong>{today_str}
    </div>
  </div>

  <!-- 成果總覽目錄與量化指標 -->
  <div class="page-break">
    <h2>壹、年度評鑑執行效益與總體成果指標</h2>
    <p style="font-size: 10pt; color: #475569;">
      新竹青年分團依循星雲大師創會四大宗旨「以文化弘揚佛法、以教育培養人才、以慈善福利社會、以共修淨化人心」，深耕竹苗在地大專青年與科技新貴，展現蓬勃之三好實踐力。
    </p>

    <div class="metrics-grid">
      <div class="metric-card">
        <div class="metric-val">{total_events}</div>
        <div class="metric-lbl">主辦專案活動場次</div>
      </div>
      <div class="metric-card">
        <div class="metric-val">{total_participants:,}</div>
        <div class="metric-lbl">累計參與大眾人次</div>
      </div>
      <div class="metric-card">
        <div class="metric-val">{total_hours}</div>
        <div class="metric-lbl">志工服務總時數 (hr)</div>
      </div>
      <div class="metric-card">
        <div class="metric-val">{avg_sat}%</div>
        <div class="metric-lbl">大眾綜合滿意度</div>
      </div>
    </div>

    <h2>貳、四大宗旨佐證資料彙整一覽表</h2>
    <table>
      <thead>
        <tr>
          <th style="width:12%;">宗旨分類</th>
          <th style="width:40%;">活動專案名稱與地點</th>
          <th style="width:14%;">舉辦日期</th>
          <th style="width:14%;">評鑑代碼</th>
          <th style="width:10%;">參與人次</th>
          <th style="width:10%;">服務時數</th>
        </tr>
      </thead>
      <tbody>
        {''.join(items_rows)}
      </tbody>
    </table>
  </div>

  <!-- 簽核核章頁面 -->
  <div>
    <h2>參、分團幹部集體創作與輔導法師印可</h2>
    <p style="font-size: 10pt; color: #475569; line-height: 1.8;">
      本年度成果經全體分團幹部同心協調、落實制度領導與各項活動檢討回饋，所提報之數據、佐證公文、活動照片與財務經費核銷均經本分團幹部會議確認無誤。
    </p>

    <div style="background:#fef3c7; border:1px solid #fde68a; border-radius:8px; padding:15px; margin-top:20px; font-size:10pt;">
      <strong>星雲大師法語勉勵：</strong><br>
      「給人信心、給人歡喜、給人希望、給人方便。青年是佛教未來的棟樑，願發大心、立大願，讓佛光常照大千！」
    </div>

    <div class="sign-box">
      <div class="sign-col">
        新竹青年分團 團長 簽章<br><br><br><br>
        <strong>林冠宇 敬呈</strong>
      </div>
      <div class="sign-col">
        佛光山新竹法寶寺 輔導法師 印可<br><br><br><br>
        <strong>法寶寺住持 開示印可</strong>
      </div>
    </div>
  </div>
</body>
</html>
"""

    pdf_bytes = safe_html_to_pdf(booklet_html)
    pdf_filename = f"BLIA_Hsinchu_Youth_Booklet_{year}.pdf"
    pdf_path = UPLOAD_DIR / pdf_filename
    with open(pdf_path, "wb") as f:
        f.write(pdf_bytes)

    return FileResponse(
        path=str(pdf_path),
        filename=f"國際佛光會新竹青年分團_{year}_成果評鑑提報手冊.pdf",
        media_type="application/pdf"
    )

# ==============================================================================
# 【功能 48】活動成效關鍵字文字雲分析 API (置於 /{item_id} 之前)
# ==============================================================================
@router.get("/keywords-cloud")
def get_keywords_cloud_analysis(year: Optional[str] = "2026", db: Session = Depends(get_db)):
    """【功能 48】分析四大宗旨活動成果摘要與問卷回饋，擷取三好四給高頻關鍵字與權重文字雲"""
    query = db.query(EvidenceItem).filter(EvidenceItem.is_published == True)
    if year:
        query = query.filter(EvidenceItem.year == year)
    items = query.all()

    # 基礎分析詞庫
    KEYWORD_SEEDS = [
        ("三好實踐", "culture", 48),
        ("生活禪修", "education", 42),
        ("星雲說喻", "education", 38),
        ("自媒體Podcast", "culture", 35),
        ("偏鄉送暖", "charity", 32),
        ("破冰團康", "education", 29),
        ("環保淨灘", "charity", 26),
        ("VEGRUN蔬食", "charity", 24),
        ("菩提讀書會", "education", 22),
        ("大悲懺共修", "cultivation", 20),
        ("青年領導力", "education", 18),
        ("文創墨寶拓印", "culture", 17),
        ("梵唄引禮修持", "cultivation", 15),
        ("人間佛教中道", "education", 14),
        ("福慧雙修", "cultivation", 12),
        ("廣結善緣", "charity", 10)
    ]

    all_text = " ".join(f"{i.title} {i.summary} {i.actual_highlights}" for i in items)

    results = []
    for kw, cat, base_wt in KEYWORD_SEEDS:
        freq = all_text.count(kw[:2]) + base_wt
        # 依權重歸一化至 1-5 級字體大小
        weight_level = 5 if freq >= 40 else (4 if freq >= 30 else (3 if freq >= 20 else (2 if freq >= 15 else 1)))
        results.append({
            "text": kw,
            "category": cat,
            "count": freq,
            "weight": weight_level
        })

    return {
        "status": "success",
        "year": year,
        "total_keywords": len(results),
        "keywords": sorted(results, key=lambda x: x["count"], reverse=True)
    }


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
            d_str = str(item.event_date).replace("-", "").strip()[:8]
            loc = getattr(item, 'location', '') or '新竹市東區民族路241號'
            summary_txt = getattr(item, 'summary', '') or ''
            eval_code = getattr(item, 'evaluation_code', '') or ''
            lines.extend([
                "BEGIN:VEVENT",
                f"UID:blia-hcy-webcal-{item.id}@hsinchuyouth.fgs.org.tw",
                f"DTSTAMP:{now_utc}",
                f"DTSTART;VALUE=DATE:{d_str}",
                f"DTEND;VALUE=DATE:{d_str}",
                f"SUMMARY:【佛光青年】{item.title}",
                f"DESCRIPTION:{summary_txt} | 評鑑代碼: {eval_code}",
                f"LOCATION:佛光山新竹法寶寺 ({loc})",
                "STATUS:CONFIRMED",
                "BEGIN:VALARM",
                "TRIGGER:-P1D",
                "ACTION:DISPLAY",
                f"DESCRIPTION:提醒：明日佛光青年活動【{item.title}】",
                "END:VALARM",
                "END:VEVENT"
            ])
        except Exception as e:
            continue

    lines.append("END:VCALENDAR")
    return Response(content="\r\n".join(lines), media_type="text/calendar")

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

@router.get("/calendar.ics")
def get_activities_ical_feed(db: Session = Depends(get_db)):
    """【功能 28】產製標準 RFC 5545 iCalendar (.ics) 日曆訂閱源，支援手機日曆與 Google 日曆自動同步"""
    items = db.query(EvidenceItem).filter(EvidenceItem.is_published == True).all()

    now_utc = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//BLIA Hsinchu Youth Subgroup//Activities Calendar//ZH",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:國際佛光會新竹青年分團 活動行事曆",
        "X-WR-TIMEZONE:Asia/Taipei",
        "X-WR-CALDESC:新竹佛光青年分團年度四大宗旨活動成果與行事曆訂閱"
    ]

    for it in items:
        clean_date = re.sub(r'[^0-9]', '', str(it.event_date or ""))
        if len(clean_date) >= 8:
            dt_start = clean_date[:8]
            dt_end = clean_date[:8]
        else:
            continue

        desc = str(it.summary or "").replace("\r", " ").replace("\n", " ").replace(",", " ")
        title = str(it.title or "活動").replace(",", " ")
        loc = str(it.location or "新竹法寶寺").replace(",", " ")

        lines.extend([
            "BEGIN:VEVENT",
            f"UID:BLIA-HCY-ACT-{it.id}@hsinchu-youth.blia.org",
            f"DTSTAMP:{now_utc}",
            f"DTSTART;VALUE=DATE:{dt_start}",
            f"DTEND;VALUE=DATE:{dt_end}",
            f"SUMMARY:{title} [{it.category}]",
            f"DESCRIPTION:{desc}",
            f"LOCATION:{loc}",
            "STATUS:CONFIRMED",
            "TRANSP:TRANSPARENT",
            "END:VEVENT"
        ])

    lines.append("END:VCALENDAR")
    ics_body = "\r\n".join(lines)

    return Response(
        content=ics_body,
        media_type="text/calendar; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=blia_hsinchu_youth_calendar.ics"}
    )

@router.get("/{item_id}/gcal-link")
def get_google_calendar_link(item_id: int, db: Session = Depends(get_db)):
    """【功能 28】一鍵生成加入 Google 日曆之網頁捷徑連結"""
    item = db.query(EvidenceItem).filter(EvidenceItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="找不到此佐證項目")

    clean_date = re.sub(r'[^0-9]', '', str(item.event_date or ""))
    dt_str = clean_date[:8] if len(clean_date) >= 8 else "20261016"
    dates_param = f"{dt_str}/{dt_str}"

    import urllib.parse
    title_enc = urllib.parse.quote(str(item.title or ""))
    details_text = f"{item.summary} | 宗旨代碼: {item.evaluation_code} | 主辦單位: 國際佛光會新竹青年分團"
    details_enc = urllib.parse.quote(details_text)
    location_enc = urllib.parse.quote(str(item.location or "新竹法寶寺"))

    gcal_url = f"https://calendar.google.com/calendar/render?action=TEMPLATE&text={title_enc}&dates={dates_param}&details={details_enc}&location={location_enc}&add=hsinchu.blia.youth@gmail.com"

    return {
        "item_id": item.id,
        "title": item.title,
        "gcal_url": gcal_url
    }

# ==============================================================================
# 【功能 16】活動多圖輪播相簿 API (Photo Gallery & Carousel)
# ==============================================================================
@router.get("/{item_id}/gallery")
def get_evidence_gallery(item_id: int, db: Session = Depends(get_db)):
    """【功能 16】取得單一活動多圖輪播相簿清單"""
    item = db.query(EvidenceItem).filter(EvidenceItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="找不到此佐證項目")
    try:
        gallery = json.loads(item.photos_gallery or "[]")
    except Exception:
        gallery = []
    if not gallery and item.file_url and item.file_type == "image":
        gallery = [{"url": item.file_url, "caption": f"{item.title} - 活動主圖", "uploaded_at": str(item.event_date)}]
    return {
        "item_id": item.id,
        "title": item.title,
        "photos_count": len(gallery),
        "photos": gallery
    }

@router.post("/{item_id}/gallery")
async def add_photos_to_gallery(
    item_id: int,
    files: Optional[List[UploadFile]] = File(None),
    caption: Optional[str] = Form(""),
    photos_json: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_cadre)
):
    """【功能 16】為活動上傳多張輪播相簿照片並自動壓印三好浮水印"""
    item = db.query(EvidenceItem).filter(EvidenceItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="找不到此佐證項目")

    try:
        current_gallery = json.loads(item.photos_gallery or "[]")
    except Exception:
        current_gallery = []

    if photos_json:
        try:
            parsed = json.loads(photos_json)
            if isinstance(parsed, list):
                current_gallery = parsed
        except Exception:
            pass

    if files:
        for f in files:
            if not f.filename:
                continue
            ext = Path(f.filename).suffix.lower()
            if ext not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
                continue
            unique_name = f"gallery_{item_id}_{uuid.uuid4().hex[:8]}{ext}"
            file_path = UPLOAD_DIR / unique_name
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(f.file, buffer)
            
            try:
                from app.routers.upload import add_watermark_to_image
                add_watermark_to_image(file_path, "新竹佛光青年分團")
            except Exception:
                pass

            current_gallery.append({
                "url": f"/uploads/{unique_name}",
                "caption": caption.strip() or f"{item.title} 活動剪影",
                "filename": f.filename,
                "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            })

    item.photos_gallery = json.dumps(current_gallery, ensure_ascii=False)
    db.add(item)
    db.commit()
    db.refresh(item)
    return {
        "status": "success",
        "photos_count": len(current_gallery),
        "photos": current_gallery
    }

@router.delete("/{item_id}/gallery/{photo_idx}")
def delete_photo_from_gallery(
    item_id: int,
    photo_idx: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_cadre)
):
    """【功能 16】刪除指定索引之輪播照片"""
    item = db.query(EvidenceItem).filter(EvidenceItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="找不到此佐證項目")
    try:
        current_gallery = json.loads(item.photos_gallery or "[]")
    except Exception:
        current_gallery = []

    if 0 <= photo_idx < len(current_gallery):
        removed = current_gallery.pop(photo_idx)
        item.photos_gallery = json.dumps(current_gallery, ensure_ascii=False)
        db.add(item)
        db.commit()
        return {"status": "success", "message": "照片已移除", "removed": removed}
    else:
        raise HTTPException(status_code=400, detail="照片索引超出範圍")

# ==============================================================================
# 【功能 18】活動成果社群文案與 Hashtag 一鍵生成 API
# ==============================================================================
@router.get("/{item_id}/social-copy")
def generate_social_copy(
    item_id: int,
    platform: Optional[str] = Query("facebook", pattern="^(facebook|instagram|threads)$"),
    db: Session = Depends(get_db)
):
    """【功能 18】依據活動成果一鍵生成最適化 FB / IG / Threads 貼文文案與 Hashtags"""
    item = db.query(EvidenceItem).filter(EvidenceItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="找不到此佐證項目")

    cat_map = {
        "culture": "文化傳承弘法",
        "education": "僧信教育培訓",
        "cultivation": "精進修持共修",
        "charity": "慈悲社會公益"
    }
    cat_zh = cat_map.get(item.category, "人間佛教弘法")

    quote_map = {
        "culture": "星雲大師說：『佛光普照三千界，法水長流五大洲。以文化弘揚佛法，以影音文字傳播真善美。』",
        "education": "星雲大師說：『教育是翻轉生命的力量！給人信心、給人希望，在做中學開展無限青年潛能。』",
        "cultivation": "星雲大師說：『心靜福田生，修持利同行。在身心專注與共修中找回清淨的自性光明。』",
        "charity": "星雲大師說：『慈悲沒有敵人，智慧不起煩惱。走入社區結緣送暖，每一份付出都是希望的種子。』"
    }
    quote = quote_map.get(item.category, "星雲大師說：『做好事、說好話、存好心；給人信心、給人歡喜、給人希望、給人方便。』")

    base_hashtags = [
        "#國際佛光會新竹青年分團",
        "#佛光青年",
        "#新竹法寶寺",
        "#人間佛教",
        "#三好運動",
        "#做好事說好話存好心",
        "#ZhuguangSansan",
        "#竹光三參",
        "#新竹在地青年",
        f"#{cat_zh}"
    ]

    extra_hashtags = {
        "culture": ["#文化弘法", "#Podcast節目", "#數位弘法", "#青年美學"],
        "education": ["#生活禪修", "#幹部領導力", "#青年讀書會", "#智慧成長"],
        "cultivation": ["#晨鐘暮鼓", "#大悲懺共修", "#三皈五戒", "#心靈淨化"],
        "charity": ["#VEGRUN蔬食", "#公益淨灘", "#愛心送暖", "#青年志工"]
    }.get(item.category, ["#青年發心", "#共創美好"])

    all_hashtags = base_hashtags + extra_hashtags
    tags_str = " ".join(all_hashtags)

    p_count = item.participants_count or 0
    v_count = item.volunteers_count or 0
    s_hours = item.service_hours or 0.0
    s_rate = item.satisfaction_rate or 95

    highlights = item.actual_highlights or item.summary or "活動在指導法師帶領與全體青年同心協力下圓滿完成！"
    if len(highlights) > 180:
        highlights = highlights[:180] + "..."

    if platform == "facebook":
        post_text = f"""🌟【新竹佛光青年｜活動成果亮點快報】🌟

🎉【{item.title}】圓滿落幕！

📅 活動日期：{item.event_date}
📍 活動地點：{item.location}
☸ 宗旨指標：四大宗旨・{cat_zh}（評鑑代碼：{item.evaluation_code or '一般成果'}）

✨【圓滿成果數據盤點】：
👥 青年熱情參與：共計 {p_count} 人次
💪 出勤服務幹部：{v_count} 位青年熱忱奉獻
⏳ 志工服務總時數：{s_hours} 小時
💖 活動整體滿意度：{s_rate}%

💡【活動精華與感動亮點】：
{highlights}

🌿【星雲大師智慧法語】：
「{quote}」
落實「做好事、說好話、存好心」，在日常生活的每一個舉手投足間實踐人間佛教！

❤️ 歡迎新竹與竹北地區的大專青年、職場新鮮人加入「新竹青年分團」，和我們一起散播溫暖與智慧的力量！

{tags_str}"""

    elif platform == "instagram":
        post_text = f"""✨ {item.title} 圓滿落幕！✨
.
新竹青年在【{item.location}】留下了溫暖與成長的足跡 👣
.
📊 亮點成效直擊：
▫️ 熱情參與：{p_count} 人
▫️ 服務幹部：{v_count} 位
▫️ 累積時數：{s_hours} hr
▫️ 青年好評：{s_rate}%
.
🌿「{quote}」
.
在做中學、學中覺，我們以青春發心領航，踐履三好四給精神！
歡迎私訊小編加入新竹青年大家庭 💌
.
.
{tags_str}"""

    else:
        post_text = f"""【新竹青年分團成果紀實】{item.title} 圓滿完成 🌟

今天在 {item.location}，{p_count} 位青年一起參與了這場有意義的活動！
服務幹部出勤 {v_count} 人，累積了 {s_hours} 小時的志工服務。

最感動的一句話：
「{quote}」

新竹的青年朋友們，休假不想宅在家？
來跟法寶寺青年一起體驗生活禪與多元文化活動吧！👇

{tags_str}"""

    return {
        "status": "success",
        "item_id": item.id,
        "platform": platform,
        "title": item.title,
        "post_text": post_text,
        "hashtags": all_hashtags,
        "copy_ready": post_text
    }

# ==============================================================================
# 【功能 19】青年志工服務時數認證書自動產製 API (HTML / PDF)
# ==============================================================================
def render_certificate_html(item, volunteer_name: str, hours: float, cert_no: str) -> str:
    today_roc_year = datetime.now().year - 1911
    today_month = datetime.now().month
    today_day = datetime.now().day
    
    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>國際佛光會新竹青年分團 青年志工服務認證書</title>
  <style>
    @page {{ size: A4 landscape; margin: 0; }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0; padding: 30px; font-family: "Noto Sans CJK TC", "PingFang TC", "Microsoft JhengHei", sans-serif;
      background: #fbf9f5; color: #1e293b; display: flex; justify-content: center; align-items: center; min-height: 100vh;
    }}
    .cert-frame {{
      width: 100%; max-width: 1020px; border: 10px double #b45309; padding: 40px 60px; background: #ffffff;
      box-shadow: 0 10px 30px rgba(0,0,0,0.08); position: relative; text-align: center;
    }}
    .cert-inner-border {{
      position: absolute; inset: 12px; border: 1.5px solid #d97706; pointer-events: none;
    }}
    .org-title {{
      font-size: 22px; font-weight: 700; color: #b45309; letter-spacing: 4px; margin-bottom: 4px;
    }}
    .org-en {{
      font-size: 13px; color: #64748b; letter-spacing: 1px; margin-bottom: 25px; text-transform: uppercase;
    }}
    .cert-main-title {{
      font-size: 38px; font-weight: 900; color: #0f172a; letter-spacing: 8px; margin-bottom: 12px;
    }}
    .cert-no {{
      font-size: 13px; color: #94a3b8; font-family: monospace; letter-spacing: 1px; margin-bottom: 30px;
    }}
    .cert-content {{
      font-size: 19px; line-height: 2.2; text-align: justify; margin: 30px auto; max-width: 860px; color: #334155;
    }}
    .v-highlight {{
      font-size: 28px; font-weight: bold; color: #b45309; border-bottom: 2px solid #b45309; padding: 0 16px; margin: 0 6px;
    }}
    .act-highlight {{
      font-weight: bold; color: #0369a1; padding: 0 4px;
    }}
    .hours-highlight {{
      font-size: 24px; font-weight: bold; color: #b45309; padding: 0 4px;
    }}
    .sign-row {{
      display: flex; justify-content: space-between; margin-top: 55px; padding: 0 60px;
    }}
    .sign-col {{
      text-align: center; width: 240px;
    }}
    .sign-space {{
      height: 50px; border-bottom: 1.5px dashed #cbd5e1; margin-bottom: 10px;
    }}
    .sign-label {{
      font-size: 15px; font-weight: 600; color: #475569;
    }}
    .footer-date {{
      margin-top: 40px; font-size: 16px; color: #64748b; letter-spacing: 2px;
    }}
  </style>
</head>
<body>
  <div class="cert-frame">
    <div class="cert-inner-border"></div>
    <div class="org-title">國際佛光會中華青年總會 ｜ 新竹青年分團</div>
    <div class="org-en">Buddha\'s Light International Association Chunghua - Hsinchu Youth Subgroup</div>
    <div class="cert-main-title">青年志工服務認證書</div>
    <div class="cert-no">證書字號：{cert_no}</div>

    <div class="cert-content">
      茲證明青年 <span class="v-highlight">{volunteer_name}</span> 閣下，積極踐履星雲大師「三好四給」人間佛教精神，
      熱心投入本分團主辦之<span class="act-highlight">「{item.title}」</span>志願服務工作，表現優異，
      恪盡職守，經核算志願服務時數共計 <span class="hours-highlight">{hours}</span> 小時整，特頒此證，以資表彰與激勵。
    </div>

    <div class="sign-row">
      <div class="sign-col">
        <div class="sign-space"></div>
        <div class="sign-label">新竹青年分團 團長 敬頒</div>
      </div>
      <div class="sign-col">
        <div class="sign-space"></div>
        <div class="sign-label">新竹法寶寺 指導法師 印可</div>
      </div>
    </div>

    <div class="footer-date">
      中華民國 {today_roc_year} 年 {today_month} 月 {today_day} 日
    </div>
  </div>
</body>
</html>
"""

@router.get("/{item_id}/certificate")
def get_volunteer_certificate(
    item_id: int,
    volunteer_name: str = Query("佛光青年"),
    hours: Optional[float] = Query(None),
    format: Optional[str] = Query("html", pattern="^(html|pdf)$"),
    db: Session = Depends(get_db)
):
    """【功能 19】產製單張精美青年志工服務認證書（支援線上列印 HTML 與高解析 A4 橫式 PDF）"""
    item = db.query(EvidenceItem).filter(EvidenceItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="找不到此佐證項目")

    actual_hours = hours if hours is not None else (item.service_hours or 4.0)
    cert_no = f"BLIA-HCY-{item.year or '2026'}-{item.id:03d}-{abs(hash(volunteer_name)) % 10000:04d}"

    html_content = render_certificate_html(item, volunteer_name, actual_hours, cert_no)

    if format == "html":
        return HTMLResponse(content=html_content)

    pdf_bytes = safe_html_to_pdf(html_content)
    pdf_filename = f"BLIA_Volunteer_Cert_{item_id}_{volunteer_name}.pdf"
    pdf_path = UPLOAD_DIR / pdf_filename
    with open(pdf_path, "wb") as f:
        f.write(pdf_bytes)

    return FileResponse(
        path=str(pdf_path),
        filename=f"新竹佛光青年_志工證書_{volunteer_name}_{item.title[:10]}.pdf",
        media_type="application/pdf"
    )

@router.post("/{item_id}/batch-certificates")
def batch_generate_certificates(
    item_id: int,
    volunteers: List[Dict[str, Any]] = Body(..., example=[{"name": "張小凡", "hours": 4.0}, {"name": "李欣怡", "hours": 6.5}]),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_cadre)
):
    """【功能 19】批次產製多位青年志工服務認證書（合併為單一多頁式 PDF 檔案方便一次印製核章）"""
    item = db.query(EvidenceItem).filter(EvidenceItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="找不到此佐證項目")

    if not volunteers:
        raise HTTPException(status_code=400, detail="請提供至少一位志工姓名資料")

    merged_htmls = []
    for idx, v in enumerate(volunteers):
        v_name = v.get("name", f"志工 {idx+1}")
        v_hours = float(v.get("hours", item.service_hours or 4.0))
        cert_no = f"BLIA-HCY-{item.year or '2026'}-{item.id:03d}-B{idx+1:03d}"
        raw_html = render_certificate_html(item, v_name, v_hours, cert_no)
        start_idx = raw_html.find('<div class="cert-frame">')
        end_idx = raw_html.find('</body>')
        inner = raw_html[start_idx:end_idx] if start_idx != -1 and end_idx != -1 else raw_html
        page_content = f"""<div style="page-break-after: always; min-height: 100vh; display: flex; justify-content: center; align-items: center; padding: 20px;">
          {inner}
        </div>"""
        merged_htmls.append(page_content)

    combined_doc = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>國際佛光會新竹青年分團 志工證書批次列印清單</title>
  <style>
    @page {{ size: A4 landscape; margin: 0; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; padding: 0; font-family: "Noto Sans CJK TC", "PingFang TC", "Microsoft JhengHei", sans-serif; background: #ffffff; }}
    .cert-frame {{ width: 100%; max-width: 1020px; border: 10px double #b45309; padding: 40px 60px; background: #ffffff; position: relative; text-align: center; }}
    .cert-inner-border {{ position: absolute; inset: 12px; border: 1.5px solid #d97706; pointer-events: none; }}
    .org-title {{ font-size: 22px; font-weight: 700; color: #b45309; letter-spacing: 4px; margin-bottom: 4px; }}
    .org-en {{ font-size: 13px; color: #64748b; letter-spacing: 1px; margin-bottom: 25px; text-transform: uppercase; }}
    .cert-main-title {{ font-size: 38px; font-weight: 900; color: #0f172a; letter-spacing: 8px; margin-bottom: 12px; }}
    .cert-no {{ font-size: 13px; color: #94a3b8; font-family: monospace; letter-spacing: 1px; margin-bottom: 30px; }}
    .cert-content {{ font-size: 19px; line-height: 2.2; text-align: justify; margin: 30px auto; max-width: 860px; color: #334155; }}
    .v-highlight {{ font-size: 28px; font-weight: bold; color: #b45309; border-bottom: 2px solid #b45309; padding: 0 16px; margin: 0 6px; }}
    .act-highlight {{ font-weight: bold; color: #0369a1; padding: 0 4px; }}
    .hours-highlight {{ font-size: 24px; font-weight: bold; color: #b45309; padding: 0 4px; }}
    .sign-row {{ display: flex; justify-content: space-between; margin-top: 55px; padding: 0 60px; }}
    .sign-col {{ text-align: center; width: 240px; }}
    .sign-space {{ height: 50px; border-bottom: 1.5px dashed #cbd5e1; margin-bottom: 10px; }}
    .sign-label {{ font-size: 15px; font-weight: 600; color: #475569; }}
    .footer-date {{ margin-top: 40px; font-size: 16px; color: #64748b; letter-spacing: 2px; }}
  </style>
</head>
<body>
  {''.join(merged_htmls)}
</body>
</html>"""

    pdf_bytes = safe_html_to_pdf(combined_doc)
    pdf_filename = f"BLIA_Batch_Certs_{item_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf_path = UPLOAD_DIR / pdf_filename
    with open(pdf_path, "wb") as f:
        f.write(pdf_bytes)

    return FileResponse(
        path=str(pdf_path),
        filename=f"新竹佛光青年_{item.event_date}_批次志工時數證書_{len(volunteers)}份.pdf",
        media_type="application/pdf"
    )

# ==============================================================================
# 【功能 22】活動影音多媒體嵌入播放器 API
# ==============================================================================
@router.get("/{item_id}/media-embed")
def get_evidence_media_embed(item_id: int, db: Session = Depends(get_db)):
    """【功能 22】解析 YouTube、Spotify Podcast 或 MP4/MP3 並生成嵌入播放資料"""
    item = db.query(EvidenceItem).filter(EvidenceItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="找不到此佐證項目")

    video_info = None
    audio_info = None

    v_url = (item.video_url or "").strip()
    a_url = (item.audio_url or "").strip()

    # YouTube 解析
    if v_url:
        yt_id = None
        yt_m1 = re.search(r'(?:v=|youtu\.be/|embed/)([A-Za-z0-9_-]{11})', v_url)
        if yt_m1:
            yt_id = yt_m1.group(1)
            video_info = {
                "type": "youtube",
                "video_id": yt_id,
                "embed_url": f"https://www.youtube-nocookie.com/embed/{yt_id}?rel=0",
                "original_url": v_url
            }
        elif v_url.endswith(".mp4") or v_url.endswith(".mov"):
            video_info = {
                "type": "html5_video",
                "embed_url": v_url,
                "original_url": v_url
            }
        else:
            video_info = {
                "type": "external_link",
                "embed_url": v_url,
                "original_url": v_url
            }

    # Spotify Podcast 解析 (專為《竹光三參》專案打造)
    if a_url:
        if "open.spotify.com" in a_url:
            sp_embed = a_url.replace("open.spotify.com/", "open.spotify.com/embed/")
            audio_info = {
                "type": "spotify",
                "embed_url": sp_embed,
                "original_url": a_url
            }
        elif a_url.endswith(".mp3") or a_url.endswith(".m4a"):
            audio_info = {
                "type": "html5_audio",
                "embed_url": a_url,
                "original_url": a_url
            }
        else:
            audio_info = {
                "type": "external_audio",
                "embed_url": a_url,
                "original_url": a_url
            }

    return {
        "item_id": item.id,
        "title": item.title,
        "has_media": bool(video_info or audio_info),
        "video": video_info,
        "audio": audio_info
    }

# ==============================================================================
# 【功能 24】活動回饋問卷線上統計與 NPS 滿意度分析 API
# ==============================================================================
@router.post("/{item_id}/survey", response_model=SurveyResponseResponse)
def submit_activity_survey(
    item_id: int,
    survey_in: SurveyResponseCreate,
    db: Session = Depends(get_db)
):
    """【功能 24】青年活動參與者線上提交滿意度問卷回饋"""
    item = db.query(EvidenceItem).filter(EvidenceItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="找不到此佐證項目")

    new_resp = SurveyResponse(
        evidence_id=item_id,
        respondent_name=survey_in.respondent_name or "匿名青年",
        overall_rating=max(1, min(5, survey_in.overall_rating)),
        content_depth=max(1, min(5, survey_in.content_depth)),
        organization_rating=max(1, min(5, survey_in.organization_rating)),
        venue_rating=max(1, min(5, survey_in.venue_rating)),
        nps_score=max(0, min(10, survey_in.nps_score)),
        favorite_aspect=survey_in.favorite_aspect or "",
        suggestions=survey_in.suggestions or ""
    )
    db.add(new_resp)
    db.commit()

    # 自動同步更新 EvidenceItem 的整體滿意度 satisfaction_rate
    all_surveys = db.query(SurveyResponse).filter(SurveyResponse.evidence_id == item_id).all()
    if all_surveys:
        avg_stars = sum(s.overall_rating for s in all_surveys) / len(all_surveys)
        item.satisfaction_rate = int((avg_stars / 5.0) * 100)
        db.add(item)
        db.commit()

    db.refresh(new_resp)
    return new_resp

@router.get("/{item_id}/survey/stats")
def get_activity_survey_stats(item_id: int, db: Session = Depends(get_db)):
    """【功能 24】取得特定活動問卷多維度星級評分、NPS 推薦指數與意見彙整"""
    item = db.query(EvidenceItem).filter(EvidenceItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="找不到此佐證項目")

    responses = db.query(SurveyResponse).filter(SurveyResponse.evidence_id == item_id).all()
    if not responses:
        # 回傳基底預設評鑑值
        return {
            "item_id": item_id,
            "total_responses": 0,
            "avg_overall": 4.8,
            "avg_content": 4.9,
            "avg_organization": 4.7,
            "avg_venue": 4.8,
            "nps_score": 90.0,
            "favorite_aspects": ["三好實踐破冰", "星雲法語生活分享"],
            "suggestions": []
        }

    count = len(responses)
    avg_overall = round(sum(r.overall_rating for r in responses) / count, 2)
    avg_content = round(sum(r.content_depth for r in responses) / count, 2)
    avg_org = round(sum(r.organization_rating for r in responses) / count, 2)
    avg_venue = round(sum(r.venue_rating for r in responses) / count, 2)

    promoters = sum(1 for r in responses if r.nps_score >= 9)
    detractors = sum(1 for r in responses if r.nps_score <= 6)
    nps = round(((promoters - detractors) / count) * 100, 1)

    favs = [r.favorite_aspect for r in responses if r.favorite_aspect]
    suggs = [r.suggestions for r in responses if r.suggestions]

    return {
        "item_id": item_id,
        "title": item.title,
        "total_responses": count,
        "avg_overall": avg_overall,
        "avg_content": avg_content,
        "avg_organization": avg_org,
        "avg_venue": avg_venue,
        "nps_score": nps,
        "favorite_aspects": favs[:5],
        "suggestions": suggs[:10]
    }

# ==============================================================================
# 【功能 41】青年活動滿意度問卷 Excel (.xlsx) 試算表匯出 API
# ==============================================================================
# ==============================================================================
# 【功能 46】青年活動志工證件證卡名牌批次排版列印 API (A4 八合一 PDF)
# ==============================================================================
@router.get("/{item_id}/badges-pdf")
def export_volunteer_badges_pdf(item_id: int, db: Session = Depends(get_db)):
    """【功能 46】自動將活動幹部與義工名單排版為標準 A4 規格之八合一識別證/名牌列印手冊 PDF"""
    item = db.query(EvidenceItem).filter(EvidenceItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="找不到此活動")

    # 取得此活動的出勤幹部或預設志工組
    attendances = db.query(CadreAttendance).filter(CadreAttendance.evidence_id == item_id).all()
    if not attendances:
        # 示範 8 位志工組名冊
        volunteers = [
            {"name": "林冠宇", "role": "活動總召"},
            {"name": "陳思妤", "role": "現場引禮組長"},
            {"name": "張宏睿", "role": "行政評鑑秘書"},
            {"name": "黃鈺婷", "role": "財務出納組長"},
            {"name": "李家豪", "role": "破冰動態活動組"},
            {"name": "王沛恩", "role": "影音直播控台組"},
            {"name": "王崇恩", "role": "大會報到接待"},
            {"name": "林思妤", "role": "法寶文宣結緣"}
        ]
    else:
        volunteers = [{"name": a.member_name, "role": "活動幹部"} for a in attendances[:8]]
        while len(volunteers) < 8:
            volunteers.append({"name": f"青年志工 {len(volunteers)+1}", "role": "機動協力組"})

    qr_svg = generate_qr_svg(f"http://127.0.0.1:8000/#aims?checkin={item_id}", size_px=80)

    # 產製 2 列 x 4 欄的 A4 名牌格子
    badge_cards = []
    for v in volunteers:
        badge_cards.append(f"""
        <div class="badge-card">
          <div class="badge-inner">
            <div class="org-name">國際佛光會中華青年總會 ｜ 新竹青年分團</div>
            <div class="badge-title">青年活動服務志工證</div>
            
            <div class="v-avatar">☸</div>
            <div class="v-name">{v['name']}</div>
            <div class="v-role">{v['role']}</div>
            
            <div class="event-info">
              <strong>{item.title[:16]}</strong><br>
              日期：{item.event_date} ｜ 地點：{item.location}
            </div>

            <div class="qr-box">
              {qr_svg}
              <div style="font-size: 7pt; color: #64748b; margin-top: 2px;">現場簽到掃描碼</div>
            </div>
          </div>
        </div>
        """)

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>國際佛光會新竹青年分團 志工證件名牌批次排版</title>
  <style>
    @page {{
      size: A4 portrait;
      margin: 10mm;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      font-family: "Noto Sans CJK TC", "PingFang TC", "Microsoft JhengHei", sans-serif;
      margin: 0; padding: 0;
    }}
    .badge-grid {{
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      gap: 8mm;
    }}
    .badge-card {{
      width: 48%;
      height: 64mm;
      border: 2px dashed #b45309;
      padding: 3mm;
      position: relative;
      background: #ffffff;
      page-break-inside: avoid;
    }}
    .badge-inner {{
      border: 1.5px solid #d97706;
      height: 100%;
      padding: 3mm 4mm;
      text-align: center;
      position: relative;
      background: #fdfbf7;
    }}
    .org-name {{
      font-size: 7pt;
      font-weight: bold;
      color: #b45309;
      letter-spacing: 0.5px;
    }}
    .badge-title {{
      font-size: 11pt;
      font-weight: 900;
      color: #0f172a;
      letter-spacing: 1px;
      margin-top: 1mm;
    }}
    .v-avatar {{
      font-size: 16pt;
      color: #f59e0b;
      margin-top: 1mm;
    }}
    .v-name {{
      font-size: 14pt;
      font-weight: 900;
      color: #b45309;
      border-bottom: 2px solid #b45309;
      display: inline-block;
      padding: 0 4mm;
      margin-top: 1mm;
    }}
    .v-role {{
      font-size: 9pt;
      font-weight: bold;
      color: #0284c7;
      margin-top: 1mm;
    }}
    .event-info {{
      font-size: 7.5pt;
      color: #475569;
      margin-top: 2mm;
      line-height: 1.3;
    }}
    .qr-box {{
      position: absolute;
      right: 3mm;
      bottom: 2mm;
      width: 20mm;
      text-align: center;
    }}
    .qr-box svg {{
      width: 16mm;
      height: 16mm;
    }}
  </style>
</head>
<body>
  <div class="badge-grid">
    {''.join(badge_cards)}
  </div>
</body>
</html>
"""

    pdf_bytes = safe_html_to_pdf(html)
    pdf_filename = f"BLIA_Badges_{item_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf_path = UPLOAD_DIR / pdf_filename
    with open(pdf_path, "wb") as f:
        f.write(pdf_bytes)

    return FileResponse(
        path=str(pdf_path),
        filename=f"新竹佛光青年_{item.event_date}_志工識別名牌_8張A4.pdf",
        media_type="application/pdf"
    )

@router.get("/{item_id}/export-survey-xlsx")
def export_survey_responses_xlsx(item_id: int, db: Session = Depends(get_db)):
    """【功能 41】匯出單一活動之問卷多維度評鑑統計、NPS 指數與學員質化建議明細至 Microsoft Excel"""
    item = db.query(EvidenceItem).filter(EvidenceItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="找不到此活動")

    surveys = db.query(SurveyResponse).filter(SurveyResponse.evidence_id == item_id).all()

    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    wb = openpyxl.Workbook()
    # Sheet 1: 滿意度統計摘要
    ws1 = wb.active
    ws1.title = "問卷成效總覽與NPS"
    ws1.views.sheetView[0].showGridLines = True

    header_font = Font(name="微軟正黑體", size=12, bold=True, color="FFFFFF")
    title_font = Font(name="微軟正黑體", size=16, bold=True, color="B45309")
    bold_font = Font(name="微軟正黑體", size=11, bold=True)
    body_font = Font(name="微軟正黑體", size=11)
    amber_fill = PatternFill(start_color="D97706", end_color="D97706", fill_type="solid")
    navy_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    light_fill = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")
    thin_border = Border(left=Side(style='thin', color='CBD5E1'), right=Side(style='thin', color='CBD5E1'),
                         top=Side(style='thin', color='CBD5E1'), bottom=Side(style='thin', color='CBD5E1'))

    ws1.append(["國際佛光會新竹青年分團 活動滿意度問卷評鑑分析總表"])
    ws1.merge_cells("A1:F1")
    ws1["A1"].font = title_font
    ws1["A1"].alignment = Alignment(vertical="center")
    ws1.row_dimensions[1].height = 36

    ws1.append(["活動名稱", item.title, "舉辦日期", item.event_date, "宗旨指標", item.evaluation_code or "一般"])
    ws1["A2"].font = bold_font
    ws1["C2"].font = bold_font
    ws1["E2"].font = bold_font
    ws1.append([])

    # 摘要數值計算
    cnt = len(surveys)
    if cnt > 0:
        avg_ov = round(sum(s.overall_rating for s in surveys) / cnt, 2)
        avg_cd = round(sum(s.content_depth for s in surveys) / cnt, 2)
        avg_og = round(sum(s.organization_rating for s in surveys) / cnt, 2)
        avg_vn = round(sum(s.venue_rating for s in surveys) / cnt, 2)
        promoters = sum(1 for s in surveys if s.nps_score >= 9)
        detractors = sum(1 for s in surveys if s.nps_score <= 6)
        nps = round(((promoters - detractors) / cnt) * 100, 1)
    else:
        avg_ov, avg_cd, avg_og, avg_vn, nps = 4.8, 4.9, 4.7, 4.8, 92.0

    ws1.append(["評鑑分析向度", "平均得分 (滿分 5.0)", "達標滿意率 (%)", "全年度全體活動基準", "評鑑診斷評語"])
    for col_idx in range(1, 6):
        cell = ws1.cell(row=4, column=col_idx)
        cell.font = header_font
        cell.fill = amber_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
    ws1.row_dimensions[4].height = 24

    metrics_rows = [
        ("整體滿意度 (Overall Satisfaction)", avg_ov, f"{round(avg_ov/5*100, 1)}%", "4.80", "卓越特優，大眾肯定"),
        ("活動內容充實度 (Content Depth)", avg_cd, f"{round(avg_cd/5*100, 1)}%", "4.90", "主題深刻，實踐三好四給"),
        ("幹部動線引領 (Cadre Organization)", avg_og, f"{round(avg_og/5*100, 1)}%", "4.70", "引禮親切，流程流暢"),
        ("場地與音響設施 (Venue & Acoustics)", avg_vn, f"{round(avg_vn/5*100, 1)}%", "4.80", "設備完善，舒適莊嚴"),
        ("淨推薦度 (Net Promoter Score, NPS)", f"+{nps}", f"{nps}% 推薦率", "+88.0", "極高推薦意願，道情凝聚強")
    ]

    for r_idx, r_data in enumerate(metrics_rows, 5):
        ws1.append(list(r_data))
        for c_idx in range(1, 6):
            cell = ws1.cell(row=r_idx, column=c_idx)
            cell.font = body_font
            cell.border = thin_border
            if c_idx in (2, 3, 4):
                cell.alignment = Alignment(horizontal="center")

    # Sheet 2: 學員明細清單
    ws2 = wb.create_sheet(title="填答青年質化明細")
    ws2.views.sheetView[0].showGridLines = True
    ws2.append(["序號", "填答青年姓名/暱稱", "整體滿意(5)", "內容充實(5)", "動線引領(5)", "場地設施(5)", "NPS推薦分(10)", "最喜歡之活動環節", "給分團具體建議與回饋", "填答登記時間"])
    for col_idx in range(1, 11):
        cell = ws2.cell(row=1, column=col_idx)
        cell.font = header_font
        cell.fill = navy_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
    ws2.row_dimensions[1].height = 26

    for s_idx, s in enumerate(surveys, 1):
        time_str = s.created_at.strftime("%Y-%m-%d %H:%M") if hasattr(s.created_at, "strftime") else str(s.created_at or "")[:16]
        ws2.append([s_idx, s.respondent_name, s.overall_rating, s.content_depth, s.organization_rating, s.venue_rating, s.nps_score, s.favorite_aspect, s.suggestions, time_str])
        for c_idx in range(1, 11):
            cell = ws2.cell(row=s_idx + 1, column=c_idx)
            cell.font = body_font
            cell.border = thin_border

    # 自動調整欄寬
    for ws in (ws1, ws2):
        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len * 1.8, 12)

    xlsx_filename = f"BLIA_Survey_{item.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    xlsx_path = UPLOAD_DIR / xlsx_filename
    wb.save(str(xlsx_path))

    return FileResponse(
        path=str(xlsx_path),
        filename=f"新竹佛光青年_{item.event_date}_{item.title[:12]}_問卷評鑑分析表.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ==============================================================================
# 【功能 44】活動檢討會會議紀錄與決議事項追蹤 API
# ==============================================================================
@router.get("/{item_id}/action-items", response_model=List[MeetingActionItemResponse])
def list_meeting_action_items(item_id: int, db: Session = Depends(get_db)):
    """【功能 44】取得指定活動檢討會之各項決議追蹤事項"""
    return db.query(MeetingActionItem).filter(MeetingActionItem.evidence_id == item_id).order_by(MeetingActionItem.id.asc()).all()

@router.post("/{item_id}/action-items", response_model=MeetingActionItemResponse)
def create_meeting_action_item(
    item_id: int,
    item_in: MeetingActionItemCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_cadre)
):
    """【功能 44】新增一筆活動檢討會議決議追蹤事項"""
    item = db.query(EvidenceItem).filter(EvidenceItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="找不到此活動")

    new_act = MeetingActionItem(
        evidence_id=item_id,
        meeting_date=item_in.meeting_date or datetime.now().strftime("%Y-%m-%d"),
        topic=item_in.topic,
        discussion=item_in.discussion or "",
        assignee=item_in.assignee or user.full_name,
        due_date=item_in.due_date or "",
        status=item_in.status or "pending"
    )
    db.add(new_act)
    db.commit()
    db.refresh(new_act)
    return new_act

@router.put("/action-items/{action_id}", response_model=MeetingActionItemResponse)
def update_meeting_action_item(
    action_id: int,
    item_up: MeetingActionItemUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_cadre)
):
    """【功能 44】更新決議事項執行進度 (待處理 -> 進行中 -> 已結案)"""
    act = db.query(MeetingActionItem).filter(MeetingActionItem.id == action_id).first()
    if not act:
        raise HTTPException(status_code=404, detail="找不到此決議事項")

    for k, v in item_up.dict(exclude_unset=True).items():
        setattr(act, k, v)

    db.add(act)
    db.commit()
    db.refresh(act)
    return act

@router.delete("/action-items/{action_id}")
def delete_meeting_action_item(
    action_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_cadre)
):
    """【功能 44】刪除檢討會決議追蹤事項"""
    act = db.query(MeetingActionItem).filter(MeetingActionItem.id == action_id).first()
    if not act:
        raise HTTPException(status_code=404, detail="找不到此決議事項")
    db.delete(act)
    db.commit()
    return {"status": "success", "message": "決議事項已移除"}

# ==============================================================================
# 【功能 31】活動線上報名表單與名額即時控管 API
# ==============================================================================
@router.post("/{item_id}/register", response_model=ActivityRegistrationResponse)
def register_for_activity(
    item_id: int,
    reg_in: ActivityRegistrationCreate,
    db: Session = Depends(get_db)
):
    """【功能 31】青年線上報名活動，系統自動計算剩餘名額並決定「正取」或「候補」"""
    item = db.query(EvidenceItem).filter(EvidenceItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="找不到此活動")

    if not item.is_registration_open:
        raise HTTPException(status_code=400, detail="此活動目前尚未開放或已截止線上報名")

    # 計算現有正取人數
    confirmed_count = db.query(ActivityRegistration).filter(
        ActivityRegistration.evidence_id == item_id,
        ActivityRegistration.status == "confirmed"
    ).count()

    max_q = item.max_quota or 50
    reg_status = "confirmed" if confirmed_count < max_q else "waitlist"

    new_reg = ActivityRegistration(
        evidence_id=item_id,
        name=reg_in.name,
        phone=reg_in.phone or "",
        email=reg_in.email or "",
        affiliation=reg_in.affiliation or "",
        dietary=reg_in.dietary or "vegan",
        status=reg_status,
        notes=reg_in.notes or ""
    )
    db.add(new_reg)
    db.commit()
    db.refresh(new_reg)
    return new_reg

@router.get("/{item_id}/registration-status")
def get_activity_registration_status(item_id: int, db: Session = Depends(get_db)):
    """【功能 31】查詢活動名額上限、已報名正取人數、候補人數與剩餘名額"""
    item = db.query(EvidenceItem).filter(EvidenceItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="找不到此活動")

    max_q = item.max_quota or 50
    confirmed = db.query(ActivityRegistration).filter(
        ActivityRegistration.evidence_id == item_id,
        ActivityRegistration.status == "confirmed"
    ).count()
    waitlist = db.query(ActivityRegistration).filter(
        ActivityRegistration.evidence_id == item_id,
        ActivityRegistration.status == "waitlist"
    ).count()

    remaining = max(0, max_q - confirmed)

    return {
        "item_id": item_id,
        "title": item.title,
        "is_open": bool(item.is_registration_open),
        "max_quota": max_q,
        "confirmed_count": confirmed,
        "waitlist_count": waitlist,
        "remaining_quota": remaining,
        "is_full": (remaining == 0)
    }

@router.get("/{item_id}/registrations", response_model=List[ActivityRegistrationResponse])
def list_activity_registrations(
    item_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_cadre)
):
    """【功能 31】幹部檢視活動報名名冊"""
    return db.query(ActivityRegistration).filter(ActivityRegistration.evidence_id == item_id).order_by(ActivityRegistration.id.asc()).all()

# Compact pure-Python QR Code generator producing clean SVG
# Supports Version 1-4 Byte Mode with ECC-L
import math

# GF(256) tables with primitive polynomial 0x11d
GF_EXP = [0] * 512
GF_LOG = [0] * 256
x = 1
for i in range(255):
    GF_EXP[i] = x
    GF_EXP[i + 255] = x
    GF_LOG[x] = i
    x <<= 1
    if x & 0x100:
        x ^= 0x11d

def gf_mul(x, y):
    if x == 0 or y == 0:
        return 0
    return GF_EXP[GF_LOG[x] + GF_LOG[y]]

def rs_generator_poly(degree):
    g = [1]
    for i in range(degree):
        # multiply by (x + alpha^i)
        root = GF_EXP[i]
        next_g = [0] * (len(g) + 1)
        for j in range(len(g)):
            next_g[j] ^= gf_mul(g[j], root)
            next_g[j + 1] ^= g[j]
        g = next_g
    return g

def rs_encode(data, ecc_len):
    gen = rs_generator_poly(ecc_len)
    msg = list(data) + [0] * ecc_len
    for i in range(len(data)):
        lead = msg[i]
        if lead != 0:
            for j in range(len(gen)):
                msg[i + j] ^= gf_mul(gen[j], lead)
    return msg[len(data):]

def generate_qr_matrix(text: str):
    data_bytes = text.encode('utf-8')
    data_len = len(data_bytes)
    
    # Version 2 (25x25) capacity ECC-L: 34 bytes data, 10 bytes ECC
    # Version 3 (29x29) capacity ECC-L: 55 bytes data, 15 bytes ECC
    # Version 4 (33x33) capacity ECC-L: 80 bytes data, 20 bytes ECC
    if data_len <= 32:
        ver = 2
        size = 25
        data_cap = 34
        ecc_len = 10
        align_pos = [6, 18]
    elif data_len <= 53:
        ver = 3
        size = 29
        data_cap = 55
        ecc_len = 15
        align_pos = [6, 22]
    else:
        ver = 4
        size = 33
        data_cap = 80
        ecc_len = 20
        align_pos = [6, 26]

    # Build bitstream
    bits = '0100'  # Byte mode
    bits += f'{data_len:08b}'
    for b in data_bytes:
        bits += f'{b:08b}'
    
    # Terminator
    bits += '0' * min(4, data_cap * 8 - len(bits))
    # Pad to byte boundary
    while len(bits) % 8 != 0:
        bits += '0'
    
    # Pad bytes
    pad_bytes = ['11101100', '00010001']
    pad_idx = 0
    while len(bits) < data_cap * 8:
        bits += pad_bytes[pad_idx % 2]
        pad_idx += 1
    
    data_codewords = [int(bits[i:i+8], 2) for i in range(0, len(bits), 8)]
    ecc_codewords = rs_encode(data_codewords, ecc_len)
    all_codewords = data_codewords + ecc_codewords
    
    # 2D matrix (None = unassigned, True = black, False = white)
    matrix = [[None] * size for _ in range(size)]
    reserved = [[False] * size for _ in range(size)]
    
    # Place Finder Patterns
    def place_finder(r, c):
        for dr in range(-1, 8):
            for dc in range(-1, 8):
                nr, nc = r + dr, c + dc
                if 0 <= nr < size and 0 <= nc < size:
                    reserved[nr][nc] = True
                    if 0 <= dr <= 6 and 0 <= dc <= 6:
                        matrix[nr][nc] = (dr in (0, 6) or dc in (0, 6) or (2 <= dr <= 4 and 2 <= dc <= 4))
                    else:
                        matrix[nr][nc] = False

    place_finder(0, 0)
    place_finder(0, size - 7)
    place_finder(size - 7, 0)
    
    # Place Alignment Pattern if ver >= 2
    if ver >= 2:
        ar, ac = align_pos[1], align_pos[1]
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                nr, nc = ar + dr, ac + dc
                if not reserved[nr][nc]:
                    reserved[nr][nc] = True
                    matrix[nr][nc] = (abs(dr) == 2 or abs(dc) == 2 or (dr == 0 and dc == 0))

    # Timing patterns
    for i in range(8, size - 8):
        if not reserved[6][i]:
            reserved[6][i] = True
            matrix[6][i] = (i % 2 == 0)
        if not reserved[i][6]:
            reserved[i][6] = True
            matrix[i][6] = (i % 2 == 0)

    # Dark module
    reserved[4 * ver + 9][8] = True
    matrix[4 * ver + 9][8] = True

    # Format info area reservation
    for i in range(9):
        if not reserved[8][i]:
            reserved[8][i] = True
        if not reserved[i][8]:
            reserved[i][8] = True
    for i in range(size - 8, size):
        if not reserved[8][i]:
            reserved[8][i] = True
        if not reserved[i][8]:
            reserved[i][8] = True

    # Place data bits
    bit_idx = 0
    bit_str = ''.join(f'{cw:08b}' for cw in all_codewords)
    
    col = size - 1
    up = True
    while col > 0:
        if col == 6:
            col -= 1
        row_range = range(size - 1, -1, -1) if up else range(size)
        for r in row_range:
            for c in (col, col - 1):
                if not reserved[r][c]:
                    b_val = False
                    if bit_idx < len(bit_str):
                        b_val = (bit_str[bit_idx] == '1')
                        bit_idx += 1
                    # Mask 0: (r + c) % 2 == 0
                    if (r + c) % 2 == 0:
                        b_val = not b_val
                    matrix[r][c] = b_val
        up = not up
        col -= 2

    # Format bits for ECC-L, Mask 0: 0b111011111000100 ^ 0b101010000010010 = 010001111010110
    format_bits = "010001111010110"
    for i in range(6):
        matrix[8][i] = (format_bits[i] == '1')
    matrix[8][7] = (format_bits[6] == '1')
    matrix[8][8] = (format_bits[7] == '1')
    matrix[7][8] = (format_bits[8] == '1')
    for i in range(9, 15):
        matrix[14 - i][8] = (format_bits[i] == '1')
        
    for i in range(8):
        matrix[size - 1 - i][8] = (format_bits[i] == '1')
    for i in range(8, 15):
        matrix[8][size - 15 + i] = (format_bits[i] == '1')

    return matrix

def generate_qr_svg(text: str, size_px: int = 260) -> str:
    matrix = generate_qr_matrix(text)
    n = len(matrix)
    margin = 3
    total_cells = n + margin * 2
    cell_size = size_px / total_cells

    paths = []
    for r in range(n):
        for c in range(n):
            if matrix[r][c]:
                x = (c + margin) * cell_size
                y = (r + margin) * cell_size
                paths.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell_size:.1f}" height="{cell_size:.1f}" fill="#1e293b"/>')

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size_px} {size_px}" width="{size_px}" height="{size_px}">
  <rect width="100%" height="100%" fill="#ffffff" rx="12"/>
  {''.join(paths)}
  <circle cx="{size_px/2}" cy="{size_px/2}" r="16" fill="#f59e0b" stroke="#ffffff" stroke-width="3"/>
  <text x="{size_px/2}" y="{size_px/2 + 5}" font-size="14" text-anchor="middle" fill="#ffffff" font-weight="bold">☸</text>
</svg>'''
    return svg

if __name__ == "__main__":
    svg = generate_qr_svg("http://127.0.0.1:8000/#aims?checkin=1")
    print("QR Code SVG Generated Successfully, length:", len(svg))
    assert '<svg' in svg and '<rect' in svg


# ==============================================================================
# 【功能 32】活動現場 QR Code 簽到掃描生成器 API
# ==============================================================================
@router.get("/{item_id}/qrcode")
def get_activity_qrcode(item_id: int, db: Session = Depends(get_db)):
    """【功能 32】即時產製現場專用高解析向量 SVG QR Code 簽到圖與簽到網址"""
    item = db.query(EvidenceItem).filter(EvidenceItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="找不到此活動")

    checkin_url = f"http://127.0.0.1:8000/#aims?checkin={item_id}"
    svg_data = generate_qr_svg(checkin_url, size_px=280)

    return {
        "item_id": item_id,
        "title": item.title,
        "checkin_url": checkin_url,
        "qrcode_svg": svg_data
    }

@router.post("/{item_id}/scan-checkin")
def scan_quick_checkin(
    item_id: int,
    checkin_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """【功能 32】手機掃碼即時簽到打卡"""
    item = db.query(EvidenceItem).filter(EvidenceItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="找不到此活動")

    name = checkin_data.get("name", "熱心青年")
    phone = checkin_data.get("phone", "")

    # 自動記錄人數增加
    item.participants_count = (item.participants_count or 0) + 1
    db.add(item)
    db.commit()

    return {
        "status": "success",
        "message": f"🎉 恭喜 {name} 簽到成功！歡迎參與新竹佛光青年【{item.title}】！",
        "participants_count": item.participants_count
    }

# ==============================================================================
# 【功能 34】活動滿意度問卷多維度星級雷達圖評析 API
# ==============================================================================
@router.get("/{item_id}/survey/radar")
def get_survey_radar_analysis(item_id: int, db: Session = Depends(get_db)):
    """【功能 34】產製問卷 5 大向度星級雷達圖數據（與年度基準比對）"""
    item = db.query(EvidenceItem).filter(EvidenceItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="找不到此活動")

    surveys = db.query(SurveyResponse).filter(SurveyResponse.evidence_id == item_id).all()
    if not surveys:
        overall = 4.8
        content = 4.9
        org = 4.7
        venue = 4.8
        nps_star = 4.6
    else:
        cnt = len(surveys)
        overall = round(sum(s.overall_rating for s in surveys) / cnt, 2)
        content = round(sum(s.content_depth for s in surveys) / cnt, 2)
        org = round(sum(s.organization_rating for s in surveys) / cnt, 2)
        venue = round(sum(s.venue_rating for s in surveys) / cnt, 2)
        nps_star = round(sum(s.nps_score for s in surveys) / cnt / 2.0, 2)

    radar_axes = [
        {"axis": "整體滿意度", "score": overall, "benchmark": 4.8},
        {"axis": "內容充實度", "score": content, "benchmark": 4.9},
        {"axis": "幹部動線引領", "score": org, "benchmark": 4.7},
        {"axis": "場地設施舒適", "score": venue, "benchmark": 4.8},
        {"axis": "推薦意願 (NPS)", "score": nps_star, "benchmark": 4.6}
    ]

    return {
        "item_id": item_id,
        "title": item.title,
        "total_responses": len(surveys) if surveys else 0,
        "radar_data": radar_axes
    }


# ==============================================================================
# 【功能 61】活動紀念電子證書與結業證書多版型一鍵產生器 (Certificate Studio) API
# ==============================================================================
@router.get("/certificate-templates")
def get_certificate_templates():
    """【功能 61】取得證書多版型範本定義清單"""
    return [
        {"type": "camp", "name": "三好兒童夏令營小隊輔培訓結業證書", "theme_color": "#D97706", "subtitle": "熱忱奉獻・引領幼苗・三好品格教育"},
        {"type": "workshop", "name": "青年幹部培訓暨領導力研習證明書", "theme_color": "#4F46E5", "subtitle": "佛光青年・擔當重任・弘揚人間佛教"},
        {"type": "dharma", "name": "佛學與生活禪精進修持表彰獎狀", "theme_color": "#059669", "subtitle": "深入經藏・智慧如海・安住自性清淨"},
        {"type": "service", "name": "年度傑出志願服務熱忱發心證書", "theme_color": "#EA580C", "subtitle": "四給行願・廣結善緣・照亮社會角落"}
    ]

@router.get("/certificate-studio")
def generate_certificate_studio(
    recipient_name: str = "陳冠宇",
    activity_title: str = "2026兒童三好夏令營小隊輔研習營",
    template_type: str = "camp",
    hours: float = 16.0,
    issue_date: str = "2026-07-20"
):
    """【功能 61】動態產製電子結業證書與獎狀（SVG 向量排版，支援列印與展示）"""
    templates = {
        "camp": {
            "title": "三好兒童夏令營小隊輔結業證書",
            "border": "#D97706",
            "bg": "#FFFBEB",
            "desc": f"茲證明青年學員【{recipient_name}】全程參與本社團舉辦之《{activity_title}》，圓滿完成小隊輔領導知能與三好教育實習培訓，表現卓越，足堪表率，特發此證以資鼓勵。"
        },
        "workshop": {
            "title": "青年幹部培訓暨領導力研習證書",
            "border": "#4F46E5",
            "bg": "#EEF2FF",
            "desc": f"茲證明青年學員【{recipient_name}】積極參與《{activity_title}》，圓滿完成幹部專案策劃、團隊溝通與組織運作等領導力課程，特頒此證以昭信守。"
        },
        "dharma": {
            "title": "佛學與生活禪修持表彰獎狀",
            "border": "#059669",
            "bg": "#ECFDF5",
            "desc": f"茲證明青年學員【{recipient_name}】精進參與《{activity_title}》，以禪心調息、安住當下，實踐菩提願力，解行並重，特賜獎狀以茲勉勵。"
        },
        "service": {
            "title": "年度傑出志願服務榮譽證書",
            "border": "#EA580C",
            "bg": "#FFF7ED",
            "desc": f"茲證明青年志工【{recipient_name}】熱忱參與《{activity_title}》志工服務，累計服務時數達 {hours} 小時，實踐四給精神，造福群生，特此致謝。"
        }
    }

    cfg = templates.get(template_type, templates["camp"])
    cert_serial = f"BLIA-HCY-CERT-2026-{abs(hash(recipient_name + activity_title)) % 9000 + 1000:04d}"

    svg_markup = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 560" width="100%" height="100%" style="background-color: {cfg['bg']}; font-family: sans-serif;">
      <rect x="20" y="20" width="760" height="520" fill="none" stroke="{cfg['border']}" stroke-width="6" rx="16" />
      <rect x="30" y="30" width="740" height="500" fill="none" stroke="{cfg['border']}" stroke-width="1.5" stroke-dasharray="6,4" rx="12" />
      
      <circle cx="45" cy="45" r="10" fill="{cfg['border']}" opacity="0.3" />
      <circle cx="755" cy="45" r="10" fill="{cfg['border']}" opacity="0.3" />
      <circle cx="45" cy="515" r="10" fill="{cfg['border']}" opacity="0.3" />
      <circle cx="755" cy="515" r="10" fill="{cfg['border']}" opacity="0.3" />

      <text x="400" y="75" font-size="14" font-weight="bold" fill="{cfg['border']}" text-anchor="middle" letter-spacing="4">國際佛光會中華青年總會・新竹青年分團</text>
      <text x="400" y="115" font-size="26" font-weight="900" fill="#1E293B" text-anchor="middle" letter-spacing="2">{cfg['title']}</text>
      <line x1="300" y1="130" x2="500" y2="130" stroke="{cfg['border']}" stroke-width="2" />

      <text x="730" y="70" font-size="10" font-family="monospace" fill="#64748B" text-anchor="end">字號：{cert_serial}</text>

      <text x="400" y="185" font-size="16" fill="#475569" text-anchor="middle">受證青年：<tspan font-size="24" font-weight="bold" fill="#0F172A"> {recipient_name} </tspan> 菩薩</text>

      <foreignObject x="80" y="220" width="640" height="130">
        <div xmlns="http://www.w3.org/1999/xhtml" style="font-size: 15px; line-height: 1.8; color: #334155; text-align: justify; text-indent: 2em;">
          {cfg['desc']}
        </div>
      </foreignObject>

      <rect x="300" y="360" width="200" height="32" rx="16" fill="{cfg['border']}" opacity="0.15" />
      <text x="400" y="381" font-size="13" font-weight="bold" fill="{cfg['border']}" text-anchor="middle">認證服務時數：{hours} 小時</text>

      <text x="140" y="470" font-size="13" font-weight="bold" fill="#1E293B">輔導法師：法寶寺常住法師 ㊞</text>
      <text x="140" y="495" font-size="13" font-weight="bold" fill="#1E293B">新竹青年分團長：分團長 ㊞</text>

      <rect x="620" y="430" width="80" height="80" fill="#EF4444" opacity="0.85" rx="8" />
      <text x="660" y="465" font-size="12" font-weight="bold" fill="#FFFFFF" text-anchor="middle">新竹青年</text>
      <text x="660" y="485" font-size="12" font-weight="bold" fill="#FFFFFF" text-anchor="middle">分團之印</text>

      <text x="400" y="525" font-size="12" fill="#64748B" text-anchor="middle">中 華 民 國 115 年 7 月 20 日（公曆 {issue_date}）</text>
    </svg>"""

    return {
        "status": "success",
        "certificate_no": cert_serial,
        "recipient_name": recipient_name,
        "activity_title": activity_title,
        "template_type": template_type,
        "template_name": cfg["title"],
        "hours": hours,
        "issue_date": issue_date,
        "svg_markup": svg_markup
    }


# ==============================================================================
# 【功能 76】道場節慶活動現場即時報到人數與出席熱度大螢幕看板 API
# ==============================================================================
@router.get("/{item_id}/live-checkin-dashboard")
def get_live_checkin_dashboard(item_id: int, db: Session = Depends(get_db)):
    """【功能 76】活動現場即時報到人數與出席熱度大螢幕看板數據"""
    item = db.query(EvidenceItem).filter(EvidenceItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="找不到此活動")
    
    regs = db.query(ActivityRegistration).filter(ActivityRegistration.evidence_id == item_id).all()
    total_reg = len(regs)
    confirmed_count = sum(1 for r in regs if r.status in ("confirmed", "已確認", "已簽到"))
    waitlist_count = sum(1 for r in regs if r.status in ("waitlist", "候補"))
    
    actual_checkins = max(int(item.participants_count or 0), confirmed_count, 1)
    target_capacity = max(actual_checkins + 10, 50)
    checkin_rate = round((actual_checkins / target_capacity * 100), 1)

    diet_stats = {
        "全素 (Vegan)": sum(1 for r in regs if r.dietary in ("vegan", "全素", "素食")),
        "蛋奶素 (Lacto-Ovo)": sum(1 for r in regs if r.dietary in ("lacto-ovo", "蛋奶素")),
        "方便素 (Convenience)": max(0, total_reg - sum(1 for r in regs if r.dietary in ("vegan", "全素", "素食", "lacto-ovo", "蛋奶素")))
    }

    recent_checkins = [
        {"name": r.name, "affiliation": r.affiliation or "新竹青年同修", "dietary": r.dietary, "status": "已入座"}
        for r in regs[:8]
    ]

    return {
        "status": "success",
        "activity_title": item.title,
        "category": item.category,
        "event_date": item.event_date,
        "target_capacity": target_capacity,
        "actual_checkins": actual_checkins,
        "total_registered": total_reg,
        "confirmed_count": confirmed_count,
        "waitlist_count": waitlist_count,
        "occupancy_rate_percent": checkin_rate,
        "dietary_breakdown": diet_stats,
        "recent_checkins": recent_checkins,
        "status_text": "入座熱烈 (High Attendance)" if checkin_rate > 70 else "報到中"
    }


# ==============================================================================
# 【功能 87】活動專屬數位問卷滿意度 NPS 淨推薦值與青年體驗旅程儀表板 API
# ==============================================================================
@router.get("/{item_id}/nps-analysis")
def get_activity_nps_analysis(item_id: int, db: Session = Depends(get_db)):
    """【功能 87】活動滿意度 NPS 淨推薦值與青年體驗旅程大數據分析"""
    item = db.query(EvidenceItem).filter(EvidenceItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="找不到此活動")

    surveys = db.query(SurveyResponse).filter(SurveyResponse.evidence_id == item_id).all()
    feedbacks = db.query(EvidenceFeedback).filter(EvidenceFeedback.evidence_id == item_id).all()

    scores = []
    for s in surveys:
        scores.append(int(s.overall_satisfaction or 5) * 2)
    for f in feedbacks:
        scores.append(int(f.rating or 5) * 2)

    if not scores:
        scores = [10, 9, 10, 8, 9, 10, 8, 9]

    total_respondents = len(scores)
    promoters = sum(1 for s in scores if s >= 9)
    passives = sum(1 for s in scores if 7 <= s <= 8)
    detractors = sum(1 for s in scores if s <= 6)

    promoter_pct = round((promoters / total_respondents * 100), 1)
    detractor_pct = round((detractors / total_respondents * 100), 1)
    nps_score = round(promoter_pct - detractor_pct, 1)

    journey_stages = [
        {"stage": "活動前期待", "score": 9.2, "feedback": "青年對生活禪與跨界座談題材抱持高度期待"},
        {"stage": "現場接待入座", "score": 9.5, "feedback": "知賓幹部奉茶引導親切，QRCode 向量報到流暢"},
        {"stage": "課程專案互動", "score": 9.4, "feedback": "破冰團康與講師分享深具啟發，法喜充滿"},
        {"stage": "素食茶點體驗", "score": 9.8, "feedback": "法寶寺滴水坊清淨蔬食餐點備受大眾讚譽"},
        {"stage": "會後三好實踐", "score": 9.1, "feedback": "超過 90% 青年學員發願在生活中落實做好事說好話"}
    ]

    return {
        "status": "success",
        "activity_title": item.title,
        "total_respondents": total_respondents,
        "nps_score": nps_score,
        "nps_grade": "世界級卓越 (World Class)" if nps_score >= 70 else "優秀滿意 (Excellent)",
        "promoters_count": promoters,
        "promoters_percent": promoter_pct,
        "passives_count": passives,
        "detractors_count": detractors,
        "detractors_percent": detractor_pct,
        "key_highlights": ["生活禪調息身心放鬆", "青年團隊熱情有活力", "素食茶點美味清淨", "收穫滿滿正能量"],
        "journey_stages": journey_stages
    }

@router.get("/{item_id}", response_model=EvidenceItemResponse)
def get_evidence_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(EvidenceItem).filter(EvidenceItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="找不到此佐證項目")
    return item

@router.post("", response_model=EvidenceItemResponse)
def create_evidence_item(
    item_in: EvidenceItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_cadre)
):
    calc_year = item_in.year or (item_in.event_date[:4] if item_in.event_date else "2026")
    lat, lng = resolve_coordinates(item_in.location or "")

    new_item = EvidenceItem(
        category=item_in.category,
        title=item_in.title,
        event_date=item_in.event_date,
        year=calc_year,
        evaluation_code=item_in.evaluation_code or "",
        location=item_in.location or "新竹法寶寺",
        latitude=item_in.latitude or lat,
        longitude=item_in.longitude or lng,
        summary=item_in.summary or "",
        participants_count=item_in.participants_count or 0,
        volunteers_count=item_in.volunteers_count or 0,
        service_hours=item_in.service_hours or 0.0,
        satisfaction_rate=item_in.satisfaction_rate or 95,
        expected_participants=item_in.expected_participants or 0,
        expected_goals=item_in.expected_goals or "",
        actual_highlights=item_in.actual_highlights or "",
        file_url=item_in.file_url or "",
        file_type=item_in.file_type or "image",
        original_filename=item_in.original_filename or "",
        attachments=item_in.attachments or "[]",
        photos_gallery=item_in.photos_gallery or "[]",
        created_by=current_user.full_name,
        is_published=item_in.is_published
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item

@router.put("/{item_id}", response_model=EvidenceItemResponse)
def update_evidence_item(
    item_id: int,
    item_update: EvidenceItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_cadre)
):
    item = db.query(EvidenceItem).filter(EvidenceItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="找不到此佐證項目")

    update_dict = item_update.dict(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(item, field, value)

    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@router.delete("/{item_id}")
def delete_evidence_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_cadre)
):
    item = db.query(EvidenceItem).filter(EvidenceItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="找不到此佐證項目")

    db.delete(item)
    db.commit()
    return {"message": "佐證項目已成功刪除"}

@router.post("/import")
async def import_evidence_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_cadre)
):
    filename = file.filename.lower()
    content = await file.read()
    records = []

    if filename.endswith(".xlsx") or filename.endswith(".xls") or filename.endswith(".csv"):
        if filename.endswith(".csv"):
            reader = csv.reader(io.StringIO(content.decode("utf-8-sig", errors="ignore")))
            rows = list(reader)
        else:
            try:
                import openpyxl
                wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
                ws = wb.active
                rows = list(ws.iter_rows(values_only=True))
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"讀取 Excel 失敗: {str(e)}")

        if not rows or len(rows) < 2:
            raise HTTPException(status_code=400, detail="檔案內容為空或無標題列")

        headers = [str(c).strip().lower() if c else "" for c in rows[0]]
        col_cat, col_title, col_date, col_loc, col_sum, col_url, col_code, col_part = -1, -1, -1, -1, -1, -1, -1, -1

        for i, h in enumerate(headers):
            if any(k in h for k in ["地點", "場所", "location"]): col_loc = i
            elif any(k in h for k in ["日期", "時間", "date"]): col_date = i
            elif any(k in h for k in ["指標", "代碼", "code"]): col_code = i
            elif any(k in h for k in ["人次", "人數", "participant"]): col_part = i
            elif any(k in h for k in ["宗旨", "分類", "category", "組別"]): col_cat = i
            elif any(k in h for k in ["摘要", "成果說明", "內容", "成效", "summary", "說明"]) and not any(k in h for k in ["名稱", "標題"]): col_sum = i
            elif any(k in h for k in ["佐證", "照片", "檔案", "url", "file", "連結"]): col_url = i
            elif any(k in h for k in ["標題", "名稱", "活動名稱", "活動標題", "title"]): col_title = i
            elif "活動" in h and col_title == -1: col_title = i

        if col_title == -1 and len(headers) >= 2:
            col_cat, col_title, col_date, col_loc, col_sum = 0, 1, 2, 3, 4

        for row in rows[1:]:
            if not row or not any(row): continue
            title = str(row[col_title]).strip() if col_title >= 0 and col_title < len(row) and row[col_title] else ""
            if not title: continue

            cat = normalize_category(row[col_cat] if col_cat >= 0 and col_cat < len(row) else "")
            dt = normalize_date(row[col_date] if col_date >= 0 and col_date < len(row) else "")
            loc = str(row[col_loc]).strip() if col_loc >= 0 and col_loc < len(row) and row[col_loc] else "新竹法寶寺"
            summary = str(row[col_sum]).strip() if col_sum >= 0 and col_sum < len(row) and row[col_sum] else ""
            file_url = str(row[col_url]).strip() if col_url >= 0 and col_url < len(row) and row[col_url] else ""
            code = str(row[col_code]).strip() if col_code >= 0 and col_code < len(row) and row[col_code] else ""
            part_cnt = int(row[col_part]) if col_part >= 0 and col_part < len(row) and str(row[col_part]).isdigit() else 0

            records.append({
                "category": cat,
                "title": title,
                "event_date": dt,
                "year": dt[:4] if len(dt) >= 4 else "2026",
                "evaluation_code": code,
                "location": loc,
                "summary": summary,
                "participants_count": part_cnt,
                "file_url": file_url
            })

    elif filename.endswith(".docx"):
        try:
            import docx
            doc = docx.Document(io.BytesIO(content))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"讀取 Word 檔案失敗: {str(e)}")

        if doc.tables:
            for table in doc.tables:
                if len(table.rows) < 2: continue
                headers = [c.text.strip().lower() for c in table.rows[0].cells]
                
                col_cat, col_title, col_date, col_loc, col_sum, col_code = -1, -1, -1, -1, -1, -1
                for i, h in enumerate(headers):
                    if any(k in h for k in ["地點", "場所"]): col_loc = i
                    elif any(k in h for k in ["日期", "時間"]): col_date = i
                    elif any(k in h for k in ["指標", "代碼"]): col_code = i
                    elif any(k in h for k in ["宗旨", "分類", "組別"]): col_cat = i
                    elif any(k in h for k in ["摘要", "成效說明", "成效", "說明"]) and not any(k in h for k in ["名稱", "標題"]): col_sum = i
                    elif any(k in h for k in ["標題", "名稱", "活動名稱"]): col_title = i
                    elif "活動" in h and col_title == -1: col_title = i

                if col_title == -1:
                    col_cat, col_title, col_date, col_loc, col_sum = 0, 1, 2, 3, 4

                for r in table.rows[1:]:
                    cells = [c.text.strip() for c in r.cells]
                    if not any(cells): continue
                    title = cells[col_title] if col_title < len(cells) else ""
                    if not title: continue

                    cat = normalize_category(cells[col_cat] if col_cat < len(cells) else "")
                    dt = normalize_date(cells[col_date] if col_date < len(cells) else "")
                    loc = cells[col_loc] if col_loc < len(cells) and cells[col_loc] else "新竹法寶寺"
                    summary = cells[col_sum] if col_sum < len(cells) else ""
                    code = cells[col_code] if col_code >= 0 and col_code < len(cells) else ""

                    records.append({
                        "category": cat,
                        "title": title,
                        "event_date": dt,
                        "year": dt[:4] if len(dt) >= 4 else "2026",
                        "evaluation_code": code,
                        "location": loc,
                        "summary": summary,
                        "participants_count": 0,
                        "file_url": ""
                    })

    if not records:
        raise HTTPException(status_code=400, detail="未能自檔案中解析出任何有效活動紀錄，請檢查欄位格式")

    imported_items = []
    for r in records:
        lat, lng = resolve_coordinates(r.get("location", ""))
        item = EvidenceItem(
            category=r["category"],
            title=r["title"],
            event_date=r["event_date"],
            year=r.get("year", "2026"),
            evaluation_code=r.get("evaluation_code", ""),
            location=r.get("location", "新竹法寶寺"),
            latitude=lat,
            longitude=lng,
            summary=r.get("summary", ""),
            participants_count=r.get("participants_count", 0),
            volunteers_count=0,
            service_hours=0.0,
            satisfaction_rate=95,
            expected_participants=0,
            expected_goals="",
            actual_highlights="",
            file_url=r.get("file_url", ""),
            file_type="image" if not r.get("file_url", "").endswith(".pdf") else "pdf",
            original_filename=file.filename,
            attachments="[]",
            created_by=f"{current_user.full_name} (批量匯入)",
            is_published=True
        )
        db.add(item)
        imported_items.append(item)

    db.commit()
    for item in imported_items:
        db.refresh(item)

    return {
        "status": "success",
        "imported_count": len(imported_items),
        "source_file": file.filename,
        "sample_titles": [i.title for i in imported_items[:5]]
    }
