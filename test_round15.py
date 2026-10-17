from fastapi.testclient import TestClient
from app.main import app
from app.auth import create_access_token

client = TestClient(app)

token = create_access_token({"sub": "admin", "role": "super_admin"})
headers = {"Authorization": f"Bearer {token}"}

print("=" * 60)
print("開始執行 Round 15 (功能 71-75) 全面自動化測試")
print("=" * 60)

# ----------------------------------------------------
# 測試【功能 71】三好微電影與短片創作腳本分鏡故事板
# ----------------------------------------------------
print("\n[測試 1] 功能 71：三好微電影分鏡故事板 API...")
res_boards = client.get("/api/storyboards")
assert res_boards.status_code == 200, f"Expected 200, got {res_boards.status_code}"
boards = res_boards.json()
assert len(boards) >= 4
print(f"  ✓ 分鏡場景列表讀取通過：共 {len(boards)} 個分鏡場景")

res_films = client.get("/api/storyboards/films")
assert res_films.status_code == 200
films = res_films.json()
assert films["status"] == "success"
assert len(films["films"]) >= 2
print(f"  ✓ 微電影專案進度總覽通過：共 {len(films['films'])} 部微電影（首部：{films['films'][0]['film_title']}，進度 {films['films'][0]['progress_percent']}%）")

# 新增分鏡
res_add_sc = client.post("/api/storyboards", headers=headers, json={
    "film_title": "《竹光閃耀・三好同行》形象微電影",
    "scene_number": "S04",
    "shot_type": "特寫",
    "visual_description": "微距拍攝青年手持蓮花心燈，眼神充滿法喜與堅定願力",
    "dialogue": "「點一盞心燈，照亮世界每一个角落。」",
    "location": "大雄寶殿前",
    "status": "未拍攝"
})
assert res_add_sc.status_code == 200
new_sc_id = res_add_sc.json()["id"]
print(f"  ✓ 新增分鏡場景通過：ID {new_sc_id}")

res_del_sc = client.delete(f"/api/storyboards/{new_sc_id}", headers=headers)
assert res_del_sc.status_code == 200
print(f"  ✓ 刪除分鏡場景通過")

# ----------------------------------------------------
# 測試【功能 72】道場法會隨喜功德箱雲端收據產生器
# ----------------------------------------------------
print("\n[測試 2] 功能 72：隨喜功德箱雲端收據產生器 API...")
res_don = client.get("/api/donations")
assert res_don.status_code == 200
don_list = res_don.json()
assert len(don_list) >= 4
print(f"  ✓ 功德芳名錄清冊通過：共 {len(don_list)} 筆隨喜收據")

res_don_sum = client.get("/api/donations/summary")
assert res_don_sum.status_code == 200
d_sum = res_don_sum.json()
assert d_sum["status"] == "success"
assert d_sum["total_amount"] >= 10000
print(f"  ✓ 隨喜總額大數據統計通過：累計募得善款 ${d_sum['total_amount']} 元")

# 登記新隨喜
res_add_d = client.post("/api/donations", json={
    "donor_name": "王大明",
    "donation_type": "護持青年基金",
    "amount": 2500.0,
    "payment_method": "轉帳",
    "dedication_notes": "祈求闔家平安吉祥"
})
assert res_add_d.status_code == 200
don_res = res_add_d.json()
rec_no = don_res["receipt_no"]
print(f"  ✓ 登記隨喜功德並產製收據通過：字號 {rec_no}")

# 產製電子收據卡
res_card = client.get(f"/api/donations/{rec_no}/card")
assert res_card.status_code == 200
card_data = res_card.json()
assert card_data["status"] == "success"
assert card_data["donor_name"] == "王大明"
assert "施者受者" in card_data["blessing_quote"]
print(f"  ✓ 電子功德收據卡片產製通過：法語「{card_data['blessing_quote'][:16]}...」")

# ----------------------------------------------------
# 測試【功能 73】佛光青年梵唄法器音聲練習調音與節拍器
# ----------------------------------------------------
print("\n[測試 3] 功能 73：佛光青年梵唄法器練習庫 API...")
res_ch = client.get("/api/chanting")
assert res_ch.status_code == 200
ch_list = res_ch.json()
assert len(ch_list) >= 3
print(f"  ✓ 梵唄練習曲目清單通過：共 {len(ch_list)} 首曲目")

res_inst = client.get("/api/chanting/instruments")
assert res_inst.status_code == 200
inst_list = res_inst.json()
assert len(inst_list) >= 2
print(f"  ✓ 法器分類清單通過：{[i['instrument_type'] for i in inst_list]}")

# ----------------------------------------------------
# 測試【功能 74】青年生涯職涯發展與三好職場導師諮詢預約
# ----------------------------------------------------
print("\n[測試 4] 功能 74：青年生涯職場導師預約諮詢 API...")
res_mentors = client.get("/api/team/mentors")
assert res_mentors.status_code == 200
m_list = res_mentors.json()
assert len(m_list) >= 3
print(f"  ✓ 職場導師清冊通過：共 {len(m_list)} 位專業導師（涵蓋：{[m['mentor_field'] for m in m_list]}）")

res_add_app = client.post("/api/team/mentorships", json={
    "mentor_name": "林學長 (資深IC設計研發主管)",
    "mentor_field": "半導體科技",
    "applicant_name": "張佑安",
    "appointment_date": "2026-11-02",
    "appointment_time": "19:30 - 20:30",
    "topic": "科技業資料庫與軟體工程師求職面試心態"
})
assert res_add_app.status_code == 200
app_id = res_add_app.json()["id"]
print(f"  ✓ 青年職涯諮詢預約寫入通過：ID {app_id}")

res_up_app = client.put(f"/api/team/mentorships/{app_id}/status", headers=headers, json={"status": "已完成"})
assert res_up_app.status_code == 200
print(f"  ✓ 更新會談進度通過")

# ----------------------------------------------------
# 測試【功能 75】全站數據匯出備份 JSON 多合一封裝包
# ----------------------------------------------------
print("\n[測試 5] 功能 75：全站多合一數據匯出封裝包 API...")
res_exp_sum = client.get("/api/export-pack/summary")
assert res_exp_sum.status_code == 200
exp_sum = res_exp_sum.json()
assert exp_sum["status"] == "success"
assert exp_sum["total_tables"] >= 10
assert exp_sum["total_records"] > 50
print(f"  ✓ 資料庫封裝矩陣統計通過：共封裝 {exp_sum['total_tables']} 個資料表，全站總記錄數 {exp_sum['total_records']} 筆")

res_exp_json = client.get("/api/export-pack/json")
assert res_exp_json.status_code == 200
exp_json = res_exp_json.json()
assert exp_json["export_metadata"]["system"] == "國際佛光會新竹青年分團 CMS"
assert "volunteer_passbooks" in exp_json["data"]
assert "zen_meditations" in exp_json["data"]
assert "film_storyboards" in exp_json["data"]
print(f"  ✓ 全站 JSON 數據備份封裝包生成通過：資料版本 {exp_json['export_metadata']['version']}，匯出時間: {exp_json['export_metadata']['export_time']}")

print("\n" + "=" * 60)
print("🎉🎉🎉 Round 15 (功能 71-75) 全部 5 項功能 100% 驗證通過！")
print("=" * 60)
