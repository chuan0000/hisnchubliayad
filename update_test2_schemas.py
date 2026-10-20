with open("app/schemas.py", "r", encoding="utf-8") as f:
    schemas_content = f.read()

old_health_schemas = """class HealthLogBase(BaseModel):
    participant_name: str
    activity_type: Optional[str] = "walk"
    log_date: str
    distance_km: Optional[float] = 0.0
    steps: Optional[int] = 0
    proof_image_url: Optional[str] = ""
    note: Optional[str] = ""

class HealthLogCreate(HealthLogBase):
    pass

class HealthLogResponse(HealthLogBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True"""

new_health_schemas = """class HealthLogBase(BaseModel):
    participant_name: str
    activity_type: Optional[str] = "walk"
    log_date: str
    distance_km: Optional[float] = 0.0
    steps: Optional[int] = 0
    proof_image_url: Optional[str] = ""
    note: Optional[str] = ""
    verification_type: Optional[str] = "device_screenshot"
    review_status: Optional[str] = "approved"
    reviewer_name: Optional[str] = ""
    reviewer_notes: Optional[str] = ""
    reviewed_at: Optional[str] = ""

class HealthLogCreate(BaseModel):
    participant_name: str
    activity_type: Optional[str] = "walk"
    log_date: str
    distance_km: Optional[float] = 0.0
    steps: Optional[int] = 0
    proof_image_url: Optional[str] = ""
    note: Optional[str] = ""
    verification_type: Optional[str] = "device_screenshot"
    review_status: Optional[str] = "pending"

class HealthLogResponse(HealthLogBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True

class HealthReviewRequest(BaseModel):
    review_status: str       # 'approved' or 'rejected'
    reviewer_name: str
    reviewer_notes: Optional[str] = ""

class HealthLeaderboardItem(BaseModel):
    rank: int
    participant_name: str
    total_km: float
    total_steps: int
    current_streak: int
    approved_logs: int

class HealthLeaderboardResponse(BaseModel):
    streak_leaderboard: List[HealthLeaderboardItem]
    distance_leaderboard: List[HealthLeaderboardItem]"""

if old_health_schemas in schemas_content:
    schemas_content = schemas_content.replace(old_health_schemas, new_health_schemas)
    print("Replaced HealthLog schemas in schemas.py")
else:
    print("Warning: old_health_schemas not matched exactly!")

if "class YouthWishCreate" not in schemas_content:
    append_schemas = """

# ==============================================================================
# 【青年心願牆】Schemas (Youth Wishlist Wall)
# ==============================================================================
class YouthWishCreate(BaseModel):
    title: str
    category: Optional[str] = "sports_gear"
    description: Optional[str] = ""
    estimated_budget: Optional[float] = 0.0
    created_by: Optional[str] = "青年同修"

class YouthWishStatusUpdate(BaseModel):
    status: str
    sponsor_note: Optional[str] = ""

class YouthWishResponse(BaseModel):
    id: int
    title: str
    category: str
    description: Optional[str] = ""
    estimated_budget: Optional[float] = 0.0
    created_by: str
    likes_count: int
    status: str
    sponsor_note: Optional[str] = ""
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True

class YouthWishSummary(BaseModel):
    total_wishes: int
    fulfilled_wishes: int
    total_likes: int
    category_distribution: dict


# ==============================================================================
# 【社群與活動爬蟲】Schemas (Event Crawler)
# ==============================================================================
class CrawledEventCreate(BaseModel):
    title: str
    source: Optional[str] = "Web/Social"
    event_date: Optional[str] = ""
    location: Optional[str] = ""
    description: Optional[str] = ""
    source_url: Optional[str] = ""

class CrawledEventResponse(BaseModel):
    id: int
    source: str
    title: str
    event_date: Optional[str] = ""
    location: Optional[str] = ""
    description: Optional[str] = ""
    source_url: Optional[str] = ""
    sync_status: str
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True
"""
    schemas_content += append_schemas
    print("Appended Wishlist and Crawler schemas to schemas.py")

with open("app/schemas.py", "w", encoding="utf-8") as f:
    f.write(schemas_content)

print("app/schemas.py updated successfully.")
