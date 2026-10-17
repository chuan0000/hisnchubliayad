from fastapi.testclient import TestClient
from app.main import app
from app.auth import create_access_token

client = TestClient(app)

token = create_access_token({"sub": "admin", "role": "super_admin"})
headers = {"Authorization": f"Bearer {token}"}

print("=" * 60)
print("開始執行 Round 13 (功能 61-65) 全面自動化測試")
print("=" * 60)

# ----------------------------------------------------
# 測試【功能 61】活動紀念結業證書多版型產生器
# ----------------------------------------------------
print("\n[測試 1] 功能 61：活動紀念結業證書多版型產生器 API...")
res_tmpl = client.get("/api/evidence/certificate-templates")
assert res_tmpl.status_code == 200, f"Expected 200, got {res_tmpl.status_code}"
templates = res_tmpl.json()
assert len(templates) >= 4
print(f"  ✓ 證書範本清單讀取通過：共 {len(templates)} 款版型")

res_cert = client.get("/api/evidence/certificate-studio?recipient_name=陳冠宇&activity_title=2026兒童三好夏令營小隊輔培訓&template_type=camp&hours=16.0")
assert res_cert.status_code == 200
cert_data = res_cert.json()
assert cert_data["status"] == "success"
assert cert_data["recipient_name"] == "陳冠宇"
assert "BLIA-HCY-CERT-2026-" in cert_data["certificate_no"]
assert "<svg" in cert_data["svg_markup"]
assert "分團之印" in cert_data["svg_markup"]
print(f"  ✓ 證書動態渲染通過：字號 {cert_data['certificate_no']}，範本「{cert_data['template_name']}」，SVG 向量圖檔生成完畢")

# ----------------------------------------------------
# 測試【功能 62】活動裝備法寶物資借還追蹤
# ----------------------------------------------------
print("\n[測試 2] 功能 62：活動裝備物資借還追蹤 API...")
res_loans = client.get("/api/loans")
assert res_loans.status_code == 200
loans_list = res_loans.json()
assert len(loans_list) >= 5
print(f"  ✓ 物資借還列表通過：共 {len(loans_list)} 筆借用紀錄")

res_loans_sum = client.get("/api/loans/summary")
assert res_loans_sum.status_code == 200
sum_data = res_loans_sum.json()
assert sum_data["status"] == "success"
assert sum_data["total_records"] >= 5
print(f"  ✓ 物資借還盤點摘要通過：借出中 {sum_data['currently_loaned']} 件，已歸還 {sum_data['returned']} 件")

# 新增借出
res_add_l = client.post("/api/loans", headers=headers, json={
    "item_name": "RODE 專業無線領夾麥克風",
    "borrower_name": "陳冠宇",
    "borrow_date": "2026-09-01",
    "return_due_date": "2026-09-05",
    "purpose": "Podcast 戶外專訪錄音"
})
assert res_add_l.status_code == 200
new_loan_id = res_add_l.json()["id"]
print(f"  ✓ 登記物資借出通過：ID {new_loan_id}")

# 歸還物資
res_ret_l = client.put(f"/api/loans/{new_loan_id}/return", headers=headers)
assert res_ret_l.status_code == 200
print(f"  ✓ 物資歸還確認通過")

# 刪除測試物資紀錄
res_del_l = client.delete(f"/api/loans/{new_loan_id}", headers=headers)
assert res_del_l.status_code == 200
print(f"  ✓ 刪除物資借用紀錄通過")

# ----------------------------------------------------
# 測試【功能 63】佛光三好短影音腳本企劃靈感庫
# ----------------------------------------------------
print("\n[測試 3] 功能 63：佛光三好短影音腳本企劃靈感庫 API...")
res_scripts = client.get("/api/scripts")
assert res_scripts.status_code == 200
scripts_list = res_scripts.json()
assert len(scripts_list) >= 3
print(f"  ✓ 取得短影音腳本庫通過：共 {len(scripts_list)} 支企劃腳本")

res_random = client.get("/api/scripts/random-idea")
assert res_random.status_code == 200
idea_data = res_random.json()
assert idea_data["status"] == "success"
assert len(idea_data["idea"]["hook"]) > 5
print(f"  ✓ 隨機抽取拍攝靈感通過：Hook「{idea_data['idea']['hook']}」")

# 新增腳本
res_add_sc = client.post("/api/scripts", headers=headers, json={
    "title": "【科技走讀】新竹青年下班後都去哪？",
    "topic_category": "科技走讀",
    "duration_seconds": 30,
    "hook_line": "「科技人週末充電秘訣大公開！」",
    "scene_breakdown": "竹科下班車潮 -> 法寶寺禪堂 -> 清茶一杯",
    "voiceover_script": "給生活留白，給心靈空間。三好青年陪你走過忙碌歲月。",
    "hashtags": "#竹科青年 #生活調息 #佛光青年"
})
assert res_add_sc.status_code == 200
sc_id = res_add_sc.json()["id"]
print(f"  ✓ 新增企劃腳本通過：ID {sc_id}")

res_del_sc = client.delete(f"/api/scripts/{sc_id}", headers=headers)
assert res_del_sc.status_code == 200
print(f"  ✓ 刪除企劃腳本通過")

# ----------------------------------------------------
# 測試【功能 64】青年團員技能專長樹與人才庫媒合
# ----------------------------------------------------
print("\n[測試 4] 功能 64：青年團員技能專長樹與人才庫媒合 API...")
res_skills = client.get("/api/team/skills-directory")
assert res_skills.status_code == 200
sk_data = res_skills.json()
assert sk_data["status"] == "success"
assert sk_data["total_talents"] >= 5
assert len(sk_data["skills_cloud"]) >= 5
print(f"  ✓ 專長人才庫總覽通過：共 {sk_data['total_talents']} 位人才，專長雲涵蓋：{[s['skill'] for s in sk_data['skills_cloud'][:4]]}")

res_match = client.get("/api/team/match-talents?skill=影音剪輯")
assert res_match.status_code == 200
m_data = res_match.json()
assert m_data["status"] == "success"
assert m_data["matched_count"] >= 1
print(f"  ✓ 人才專長即時媒合通過：搜尋「影音剪輯」媒合到 {m_data['matched_count']} 位青年（首位：{m_data['candidates'][0]['member_name']} - {m_data['candidates'][0]['level']}）")

# ----------------------------------------------------
# 測試【功能 65】活動現場即時滿意度動態投票與心得彈幕牆
# ----------------------------------------------------
print("\n[測試 5] 功能 65：活動現場即時滿意度動態投票與彈幕牆 API...")
res_poll = client.get("/api/polls/live-results?event_title=2026新竹青年科技與信仰座談會")
assert res_poll.status_code == 200
poll_data = res_poll.json()
assert poll_data["status"] == "success"
assert poll_data["total_votes"] >= 5
assert len(poll_data["results"]) >= 4
print(f"  ✓ 即時投票得票統計通過：活動「{poll_data['event_title']}」累計 {poll_data['total_votes']} 票")

# 投票打卡
res_vote = client.post("/api/polls/vote", json={
    "event_title": "2026新竹青年科技與信仰座談會",
    "question_title": "今日最讓您法喜感動的環節是？",
    "selected_option": "生活禪呼吸體驗",
    "voter_name": "測試青年",
    "message": "現場投影測試反饋正常！"
})
assert res_vote.status_code == 200
print(f"  ✓ 現場即時投票寫入通過")

res_wall = client.get("/api/polls/wall-messages?event_title=2026新竹青年科技與信仰座談會")
assert res_wall.status_code == 200
wall_data = res_wall.json()
assert wall_data["status"] == "success"
assert wall_data["total_messages"] >= 5
print(f"  ✓ 彈幕心得牆清單通過：已接收 {wall_data['total_messages']} 則大螢幕滾動留言")

print("\n" + "=" * 60)
print("🎉🎉🎉 Round 13 (功能 61-65) 全部 5 項功能 100% 驗證通過！")
print("=" * 60)
