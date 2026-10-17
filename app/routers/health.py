from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
try:
    from sqlalchemy.orm import Session
except ImportError:
    Session = object

try:
    from sqlalchemy import func
except ImportError:
    class FuncHelper:
        class SumHelper:
            def __init__(self, col):
                self.col_name = col.name if hasattr(col, 'name') else str(col)
                self.table = "health_logs"
        def sum(self, col):
            return self.SumHelper(col)
    func = FuncHelper()

from app.database import get_db
from app.models import HealthLog, User, ZenMeditation, GoodDeedJournal
from app.schemas import HealthLogCreate, HealthLogResponse, HealthReviewRequest, HealthLeaderboardResponse, HealthLeaderboardItem, ZenMeditationCreate, ZenMeditationResponse, GoodDeedJournalCreate, GoodDeedJournalResponse
from app.auth import require_cadre

router = APIRouter(prefix="/api/health", tags=["健走跑步與健康打卡 (Health & VEGRUN Logs)"])

@router.get("", response_model=List[HealthLogResponse])
def list_health_logs(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """【公開前台/後台】取得健走跑步打卡紀錄列表（最新日期優先）"""
    return db.query(HealthLog).order_by(HealthLog.log_date.desc(), HealthLog.id.desc()).limit(limit).all()

@router.get("/stats")
def get_health_stats(db: Session = Depends(get_db)):
    """【公開前台】計算總累積打卡人次、總公里數、總步數"""
    total_logs = db.query(HealthLog).count()
    total_km = db.query(func.sum(HealthLog.distance_km)).scalar() or 0.0
    total_steps = db.query(func.sum(HealthLog.steps)).scalar() or 0
    unique_members = db.query(HealthLog.participant_name).distinct().count()

    return {
        "total_logs": total_logs,
        "total_km": round(float(total_km), 2),
        "total_steps": int(total_steps),
        "unique_members": unique_members
    }

@router.post("", response_model=HealthLogResponse)
def create_health_log(
    log_in: HealthLogCreate,
    db: Session = Depends(get_db)
):
    """【青年/幹部】新增健康打卡紀錄（支援雙軌截圖核驗：裝置截圖 vs 視訊截圖）"""
    new_log = HealthLog(
        participant_name=log_in.participant_name,
        activity_type=log_in.activity_type or "walk",
        log_date=log_in.log_date,
        distance_km=log_in.distance_km or 0.0,
        steps=log_in.steps or 0,
        proof_image_url=log_in.proof_image_url or "",
        note=log_in.note or "",
        verification_type=getattr(log_in, 'verification_type', 'device_screenshot') or 'device_screenshot',
        review_status=getattr(log_in, 'review_status', 'pending') or 'pending'
    )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    return new_log


@router.get("/pending", response_model=List[HealthLogResponse])
def list_pending_health_logs(
    db: Session = Depends(get_db)
):
    """【幹部審核專區】取得所有待審核（pending）之青年打卡紀錄"""
    all_logs = db.query(HealthLog).all()
    pending = [log for log in all_logs if getattr(log, 'review_status', 'approved') == 'pending']
    pending.sort(key=lambda x: getattr(x, 'log_date', ''), reverse=True)
    return pending


@router.put("/{log_id}/review", response_model=HealthLogResponse)
def review_health_log(
    log_id: int,
    review_in: HealthReviewRequest,
    db: Session = Depends(get_db)
):
    """【幹部審核】審核青年雙軌打卡紀錄（核准 approved 或 退回 rejected，並附加鼓勵評語）"""
    from datetime import datetime
    log_item = db.query(HealthLog).filter(HealthLog.id == log_id).first()
    if not log_item:
        raise HTTPException(status_code=404, detail="找不到此打卡紀錄")
    
    log_item.review_status = review_in.review_status
    log_item.reviewer_name = review_in.reviewer_name
    log_item.reviewer_notes = review_in.reviewer_notes or ""
    log_item.reviewed_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    db.add(log_item)
    db.commit()
    db.refresh(log_item)
    return log_item


@router.get("/leaderboards", response_model=HealthLeaderboardResponse)
def get_health_leaderboards(db: Session = Depends(get_db)):
    """【雙榜排行榜】連續打卡天數榜 (Streak Leaderboard) 與 累積里程先鋒榜 (Km Leaderboard)"""
    from datetime import datetime, timedelta
    
    all_logs = db.query(HealthLog).all()
    # 統計已審核通過（approved）之紀錄
    approved_logs = [log for log in all_logs if getattr(log, 'review_status', 'approved') in ('approved', '')]
    
    member_data = {}
    for log in approved_logs:
        name = log.participant_name
        if name not in member_data:
            member_data[name] = {
                "total_km": 0.0,
                "total_steps": 0,
                "dates": set(),
                "approved_logs": 0
            }
        member_data[name]["total_km"] += float(log.distance_km or 0.0)
        member_data[name]["total_steps"] += int(log.steps or 0)
        member_data[name]["approved_logs"] += 1
        if log.log_date:
            member_data[name]["dates"].add(log.log_date.strip())
            
    # 計算每位青年的連續打卡天數 (Streak)
    leaderboard_list = []
    for name, data in member_data.items():
        sorted_dates = sorted(list(data["dates"]), reverse=True)
        streak = 0
        if sorted_dates:
            streak = 1
            cur_d = None
            try:
                cur_d = datetime.strptime(sorted_dates[0], "%Y-%m-%d").date()
                for d_str in sorted_dates[1:]:
                    prev_d = datetime.strptime(d_str, "%Y-%m-%d").date()
                    if (cur_d - prev_d).days == 1:
                        streak += 1
                        cur_d = prev_d
                    else:
                        break
            except Exception:
                streak = len(sorted_dates)
                
        leaderboard_list.append({
            "participant_name": name,
            "total_km": round(data["total_km"], 2),
            "total_steps": data["total_steps"],
            "current_streak": streak,
            "approved_logs": data["approved_logs"]
        })
        
    # 排序：Streak 榜
    streak_sorted = sorted(leaderboard_list, key=lambda x: (x["current_streak"], x["total_km"]), reverse=True)
    streak_lb = [
        HealthLeaderboardItem(
            rank=i + 1,
            participant_name=item["participant_name"],
            total_km=item["total_km"],
            total_steps=item["total_steps"],
            current_streak=item["current_streak"],
            approved_logs=item["approved_logs"]
        ) for i, item in enumerate(streak_sorted[:10])
    ]
    
    # 排序：Distance 里程榜
    distance_sorted = sorted(leaderboard_list, key=lambda x: (x["total_km"], x["current_streak"]), reverse=True)
    distance_lb = [
        HealthLeaderboardItem(
            rank=i + 1,
            participant_name=item["participant_name"],
            total_km=item["total_km"],
            total_steps=item["total_steps"],
            current_streak=item["current_streak"],
            approved_logs=item["approved_logs"]
        ) for i, item in enumerate(distance_sorted[:10])
    ]
    
    return HealthLeaderboardResponse(
        streak_leaderboard=streak_lb,
        distance_leaderboard=distance_lb
    )

@router.delete("/{log_id}")
def delete_health_log(
    log_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_cadre)
):
    """【幹部/管理員】刪除打卡紀錄"""
    log_item = db.query(HealthLog).filter(HealthLog.id == log_id).first()
    if not log_item:
        raise HTTPException(status_code=404, detail="找不到此打卡紀錄")
    db.delete(log_item)
    db.commit()
    return {"message": "打卡紀錄已成功刪除"}


# ==============================================================================
# 【功能 54】青年生活禪每日靜心打卡計時鐘 API
# ==============================================================================
@router.post("/zen-meditation", response_model=ZenMeditationResponse)
def log_zen_meditation(
    meditation_in: ZenMeditationCreate,
    db: Session = Depends(get_db)
):
    """【功能 54】青年生活禪靜心打卡（記錄靜坐時間、心得法語與心境）"""
    new_zen = ZenMeditation(
        participant_name=meditation_in.participant_name,
        duration_minutes=meditation_in.duration_minutes or 10,
        reflection_notes=meditation_in.reflection_notes or "",
        mood=meditation_in.mood or "心平氣和"
    )
    db.add(new_zen)
    db.commit()
    db.refresh(new_zen)
    return new_zen

@router.get("/zen-meditations", response_model=List[ZenMeditationResponse])
def list_zen_meditations(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """【功能 54】取得近期青年生活禪靜心打卡紀錄"""
    return db.query(ZenMeditation).order_by(ZenMeditation.id.desc()).limit(limit).all()

@router.get("/zen-stats")
def get_zen_stats(db: Session = Depends(get_db)):
    """【功能 54】青年生活禪靜心打卡大數據統計與菩提心境分佈"""
    all_meditations = db.query(ZenMeditation).all()
    total_sessions = len(all_meditations)
    total_mins = sum(m.duration_minutes or 0 for m in all_meditations)
    
    unique_members = len(set(m.participant_name for m in all_meditations))
    mood_counts = {}
    for m in all_meditations:
        mood = m.mood or "心平氣和"
        mood_counts[mood] = mood_counts.get(mood, 0) + 1

    zen_quotes = [
        "心中有佛，所見皆佛；安住當下，清涼自在。",
        "忙就是營養，要忙得歡喜，忙得健康，忙得有價值。",
        "微笑是世界上最美麗的語言，合掌是世界上最和平的姿態。",
        "給人信心，給人希望，給人歡喜，給人方便。",
        "心淨則國土淨，心安則眾生安。"
    ]
    import random
    daily_quote = random.choice(zen_quotes)

    return {
        "status": "success",
        "total_sessions": total_sessions,
        "total_minutes": total_mins,
        "total_hours": round(total_mins / 60.0, 1),
        "unique_participants": unique_members,
        "mood_distribution": mood_counts,
        "zen_quote": daily_quote
    }


# ==============================================================================
# 【功能 69】三好青年日常行善實踐微日記 API
# ==============================================================================
@router.post("/good-deeds", response_model=GoodDeedJournalResponse)
def create_good_deed_journal(
    journal_in: GoodDeedJournalCreate,
    db: Session = Depends(get_db)
):
    """【青年打卡】提交今日做好事、說好話、存好心三好實踐微日記"""
    new_j = GoodDeedJournal(
        author_name=journal_in.author_name or "三好青年",
        journal_date=journal_in.journal_date,
        good_deed=journal_in.good_deed,
        good_words=journal_in.good_words,
        good_heart=journal_in.good_heart,
        mood=journal_in.mood or "法喜充滿"
    )
    db.add(new_j)
    db.commit()
    db.refresh(new_j)
    return new_j

@router.get("/good-deeds", response_model=List[GoodDeedJournalResponse])
def list_good_deed_journals(
    author_name: Optional[str] = None,
    limit: int = 30,
    db: Session = Depends(get_db)
):
    """【公開/青年】調閱三好微日記動態打卡清單"""
    query = db.query(GoodDeedJournal)
    if author_name:
        query = query.filter(GoodDeedJournal.author_name == author_name)
    return query.order_by(GoodDeedJournal.id.desc()).limit(limit).all()

@router.get("/good-deeds/stats")
def get_good_deeds_stats(db: Session = Depends(get_db)):
    """【公開/青年】三好行善微日記大數據統計"""
    all_j = db.query(GoodDeedJournal).all()
    tot = len(all_j)
    authors = len(set(j.author_name for j in all_j))
    
    mood_dist = {}
    for j in all_j:
        m = j.mood or "法喜充滿"
        mood_dist[m] = mood_dist.get(m, 0) + 1
        
    return {
        "status": "success",
        "total_journals": tot,
        "participating_members": authors,
        "mood_distribution": mood_dist,
        "motto": "做好事舉手之勞功德大，說好話慈悲愛語如春風，存好心誠意正心自吉祥。"
    }
