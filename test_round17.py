from fastapi.testclient import TestClient
from app.main import app
from app.auth import create_access_token

client = TestClient(app)

token = create_access_token({"sub": "admin", "role": "super_admin"})
headers = {"Authorization": f"Bearer {token}"}

print("=" * 60)
print("開始執行 Round 17 (功能 81-85) 全面自動化測試")
print("=" * 60)

# ----------------------------------------------------
# 測試【功能 81】青年活動現場失物招領與尋獲認領登記處
# ----------------------------------------------------
print("\n[測試 1] 功能 81：活動失物招領與認領處 API...")
res_lost = client.get("/api/lost-found")
assert res_lost.status_code == 200, f"Expected 200, got {res_lost.status_code}"
lost_items = res_lost.json()
assert len(lost_items) >= 3
print(f"  ✓ 失物招領清單讀取通過：共 {len(lost_items)} 筆拾得紀錄")

res_lost_sum = client.get("/api/lost-found/summary")
assert res_lost_sum.status_code == 200
l_sum = res_lost_sum.json()
assert l_sum["status"] == "success"
assert l_sum["pending_claim"] >= 2
print(f"  ✓ 失物招領盤點統計通過：待認領 {l_sum['pending_claim']} 件，已領回 {l_sum['claimed_count']} 件")

# 新增失物
res_add_l = client.post("/api/lost-found", json={
    "item_name": "星雲大師法語書籤 (金色)",
    "category": "其他",
    "found_location": "法寶寺滴水坊茶席",
    "found_date": "2026-10-16",
    "finder_name": "陳冠宇",
    "notes": "夾在讀書會筆記本中"
})
assert res_add_l.status_code == 200
new_lost_id = res_add_l.json()["id"]
print(f"  ✓ 登記拾得遺失物通過：ID {new_lost_id}")

# 認領核銷
res_claim = client.put(f"/api/lost-found/{new_lost_id}/claim", json={"claimer_name": "王同學"})
assert res_claim.status_code == 200
print(f"  ✓ 失主認領核銷手續通過")

res_del_l = client.delete(f"/api/lost-found/{new_lost_id}", headers=headers)
assert res_del_l.status_code == 200
print(f"  ✓ 刪除失物紀錄通過")

# ----------------------------------------------------
# 測試【功能 82】新竹與竹北青年共乘交通媒合與減碳里程計算
# ----------------------------------------------------
print("\n[測試 2] 功能 82：青年共乘與低碳減碳里程 API...")
res_cp = client.get("/api/carpool")
assert res_cp.status_code == 200
cp_trips = res_cp.json()
assert len(cp_trips) >= 3
print(f"  ✓ 青年共乘車次列表通過：共 {len(cp_trips)} 車次")

res_cp_sum = client.get("/api/carpool/summary")
assert res_cp_sum.status_code == 200
cp_sum = res_cp_sum.json()
assert cp_sum["status"] == "success"
assert cp_sum["total_carbon_saved_kg"] > 10.0
print(f"  ✓ 綠色減碳數據大數據統計通過：累計減碳 {cp_sum['total_carbon_saved_kg']} kg CO₂")

# 發布共乘行程
res_add_cp = client.post("/api/carpool", json={
    "driver_name": "測試青年",
    "departure_location": "清華大學南門",
    "destination": "新竹法寶寺",
    "departure_time": "2026-11-05 08:30",
    "available_seats": 3,
    "distance_km": 10.0,
    "contact_info": "Line: nthu_youth"
})
assert res_add_cp.status_code == 200
new_cp_id = res_add_cp.json()["id"]
print(f"  ✓ 發布共乘行程通過：ID {new_cp_id}，自動試算減碳 {res_add_cp.json()['carbon_saved_kg']} kg")

# 預約座位
res_book_cp = client.put(f"/api/carpool/{new_cp_id}/book")
assert res_book_cp.status_code == 200
print(f"  ✓ 預約共乘座位通過")

res_del_cp = client.delete(f"/api/carpool/{new_cp_id}", headers=headers)
assert res_del_cp.status_code == 200
print(f"  ✓ 刪除共乘車次通過")

# ----------------------------------------------------
# 測試【功能 83】佛光三好Podcast《竹光三參》逐字稿與音訊章節筆記庫
# ----------------------------------------------------
print("\n[測試 3] 功能 83：Podcast《竹光三參》逐字稿與章節筆記庫 API...")
res_pod = client.get("/api/podcasts")
assert res_pod.status_code == 200
episodes = res_pod.json()
assert len(episodes) >= 2
print(f"  ✓ 取得 Podcast 全部集數通過：共 {len(episodes)} 集（最新：{episodes[0]['episode_number']} - {episodes[0]['title']}）")

# 新增集數
res_add_ep = client.post("/api/podcasts", headers=headers, json={
    "episode_number": "EP20",
    "title": "【竹光三參】國際青年大會震撼直擊：與全球三好青年的心靈對話",
    "host_name": "冠宇 & 思妤",
    "guest_name": "世界青年總會副秘書長",
    "duration_minutes": 32,
    "summary": "跨越五大洲佛光青年的真誠交流，探討海外道場青年如何弘傳人間佛教。",
    "chapter_timestamps": "00:00 精彩片頭 / 05:00 世界青年大會緣起 / 18:00 跨文化同理心 / 28:00 三好祝福",
    "key_quotes": "「佛光普照三千界，法水長流五大洲。青年在哪裡，佛教希望就在哪裡。」"
})
assert res_add_ep.status_code == 200
new_ep_id = res_add_ep.json()["id"]
print(f"  ✓ 上架 Podcast 篇章通過：ID {new_ep_id}")

res_del_ep = client.delete(f"/api/podcasts/{new_ep_id}", headers=headers)
assert res_del_ep.status_code == 200
print(f"  ✓ 刪除 Podcast 集數通過")

# ----------------------------------------------------
# 測試【功能 84】青年幹部值班輪值與道場巡檢交接電子日誌
# ----------------------------------------------------
print("\n[測試 4] 功能 84：幹部值班巡檢交接電子日誌 API...")
res_duty = client.get("/api/team/duty-logs", headers=headers)
assert res_duty.status_code == 200
duties = res_duty.json()
assert len(duties) >= 2
print(f"  ✓ 幹部巡檢日誌清冊通過：共 {len(duties)} 篇交接紀錄")

res_duty_sum = client.get("/api/team/duty-logs/summary", headers=headers)
assert res_duty_sum.status_code == 200
d_sum = res_duty_sum.json()
assert d_sum["status"] == "success"
assert d_sum["inspection_safety_rate"] == 100.0
print(f"  ✓ 道場巡檢執行率通過：安全落實率 {d_sum['inspection_safety_rate']}%，狀態「{d_sum['security_status']}」")

# 提交巡檢日誌
res_add_d = client.post("/api/team/duty-logs", headers=headers, json={
    "duty_date": "2026-10-25",
    "duty_cadre": "陳冠宇",
    "inspection_items_checked": True,
    "hall_lights_status": "正常關閉",
    "ac_status": "已斷電",
    "security_status": "防盜安全鎖閉",
    "handover_notes": "大殿供品花果已收拾完畢，巡檢正常",
    "next_duty_cadre": "林思妤"
})
assert res_add_d.status_code == 200
print(f"  ✓ 提交幹部巡檢日誌通過")

# ----------------------------------------------------
# 測試【功能 85】國際佛光青年交流外語自我介紹與英文佛學單字卡
# ----------------------------------------------------
print("\n[測試 5] 功能 85：國際青年交流英文佛學閃卡與自介產生器 API...")
res_fc = client.get("/api/exchange/flashcards")
assert res_fc.status_code == 200
fc_list = res_fc.json()
assert len(fc_list) >= 5
print(f"  ✓ 國際交流雙語佛學詞彙閃卡通過：共 {len(fc_list)} 張核心詞彙卡（涵蓋：{[f['term_zh'] for f in fc_list]}）")

res_intro = client.get("/api/exchange/intro-template?name=Chen%20Kuan-Yu&role=Subgroup%20President&interests=Video%20production%20and%20Life%20Zen")
assert res_intro.status_code == 200
intro_data = res_intro.json()
assert intro_data["status"] == "success"
assert "Chen Kuan-Yu" in intro_data["speech_template"]
assert "Auspicious Greetings" in intro_data["speech_template"]
assert "吉祥" in intro_data["icebreaker_tip"]
print(f"  ✓ 國際會議英文自我介紹演講講稿生成通過：")
print(f"    講稿摘錄：{intro_data['speech_template'][:60]}...")
print(f"    破冰技巧：{intro_data['icebreaker_tip']}")

print("\n" + "=" * 60)
print("🎉🎉🎉 Round 17 (功能 81-85) 全部 5 項功能 100% 驗證通過！")
print("=" * 60)
