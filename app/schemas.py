from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

# ----------------- Auth & User -----------------
class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    username: str
    full_name: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    role: str = "cadre"

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(BaseModel):
    id: int
    username: str
    full_name: str
    role: str
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True

# ----------------- 評審通行證 -----------------
class ReviewerTokenCreate(BaseModel):
    name: str
    expiry_days: Optional[int] = 30

class ReviewerTokenResponse(BaseModel):
    id: int
    token: str
    name: str
    expires_at: str
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True

# ----------------- 評審評分與評語 -----------------
class EvidenceFeedbackCreate(BaseModel):
    reviewer_name: Optional[str] = "評鑑委員"
    rating: int = 5
    comment: str

class EvidenceFeedbackResponse(BaseModel):
    id: int
    evidence_id: int
    reviewer_name: str
    rating: int
    comment: str
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True

# ----------------- Site Block -----------------
class SiteBlockBase(BaseModel):
    block_key: str
    block_title: str
    block_value: str
    category: Optional[str] = "general"
    value_type: Optional[str] = "text"

class SiteBlockUpdate(BaseModel):
    block_value: str
    block_title: Optional[str] = None

class SiteBlockResponse(SiteBlockBase):
    id: int
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True

# ----------------- Evidence Item -----------------
class EvidenceItemBase(BaseModel):
    category: str
    title: str
    event_date: str
    year: Optional[str] = "2026"
    evaluation_code: Optional[str] = ""
    location: Optional[str] = "新竹法寶寺"
    latitude: Optional[float] = 24.805
    longitude: Optional[float] = 120.971
    summary: Optional[str] = ""
    participants_count: Optional[int] = 0
    volunteers_count: Optional[int] = 0
    service_hours: Optional[float] = 0.0
    satisfaction_rate: Optional[int] = 95
    expected_participants: Optional[int] = 0
    expected_goals: Optional[str] = ""
    actual_highlights: Optional[str] = ""
    file_url: Optional[str] = ""
    file_type: Optional[str] = "image"
    original_filename: Optional[str] = ""
    attachments: Optional[str] = "[]"
    photos_gallery: Optional[str] = "[]"
    video_url: Optional[str] = ""
    audio_url: Optional[str] = ""
    max_quota: Optional[int] = 50
    is_registration_open: Optional[bool] = True
    is_published: Optional[bool] = True

class EvidenceItemCreate(EvidenceItemBase):
    pass

class EvidenceItemUpdate(BaseModel):
    category: Optional[str] = None
    title: Optional[str] = None
    event_date: Optional[str] = None
    year: Optional[str] = None
    evaluation_code: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    summary: Optional[str] = None
    participants_count: Optional[int] = None
    volunteers_count: Optional[int] = None
    service_hours: Optional[float] = None
    satisfaction_rate: Optional[int] = None
    expected_participants: Optional[int] = None
    expected_goals: Optional[str] = None
    actual_highlights: Optional[str] = None
    file_url: Optional[str] = None
    file_type: Optional[str] = None
    original_filename: Optional[str] = None
    attachments: Optional[str] = None
    photos_gallery: Optional[str] = None
    video_url: Optional[str] = None
    audio_url: Optional[str] = None
    max_quota: Optional[int] = None
    is_registration_open: Optional[bool] = None
    is_published: Optional[bool] = None

class EvidenceItemResponse(EvidenceItemBase):
    id: int
    created_by: str
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True

# ----------------- Team Member -----------------
class TeamMemberBase(BaseModel):
    name: str
    position: str
    term: Optional[str] = "現任幹部"
    term_start: Optional[str] = ""
    term_end: Optional[str] = ""
    previous_roles: Optional[str] = "[]"
    avatar_url: Optional[str] = ""
    bio: Optional[str] = ""
    contact: Optional[str] = ""
    birthday: Optional[str] = ""
    blessing_sent: Optional[bool] = False
    emergency_contact_name: Optional[str] = ""
    emergency_contact_phone: Optional[str] = ""
    blood_type: Optional[str] = "O"
    emergency_group: Optional[str] = "活動應變組"
    sort_order: Optional[int] = 0
    is_active: Optional[bool] = True

class TeamMemberCreate(TeamMemberBase):
    pass

class TeamMemberUpdate(BaseModel):
    name: Optional[str] = None
    position: Optional[str] = None
    term: Optional[str] = None
    term_start: Optional[str] = None
    term_end: Optional[str] = None
    previous_roles: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    contact: Optional[str] = None
    birthday: Optional[str] = None
    blessing_sent: Optional[bool] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    blood_type: Optional[str] = None
    emergency_group: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None

class TeamMemberResponse(TeamMemberBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True

# ----------------- Health Log -----------------
class HealthLogBase(BaseModel):
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
    distance_leaderboard: List[HealthLeaderboardItem]

# ----------------- 【功能 21】幹部出勤與簽到 -----------------
class CadreAttendanceCreate(BaseModel):
    evidence_id: int
    member_id: int
    member_name: str
    status: Optional[str] = "present"
    hours: Optional[float] = 4.0
    note: Optional[str] = ""

class CadreAttendanceResponse(CadreAttendanceCreate):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True

# ----------------- 【功能 23】青年佛學會考與測驗 -----------------
class ExamRecordCreate(BaseModel):
    exam_name: str
    exam_date: str
    exam_level: Optional[str] = "中級"
    examinee_name: str
    score: float
    is_passed: Optional[bool] = None
    certificate_no: Optional[str] = ""
    notes: Optional[str] = ""

class ExamRecordResponse(ExamRecordCreate):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True

# ----------------- 【功能 24】活動滿意度問卷 -----------------
class SurveyResponseCreate(BaseModel):
    evidence_id: int
    respondent_name: Optional[str] = "匿名青年"
    overall_rating: int = 5
    content_depth: int = 5
    organization_rating: int = 5
    venue_rating: int = 5
    nps_score: int = 10
    favorite_aspect: Optional[str] = ""
    suggestions: Optional[str] = ""

class SurveyResponseResponse(SurveyResponseCreate):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True

# ----------------- 【功能 26】活動物資與庫存 -----------------
class InventoryItemBase(BaseModel):
    item_name: str
    category: Optional[str] = "活動器材"
    quantity: Optional[int] = 1
    unit: Optional[str] = "件"
    location: Optional[str] = "法寶寺青年分團室"
    status: Optional[str] = "normal"
    loan_to: Optional[str] = ""
    note: Optional[str] = ""

class InventoryItemCreate(InventoryItemBase):
    pass

class InventoryItemUpdate(BaseModel):
    item_name: Optional[str] = None
    category: Optional[str] = None
    quantity: Optional[int] = None
    unit: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    loan_to: Optional[str] = None
    note: Optional[str] = None

class InventoryItemResponse(InventoryItemBase):
    id: int
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True

# ----------------- 【功能 27】財務流水帳與核銷 -----------------
class FinanceTransactionBase(BaseModel):
    tx_date: str
    tx_type: str
    category: Optional[str] = "活動經費"
    title: str
    amount: float
    evidence_id: Optional[int] = 0
    handler: Optional[str] = "財務長"
    receipt_voucher: Optional[str] = ""
    note: Optional[str] = ""

class FinanceTransactionCreate(FinanceTransactionBase):
    pass

class FinanceTransactionResponse(FinanceTransactionBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True


# ----------------- 【功能 31】活動線上報名 -----------------
class ActivityRegistrationCreate(BaseModel):
    evidence_id: int
    name: str
    phone: Optional[str] = ""
    email: Optional[str] = ""
    affiliation: Optional[str] = ""
    dietary: Optional[str] = "vegan"
    notes: Optional[str] = ""

class ActivityRegistrationUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None

class ActivityRegistrationResponse(BaseModel):
    id: int
    evidence_id: int
    name: str
    phone: Optional[str] = ""
    email: Optional[str] = ""
    affiliation: Optional[str] = ""
    dietary: Optional[str] = "vegan"
    status: str
    notes: Optional[str] = ""
    registered_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True


# ----------------- 【功能 42】特約友好商家 -----------------
class PartnerStoreBase(BaseModel):
    name: str
    category: Optional[str] = "蔬食美饌"
    address: str
    latitude: Optional[float] = 24.805
    longitude: Optional[float] = 120.971
    perk: Optional[str] = "持佛光青年證享專屬優惠"
    contact: Optional[str] = ""
    is_active: Optional[bool] = True

class PartnerStoreCreate(PartnerStoreBase):
    pass

class PartnerStoreUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    perk: Optional[str] = None
    contact: Optional[str] = None
    is_active: Optional[bool] = None

class PartnerStoreResponse(PartnerStoreBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True

# ----------------- 【功能 44】活動檢討會與決議追蹤 -----------------
class MeetingActionItemBase(BaseModel):
    evidence_id: int
    meeting_date: str
    topic: str
    discussion: Optional[str] = ""
    assignee: Optional[str] = "幹部"
    due_date: Optional[str] = ""
    status: Optional[str] = "pending"

class MeetingActionItemCreate(MeetingActionItemBase):
    pass

class MeetingActionItemUpdate(BaseModel):
    topic: Optional[str] = None
    discussion: Optional[str] = None
    assignee: Optional[str] = None
    due_date: Optional[str] = None
    status: Optional[str] = None

class MeetingActionItemResponse(MeetingActionItemBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True


# ----------------- 【功能 47】節慶活動倒數看板 -----------------
class CountdownEventBase(BaseModel):
    title: str
    target_date: str
    category: Optional[str] = "總會盛事"
    description: Optional[str] = ""
    is_active: Optional[bool] = True

class CountdownEventCreate(CountdownEventBase):
    pass

class CountdownEventUpdate(BaseModel):
    title: Optional[str] = None
    target_date: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class CountdownEventResponse(CountdownEventBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True


# ----------------- 【功能 51】志工服務時數存摺 -----------------
class VolunteerPassbookBase(BaseModel):
    volunteer_name: str
    member_id: Optional[int] = 0
    evidence_id: Optional[int] = 0
    service_date: str
    activity_title: str
    service_hours: float = 4.0
    verifier: Optional[str] = "分團長"
    notes: Optional[str] = ""

class VolunteerPassbookCreate(VolunteerPassbookBase):
    pass

class VolunteerPassbookResponse(VolunteerPassbookBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True


# ----------------- 【功能 53】常見問題 FAQ 知識庫 -----------------
class FaqItemBase(BaseModel):
    category: Optional[str] = "活動參與"
    question: str
    answer: str
    sort_order: Optional[int] = 0
    is_published: Optional[bool] = True

class FaqItemCreate(FaqItemBase):
    pass

class FaqItemResponse(FaqItemBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True


# ----------------- 【功能 55】全站操作審計日誌 -----------------
class AuditLogBase(BaseModel):
    username: str
    user_role: Optional[str] = "cadre"
    action: str
    target: Optional[str] = ""
    ip_address: Optional[str] = "127.0.0.1"
    details: Optional[str] = ""

class AuditLogCreate(AuditLogBase):
    pass

class AuditLogResponse(AuditLogBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True


# ----------------- 【功能 54】青年生活禪靜心打卡 -----------------
class ZenMeditationBase(BaseModel):
    participant_name: str
    duration_minutes: Optional[int] = 10
    reflection_notes: Optional[str] = ""
    mood: Optional[str] = "心平氣和"

class ZenMeditationCreate(ZenMeditationBase):
    pass

class ZenMeditationResponse(ZenMeditationBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True


# ----------------- 【功能 57】活動經費請購與核銷 -----------------
class BudgetRequisitionBase(BaseModel):
    title: str
    applicant_name: str
    category: Optional[str] = "活動耗材"
    requested_amount: float = 0.0
    approved_amount: Optional[float] = 0.0
    status: Optional[str] = "待審核"
    invoice_no: Optional[str] = ""
    receipt_url: Optional[str] = ""
    notes: Optional[str] = ""

class BudgetRequisitionCreate(BudgetRequisitionBase):
    pass

class BudgetRequisitionResponse(BudgetRequisitionBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True


# ----------------- 【功能 58】道場活動志工排班表 -----------------
class VolunteerShiftBase(BaseModel):
    activity_title: str
    shift_date: str
    shift_time: Optional[str] = "08:00 - 12:00"
    role_name: Optional[str] = "場務組"
    volunteer_name: str
    status: Optional[str] = "已確認"
    notes: Optional[str] = ""

class VolunteerShiftCreate(VolunteerShiftBase):
    pass

class VolunteerShiftResponse(VolunteerShiftBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True


# ----------------- 【功能 60】站內即時公告與跑馬燈 -----------------
class SiteAnnouncementBase(BaseModel):
    title: str
    content: Optional[str] = ""
    announcement_type: Optional[str] = "info"
    is_marquee: Optional[bool] = True
    is_popup: Optional[bool] = False
    priority: Optional[int] = 0
    is_active: Optional[bool] = True

class SiteAnnouncementCreate(SiteAnnouncementBase):
    pass

class SiteAnnouncementResponse(SiteAnnouncementBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True


# ----------------- 【功能 62】物資借用與歸還流水帳 -----------------
class AssetLoanBase(BaseModel):
    item_name: str
    borrower_name: str
    borrow_date: str
    return_due_date: str
    actual_return_date: Optional[str] = ""
    status: Optional[str] = "借出中"
    purpose: Optional[str] = ""
    notes: Optional[str] = ""

class AssetLoanCreate(AssetLoanBase):
    pass

class AssetLoanResponse(AssetLoanBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True


# ----------------- 【功能 63】三好短影音腳本庫 -----------------
class VideoScriptBase(BaseModel):
    title: str
    topic_category: Optional[str] = "三好日常"
    duration_seconds: Optional[int] = 30
    hook_line: Optional[str] = ""
    scene_breakdown: Optional[str] = ""
    voiceover_script: Optional[str] = ""
    hashtags: Optional[str] = ""

class VideoScriptCreate(VideoScriptBase):
    pass

class VideoScriptResponse(VideoScriptBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True


# ----------------- 【功能 64】青年技能專長與人才媒合 -----------------
class MemberSkillBase(BaseModel):
    member_name: str
    primary_skills: str
    level: Optional[str] = "專業熟練"
    portfolio_link: Optional[str] = ""
    notes: Optional[str] = ""

class MemberSkillCreate(MemberSkillBase):
    pass

class MemberSkillResponse(MemberSkillBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True


# ----------------- 【功能 65】活動現場滿意度投票與彈幕 -----------------
class LivePollVoteBase(BaseModel):
    event_title: str
    question_title: str
    selected_option: str
    voter_name: Optional[str] = "青年同修"
    message: Optional[str] = ""

class LivePollVoteCreate(LivePollVoteBase):
    pass

class LivePollVoteResponse(LivePollVoteBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True


# ----------------- 【功能 66】讀書會導讀筆記 -----------------
class StudyGroupNoteBase(BaseModel):
    book_title: str
    chapter_title: str
    moderator_name: str
    discussion_date: str
    core_questions: Optional[str] = ""
    key_takeaways: Optional[str] = ""
    action_pledge: Optional[str] = ""

class StudyGroupNoteCreate(StudyGroupNoteBase):
    pass

class StudyGroupNoteResponse(StudyGroupNoteBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True


# ----------------- 【功能 67】志工便當與茶水需求統計 -----------------
class MealCateringBase(BaseModel):
    activity_title: str
    event_date: str
    meal_type: Optional[str] = "午餐便當"
    vegetarian_type: Optional[str] = "全素"
    quantity: Optional[int] = 20
    contact_person: Optional[str] = "活動幹部"
    status: Optional[str] = "已統計"
    notes: Optional[str] = ""

class MealCateringCreate(MealCateringBase):
    pass

class MealCateringResponse(MealCateringBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True


# ----------------- 【功能 68】幹部改選與開票計票 -----------------
class ElectionCandidateBase(BaseModel):
    election_term: Optional[str] = "第十四屆 (2026-2028)"
    position: Optional[str] = "分團長"
    candidate_name: str
    declaration: Optional[str] = ""
    votes_count: Optional[int] = 0
    is_active: Optional[bool] = True

class ElectionCandidateCreate(ElectionCandidateBase):
    pass

class ElectionCandidateResponse(ElectionCandidateBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True


# ----------------- 【功能 69】三好日常行善微日記 -----------------
class GoodDeedJournalBase(BaseModel):
    author_name: str
    journal_date: str
    good_deed: str
    good_words: str
    good_heart: str
    mood: Optional[str] = "法喜充滿"

class GoodDeedJournalCreate(GoodDeedJournalBase):
    pass

class GoodDeedJournalResponse(GoodDeedJournalBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True


# ----------------- 【功能 70】隨喜祈福迴向與祈願燈 -----------------
class BlessingLampBase(BaseModel):
    donor_name: str
    lamp_type: Optional[str] = "光明智慧燈"
    recipient_name: str
    prayer_text: Optional[str] = ""
    dedication_target: Optional[str] = ""

class BlessingLampCreate(BlessingLampBase):
    pass

class BlessingLampResponse(BlessingLampBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True


# ----------------- 【功能 71】微電影腳本故事板 -----------------
class FilmStoryboardBase(BaseModel):
    film_title: str
    scene_number: Optional[str] = "S01"
    shot_type: Optional[str] = "中景"
    visual_description: Optional[str] = ""
    dialogue: Optional[str] = ""
    location: Optional[str] = "新竹法寶寺"
    status: Optional[str] = "未拍攝"

class FilmStoryboardCreate(FilmStoryboardBase):
    pass

class FilmStoryboardResponse(FilmStoryboardBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True


# ----------------- 【功能 72】隨喜功德箱雲端收據 -----------------
class DonationReceiptBase(BaseModel):
    receipt_no: Optional[str] = ""
    donor_name: str
    donation_type: Optional[str] = "護持青年基金"
    amount: float = 1000.0
    payment_method: Optional[str] = "轉帳"
    dedication_notes: Optional[str] = ""

class DonationReceiptCreate(DonationReceiptBase):
    pass

class DonationReceiptResponse(DonationReceiptBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True


# ----------------- 【功能 73】梵唄法器音聲練習庫 -----------------
class ChantingItemBase(BaseModel):
    title: str
    instrument_type: Optional[str] = "大磬與木魚"
    bpm: Optional[int] = 60
    lyrics: Optional[str] = ""
    notations: Optional[str] = ""
    audio_guide_url: Optional[str] = ""

class ChantingItemCreate(ChantingItemBase):
    pass

class ChantingItemResponse(ChantingItemBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True


# ----------------- 【功能 74】青年職涯導師諮詢預約 -----------------
class CareerMentorshipBase(BaseModel):
    mentor_name: str
    mentor_field: Optional[str] = "半導體科技"
    applicant_name: str
    appointment_date: str
    appointment_time: Optional[str] = "19:00 - 20:00"
    topic: Optional[str] = ""
    status: Optional[str] = "已確認"
    notes: Optional[str] = ""

class CareerMentorshipCreate(CareerMentorshipBase):
    pass

class CareerMentorshipResponse(CareerMentorshipBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True


# ----------------- 【功能 78】道場空間借用與排審 -----------------
class VenueBookingBase(BaseModel):
    venue_name: Optional[str] = "青年團部會議室"
    booking_date: str
    start_time: Optional[str] = "14:00"
    end_time: Optional[str] = "17:00"
    applicant_name: str
    purpose: Optional[str] = ""
    status: Optional[str] = "已核准"
    notes: Optional[str] = ""

class VenueBookingCreate(VenueBookingBase):
    pass

class VenueBookingResponse(VenueBookingBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True


# ----------------- 【功能 79】經典圖書借閱與反思卡 -----------------
class LibraryBookLoanBase(BaseModel):
    book_title: str
    call_number: Optional[str] = "FGS-BK-001"
    borrower_name: str
    borrow_date: str
    return_due_date: str
    actual_return_date: Optional[str] = ""
    status: Optional[str] = "借閱中"
    rating_stars: Optional[int] = 5
    reflection_snippet: Optional[str] = ""

class LibraryBookLoanCreate(LibraryBookLoanBase):
    pass

class LibraryBookLoanResponse(LibraryBookLoanBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True


# ----------------- 【功能 81】失物招領與認領處 -----------------
class LostAndFoundItemBase(BaseModel):
    item_name: str
    category: Optional[str] = "生活用品"
    found_location: Optional[str] = "大雄寶殿"
    found_date: str
    finder_name: Optional[str] = "道場義工"
    status: Optional[str] = "待認領"
    claimer_name: Optional[str] = ""
    notes: Optional[str] = ""

class LostAndFoundItemCreate(LostAndFoundItemBase):
    pass

class LostAndFoundItemResponse(LostAndFoundItemBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True


# ----------------- 【功能 82】青年共乘與減碳里程 -----------------
class CarpoolTripBase(BaseModel):
    driver_name: str
    departure_location: str
    destination: Optional[str] = "新竹法寶寺"
    departure_time: str
    available_seats: Optional[int] = 3
    total_seats: Optional[int] = 4
    distance_km: Optional[float] = 15.0
    carbon_saved_kg: Optional[float] = 2.8
    contact_info: Optional[str] = ""
    status: Optional[str] = "開放共乘"

class CarpoolTripCreate(CarpoolTripBase):
    pass

class CarpoolTripResponse(CarpoolTripBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True


# ----------------- 【功能 83】Podcast 逐字稿與章節筆記 -----------------
class PodcastEpisodeBase(BaseModel):
    episode_number: Optional[str] = "EP01"
    title: str
    host_name: Optional[str] = "冠宇 & 思妤"
    guest_name: Optional[str] = ""
    duration_minutes: Optional[int] = 25
    summary: Optional[str] = ""
    chapter_timestamps: Optional[str] = ""
    key_quotes: Optional[str] = ""
    audio_url: Optional[str] = ""

class PodcastEpisodeCreate(PodcastEpisodeBase):
    pass

class PodcastEpisodeResponse(PodcastEpisodeBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True


# ----------------- 【功能 84】幹部值班輪值與巡檢日誌 -----------------
class DutyInspectionLogBase(BaseModel):
    duty_date: str
    duty_cadre: str
    inspection_items_checked: Optional[bool] = True
    hall_lights_status: Optional[str] = "正常關閉"
    ac_status: Optional[str] = "已關閉並斷電"
    security_status: Optional[str] = "門窗上鎖防盜安全"
    handover_notes: Optional[str] = ""
    next_duty_cadre: Optional[str] = ""

class DutyInspectionLogCreate(DutyInspectionLogBase):
    pass

class DutyInspectionLogResponse(DutyInspectionLogBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True


# ----------------- 【功能 86】三好生活茶席預約 -----------------
class TeaCeremonyBookingBase(BaseModel):
    guest_name: str
    guest_count: Optional[int] = 2
    booking_date: str
    tea_time: Optional[str] = "14:30 - 16:00"
    tea_variety: Optional[str] = "東方美人茶"
    tea_slip_quote: Optional[str] = "茶禪一味，吃茶去！"
    status: Optional[str] = "已確認"
    notes: Optional[str] = ""

class TeaCeremonyBookingCreate(TeaCeremonyBookingBase):
    pass

class TeaCeremonyBookingResponse(TeaCeremonyBookingBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True


# ----------------- 【功能 91】問卷題目自訂設計器 -----------------
class SurveyCustomQuestionBase(BaseModel):
    evidence_id: Optional[int] = 0
    question_text: str
    question_type: Optional[str] = "rating"
    options_json: Optional[str] = "[]"
    sort_order: Optional[int] = 0
    is_required: Optional[bool] = True

class SurveyCustomQuestionCreate(SurveyCustomQuestionBase):
    pass

class SurveyCustomQuestionResponse(SurveyCustomQuestionBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True


# ----------------- 【功能 93】廠商名冊與比價 -----------------
class VendorDirectoryBase(BaseModel):
    vendor_name: str
    category: Optional[str] = "印刷文宣"
    contact_person: Optional[str] = ""
    phone: Optional[str] = ""
    address: Optional[str] = ""
    rating_score: Optional[float] = 5.0
    notes: Optional[str] = ""

class VendorDirectoryCreate(VendorDirectoryBase):
    pass

class VendorDirectoryResponse(VendorDirectoryBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True


class PriceComparisonBase(BaseModel):
    item_title: str
    category: Optional[str] = "團服製衣"
    vendor_a: Optional[str] = ""
    price_a: Optional[float] = 0.0
    vendor_b: Optional[str] = ""
    price_b: Optional[float] = 0.0
    vendor_c: Optional[str] = ""
    price_c: Optional[float] = 0.0
    selected_vendor: Optional[str] = ""
    rationale: Optional[str] = ""

class PriceComparisonCreate(PriceComparisonBase):
    pass

class PriceComparisonResponse(PriceComparisonBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True


# ----------------- 【功能 94】幹部內部通知公佈欄 -----------------
class CadreNoticeBase(BaseModel):
    title: str
    content: Optional[str] = ""
    priority: Optional[str] = "normal"
    publisher_name: Optional[str] = "分團長"
    target_roles: Optional[str] = "all"

class CadreNoticeCreate(CadreNoticeBase):
    pass

class CadreNoticeResponse(CadreNoticeBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True

# ==============================================================================
# Round 20 (Features 96-100) Schemas
# ==============================================================================

class DharmaWisdomCardBase(BaseModel):
    theme: str = "福慧雙修"
    quote: str
    source: str = "星雲大師《佛光菜根譚》"
    practical_action: str = ""
    bg_color: str = "#FFFBEB"

class DharmaWisdomCardCreate(DharmaWisdomCardBase):
    pass

class DharmaWisdomCardResponse(DharmaWisdomCardBase):
    id: int
    created_at: Any
    class Config:
        orm_mode = True
        from_attributes = True

class EmergencyIncidentSopBase(BaseModel):
    incident_type: str
    severity_level: str = "level_2"
    immediate_actions: str
    escalation_contact: str = ""
    calming_script: str = ""
    first_aid_kit_location: str = "法寶寺 1F 知賓處急救箱與 2F 青年團部"

class EmergencyIncidentSopCreate(EmergencyIncidentSopBase):
    pass

class EmergencyIncidentSopResponse(EmergencyIncidentSopBase):
    id: int
    created_at: Any
    class Config:
        orm_mode = True
        from_attributes = True

class TeamDynamicsHealthBase(BaseModel):
    evaluation_period: str
    attendance_rate: float = 85.0
    cross_support_score: float = 88.0
    good_deeds_activity_score: float = 90.0
    cadre_satisfaction_score: float = 92.0
    composite_health_index: Optional[float] = None
    status_level: Optional[str] = None
    leadership_recommendation: Optional[str] = ""

class TeamDynamicsHealthCreate(TeamDynamicsHealthBase):
    pass

class TeamDynamicsHealthResponse(TeamDynamicsHealthBase):
    id: int
    composite_health_index: float
    status_level: str
    created_at: Any
    class Config:
        orm_mode = True
        from_attributes = True

class VegetarianRecipeBase(BaseModel):
    dish_name: str
    category: str = "tea_snack"
    ingredients: str
    steps: str
    dietary_tags: str = "全素,無五辛"
    carbon_offset_kg: float = 1.8
    prep_difficulty: str = "easy"

class VegetarianRecipeCreate(VegetarianRecipeBase):
    pass

class VegetarianRecipeResponse(VegetarianRecipeBase):
    id: int
    created_at: Any
    class Config:
        orm_mode = True
        from_attributes = True

class CentenaryWhitepaperCreate(BaseModel):
    title: str = "國際佛光會新竹青年分團 100 項數位弘法創新成效白皮書"
    summary: str = ""
    vision_statement: str = ""
    published_by: str = "新竹佛光青年分團秘書處"


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
