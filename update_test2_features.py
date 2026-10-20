import re

# 1. Update app/models.py
with open("app/models.py", "r", encoding="utf-8") as f:
    models_content = f.read()

# Replace HealthLog definition
old_health_log = """class HealthLog(Base):
    \"\"\"健康打卡表（VEGRUN 蔬食路跑 / 青年健走運動累積）\"\"\"
    __tablename__ = "health_logs"

    id = Column(Integer, primary_key=True, index=True)
    participant_name = Column(String(100), nullable=False)
    activity_type = Column(String(20), default="walk")
    log_date = Column(String(30), nullable=False)
    distance_km = Column(Float, default=0.0)
    steps = Column(Integer, default=0)
    proof_image_url = Column(String(255), default="")
    note = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)"""

new_health_log = """class HealthLog(Base):
    \"\"\"健康打卡表（VEGRUN 蔬食路跑 / 青年健走運動累積，含雙軌截圖審核）\"\"\"
    __tablename__ = "health_logs"

    id = Column(Integer, primary_key=True, index=True)
    participant_name = Column(String(100), nullable=False)
    activity_type = Column(String(20), default="walk")
    log_date = Column(String(30), nullable=False)
    distance_km = Column(Float, default=0.0)
    steps = Column(Integer, default=0)
    proof_image_url = Column(String(255), default="")
    note = Column(Text, default="")
    verification_type = Column(String(50), default="device_screenshot")  # 'device_screenshot' vs 'video_screenshot'
    review_status = Column(String(20), default="approved")               # 'pending', 'approved', 'rejected'
    reviewer_name = Column(String(100), default="")
    reviewer_notes = Column(Text, default="")
    reviewed_at = Column(String(30), default="")
    created_at = Column(DateTime, default=datetime.utcnow)"""

if old_health_log in models_content:
    models_content = models_content.replace(old_health_log, new_health_log)
    print("Replaced HealthLog in models.py")
else:
    print("Warning: old_health_log not matched exactly, checking...")

# Append YouthWish and CrawledEvent if not present
if "class YouthWish" not in models_content:
    models_append = """

class YouthWish(Base):
    \"\"\"【青年心願牆】青年心願許願卡片、分類、預算、點讚集氣與圓滿狀態\"\"\"
    __tablename__ = "youth_wishes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150), nullable=False)
    category = Column(String(50), default="sports_gear")      # 'sports_gear', 'digital_3c', 'wellness', 'lifestyle'
    description = Column(Text, default="")
    estimated_budget = Column(Float, default=0.0)
    created_by = Column(String(100), default="青年同修")
    likes_count = Column(Integer, default=0)
    status = Column(String(30), default="open")                # 'open', 'in_progress', 'fulfilled'
    sponsor_note = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)


class CrawledEvent(Base):
    \"\"\"【社群與活動爬蟲】外部社群與公開活動爬蟲抓取紀錄與匯入佐證清冊\"\"\"
    __tablename__ = "crawled_events"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(100), default="Facebook/Web")
    title = Column(String(200), nullable=False)
    event_date = Column(String(50), default="")
    location = Column(String(200), default="")
    description = Column(Text, default="")
    source_url = Column(String(255), default="")
    sync_status = Column(String(30), default="synced")         # 'synced', 'imported_to_evidence', 'archived'
    created_at = Column(DateTime, default=datetime.utcnow)
"""
    models_content += models_append
    print("Appended YouthWish and CrawledEvent to models.py")

with open("app/models.py", "w", encoding="utf-8") as f:
    f.write(models_content)

print("app/models.py updated successfully.")
