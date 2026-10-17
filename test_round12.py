from fastapi.testclient import TestClient
from app.main import app
from app.auth import create_access_token

client = TestClient(app)

token = create_access_token({"sub": "admin", "role": "super_admin"})
headers = {"Authorization": f"Bearer {token}"}

print("=" * 60)
print("開始執行 Round 12 (功能 56-60) 全面自動化測試")
print("=" * 60)

# ----------------------------------------------------
# 測試【功能 56】三好青年數位電子志工證 / 會員證
# ----------------------------------------------------
print("\n[測試 1] 功能 56：三好青年數位電子志工證 / 會員證 API...")
res_card = client.get("/api/team/digital-id/陳冠宇")
assert res_card.status_code == 200, f"Expected 200, got {res_card.status_code}"
card_data = res_card.json()
assert card_data["status"] == "success"
assert card_data["volunteer_name"] == "陳冠宇"
assert "BLIA-HCY-MEMBER-" in card_data["member_no"]
assert card_data["total_hours"] >= 34.0
assert "<svg" in card_data["barcode_svg"]
assert "有效會員證" in card_data["status_text"]
print(f"  ✓ 數位會員證測試通過：會員編號 {card_data['member_no']}，星級「{card_data['star_level']}」，累積時數 {card_data['total_hours']}h，SVG條碼產生成功")

# ----------------------------------------------------
# 測試【功能 57】活動經費線上請購預算與核銷請款單
# ----------------------------------------------------
print("\n[測試 2] 功能 57：活動經費線上請購預算與核銷請款單 API...")
res_budget_list = client.get("/api/budget")
assert res_budget_list.status_code == 200
b_list = res_budget_list.json()
assert len(b_list) >= 5
print(f"  ✓ 調閱經費請購單通過：共 {len(b_list)} 筆請購紀錄")

res_budget_sum = client.get("/api/budget/summary")
assert res_budget_sum.status_code == 200
b_sum = res_budget_sum.json()
assert b_sum["status"] == "success"
assert b_sum["total_requested"] > 40000
assert b_sum["execution_rate_percent"] > 50
print(f"  ✓ 預算執行率摘要通過：申請總額 ${b_sum['total_requested']}，已核准 ${b_sum['total_approved']}，執行率 {b_sum['execution_rate_percent']}%")

# 新增請購單
res_add_b = client.post("/api/budget", headers=headers, json={
    "title": "2026佛光青年共修生活茶席物資購置",
    "applicant_name": "陳冠宇",
    "category": "活動耗材",
    "requested_amount": 3600.0,
    "approved_amount": 0.0,
    "status": "待審核",
    "notes": "茶具與有機高山茶葉採購"
})
assert res_add_b.status_code == 200
new_b_id = res_add_b.json()["id"]
print(f"  ✓ 新增經費請購單通過：ID {new_b_id}")

# 審核請購單
res_app_b = client.put(f"/api/budget/{new_b_id}/approve?approved_amount=3600", headers=headers)
assert res_app_b.status_code == 200
print(f"  ✓ 審核經費請購單通過")

# 刪除測試請購單
res_del_b = client.delete(f"/api/budget/{new_b_id}", headers=headers)
assert res_del_b.status_code == 200
print(f"  ✓ 刪除經費請購單通過")

# ----------------------------------------------------
# 測試【功能 58】道場法會與活動現場排班表甘特時序
# ----------------------------------------------------
print("\n[測試 3] 功能 58：道場法會與活動現場排班表甘特時序 API...")
res_roster_list = client.get("/api/roster")
assert res_roster_list.status_code == 200
r_list = res_roster_list.json()
assert len(r_list) >= 7
print(f"  ✓ 志工排班清單通過：共 {len(r_list)} 筆現場排班")

res_gantt = client.get("/api/roster/gantt")
assert res_gantt.status_code == 200
gantt_data = res_gantt.json()
assert gantt_data["status"] == "success"
assert len(gantt_data["activities"]) >= 2
print(f"  ✓ 甘特排班矩陣分組通過：共 {len(gantt_data['activities'])} 場重大法會活動")

# 新增排班
res_add_s = client.post("/api/roster", headers=headers, json={
    "activity_title": "2026新竹青年浴佛法會",
    "shift_date": "2026-05-10",
    "shift_time": "13:00 - 17:00",
    "role_name": "場務組",
    "volunteer_name": "林思妤",
    "status": "已確認",
    "notes": "午後善後與供品整理"
})
assert res_add_s.status_code == 200
shift_id = res_add_s.json()["id"]
print(f"  ✓ 新增排班項目通過：ID {shift_id}")

# 移除測試排班
res_del_s = client.delete(f"/api/roster/{shift_id}", headers=headers)
assert res_del_s.status_code == 200
print(f"  ✓ 移除排班項目通過")

# ----------------------------------------------------
# 測試【功能 59】青年學員活動出席歷程與成長雷達
# ----------------------------------------------------
print("\n[測試 4] 功能 59：青年學員活動出席歷程與成長雷達 API...")
res_radar = client.get("/api/team/growth-radar/陳冠宇")
assert res_radar.status_code == 200
r_data = res_radar.json()
assert r_data["status"] == "success"
assert r_data["volunteer_name"] == "陳冠宇"
assert r_data["overall_score"] > 60
assert len(r_data["radar_axes"]) == 5
assert len(r_data["mentor_advice"]) > 5
print(f"  ✓ 陳冠宇成長雷達分析通過：五維總評 {r_data['overall_score']} 分，稱號「{r_data['rank_title']}」，導師寄語：「{r_data['mentor_advice']}」")

res_radar_all = client.get("/api/team/growth-radar/summary/all")
assert res_radar_all.status_code == 200
all_radars = res_radar_all.json()
assert all_radars["status"] == "success"
assert len(all_radars["leaderboard"]) >= 5
print(f"  ✓ 全員成長排行榜通過：共評估 {all_radars['total_members']} 位青年學員")

# ----------------------------------------------------
# 測試【功能 60】站內即時公告推播跑馬燈與彈窗通知
# ----------------------------------------------------
print("\n[測試 5] 功能 60：站內即時公告推播跑馬燈與彈窗通知 API...")
res_active_ann = client.get("/api/announcements/active")
assert res_active_ann.status_code == 200
ann_active = res_active_ann.json()
assert ann_active["status"] == "success"
assert len(ann_active["marquee"]) >= 2
assert len(ann_active["popups"]) >= 1
print(f"  ✓ 前台有效公告通過：跑馬燈 {len(ann_active['marquee'])} 則，彈窗推播 {len(ann_active['popups'])} 則")

res_add_ann = client.post("/api/announcements", headers=headers, json={
    "title": "【自動化測試】全站通知管道連線正常",
    "content": "系統測試廣播已通過驗證",
    "announcement_type": "info",
    "is_marquee": True,
    "is_popup": False,
    "priority": 99
})
assert res_add_ann.status_code == 200
test_ann_id = res_add_ann.json()["id"]
print(f"  ✓ 建立即時推播公告通過：ID {test_ann_id}")

res_del_ann = client.delete(f"/api/announcements/{test_ann_id}", headers=headers)
assert res_del_ann.status_code == 200
print(f"  ✓ 刪除即時推播公告通過")

print("\n" + "=" * 60)
print("🎉🎉🎉 Round 12 (功能 56-60) 全部 5 項功能 100% 驗證通過！")
print("=" * 60)
