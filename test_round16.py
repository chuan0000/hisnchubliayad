from fastapi.testclient import TestClient
from app.main import app
from app.auth import create_access_token

client = TestClient(app)

token = create_access_token({"sub": "admin", "role": "super_admin"})
headers = {"Authorization": f"Bearer {token}"}

print("=" * 60)
print("開始執行 Round 16 (功能 76-80) 全面自動化測試")
print("=" * 60)

# ----------------------------------------------------
# 測試【功能 76】活動現場即時報到人數與出席熱度大螢幕看板
# ----------------------------------------------------
print("\n[測試 1] 功能 76：現場即時報到熱度大螢幕看板 API...")
res_evs = client.get("/api/evidence")
assert res_evs.status_code == 200
evs = res_evs.json()
assert len(evs) > 0
item_id = evs[0]["id"]

res_dash = client.get(f"/api/evidence/{item_id}/live-checkin-dashboard")
assert res_dash.status_code == 200, f"Expected 200, got {res_dash.status_code}"
d_data = res_dash.json()
assert d_data["status"] == "success"
assert d_data["actual_checkins"] >= 1
assert "occupancy_rate_percent" in d_data
assert "dietary_breakdown" in d_data
print(f"  ✓ 現場即時報到看板通過：活動「{d_data['activity_title']}」，目前入座率 {d_data['occupancy_rate_percent']}%，狀態「{d_data['status_text']}」")

# ----------------------------------------------------
# 測試【功能 77】佛光三好祈福卡社群分享圖片生成器
# ----------------------------------------------------
print("\n[測試 2] 功能 77：三好祈福社群圖卡生成器 API...")
res_sc = client.get("/api/upload/social-share-card?quote=心淨則國土淨，心安則眾生安&author=星雲大師&youth_name=陳冠宇&theme=golden")
assert res_sc.status_code == 200
sc_data = res_sc.json()
assert sc_data["status"] == "success"
assert "<svg" in sc_data["svg_markup"]
assert "心淨則國土淨" in sc_data["svg_markup"]
print(f"  ✓ 社群分享圖卡向量 SVG 渲染通過：主題「{sc_data['theme']}」，發願青年「{sc_data['youth_name']}」")

# ----------------------------------------------------
# 測試【功能 78】道場場地借用與衝突排審
# ----------------------------------------------------
print("\n[測試 3] 功能 78：道場場地借用時段預約與衝突排審 API...")
res_v_list = client.get("/api/venues/list")
assert res_v_list.status_code == 200
v_list = res_v_list.json()
assert len(v_list) >= 4
print(f"  ✓ 道場弘法空間清冊通過：共 {len(v_list)} 處場所（涵蓋：{[v['name'] for v in v_list]}）")

res_bookings = client.get("/api/venues/bookings")
assert res_bookings.status_code == 200
assert len(res_bookings.json()) >= 3
print(f"  ✓ 場地預約清單通過：共 {len(res_bookings.json())} 筆排程")

# 測試衝突檢查
res_conflict = client.post("/api/venues/check-conflict", json={
    "venue_name": "青年團部會議室",
    "booking_date": "2026-11-01",
    "start_time": "15:00",
    "end_time": "16:00",
    "applicant_name": "測試青年"
})
assert res_conflict.status_code == 200
assert res_conflict.json()["has_conflict"] is True
print(f"  ✓ 時段衝突防呆檢核通過：成功偵測到既有預約衝突")

# 登記無衝突預約
res_add_vb = client.post("/api/venues/bookings", headers=headers, json={
    "venue_name": "滴水坊生活茶席",
    "booking_date": "2026-11-20",
    "start_time": "10:00",
    "end_time": "12:00",
    "applicant_name": "陳冠宇",
    "purpose": "青年茶道與生活思辨分享"
})
assert res_add_vb.status_code == 200
new_vb_id = res_add_vb.json()["id"]
print(f"  ✓ 登記新場地預約通過：ID {new_vb_id}")

res_del_vb = client.delete(f"/api/venues/bookings/{new_vb_id}", headers=headers)
assert res_del_vb.status_code == 200
print(f"  ✓ 取消場地預約通過")

# ----------------------------------------------------
# 測試【功能 79】青年學員法寶經典借閱歸還與心得反思卡
# ----------------------------------------------------
print("\n[測試 4] 功能 79：經典圖書借閱與心得反思卡 API...")
res_lib = client.get("/api/library/loans")
assert res_lib.status_code == 200
lib_loans = res_lib.json()
assert len(lib_loans) >= 3
print(f"  ✓ 圖書借閱清冊通過：共 {len(lib_loans)} 筆借閱紀錄")

res_lib_sum = client.get("/api/library/summary")
assert res_lib_sum.status_code == 200
lib_sum = res_lib_sum.json()
assert lib_sum["status"] == "success"
assert lib_sum["average_rating_stars"] >= 4.5
print(f"  ✓ 圖書流通大數據通過：總借次 {lib_sum['total_borrowed_times']} 次，讀者均評 ★ {lib_sum['average_rating_stars']}")

# 借書
res_add_bk = client.post("/api/library/loans", json={
    "book_title": "《佛法真義》",
    "call_number": "FGS-BK-077",
    "borrower_name": "測試同修",
    "borrow_date": "2026-10-16",
    "return_due_date": "2026-11-16"
})
assert res_add_bk.status_code == 200
bk_id = res_add_bk.json()["id"]
print(f"  ✓ 線上借閱經典出庫通過：ID {bk_id}")

# 還書並留心得
res_ret_bk = client.put(f"/api/library/loans/{bk_id}/return", json={
    "rating_stars": 5,
    "reflection_snippet": "深入淺出解析佛法精髓，非常受用！"
})
assert res_ret_bk.status_code == 200
print(f"  ✓ 圖書歸還並寫入五星反思便籤通過")

res_del_bk = client.delete(f"/api/library/loans/{bk_id}", headers=headers)
assert res_del_bk.status_code == 200
print(f"  ✓ 刪除借閱紀錄通過")

# ----------------------------------------------------
# 測試【功能 80】多語系在地化擴充（客語與台語三好法語）
# ----------------------------------------------------
print("\n[測試 5] 功能 80：多語系在地化客台法語擴充 API...")
res_dialects = client.get("/api/i18n/local-dialects")
assert res_dialects.status_code == 200
dial_data = res_dialects.json()
assert dial_data["status"] == "success"
assert "hakka_hailu" in dial_data["three_acts_of_goodness"]["languages"]
assert "taiwanese" in dial_data["three_acts_of_goodness"]["languages"]
hakka_good = dial_data["three_acts_of_goodness"]["languages"]["hakka_hailu"]["good_deed"]
taiwan_good = dial_data["three_acts_of_goodness"]["languages"]["taiwanese"]["good_deed"]
assert "zo si hao" in hakka_good
assert "tsò hó-sū" in taiwan_good
print(f"  ✓ 在地客語台語法語對照讀取通過：")
print(f"    - 新竹海陸客語三好：{hakka_good}")
print(f"    - 臺灣閩南語三好：{taiwan_good}")
print(f"    - 英文三好：{dial_data['three_acts_of_goodness']['languages']['en']['good_deed']}")
print(f"    - 日文三好：{dial_data['three_acts_of_goodness']['languages']['ja']['good_deed']}")

print("\n" + "=" * 60)
print("🎉🎉🎉 Round 16 (功能 76-80) 全部 5 項功能 100% 驗證通過！")
print("=" * 60)
