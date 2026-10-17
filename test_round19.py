from fastapi.testclient import TestClient
from app.main import app
from app.auth import create_access_token

client = TestClient(app)
token = create_access_token({"sub": "admin", "role": "super_admin"})
headers = {"Authorization": f"Bearer {token}"}

def test_feature_91_custom_survey_builder():
    # 1. GET questions for evidence 1
    res = client.get("/api/custom-surveys/1")
    assert res.status_code == 200, res.text
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1

    # 2. POST new question
    new_q = {
        "evidence_id": 1,
        "question_text": "您對本次青年禪修活動的整體音響與環境感受？",
        "question_type": "single_choice",
        "options_json": "極為莊嚴舒適,良好,普通,需改進",
        "is_required": 1,
        "sort_order": 4
    }
    res_post = client.post("/api/custom-surveys", json=new_q, headers=headers)
    assert res_post.status_code in [200, 201], res_post.text
    created = res_post.json()
    assert created["question_text"] == new_q["question_text"]
    q_id = created["id"]

    # 3. DELETE created question
    res_del = client.delete(f"/api/custom-surveys/{q_id}", headers=headers)
    assert res_del.status_code == 200, res_del.text
    print("Test 91 Custom Survey Builder: PASSED")

def test_feature_92_dharma_dedication_liturgy_printer():
    # Test GET liturgy print-slip SVG / HTML
    res = client.get("/api/liturgy/print-slip?donor_name=陳弘法&target=新竹鄉親與全體青年&prayer_text=福慧雙修&date=2026-10-17")
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["status"] == "success"
    assert "陳弘法" in data["donor_name"]
    assert "新竹鄉親" in data["target"]
    assert "<svg" in data["svg_markup"]
    assert "三好微行持功德回向文疏" in data["svg_markup"]
    print("Test 92 Dharma Dedication Liturgy Printer: PASSED")

def test_feature_93_procurement_and_vendors():
    # 1. GET vendors
    res_v = client.get("/api/procurement/vendors")
    assert res_v.status_code == 200, res_v.text
    vendors = res_v.json()
    assert len(vendors) >= 1

    # 2. POST vendor
    new_v = {
        "vendor_name": "竹塹法音音響工程行",
        "category": "音響燈光",
        "contact_person": "黃技師",
        "phone": "03-5221111",
        "address": "新竹市北區大同路",
        "rating_score": 4.9,
        "notes": "多次支援青年弘法音響工程"
    }
    res_vp = client.post("/api/procurement/vendors", json=new_v, headers=headers)
    assert res_vp.status_code in [200, 201], res_vp.text

    # 3. GET comparisons
    res_c = client.get("/api/procurement/comparisons")
    assert res_c.status_code == 200, res_c.text
    comps = res_c.json()
    assert len(comps) >= 1

    # 4. POST comparison
    new_c = {
        "item_title": "青年幹部培訓手冊 (150本)",
        "category": "文宣印刷",
        "vendor_a": "新竹光華數位印刷文創",
        "price_a": 4500.0,
        "vendor_b": "竹北快印輸出館",
        "price_b": 5200.0,
        "vendor_c": "風城文教社",
        "price_c": 5000.0,
        "selected_vendor": "新竹光華數位印刷文創",
        "rationale": "印刷清晰且具備護膜燙金優惠"
    }
    res_cp = client.post("/api/procurement/comparisons", json=new_c, headers=headers)
    assert res_cp.status_code in [200, 201], res_cp.text
    print("Test 93 Procurement and Vendors: PASSED")

def test_feature_94_cadre_internal_notice_board():
    # 1. GET notices
    res_n = client.get("/api/team/cadre-notices", headers=headers)
    assert res_n.status_code == 200, res_n.text
    notices = res_n.json()
    assert len(notices) >= 1

    # 2. POST notice
    new_n = {
        "title": "【演練通知】週日法會青年司儀與音控全體採排",
        "content": "請司儀組與音控組幹部提早半小時至大殿就位測試。",
        "priority": "urgent",
        "publisher_name": "副分團長",
        "target_roles": "司儀組/音控組"
    }
    res_np = client.post("/api/team/cadre-notices", json=new_n, headers=headers)
    assert res_np.status_code in [200, 201], res_np.text
    created = res_np.json()
    n_id = created["id"]

    # 3. DELETE notice
    res_del = client.delete(f"/api/team/cadre-notices/{n_id}", headers=headers)
    assert res_del.status_code == 200, res_del.text
    print("Test 94 Cadre Internal Notice Board: PASSED")

def test_feature_95_calendar_webcal_and_sync():
    # 1. GET webcal ics feed
    res_ics = client.get("/api/evidence/calendar/webcal-feed")
    assert res_ics.status_code == 200, res_ics.text
    assert "BEGIN:VCALENDAR" in res_ics.text
    assert "END:VCALENDAR" in res_ics.text
    assert "SUMMARY" in res_ics.text

    # 2. GET sync-guide
    res_guide = client.get("/api/evidence/calendar/sync-guide")
    assert res_guide.status_code == 200, res_guide.text
    guide = res_guide.json()
    assert guide["status"] == "success"
    assert "webcal_url" in guide
    assert "google_cal_import_guide" in guide
    assert "apple_cal_guide" in guide
    print("Test 95 Calendar WebCal and Sync: PASSED")

if __name__ == "__main__":
    print("=" * 60)
    print("開始執行 Round 19 (功能 91-95) 自動化測試")
    print("=" * 60)
    test_feature_91_custom_survey_builder()
    test_feature_92_dharma_dedication_liturgy_printer()
    test_feature_93_procurement_and_vendors()
    test_feature_94_cadre_internal_notice_board()
    test_feature_95_calendar_webcal_and_sync()
    print("\nALL ROUND 19 TESTS PASSED 100%!")
