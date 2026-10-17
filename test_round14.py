from fastapi.testclient import TestClient
from app.main import app
from app.auth import create_access_token

client = TestClient(app)

token = create_access_token({"sub": "admin", "role": "super_admin"})
headers = {"Authorization": f"Bearer {token}"}

print("=" * 60)
print("開始執行 Round 14 (功能 66-70) 全面自動化測試")
print("=" * 60)

# ----------------------------------------------------
# 測試【功能 66】道場青年讀書會篇章研討與導讀筆記庫
# ----------------------------------------------------
print("\n[測試 1] 功能 66：道場青年讀書會篇章研討與導讀筆記庫 API...")
res_study = client.get("/api/study-groups")
assert res_study.status_code == 200, f"Expected 200, got {res_study.status_code}"
notes = res_study.json()
assert len(notes) >= 3
print(f"  ✓ 讀書會筆記清冊讀取通過：共 {len(notes)} 篇導讀筆記")

res_books = client.get("/api/study-groups/books")
assert res_books.status_code == 200
books = res_books.json()
assert len(books) >= 2
print(f"  ✓ 研討書目總覽通過：共 {len(books)} 本經典著作，涵蓋：{[b['book_title'] for b in books]}")

# 新增筆記
res_add_study = client.post("/api/study-groups", headers=headers, json={
    "book_title": "《華嚴經淨行品》",
    "chapter_title": "青年日常生活發願偈",
    "moderator_name": "陳冠宇",
    "discussion_date": "2026-10-18",
    "core_questions": "日常起心動念如何皆發大願？",
    "key_takeaways": "善用其心，則獲一切勝妙功德。",
    "action_pledge": "行住坐臥皆念眾生安樂。"
})
assert res_add_study.status_code == 200
new_study_id = res_add_study.json()["id"]
print(f"  ✓ 新增讀書會導讀筆記通過：ID {new_study_id}")

res_del_study = client.delete(f"/api/study-groups/{new_study_id}", headers=headers)
assert res_del_study.status_code == 200
print(f"  ✓ 刪除讀書會筆記通過")

# ----------------------------------------------------
# 測試【功能 67】活動現場志工愛心便當與茶水需求統計
# ----------------------------------------------------
print("\n[測試 2] 功能 67：活動現場志工愛心便當與茶水需求統計 API...")
res_catering = client.get("/api/catering")
assert res_catering.status_code == 200
cat_list = res_catering.json()
assert len(cat_list) >= 4
print(f"  ✓ 志工便當訂餐清單通過：共 {len(cat_list)} 筆餐飲需求")

res_cat_sum = client.get("/api/catering/summary")
assert res_cat_sum.status_code == 200
cat_sum = res_cat_sum.json()
assert cat_sum["status"] == "success"
assert cat_sum["total_meals"] >= 80
print(f"  ✓ 便當總量大數據統計通過：總餐點 {cat_sum['total_meals']} 份，全素 {cat_sum['vegetarian_breakdown'].get('全素', 0)} 份")

# 新增餐點需求
res_add_cat = client.post("/api/catering", headers=headers, json={
    "activity_title": "新竹青年科技生活禪研習營",
    "event_date": "2026-11-05",
    "meal_type": "午餐便當",
    "vegetarian_type": "全素",
    "quantity": 25,
    "contact_person": "林思妤",
    "notes": "竹科青年素食輕食便當"
})
assert res_add_cat.status_code == 200
cat_id = res_add_cat.json()["id"]
print(f"  ✓ 登記便當需求通過：ID {cat_id}")

# 更新餐點狀態
res_up_cat = client.put(f"/api/catering/{cat_id}/status", headers=headers, json={"status": "已送達"})
assert res_up_cat.status_code == 200
print(f"  ✓ 更新送餐進度狀態通過")

res_del_cat = client.delete(f"/api/catering/{cat_id}", headers=headers)
assert res_del_cat.status_code == 200
print(f"  ✓ 刪除餐飲紀錄通過")

# ----------------------------------------------------
# 測試【功能 68】青年團員年度幹部改選線上推薦與開票計票器
# ----------------------------------------------------
print("\n[測試 3] 功能 68：青年團員年度幹部改選線上推薦與開票計票器 API...")
res_cand = client.get("/api/team/election/candidates")
assert res_cand.status_code == 200
cands = res_cand.json()
assert cands["status"] == "success"
assert len(cands["positions"]) >= 4
print(f"  ✓ 幹部候選人清冊通過：共 {len(cands['positions'])} 個競選職位")

res_tally = client.get("/api/team/election/tally")
assert res_tally.status_code == 200
tally = res_tally.json()
assert tally["status"] == "success"
assert tally["total_votes_cast"] >= 50
print(f"  ✓ 即時開票計票看板通過：已開出 {tally['total_votes_cast']} 票，分團長目前領先：{tally['positions']['分團長']['leader']}")

# 投票測試
res_vote = client.post("/api/team/election/vote", json={"candidate_id": 1})
assert res_vote.status_code == 200
print(f"  ✓ 線上投票計票累加通過")

# ----------------------------------------------------
# 測試【功能 69】三好青年日常行善實踐微日記
# ----------------------------------------------------
print("\n[測試 4] 功能 69：三好青年日常行善實踐微日記 API...")
res_jd = client.post("/api/health/good-deeds", json={
    "author_name": "測試青年",
    "journal_date": "2026-10-16",
    "good_deed": "隨手關閉道場無人使用的電燈與空調",
    "good_words": "向辛苦的典座行堂義工媽媽真誠道謝",
    "good_heart": "願大眾皆能惜福愛物，福慧雙修",
    "mood": "法喜充滿"
})
assert res_jd.status_code == 200
jd_data = res_jd.json()
assert jd_data["id"] > 0
print(f"  ✓ 提交三好微日記通過：ID {jd_data['id']}，作者：{jd_data['author_name']}")

res_jd_list = client.get("/api/health/good-deeds")
assert res_jd_list.status_code == 200
assert len(res_jd_list.json()) >= 4
print(f"  ✓ 三好微日記清冊調閱通過：共 {len(res_jd_list.json())} 篇")

res_jd_stats = client.get("/api/health/good-deeds/stats")
assert res_jd_stats.status_code == 200
jd_st = res_jd_stats.json()
assert jd_st["total_journals"] >= 4
print(f"  ✓ 三好大數據統計通過：累積實踐 {jd_st['total_journals']} 篇，參與青年 {jd_st['participating_members']} 位")

# ----------------------------------------------------
# 測試【功能 70】道場法會隨喜祈福迴向卡與虛擬祈願燈
# ----------------------------------------------------
print("\n[測試 5] 功能 70：道場法會隨喜祈福迴向卡與虛擬祈願燈 API...")
res_lamp_post = client.post("/api/blessing-lamps", json={
    "donor_name": "測試信眾",
    "lamp_type": "光明智慧燈",
    "recipient_name": "考生祈願",
    "prayer_text": "祈願佛光加被，智慧現前，考運亨通，金榜題名！",
    "dedication_target": "學業光明・福慧雙全"
})
assert res_lamp_post.status_code == 200
lamp_res = res_lamp_post.json()
assert lamp_res["id"] > 0
print(f"  ✓ 發心點亮祈願燈通過：ID {lamp_res['id']}，燈種「{lamp_res['lamp_type']}」")

res_lamp_list = client.get("/api/blessing-lamps")
assert res_lamp_list.status_code == 200
assert len(res_lamp_list.json()) >= 4
print(f"  ✓ 線上心燈池清冊通過：共 {len(res_lamp_list.json())} 盞光明心燈")

res_lamp_stats = client.get("/api/blessing-lamps/stats")
assert res_lamp_stats.status_code == 200
l_st = res_lamp_stats.json()
assert l_st["status"] == "success"
assert l_st["total_lamps"] >= 4
print(f"  ✓ 點燈大數據統計通過：全站點亮 {l_st['total_lamps']} 盞蓮花燈，開示法語：「{l_st['dharma_blessing'][:24]}...」")

print("\n" + "=" * 60)
print("🎉🎉🎉 Round 14 (功能 66-70) 全部 5 項功能 100% 驗證通過！")
print("=" * 60)
