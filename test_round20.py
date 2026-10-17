from fastapi.testclient import TestClient
from app.main import app
from app.auth import create_access_token

client = TestClient(app)
token = create_access_token({"sub": "admin", "role": "super_admin"})
headers = {"Authorization": f"Bearer {token}"}

print("=" * 60)
print("開始執行 Round 20 (功能 96-100) 全面自動化測試")
print("=" * 60)

# ----------------------------------------------------
# 測試【功能 96】佛光三好微行持每日福慧籤卡與智慧法語庫
# ----------------------------------------------------
print("\n[測試 1] 功能 96：佛光三好微行持每日福慧籤卡 API...")
res_rand = client.get("/api/wisdom-cards/random")
assert res_rand.status_code == 200, res_rand.text
data_rand = res_rand.json()
assert data_rand["status"] == "success"
assert "card" in data_rand
assert "svg_markup" in data_rand
assert "<svg" in data_rand["svg_markup"]
print(f"  ✓ 隨機福慧籤卡抽取通過：主題「{data_rand['card']['theme']}」，出處「{data_rand['card']['source']}」")

res_list = client.get("/api/wisdom-cards")
assert res_list.status_code == 200, res_list.text
cards = res_list.json()
assert len(cards) >= 1
print(f"  ✓ 智慧法語清冊調閱通過：共 {len(cards)} 張籤卡")

# 新增法語卡
res_add = client.post("/api/wisdom-cards", json={
    "theme": "精進波羅蜜",
    "quote": "精進是不疲不倦的勇氣，是轉凡成聖的活水源頭。",
    "source": "星雲大師《佛光菜根譚》",
    "practical_action": "今日為常住或大眾默默承擔一件有意義的事。",
    "bg_color": "#FFFBEB"
}, headers=headers)
assert res_add.status_code in [200, 201], res_add.text
created_card = res_add.json()
card_id = created_card["id"]

# SVG 排版
res_svg = client.get(f"/api/wisdom-cards/{card_id}/card-svg")
assert res_svg.status_code == 200, res_svg.text
assert "<svg" in res_svg.text
assert "精進波羅蜜" in res_svg.text
print("  ✓ 高畫質直排福慧籤卡 SVG 產生通過")

# 刪除法語卡
res_del = client.delete(f"/api/wisdom-cards/{card_id}", headers=headers)
assert res_del.status_code == 200, res_del.text
print("  ✓ 刪除法語籤卡通過")

# ----------------------------------------------------
# 測試【功能 97】道場活動突發事件應變與青年安撫SOP指南庫
# ----------------------------------------------------
print("\n[測試 2] 功能 97：道場活動突發事件應變與青年安撫 SOP 指南 API...")
res_sops = client.get("/api/emergency-sops")
assert res_sops.status_code == 200, res_sops.text
sops = res_sops.json()
assert len(sops) >= 1
print(f"  ✓ 緊急事件 SOP 清冊調閱通過：共 {len(sops)} 項標準處置指南")

first_sop = sops[0]
res_detail = client.get(f"/api/emergency-sops/{first_sop['id']}")
assert res_detail.status_code == 200, res_detail.text
sop_data = res_detail.json()
assert "immediate_actions" in sop_data
assert "calming_script" in sop_data
print(f"  ✓ 調閱 SOP 詳情通過：處置情境「{sop_data['incident_type']}」")

# 新增與刪除 SOP
res_sop_add = client.post("/api/emergency-sops", json={
    "incident_type": "戶外走讀學員隨身貴重物品遺失",
    "severity_level": "level_1",
    "immediate_actions": "1. 詢問最後目擊時間地點。2. 請幹部沿線折返搜尋。3. 調閱分團公務背包確認。",
    "escalation_contact": "小隊輔 -> 庶務組長",
    "calming_script": "同學不要著急，大家都在幫忙找，先定下心來。",
    "first_aid_kit_location": "法寶寺 2F 青年團部"
}, headers=headers)
assert res_sop_add.status_code in [200, 201], res_sop_add.text
created_sop = res_sop_add.json()
res_sop_del = client.delete(f"/api/emergency-sops/{created_sop['id']}", headers=headers)
assert res_sop_del.status_code == 200, res_sop_del.text
print("  ✓ 新增與刪除應變處置 SOP 通過")

# ----------------------------------------------------
# 測試【功能 98】青年義工團隊動能與向心力健康指數評估器
# ----------------------------------------------------
print("\n[測試 3] 功能 98：青年義工團隊動能與向心力健康指數評估器 API...")
res_health = client.get("/api/team/dynamics-health/latest")
assert res_health.status_code == 200, res_health.text
health_data = res_health.json()
assert health_data["status"] == "success"
assert "composite_health_index" in health_data
assert "radar_series" in health_data
assert len(health_data["radar_series"]) == 4
print(f"  ✓ 最新團隊動能向心力評估通過：綜合指數 {health_data['composite_health_index']} 分（狀態：{health_data['status_level']}）")

res_health_list = client.get("/api/team/dynamics-health")
assert res_health_list.status_code == 200, res_health_list.text
print(f"  ✓ 歷期向心力評估紀錄清單通過：共 {len(res_health_list.json())} 筆評估")

# 幹部提交新一期評估
res_health_post = client.post("/api/team/dynamics-health", json={
    "evaluation_period": "2026 Q4 (預估)",
    "attendance_rate": 93.0,
    "cross_support_score": 91.0,
    "good_deeds_activity_score": 95.0,
    "cadre_satisfaction_score": 94.0,
    "leadership_recommendation": "百大功能里程碑達成，團隊向心力攀至頂峰！"
}, headers=headers)
assert res_health_post.status_code in [200, 201], res_health_post.text
print("  ✓ 幹部提交向心力健康評估通過")

# ----------------------------------------------------
# 測試【功能 99】佛門茶水點心與蔬食環保無肉菜單食譜庫
# ----------------------------------------------------
print("\n[測試 4] 功能 99：佛門茶水點心與蔬食環保無肉菜單食譜庫 API...")
res_recipes = client.get("/api/vegetarian-recipes")
assert res_recipes.status_code == 200, res_recipes.text
recipes = res_recipes.json()
assert len(recipes) >= 1
print(f"  ✓ 蔬食食譜清單調閱通過：共 {len(recipes)} 道健康全素食譜")

res_recipe_stats = client.get("/api/vegetarian-recipes/stats")
assert res_recipe_stats.status_code == 200, res_recipe_stats.text
stats_data = res_recipe_stats.json()
assert stats_data["status"] == "success"
assert "total_carbon_offset_kg" in stats_data
print(f"  ✓ 蔬食無肉減碳大數據分析通過：累計減碳效益 {stats_data['total_carbon_offset_kg']} kg CO₂")

# 新增與刪除食譜
res_rec_add = client.post("/api/vegetarian-recipes", json={
    "dish_name": "清涼降火三好綠豆薏仁甜湯",
    "category": "beverage",
    "ingredients": "毛綠豆 100g、大薏仁 50g、純純紅冰糖 30g、過濾水 1000ml",
    "steps": "1. 綠豆薏仁洗淨浸泡2小時。2. 慢火燉煮40分鐘至軟爛。3. 加入冰糖調味放涼即成消暑甜品。",
    "dietary_tags": "全素,生津消暑",
    "carbon_offset_kg": 1.2,
    "prep_difficulty": "easy"
}, headers=headers)
assert res_rec_add.status_code in [200, 201], res_rec_add.text
created_rec = res_rec_add.json()
res_rec_del = client.delete(f"/api/vegetarian-recipes/{created_rec['id']}", headers=headers)
assert res_rec_del.status_code == 200, res_rec_del.text
print("  ✓ 新增與刪除蔬食食譜通過")

# ----------------------------------------------------
# 測試【功能 100】佛光青年分團年度弘法成效大數據全景總覽與百年弘法白皮書
# ----------------------------------------------------
print("\n[測試 5] 功能 100：【百項成就盛典】大數據全景總覽與百年弘法白皮書 API...")
res_pano = client.get("/api/centenary/panorama-dashboard")
assert res_pano.status_code == 200, res_pano.text
pano_data = res_pano.json()
assert pano_data["status"] == "success"
assert pano_data["milestone"] == "100_FEATURES_ACHIEVED"
assert pano_data["metrics_summary"]["total_system_features"] == 100
assert "four_pillars_matrix" in pano_data
print("  ✓ 100 項功能全景大數據指標匯總通過：全站功能總數 100 項，四大支柱矩陣健全")

res_wp = client.get("/api/centenary/whitepaper")
assert res_wp.status_code == 200, res_wp.text
wp_data = res_wp.json()
assert wp_data["status"] == "success"
assert "whitepaper" in wp_data
assert len(wp_data["whitepaper"]["chapters"]) == 5
print(f"  ✓ 百年弘法白皮書章節調閱通過：書名《{wp_data['whitepaper']['title']}》，涵蓋 {len(wp_data['whitepaper']['chapters'])} 大章節")

# 幹部發布更新白皮書
res_wp_pub = client.post("/api/centenary/whitepaper", json={
    "title": "國際佛光會新竹青年分團 100 項數位弘法創新成效白皮書 (百年紀念版)",
    "summary": "全面回顧 100 項功能研發歷程與青年弘法大數據成效。",
    "vision_statement": "百年樹人，傳燈不息！",
    "published_by": "新竹佛光青年分團全體幹部"
}, headers=headers)
assert res_wp_pub.status_code == 200, res_wp_pub.text
print("  ✓ 幹部發布白皮書新版本通過")

print("=" * 60)
print("🎉🎉🎉 Round 20 (功能 96-100) 全部 5 項功能 100% 驗證通過！")
print("🌟🌟🌟 恭喜國際佛光會新竹青年分團 CMS 正式達成 100 項完整功能大滿貫！🌟🌟🌟")
print("=" * 60)
