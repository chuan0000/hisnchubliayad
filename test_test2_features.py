from fastapi.testclient import TestClient
from app.main import app
from app.database import engine, Base

# 確保資料表已建立
Base.metadata.create_all(bind=engine)

client = TestClient(app)

def test_feature1_dual_track_and_review():
    print("Testing Feature 1: Dual-track checkin & review workflow...")
    # 1. Submit device screenshot check-in
    payload1 = {
        "participant_name": "王大明",
        "activity_type": "run",
        "log_date": "2026-10-15",
        "distance_km": 5.2,
        "steps": 6500,
        "proof_image_url": "https://example.com/garmin_proof.jpg",
        "note": "清晨跑完十八尖山，法喜充滿",
        "verification_type": "device_screenshot",
        "review_status": "pending"
    }
    res1 = client.post("/api/health", json=payload1)
    assert res1.status_code == 200, res1.text
    data1 = res1.json()
    assert data1["verification_type"] == "device_screenshot"
    assert data1["review_status"] == "pending"
    log_id1 = data1["id"]

    # 2. Submit video screenshot check-in
    payload2 = {
        "participant_name": "李小美",
        "activity_type": "walk",
        "log_date": "2026-10-15",
        "distance_km": 3.0,
        "steps": 4000,
        "proof_image_url": "https://example.com/line_video_proof.jpg",
        "note": "參加青年團線上視訊健走連線打卡",
        "verification_type": "video_screenshot",
        "review_status": "pending"
    }
    res2 = client.post("/api/health", json=payload2)
    assert res2.status_code == 200, res2.text
    data2 = res2.json()
    assert data2["verification_type"] == "video_screenshot"
    log_id2 = data2["id"]

    # 3. List pending logs
    res_pend = client.get("/api/health/pending")
    assert res_pend.status_code == 200
    pend_list = res_pend.json()
    assert any(item["id"] == log_id1 for item in pend_list)
    assert any(item["id"] == log_id2 for item in pend_list)

    # 4. Cadre reviews log1 -> approve
    review_payload = {
        "review_status": "approved",
        "reviewer_name": "幹部陳冠宇",
        "reviewer_notes": "Garmin GPS 里程與配速核實無誤，三好精神讚！"
    }
    res_rev = client.put(f"/api/health/{log_id1}/review", json=review_payload)
    assert res_rev.status_code == 200
    rev_data = res_rev.json()
    assert rev_data["review_status"] == "approved"
    assert rev_data["reviewer_name"] == "幹部陳冠宇"
    assert "核實無誤" in rev_data["reviewer_notes"]
    print("Feature 1 Passed!")

def test_feature2_streak_and_leaderboards():
    print("Testing Feature 2: Streak calculation & Leaderboards...")
    # Add consecutive days for 王大明: 2026-10-16, 2026-10-17
    for date_str in ["2026-10-16", "2026-10-17"]:
        client.post("/api/health", json={
            "participant_name": "王大明",
            "activity_type": "run",
            "log_date": date_str,
            "distance_km": 4.0,
            "steps": 5000,
            "verification_type": "device_screenshot",
            "review_status": "approved"
        })

    res = client.get("/api/health/leaderboards")
    assert res.status_code == 200, res.text
    lb_data = res.json()
    assert "streak_leaderboard" in lb_data
    assert "distance_leaderboard" in lb_data
    
    streak_lb = lb_data["streak_leaderboard"]
    dist_lb = lb_data["distance_leaderboard"]
    assert len(streak_lb) > 0
    assert len(dist_lb) > 0
    
    # Check 王大明 in leaderboard
    wang = next((item for item in streak_lb if item["participant_name"] == "王大明"), None)
    assert wang is not None
    assert wang["current_streak"] >= 3  # 15, 16, 17 are consecutive!
    print(f"Feature 2 Passed! 王大明 Streak = {wang['current_streak']}, Total Km = {wang['total_km']}")

def test_feature3_youth_wishlist_wall():
    print("Testing Feature 3: Youth Wishlist Wall...")
    # 1. Create a wish
    payload = {
        "title": "購置青年團健走與夜跑高反光安全背心 20 件",
        "category": "sports_gear",
        "description": "提供團員夜跑與走讀活動時穿戴，提升夜間辨識度與安全",
        "estimated_budget": 3500.0,
        "created_by": "青年活動組"
    }
    res = client.post("/api/wishlist", json=payload)
    assert res.status_code == 200, res.text
    wish_data = res.json()
    assert wish_data["title"] == payload["title"]
    assert wish_data["status"] == "open"
    assert wish_data["likes_count"] == 0
    wish_id = wish_data["id"]

    # 2. Like the wish (+1)
    res_like = client.post(f"/api/wishlist/{wish_id}/like")
    assert res_like.status_code == 200
    assert res_like.json()["likes_count"] == 1

    # 3. Update status to fulfilled
    status_payload = {
        "status": "fulfilled",
        "sponsor_note": "感謝常住法師慈悲結緣護持，物資已採購到位！"
    }
    res_status = client.put(f"/api/wishlist/{wish_id}/status", json=status_payload)
    assert res_status.status_code == 200
    assert res_status.json()["status"] == "fulfilled"
    assert "感謝常住" in res_status.json()["sponsor_note"]

    # 4. Summary
    res_sum = client.get("/api/wishlist/summary")
    assert res_sum.status_code == 200
    sum_data = res_sum.json()
    assert sum_data["total_wishes"] >= 1
    assert sum_data["fulfilled_wishes"] >= 1
    assert sum_data["total_likes"] >= 1
    print("Feature 3 Passed!")

def test_feature4_event_crawler():
    print("Testing Feature 4: Social / Event Crawler...")
    # 1. Get sources
    res_src = client.get("/api/crawler/sources")
    assert res_src.status_code == 200
    assert "sources" in res_src.json()

    # 2. Trigger fetch
    res_crawl = client.post("/api/crawler/fetch-external-events")
    assert res_crawl.status_code == 200, res_crawl.text
    events = res_crawl.json()
    assert len(events) >= 1
    event_id = events[0]["id"]


    # Login as admin to get auth header
    login_res = client.post("/api/auth/login", json={"username": "admin", "password": "blia123456"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Import crawled event to evidence
    res_imp = client.post(f"/api/crawler/events/{event_id}/import-to-evidence?category=culture", headers=headers)

    assert res_imp.status_code == 200, res_imp.text
    imp_data = res_imp.json()
    assert imp_data["status"] == "success"
    assert "evidence_id" in imp_data
    print(f"Feature 4 Passed! Imported crawled event ID {event_id} into evidence ID {imp_data['evidence_id']}")

if __name__ == "__main__":
    test_feature1_dual_track_and_review()
    test_feature2_streak_and_leaderboards()
    test_feature3_youth_wishlist_wall()
    test_feature4_event_crawler()
    print("\nALL 4 FEATURES TESTED AND PASSED 100%!")
