from fastapi.testclient import TestClient
from app.main import app
from app.auth import create_access_token

client = TestClient(app)

token = create_access_token({"sub": "admin", "role": "super_admin"})
headers = {"Authorization": f"Bearer {token}"}

print("=" * 60)
print("開始執行 Round 18 (功能 86-90) 全面自動化測試")
print("=" * 60)

# ----------------------------------------------------
# 測試【功能 86】佛光三好茶席茶道品茗會預約與茶帖心靈籤語
# ----------------------------------------------------
print("\n[測試 1] 功能 86：三好生活茶席預約與心靈茶帖 API...")
res_slips = client.get("/api/tea-ceremony/slips")
assert res_slips.status_code == 200, f"Expected 200, got {res_slips.status_code}"
slip_data = res_slips.json()
assert slip_data["status"] == "success"
assert len(slip_data["tea_slip"]) > 5
print(f"  ✓ 抽取心靈茶帖通過：茶帖「{slip_data['tea_slip']}」")

res_add_tea = client.post("/api/tea-ceremony/bookings", json={
    "guest_name": "張同學",
    "guest_count": 2,
    "booking_date": "2026-11-25",
    "tea_time": "14:00 - 15:30",
    "tea_variety": "東方美人茶",
    "notes": "青年靜心品茗"
})
assert res_add_tea.status_code == 200
tea_res = res_add_tea.json()
tea_id = tea_res["id"]
print(f"  ✓ 預約生活茶席通過：ID {tea_id}，自動獲賜茶帖：「{tea_res['tea_slip_quote']}」")

res_del_tea = client.delete(f"/api/tea-ceremony/bookings/{tea_id}", headers=headers)
assert res_del_tea.status_code == 200
print(f"  ✓ 取消茶席預約通過")

# ----------------------------------------------------
# 測試【功能 87】活動滿意度 NPS 淨推薦值與青年體驗旅程
# ----------------------------------------------------
print("\n[測試 2] 功能 87：活動滿意度 NPS 淨推薦值與體驗旅程 API...")
res_evs = client.get("/api/evidence")
assert res_evs.status_code == 200
evs = res_evs.json()
assert len(evs) > 0
item_id = evs[0]["id"]

res_nps = client.get(f"/api/evidence/{item_id}/nps-analysis")
assert res_nps.status_code == 200
nps_data = res_nps.json()
assert nps_data["status"] == "success"
assert nps_data["total_respondents"] >= 5
assert -100 <= nps_data["nps_score"] <= 100
assert len(nps_data["journey_stages"]) == 5
print(f"  ✓ NPS 淨推薦值分析通過：活動「{nps_data['activity_title']}」，NPS 得分 {nps_data['nps_score']}（{nps_data['nps_grade']}），推薦者 {nps_data['promoters_percent']}%，體驗旅程涵蓋 5 階段")

# ----------------------------------------------------
# 測試【功能 88】青年團員徽章榮譽成就成就樹解鎖系統
# ----------------------------------------------------
print("\n[測試 3] 功能 88：青年成就榮譽徽章樹解鎖系統 API...")
res_b_sys = client.get("/api/team/badges/system")
assert res_b_sys.status_code == 200
b_sys = res_b_sys.json()
assert b_sys["status"] == "success"
assert b_sys["total_badges"] >= 6
print(f"  ✓ 徽章樹規範定義通過：共 {b_sys['total_badges']} 枚成就徽章（涵蓋：{[b['name'] for b in b_sys['badges'][:3]]}）")

res_m_badges = client.get("/api/team/badges/member/陳冠宇")
assert res_m_badges.status_code == 200
mb_data = res_m_badges.json()
assert mb_data["status"] == "success"
assert mb_data["volunteer_name"] == "陳冠宇"
assert mb_data["unlocked_count"] >= 3
print(f"  ✓ 陳冠宇成就徽章動態解鎖通過：已解鎖 {mb_data['unlocked_count']}/{mb_data['total_badges']} 枚徽章，成就達成率 {mb_data['completion_rate_percent']}%")

# ----------------------------------------------------
# 測試【功能 89】佛門行儀與殿堂禮儀動態圖解互動小測驗
# ----------------------------------------------------
print("\n[測試 4] 功能 89：佛門行儀與殿堂禮儀互動測驗 API...")
res_quiz = client.get("/api/etiquette/quiz")
assert res_quiz.status_code == 200
quiz_data = res_quiz.json()
assert quiz_data["status"] == "success"
assert quiz_data["total_questions"] == 5
print(f"  ✓ 取得佛門行儀題庫通過：共 {quiz_data['total_questions']} 題互動題目")

# 答題交卷
res_sub_q = client.post("/api/etiquette/submit-quiz", json=[0, 0, 0, 0, 0])
assert res_sub_q.status_code == 200
q_res = res_sub_q.json()
assert q_res["status"] == "success"
assert q_res["score"] == 100
assert q_res["passed"] is True
assert q_res["badge_awarded"] == "佛門威儀好青年"
print(f"  ✓ 測驗交卷計分通過：滿分 100 分，獲頒稱號「{q_res['badge_awarded']}」")

# ----------------------------------------------------
# 測試【功能 90】道場弘法大事紀歷年里程碑高畫質向量時序圖
# ----------------------------------------------------
print("\n[測試 5] 功能 90：大事紀歷年里程碑向量時序長圖 API...")
res_svg = client.get("/api/milestone-chart/svg")
assert res_svg.status_code == 200
svg_data = res_svg.json()
assert svg_data["status"] == "success"
assert svg_data["milestones_count"] >= 8
assert "<svg" in svg_data["svg_markup"]
assert "新竹青年分團 歷年弘法大事紀" in svg_data["svg_markup"]
print(f"  ✓ 向量時序長圖生成通過：共串聯 {svg_data['milestones_count']} 個重大歷史里程碑，SVG 畫布高度 {svg_data['total_height']}px")

print("\n" + "=" * 60)
print("🎉🎉🎉 Round 18 (功能 86-90) 全部 5 項功能 100% 驗證通過！")
print("=" * 60)
