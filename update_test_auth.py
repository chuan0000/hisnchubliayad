with open("test_test2_features.py", "r", encoding="utf-8") as f:
    text = f.read()

# Login to get cadre token
login_code = """
    # Login as admin to get auth header
    login_res = client.post("/api/auth/login", json={"username": "admin", "password": "blia123456"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Import crawled event to evidence
    res_imp = client.post(f"/api/crawler/events/{event_id}/import-to-evidence?category=culture", headers=headers)
"""

text = text.replace(
    '    # 3. Import crawled event to evidence\n    res_imp = client.post(f"/api/crawler/events/{event_id}/import-to-evidence?category=culture")',
    login_code
)

with open("test_test2_features.py", "w", encoding="utf-8") as f:
    f.write(text)

print("test_test2_features.py updated with auth!")
