with open("app/routers/health.py", "r", encoding="utf-8") as f:
    health_code = f.read()

# Update import of schemas in health.py
old_import = "from app.schemas import HealthLogCreate, HealthLogResponse, ZenMeditationCreate, ZenMeditationResponse, GoodDeedJournalCreate, GoodDeedJournalResponse"
new_import = "from app.schemas import HealthLogCreate, HealthLogResponse, HealthReviewRequest, HealthLeaderboardResponse, HealthLeaderboardItem, ZenMeditationCreate, ZenMeditationResponse, GoodDeedJournalCreate, GoodDeedJournalResponse"

health_code = health_code.replace(old_import, new_import)

# Update create_health_log to save verification_type and review_status
old_create = """@router.post("", response_model=HealthLogResponse)
def create_health_log(
    log_in: HealthLogCreate,
    db: Session = Depends(get_db)
):
    \"\"\"【幹部或青年】新增健康打卡紀錄\"\"\"
    new_log = HealthLog(
        participant_name=log_in.participant_name,
        activity_type=log_in.activity_type or "walk",
        log_date=log_in.log_date,
        distance_km=log_in.distance_km or 0.0,
        steps=log_in.steps or 0,
        proof_image_url=log_in.proof_image_url or "",
        note=log_in.note or ""
    )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    return new_log"""

new_create = """@router.post("", response_model=HealthLogResponse)
def create_health_log(
    log_in: HealthLogCreate,
    db: Session = Depends(get_db)
):
    \"\"\"【青年/幹部】新增健康打卡紀錄（支援雙軌截圖核驗：裝置截圖 vs 視訊截圖）\"\"\"
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
    \"\"\"【幹部審核專區】取得所有待審核（pending）之青年打卡紀錄\"\"\"
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
    \"\"\"【幹部審核】審核青年雙軌打卡紀錄（核准 approved 或 退回 rejected，並附加鼓勵評語）\"\"\"
    from datetime import datetime
    log_item = db.query(HealthLog).filter(HealthLog.id == log_id).first()
    if not log_item:
        raise HTTPException(status_code=404, detail="找不到此打卡紀錄")
    
    log_item.review_status = review_in.review_status
    log_item.reviewer_name = review_in.reviewer_name
    log_item.reviewer_notes = review_in.reviewer_notes or ""
    log_item.reviewed_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    
    db.commit()
    db.refresh(log_item)
    return log_item


@router.get("/leaderboards", response_model=HealthLeaderboardResponse)
def get_health_leaderboards(db: Session = Depends(get_db)):
    \"\"\"【雙榜排行榜】連續打卡天數榜 (Streak Leaderboard) 與 累積里程先鋒榜 (Km Leaderboard)\"\"\"
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
    )"""

health_code = health_code.replace(old_create, new_create)

with open("app/routers/health.py", "w", encoding="utf-8") as f:
    f.write(health_code)

print("app/routers/health.py updated successfully.")
