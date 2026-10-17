import sys
from fastapi.testclient import TestClient
from app.main import app
from app.auth import create_access_token

client = TestClient(app)

token = create_access_token({"sub": "admin", "role": "super_admin"})
headers = {"Authorization": f"Bearer {token}"}

print("=" * 60)
print("開始執行 Round 11 (功能 51-55) 全面自動化測試")
print("=" * 60)

# ----------------------------------------------------
# 測試【功能 51】志工服務時數歷史存摺帳戶
# ----------------------------------------------------
print("\n[測試 1] 功能 51：志工服務時數存摺總覽與個別明細...")
res_sum = client.get("/api/team/passbook/summary/all")
assert res_sum.status_code == 200, f"Expected 200, got {res_sum.status_code}"
sum_data = res_sum.json()
assert sum_data["status"] == "success"
assert sum_data["total_volunteers"] >= 5, f"Expected >= 5 volunteers, got {sum_data['total_volunteers']}"
assert sum_data["total_service_hours"] > 50, f"Expected > 50 total hours, got {sum_data['total_service_hours']}"
print(f"  ✓ 志工存摺總覽測試通過：共 {sum_data['total_volunteers']} 位志工，累積 {sum_data['total_service_hours']} 小時")

res_detail = client.get("/api/team/passbook/陳冠宇")
assert res_detail.status_code == 200
detail_data = res_detail.json()
assert detail_data["volunteer_name"] == "陳冠宇"
assert "BLIA-HCY-VOL-" in detail_data["passbook_no"]
assert detail_data["total_hours"] >= 34.0
assert len(detail_data["records"]) >= 4
print(f"  ✓ 陳冠宇存摺明細測試通過：存摺帳號 {detail_data['passbook_no']}，累積結餘 {detail_data['total_hours']} 小時，共 {detail_data['total_records']} 筆明細")

# 新增一筆時數存摺
res_add_p = client.post("/api/team/passbook", headers=headers, json={
    "volunteer_name": "陳冠宇",
    "service_date": "2026-10-15",
    "activity_title": "新竹青年科技弘法專案測試",
    "service_hours": 4.0,
    "verifier": "分團長",
    "notes": "系統自動化測試驗證"
})
assert res_add_p.status_code == 200
print("  ✓ 幹部登錄新時數存摺測試通過")

# ----------------------------------------------------
# 測試【功能 52】活動相片佛光金暖色柔膚濾鏡預處理
# ----------------------------------------------------
print("\n[測試 2] 功能 52：活動相片自動美膚與佛光金暖色濾鏡預處理...")
res_filter_get = client.get("/api/upload/apply-filter?filename=sample_youth_activity.jpg&intensity=1.0")
assert res_filter_get.status_code == 200
fg_data = res_filter_get.json()
assert fg_data["status"] == "success"
assert "golden_" in fg_data["filtered_filename"]
assert "url" in fg_data
print(f"  ✓ GET 濾鏡預處理通過：產生 {fg_data['filtered_filename']}，URL: {fg_data['url']}")

res_filter_post = client.post("/api/upload/apply-filter", json={
    "filename": "sample_youth_activity.jpg",
    "filter_type": "golden_warmth",
    "intensity": 1.2
})
assert res_filter_post.status_code == 200
fp_data = res_filter_post.json()
assert fp_data["status"] == "success"
print(f"  ✓ POST 濾鏡預處理通過：{fp_data['filter_name']}，調色：{fp_data['enhancements']['color_temperature']}")

# ----------------------------------------------------
# 測試【功能 53】活動常見問題 FAQ 摺疊式知識庫
# ----------------------------------------------------
print("\n[測試 3] 功能 53：活動常見問題 FAQ 摺疊式知識庫...")
res_faq = client.get("/api/faq")
assert res_faq.status_code == 200
faqs = res_faq.json()
assert len(faqs) >= 7, f"Expected >= 7 faqs, got {len(faqs)}"
print(f"  ✓ 前台公開 FAQ 列表通過：共 {len(faqs)} 題常見問答")

res_cat = client.get("/api/faq/categories")
assert res_cat.status_code == 200
cats = res_cat.json()
assert len(cats) >= 4
cat_names = [c["category"] for c in cats]
assert "入團須知" in cat_names and "活動參與" in cat_names and "時數認證" in cat_names
print(f"  ✓ FAQ 分類統計通過：{cat_names}")

# 新增 FAQ
res_new_faq = client.post("/api/faq", headers=headers, json={
    "category": "評鑑佐證",
    "question": "分團評鑑佐證如何自動壓印三好浮水印？",
    "answer": "系統在上傳佐證圖片時，後端 Pillow 引擎會自動於右下角疊加三好四給金色認證浮水印，確保評鑑檔案原創性與公信力。",
    "sort_order": 99,
    "is_published": True
})
assert res_new_faq.status_code == 200
new_faq_data = res_new_faq.json()
faq_id = new_faq_data["id"]
print(f"  ✓ 幹部新增 FAQ 項目通過：ID {faq_id}")

# 刪除測試 FAQ
res_del_faq = client.delete(f"/api/faq/{faq_id}", headers=headers)
assert res_del_faq.status_code == 200
print(f"  ✓ 幹部刪除 FAQ 項目通過")

# ----------------------------------------------------
# 測試【功能 54】青年生活禪每日靜心打卡計時鐘
# ----------------------------------------------------
print("\n[測試 4] 功能 54：青年生活禪每日靜心打卡計時鐘...")
res_zen_post = client.post("/api/health/zen-meditation", json={
    "participant_name": "林思妤",
    "duration_minutes": 15,
    "reflection_notes": "專心調息，身心舒暢放鬆。",
    "mood": "安住當下"
})
assert res_zen_post.status_code == 200
zen_rec = res_zen_post.json()
assert zen_rec["id"] > 0
print(f"  ✓ 青年靜心打卡寫入通過：ID {zen_rec['id']}，參與者: {zen_rec['participant_name']}，時長: {zen_rec['duration_minutes']} 分鐘")

res_zen_list = client.get("/api/health/zen-meditations?limit=10")
assert res_zen_list.status_code == 200
z_list = res_zen_list.json()
assert len(z_list) >= 7
print(f"  ✓ 近期靜心同修紀錄讀取通過：共 {len(z_list)} 筆")

res_zen_stats = client.get("/api/health/zen-stats")
assert res_zen_stats.status_code == 200
z_stats = res_zen_stats.json()
assert z_stats["status"] == "success"
assert z_stats["total_sessions"] >= 7
assert z_stats["total_minutes"] >= 70
assert len(z_stats["zen_quote"]) > 5
print(f"  ✓ 靜心大數據統計通過：累計 {z_stats['total_sessions']} 次，共 {z_stats['total_hours']} 小時，今日法語：「{z_stats['zen_quote']}」")

# ----------------------------------------------------
# 測試【功能 55】全站操作審計日誌與安全監控
# ----------------------------------------------------
print("\n[測試 5] 功能 55：全站操作審計日誌 Audit Log 與安全監控...")
res_audit_list = client.get("/api/audit/logs?limit=20", headers=headers)
assert res_audit_list.status_code == 200
audit_data = res_audit_list.json()
assert audit_data["status"] == "success"
assert audit_data["total"] >= 5
print(f"  ✓ 調閱審計日誌通過：全站已記錄 {audit_data['total']} 筆操作審計日誌")

res_audit_stats = client.get("/api/audit/stats", headers=headers)
assert res_audit_stats.status_code == 200
stats_data = res_audit_stats.json()
assert stats_data["status"] == "success"
assert "道場" in stats_data["security_status"] or "Secure" in stats_data["security_status"]
print(f"  ✓ 系統安全監控摘要通過：狀態「{stats_data['security_status']}」，最新稽核時間: {stats_data['last_checked']}")

res_audit_rec = client.post("/api/audit/record", headers=headers, json={
    "username": "admin",
    "user_role": "super_admin",
    "action": "執行Round11安全稽核",
    "target": "全站功能51-55驗證",
    "ip_address": "127.0.0.1",
    "details": "自動化驗證測試已全數完成通過"
})
assert res_audit_rec.status_code == 200
print("  ✓ 手動寫入安全審計日誌通過")

print("\n" + "=" * 60)
print("🎉🎉🎉 Round 11 (功能 51-55) 全部 5 項功能 100% 驗證通過！")
print("=" * 60)
