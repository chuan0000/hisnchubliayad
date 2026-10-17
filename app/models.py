from datetime import datetime
from app.database import Base, HAS_SQLALCHEMY

if HAS_SQLALCHEMY:
    from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float
else:
    class MiniColumn:
        def __init__(self, col_type="String", primary_key=False, unique=False, index=False, nullable=True, default=None, onupdate=None):
            self.col_type = col_type
            self.primary_key = primary_key
            self.unique = unique
            self.index = index
            self.nullable = nullable
            self.default = default
            self.onupdate = onupdate
            self.name = None
            self.table = None
            self._is_column = True

        def __eq__(self, other):
            return ('eq', self.name, other)
        def __ne__(self, other):
            return ('ne', self.name, other)
        def asc(self):
            return ('asc', self.name)
        def desc(self):
            return ('desc', self.name)
        def contains(self, other):
            return ('contains', self.name, other)
        def __or__(self, other):
            return ('or', [self, other])

    def Column(col_type="String", *args, **kwargs):
        ctype = "String"
        if isinstance(col_type, str):
            ctype = col_type
        elif hasattr(col_type, '__name__'):
            ctype = col_type.__name__
        elif type(col_type).__name__ in ('Integer', 'String', 'Text', 'Boolean', 'DateTime', 'Float'):
            ctype = type(col_type).__name__

        return MiniColumn(
            col_type=ctype,
            primary_key=kwargs.get('primary_key', False),
            unique=kwargs.get('unique', False),
            index=kwargs.get('index', False),
            nullable=kwargs.get('nullable', True),
            default=kwargs.get('default', None),
            onupdate=kwargs.get('onupdate', None)
        )

    Integer = "Integer"
    String = lambda length=255: "String"
    Text = "Text"
    Boolean = "Boolean"
    DateTime = "DateTime"
    Float = "Float"

class User(Base):
    """使用者表（RBAC：超級管理員 super_admin、活動幹部 cadre）"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(String(20), default="cadre", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class SiteBlock(Base):
    """全站區塊動態內容表（Key-Value CMS，首頁文字、看版數值、Banner 等）"""
    __tablename__ = "site_blocks"

    id = Column(Integer, primary_key=True, index=True)
    block_key = Column(String(100), unique=True, index=True, nullable=False)
    block_title = Column(String(100), nullable=False)
    block_value = Column(Text, nullable=False)
    category = Column(String(50), default="general")
    value_type = Column(String(20), default="text")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class EvidenceItem(Base):
    """四大宗旨佐證表（文化、教育、共修、慈善之活動成果與公文檔案）"""
    __tablename__ = "evidence_items"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(20), index=True, nullable=False)  # 'culture', 'education', 'cultivation', 'charity'
    title = Column(String(200), nullable=False)
    event_date = Column(String(30), nullable=False)            # YYYY-MM-DD
    year = Column(String(10), default="2026")                  # 【功能 5】歷史年度成果庫
    evaluation_code = Column(String(50), default="")           # 【功能 1】總會評鑑指標代碼
    location = Column(String(150), default="新竹法寶寺")
    latitude = Column(Float, default=24.805)                   # 【功能 13】新竹與竹北在地足跡經緯度
    longitude = Column(Float, default=120.971)                 # 【功能 13】新竹與竹北在地足跡經緯度
    summary = Column(Text, default="")
    participants_count = Column(Integer, default=0)            # 【功能 4】實際參與人次
    volunteers_count = Column(Integer, default=0)              # 【功能 4】出勤幹部人數
    service_hours = Column(Float, default=0.0)                 # 【功能 4】服務總時數
    satisfaction_rate = Column(Integer, default=95)            # 【功能 4】活動滿意度 %
    expected_participants = Column(Integer, default=0)         # 【功能 8】籌備前預期參與人次
    expected_goals = Column(Text, default="")                  # 【功能 8】籌備前預期目標
    actual_highlights = Column(Text, default="")               # 【功能 8】舉辦後成效亮點與超標說明
    file_url = Column(String(255), default="")                 # 主要檔案路徑
    file_type = Column(String(20), default="image")            # 'image', 'pdf', 'link'
    original_filename = Column(String(255), default="")
    attachments = Column(Text, default="[]")                   # 【功能 3】多檔案附件 (JSON)
    photos_gallery = Column(Text, default="[]")                # 【功能 16】活動多圖輪播相簿 (JSON)
    video_url = Column(String(500), default="")                 # 【功能 22】YouTube 或影音串流嵌入網址
    audio_url = Column(String(500), default="")                 # 【功能 22】Spotify Podcast 或本機音訊網址
    max_quota = Column(Integer, default=50)                    # 【功能 31】活動線上報名名額上限
    is_registration_open = Column(Boolean, default=True)       # 【功能 31】是否開放線上報名
    created_by = Column(String(100), default="幹部")
    is_published = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ReviewerToken(Base):
    """【功能 9】評審委員專用免登入唯讀通行證"""
    __tablename__ = "reviewer_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    expires_at = Column(String(30), default="")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class EvidenceFeedback(Base):
    """【功能 10】評審線上星級評分與指導意見"""
    __tablename__ = "evidence_feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    evidence_id = Column(Integer, index=True, nullable=False)
    reviewer_name = Column(String(100), default="評鑑委員")
    rating = Column(Integer, default=5)
    comment = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

class TeamMember(Base):
    """幹部團隊表"""
    __tablename__ = "team_members"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    position = Column(String(100), nullable=False)
    term = Column(String(50), default="現任幹部")
    term_start = Column(String(20), default="")                # 【功能 17】任期起（如 2026）
    term_end = Column(String(20), default="")                  # 【功能 17】任期訖（如 2027）
    previous_roles = Column(Text, default="[]")                # 【功能 17】歷任職務輪調與傳承歷程 (JSON)
    avatar_url = Column(String(255), default="")
    bio = Column(Text, default="")
    contact = Column(String(150), default="")
    birthday = Column(String(20), default="")                 # 【功能 29】幹部團員生日 (MM-DD 或 YYYY-MM-DD)
    blessing_sent = Column(Boolean, default=False)             # 【功能 29】本年度是否已送出祝福
    emergency_contact_name = Column(String(100), default="")   # 【功能 43】緊急聯絡人姓名
    emergency_contact_phone = Column(String(50), default="")   # 【功能 43】緊急聯絡人電話
    blood_type = Column(String(10), default="O")               # 【功能 43】血型
    emergency_group = Column(String(50), default="活動應變組") # 【功能 43】道場防救災編組
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class HealthLog(Base):
    """健康打卡表（VEGRUN 蔬食路跑 / 青年健走運動累積，含雙軌截圖審核）"""
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
    created_at = Column(DateTime, default=datetime.utcnow)


class CadreAttendance(Base):
    """【功能 21】幹部活動出勤簽到與服務時數表"""
    __tablename__ = "cadre_attendances"

    id = Column(Integer, primary_key=True, index=True)
    evidence_id = Column(Integer, index=True, nullable=False)
    member_id = Column(Integer, index=True, nullable=False)
    member_name = Column(String(100), nullable=False)
    status = Column(String(20), default="present")             # 'present', 'absent', 'leave'
    hours = Column(Float, default=4.0)
    note = Column(String(255), default="")
    created_at = Column(DateTime, default=datetime.utcnow)

class ExamRecord(Base):
    """【功能 23】青年佛學會考與幹部培訓測驗登記表"""
    __tablename__ = "exam_records"

    id = Column(Integer, primary_key=True, index=True)
    exam_name = Column(String(200), nullable=False)
    exam_date = Column(String(30), nullable=False)
    exam_level = Column(String(50), default="中級")             # '初級', '中級', '高級', '幹部必修'
    examinee_name = Column(String(100), nullable=False)
    score = Column(Float, default=0.0)
    is_passed = Column(Boolean, default=True)
    certificate_no = Column(String(100), default="")
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

class SurveyResponse(Base):
    """【功能 24】活動回饋問卷線上評分與建議表"""
    __tablename__ = "survey_responses"

    id = Column(Integer, primary_key=True, index=True)
    evidence_id = Column(Integer, index=True, nullable=False)
    respondent_name = Column(String(100), default="匿名青年")
    overall_rating = Column(Integer, default=5)                # 1-5 星
    content_depth = Column(Integer, default=5)                 # 內容充實度 1-5 星
    organization_rating = Column(Integer, default=5)           # 流程動線 1-5 星
    venue_rating = Column(Integer, default=5)                  # 場地設施 1-5 星
    nps_score = Column(Integer, default=10)                    # 推薦度 NPS 0-10
    favorite_aspect = Column(String(255), default="")          # 最喜歡的環節
    suggestions = Column(Text, default="")                     # 建議回饋
    created_at = Column(DateTime, default=datetime.utcnow)


class InventoryItem(Base):
    """【功能 26】活動物資與法寶庫存盤點表"""
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, index=True)
    item_name = Column(String(100), nullable=False)
    category = Column(String(50), default="活動器材")         # '活動器材', '法寶經書', '文宣服裝', '行政耗材'
    quantity = Column(Integer, default=1)
    unit = Column(String(20), default="件")
    location = Column(String(100), default="法寶寺青年分團室")
    status = Column(String(20), default="normal")             # 'normal', 'loaned', 'low_stock', 'maintenance'
    loan_to = Column(String(100), default="")                 # 外借幹部或單位
    note = Column(Text, default="")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class FinanceTransaction(Base):
    """【功能 27】分團年度財務經費收支流水帳與核銷表"""
    __tablename__ = "finance_transactions"

    id = Column(Integer, primary_key=True, index=True)
    tx_date = Column(String(30), nullable=False)               # YYYY-MM-DD
    tx_type = Column(String(20), nullable=False)               # 'income' (收入) 或 'expense' (支出)
    category = Column(String(50), default="活動經費")
    title = Column(String(200), nullable=False)
    amount = Column(Float, nullable=False)
    evidence_id = Column(Integer, default=0)                   # 關聯之活動 ID
    handler = Column(String(100), default="財務長")
    receipt_voucher = Column(String(100), default="")         # 憑證單據編號
    note = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)


class ActivityRegistration(Base):
    """【功能 31】活動線上報名表與名額控管"""
    __tablename__ = "activity_registrations"

    id = Column(Integer, primary_key=True, index=True)
    evidence_id = Column(Integer, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    phone = Column(String(50), default="")
    email = Column(String(100), default="")
    affiliation = Column(String(100), default="")              # 就讀學校或服務機關
    dietary = Column(String(20), default="vegan")              # 'vegan', 'lacto-ovo', 'convenience'
    status = Column(String(20), default="confirmed")           # 'confirmed', 'waitlist', 'cancelled'
    notes = Column(Text, default="")
    registered_at = Column(DateTime, default=datetime.utcnow)


class PartnerStore(Base):
    """【功能 42】新竹與竹北在地青年特約友好商家表"""
    __tablename__ = "partner_stores"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    category = Column(String(50), default="蔬食美饌")          # '蔬食美饌', '文創書店', '青年咖啡', '生活選物'
    address = Column(String(200), nullable=False)
    latitude = Column(Float, default=24.805)
    longitude = Column(Float, default=120.971)
    perk = Column(String(200), default="持佛光青年證享專屬優惠")
    contact = Column(String(100), default="")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class MeetingActionItem(Base):
    """【功能 44】活動檢討會會議紀錄與決議事項追蹤表"""
    __tablename__ = "meeting_action_items"

    id = Column(Integer, primary_key=True, index=True)
    evidence_id = Column(Integer, index=True, nullable=False)
    meeting_date = Column(String(30), nullable=False)
    topic = Column(String(200), nullable=False)
    discussion = Column(Text, default="")
    assignee = Column(String(100), default="幹部")
    due_date = Column(String(30), default="")
    status = Column(String(20), default="pending")             # 'pending', 'in_progress', 'completed'
    created_at = Column(DateTime, default=datetime.utcnow)


class CountdownEvent(Base):
    """【功能 47】道場重大節慶活動倒數計時表"""
    __tablename__ = "countdown_events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    target_date = Column(String(30), nullable=False)           # YYYY-MM-DD HH:MM:SS
    category = Column(String(50), default="總會盛事")          # '總會盛事', '常住節慶', '分團主辦'
    description = Column(Text, default="")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class VolunteerPassbook(Base):
    """【功能 51】青年志工服務時數歷史存摺帳戶"""
    __tablename__ = "volunteer_passbooks"

    id = Column(Integer, primary_key=True, index=True)
    volunteer_name = Column(String(100), index=True, nullable=False)
    member_id = Column(Integer, default=0)
    evidence_id = Column(Integer, default=0)
    service_date = Column(String(30), nullable=False)
    activity_title = Column(String(200), nullable=False)
    service_hours = Column(Float, default=4.0)
    verifier = Column(String(100), default="分團長")
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

class FaqItem(Base):
    """【功能 53】活動常見問題 FAQ 摺疊式知識庫"""
    __tablename__ = "faq_items"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50), default="活動參與")          # '入團須知', '活動參與', '時數認證', '道場生活'
    question = Column(String(255), nullable=False)
    answer = Column(Text, nullable=False)
    sort_order = Column(Integer, default=0)
    is_published = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    """【功能 55】全站操作審計日誌與安全監控"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False)
    user_role = Column(String(20), default="cadre")
    action = Column(String(100), nullable=False)               # '登入系統', '新增佐證', '還原備份', '修改區塊'
    target = Column(String(200), default="")
    ip_address = Column(String(50), default="127.0.0.1")
    details = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)


class ZenMeditation(Base):
    """【功能 54】青年生活禪每日靜心打卡計時鐘"""
    __tablename__ = "zen_meditations"

    id = Column(Integer, primary_key=True, index=True)
    participant_name = Column(String(100), index=True, nullable=False)
    duration_minutes = Column(Integer, default=10)
    reflection_notes = Column(Text, default="")
    mood = Column(String(50), default="心平氣和")
    created_at = Column(DateTime, default=datetime.utcnow)


class BudgetRequisition(Base):
    """【功能 57】活動經費線上請購預算與核銷請款單"""
    __tablename__ = "budget_requisitions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    applicant_name = Column(String(100), nullable=False)
    category = Column(String(50), default="活動耗材")         # '活動耗材', '宣傳文宣', '膳食點心', '交通租車', '講師鐘點'
    requested_amount = Column(Float, default=0.0)
    approved_amount = Column(Float, default=0.0)
    status = Column(String(30), default="待審核")             # '待審核', '已核准', '已核銷', '已退回'
    invoice_no = Column(String(100), default="")
    receipt_url = Column(String(255), default="")
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

class VolunteerShift(Base):
    """【功能 58】道場法會與活動現場排班表"""
    __tablename__ = "volunteer_shifts"

    id = Column(Integer, primary_key=True, index=True)
    activity_title = Column(String(200), nullable=False)
    shift_date = Column(String(30), nullable=False)
    shift_time = Column(String(50), default="08:00 - 12:00")
    role_name = Column(String(50), default="場務組")           # '音控組', '場務組', '交通導引', '知賓接待', '大會攝影', '典座行堂'
    volunteer_name = Column(String(100), nullable=False)
    status = Column(String(30), default="已確認")             # '已排班', '已確認', '已簽到', '請假換班'
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

class SiteAnnouncement(Base):
    """【功能 60】站內即時公告推播跑馬燈與彈窗通知"""
    __tablename__ = "site_announcements"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, default="")
    announcement_type = Column(String(30), default="info")    # 'info', 'urgent', 'event', 'blessing'
    is_marquee = Column(Boolean, default=True)
    is_popup = Column(Boolean, default=False)
    priority = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AssetLoan(Base):
    """【功能 62】活動物資借用登記與歸還時效追蹤流水帳"""
    __tablename__ = "asset_loans"

    id = Column(Integer, primary_key=True, index=True)
    item_name = Column(String(200), nullable=False)
    borrower_name = Column(String(100), nullable=False)
    borrow_date = Column(String(30), nullable=False)
    return_due_date = Column(String(30), nullable=False)
    actual_return_date = Column(String(30), default="")
    status = Column(String(30), default="借出中")             # '借出中', '已歸還', '逾期未還'
    purpose = Column(String(200), default="")
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

class VideoScript(Base):
    """【功能 63】佛光三好短影音腳本企劃靈感庫"""
    __tablename__ = "video_scripts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    topic_category = Column(String(50), default="三好日常")     # '三好日常', '青年生活禪', '科技走讀', '道場美食'
    duration_seconds = Column(Integer, default=30)
    hook_line = Column(String(255), default="")
    scene_breakdown = Column(Text, default="")
    voiceover_script = Column(Text, default="")
    hashtags = Column(String(255), default="")
    created_at = Column(DateTime, default=datetime.utcnow)

class MemberSkill(Base):
    """【功能 64】青年團員技能專長樹與人才庫媒合"""
    __tablename__ = "member_skills"

    id = Column(Integer, primary_key=True, index=True)
    member_name = Column(String(100), index=True, nullable=False)
    primary_skills = Column(String(255), nullable=False)       # '影音剪輯, 平面美編, 主持司儀'
    level = Column(String(50), default="專業熟練")              # '基礎熱心', '進階熟練', '專業精通'
    portfolio_link = Column(String(255), default="")
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

class LivePollVote(Base):
    """【功能 65】活動現場即時滿意度動態投票與彈幕心得牆"""
    __tablename__ = "live_poll_votes"

    id = Column(Integer, primary_key=True, index=True)
    event_title = Column(String(200), nullable=False)
    question_title = Column(String(255), nullable=False)
    selected_option = Column(String(100), nullable=False)
    voter_name = Column(String(100), default="青年同修")
    message = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)


class StudyGroupNote(Base):
    """【功能 66】道場青年讀書會篇章研討與導讀筆記庫"""
    __tablename__ = "study_group_notes"

    id = Column(Integer, primary_key=True, index=True)
    book_title = Column(String(200), nullable=False)
    chapter_title = Column(String(200), nullable=False)
    moderator_name = Column(String(100), nullable=False)
    discussion_date = Column(String(30), nullable=False)
    core_questions = Column(Text, default="")
    key_takeaways = Column(Text, default="")
    action_pledge = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

class MealCatering(Base):
    """【功能 67】活動現場志工愛心便當與茶水需求統計"""
    __tablename__ = "meal_caterings"

    id = Column(Integer, primary_key=True, index=True)
    activity_title = Column(String(200), nullable=False)
    event_date = Column(String(30), nullable=False)
    meal_type = Column(String(50), default="午餐便當")        # '午餐便當', '晚餐便當', '下午茶點'
    vegetarian_type = Column(String(50), default="全素")      # '全素', '蛋奶素', '特殊過敏'
    quantity = Column(Integer, default=20)
    contact_person = Column(String(100), default="活動幹部")
    status = Column(String(30), default="已統計")             # '已統計', '已訂餐', '已送達', '已發放'
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

class ElectionCandidate(Base):
    """【功能 68】青年團員年度幹部改選線上推薦與開票計票器"""
    __tablename__ = "election_candidates"

    id = Column(Integer, primary_key=True, index=True)
    election_term = Column(String(50), default="第十四屆 (2026-2028)")
    position = Column(String(50), default="分團長")           # '分團長', '副分團長', '秘書', '財務長', '活動長'
    candidate_name = Column(String(100), nullable=False)
    declaration = Column(Text, default="")
    votes_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class GoodDeedJournal(Base):
    """【功能 69】三好青年日常行善實踐微日記"""
    __tablename__ = "good_deed_journals"

    id = Column(Integer, primary_key=True, index=True)
    author_name = Column(String(100), index=True, nullable=False)
    journal_date = Column(String(30), nullable=False)
    good_deed = Column(Text, nullable=False)
    good_words = Column(Text, nullable=False)
    good_heart = Column(Text, nullable=False)
    mood = Column(String(50), default="法喜充滿")
    created_at = Column(DateTime, default=datetime.utcnow)

class BlessingLamp(Base):
    """【功能 70】道場法會隨喜祈福迴向卡與虛擬祈願燈"""
    __tablename__ = "blessing_lamps"

    id = Column(Integer, primary_key=True, index=True)
    donor_name = Column(String(100), nullable=False)
    lamp_type = Column(String(50), default="光明智慧燈")       # '光明智慧燈', '三好平安燈', '菩提精進燈', '如意福慧燈'
    recipient_name = Column(String(100), nullable=False)
    prayer_text = Column(Text, default="")
    dedication_target = Column(String(200), default="")
    created_at = Column(DateTime, default=datetime.utcnow)


class FilmStoryboard(Base):
    """【功能 71】三好微電影與短片創作腳本分鏡故事板"""
    __tablename__ = "film_storyboards"

    id = Column(Integer, primary_key=True, index=True)
    film_title = Column(String(200), nullable=False)
    scene_number = Column(String(20), default="S01")
    shot_type = Column(String(50), default="中景")           # '特寫', '中景', '全景', '空拍'
    visual_description = Column(Text, default="")
    dialogue = Column(Text, default="")
    location = Column(String(100), default="新竹法寶寺")
    status = Column(String(30), default="未拍攝")             # '未拍攝', '已完成', '後製中'
    created_at = Column(DateTime, default=datetime.utcnow)

class DonationReceipt(Base):
    """【功能 72】道場法會與活動隨喜功德箱雲端收據產生器"""
    __tablename__ = "donation_receipts"

    id = Column(Integer, primary_key=True, index=True)
    receipt_no = Column(String(50), nullable=False)
    donor_name = Column(String(100), nullable=False)
    donation_type = Column(String(50), default="護持青年基金")  # '護持青年基金', '隨喜助印經典', '道場法會供養', '三好營隊贊助'
    amount = Column(Float, default=1000.0)
    payment_method = Column(String(50), default="轉帳")         # '轉帳', '現金', 'LinePay'
    dedication_notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

class ChantingItem(Base):
    """【功能 73】佛光青年梵唄法器音聲練習調音與節拍器"""
    __tablename__ = "chanting_items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    instrument_type = Column(String(50), default="大磬與木魚")  # '大磬', '木魚', '引磬', '鐺鈸', '大磬與木魚'
    bpm = Column(Integer, default=60)
    lyrics = Column(Text, default="")
    notations = Column(Text, default="")
    audio_guide_url = Column(String(255), default="")
    created_at = Column(DateTime, default=datetime.utcnow)

class CareerMentorship(Base):
    """【功能 74】青年生涯職涯發展與三好職場導師諮詢預約"""
    __tablename__ = "career_mentorships"

    id = Column(Integer, primary_key=True, index=True)
    mentor_name = Column(String(100), nullable=False)
    mentor_field = Column(String(50), default="半導體科技")    # '半導體科技', '文創設計', '教育輔導', '組織管理'
    applicant_name = Column(String(100), nullable=False)
    appointment_date = Column(String(30), nullable=False)
    appointment_time = Column(String(30), default="19:00 - 20:00")
    topic = Column(String(200), default="")
    status = Column(String(30), default="已確認")             # '待確認', '已確認', '已完成'
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)


class VenueBooking(Base):
    """【功能 78】活動場地借用時段預約與道場空間衝突排審"""
    __tablename__ = "venue_bookings"

    id = Column(Integer, primary_key=True, index=True)
    venue_name = Column(String(100), default="青年團部會議室")  # '大雄寶殿', '生活禪堂', '青年團部會議室', '多功能教室', '滴水坊生活茶席'
    booking_date = Column(String(30), nullable=False)
    start_time = Column(String(30), default="14:00")
    end_time = Column(String(30), default="17:00")
    applicant_name = Column(String(100), nullable=False)
    purpose = Column(String(200), default="")
    status = Column(String(30), default="已核准")             # '待審核', '已核准', '已退回'
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

class LibraryBookLoan(Base):
    """【功能 79】青年學員法寶經典借閱歸還與心得反思卡"""
    __tablename__ = "library_book_loans"

    id = Column(Integer, primary_key=True, index=True)
    book_title = Column(String(200), nullable=False)
    call_number = Column(String(50), default="FGS-BK-001")
    borrower_name = Column(String(100), nullable=False)
    borrow_date = Column(String(30), nullable=False)
    return_due_date = Column(String(30), nullable=False)
    actual_return_date = Column(String(30), default="")
    status = Column(String(30), default="借閱中")             # '借閱中', '已歸還', '逾期'
    rating_stars = Column(Integer, default=5)
    reflection_snippet = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)


class LostAndFoundItem(Base):
    """【功能 81】青年活動現場失物招領與尋獲認領登記處"""
    __tablename__ = "lost_and_found_items"

    id = Column(Integer, primary_key=True, index=True)
    item_name = Column(String(200), nullable=False)
    category = Column(String(50), default="生活用品")          # '證件錢包', '3C電子', '生活用品', '衣物飾品', '其他'
    found_location = Column(String(100), default="大雄寶殿")
    found_date = Column(String(30), nullable=False)
    finder_name = Column(String(100), default="道場義工")
    status = Column(String(30), default="待認領")             # '待認領', '已領回'
    claimer_name = Column(String(100), default="")
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

class CarpoolTrip(Base):
    """【功能 82】新竹與竹北青年共乘交通媒合與減碳里程計算"""
    __tablename__ = "carpool_trips"

    id = Column(Integer, primary_key=True, index=True)
    driver_name = Column(String(100), nullable=False)
    departure_location = Column(String(100), nullable=False)
    destination = Column(String(100), default="新竹法寶寺")
    departure_time = Column(String(50), nullable=False)
    available_seats = Column(Integer, default=3)
    total_seats = Column(Integer, default=4)
    distance_km = Column(Float, default=15.0)
    carbon_saved_kg = Column(Float, default=2.8)
    contact_info = Column(String(100), default="")
    status = Column(String(30), default="開放共乘")             # '開放共乘', '已滿座', '已出發'
    created_at = Column(DateTime, default=datetime.utcnow)

class PodcastEpisode(Base):
    """【功能 83】佛光三好Podcast《竹光三參》逐字稿與音訊章節筆記庫"""
    __tablename__ = "podcast_episodes"

    id = Column(Integer, primary_key=True, index=True)
    episode_number = Column(String(20), default="EP01")
    title = Column(String(200), nullable=False)
    host_name = Column(String(100), default="冠宇 & 思妤")
    guest_name = Column(String(100), default="")
    duration_minutes = Column(Integer, default=25)
    summary = Column(Text, default="")
    chapter_timestamps = Column(Text, default="")
    key_quotes = Column(Text, default="")
    audio_url = Column(String(255), default="")
    created_at = Column(DateTime, default=datetime.utcnow)

class DutyInspectionLog(Base):
    """【功能 84】青年幹部值班輪值與道場巡檢交接電子日誌"""
    __tablename__ = "duty_inspection_logs"

    id = Column(Integer, primary_key=True, index=True)
    duty_date = Column(String(30), nullable=False)
    duty_cadre = Column(String(100), nullable=False)
    inspection_items_checked = Column(Boolean, default=True)
    hall_lights_status = Column(String(50), default="正常關閉")
    ac_status = Column(String(50), default="已關閉並斷電")
    security_status = Column(String(50), default="門窗上鎖防盜安全")
    handover_notes = Column(Text, default="")
    next_duty_cadre = Column(String(100), default="")
    created_at = Column(DateTime, default=datetime.utcnow)


class TeaCeremonyBooking(Base):
    """【功能 86】佛光三好茶席茶道品茗會預約與茶帖心靈籤語"""
    __tablename__ = "tea_ceremony_bookings"

    id = Column(Integer, primary_key=True, index=True)
    guest_name = Column(String(100), nullable=False)
    guest_count = Column(Integer, default=2)
    booking_date = Column(String(30), nullable=False)
    tea_time = Column(String(30), default="14:30 - 16:00")
    tea_variety = Column(String(50), default="東方美人茶")     # '東方美人茶', '高山烏龍', '白毫普洱', '舒壓花草茶'
    tea_slip_quote = Column(Text, default="茶禪一味，吃茶去！")
    status = Column(String(30), default="已確認")             # '待確認', '已確認', '已完成'
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)


class SurveyCustomQuestion(Base):
    """【功能 91】活動滿意度問卷自訂題目設計器"""
    __tablename__ = "survey_custom_questions"

    id = Column(Integer, primary_key=True, index=True)
    evidence_id = Column(Integer, index=True, default=0)
    question_text = Column(String(255), nullable=False)
    question_type = Column(String(50), default="rating")      # 'rating', 'choice', 'text'
    options_json = Column(String(255), default="[]")
    sort_order = Column(Integer, default=0)
    is_required = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class VendorDirectory(Base):
    """【功能 93】活動物資採購廠商名錄"""
    __tablename__ = "vendor_directories"

    id = Column(Integer, primary_key=True, index=True)
    vendor_name = Column(String(100), nullable=False)
    category = Column(String(50), default="印刷文宣")          # '印刷文宣', '團服製衣', '音響租賃', '蔬食餐飲', '交通租車'
    contact_person = Column(String(100), default="")
    phone = Column(String(50), default="")
    address = Column(String(200), default="")
    rating_score = Column(Float, default=5.0)
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

class PriceComparison(Base):
    """【功能 93】活動物資採購三家比價單"""
    __tablename__ = "price_comparisons"

    id = Column(Integer, primary_key=True, index=True)
    item_title = Column(String(200), nullable=False)
    category = Column(String(50), default="團服製衣")
    vendor_a = Column(String(100), default="")
    price_a = Column(Float, default=0.0)
    vendor_b = Column(String(100), default="")
    price_b = Column(Float, default=0.0)
    vendor_c = Column(String(100), default="")
    price_c = Column(Float, default=0.0)
    selected_vendor = Column(String(100), default="")
    rationale = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

class CadreNotice(Base):
    """【功能 94】道場青年幹部即時通訊公告與內部公佈欄"""
    __tablename__ = "cadre_notices"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, default="")
    priority = Column(String(20), default="normal")           # 'normal', 'urgent', 'top'
    publisher_name = Column(String(100), default="分團長")
    target_roles = Column(String(100), default="all")
    created_at = Column(DateTime, default=datetime.utcnow)

# ==============================================================================
# Round 20 (Features 96-100) Data Models
# ==============================================================================

class DharmaWisdomCard(Base):
    """【功能 96】佛光三好微行持每日福慧籤卡與智慧法語庫"""
    __tablename__ = "dharma_wisdom_cards"

    id = Column(Integer, primary_key=True, index=True)
    theme = Column(String(50), default="福慧雙修")         # 福慧雙修、身心自在、慈悲喜捨、精進無畏
    quote = Column(Text, nullable=False)
    source = Column(String(100), default="星雲大師《佛光菜根譚》")
    practical_action = Column(Text, default="")            # 今日三好修持行動
    bg_color = Column(String(20), default="#FFFBEB")
    created_at = Column(DateTime, default=datetime.utcnow)

class EmergencyIncidentSop(Base):
    """【功能 97】道場活動突發事件應變與青年安撫SOP指南庫"""
    __tablename__ = "emergency_incident_sops"

    id = Column(Integer, primary_key=True, index=True)
    incident_type = Column(String(100), nullable=False)   # 學員中暑、突發停電、地震疏散、走失協尋等
    severity_level = Column(String(20), default="level_2") # level_1 (輕度), level_2 (中度), level_3 (重大)
    immediate_actions = Column(Text, nullable=False)      # 第一步現場處置
    escalation_contact = Column(String(200), default="")  # 通報回報鏈
    calming_script = Column(Text, default="")             # 青年與家長安撫話術
    first_aid_kit_location = Column(String(150), default="法寶寺 1F 知賓處急救箱與 2F 青年團部")
    created_at = Column(DateTime, default=datetime.utcnow)

class TeamDynamicsHealth(Base):
    """【功能 98】青年義工團隊動能與向心力健康指數評估器"""
    __tablename__ = "team_dynamics_health"

    id = Column(Integer, primary_key=True, index=True)
    evaluation_period = Column(String(50), nullable=False) # 季度或月份
    attendance_rate = Column(Float, default=85.0)          # 出席率 %
    cross_support_score = Column(Float, default=88.0)      # 跨組支援度 (1-100)
    good_deeds_activity_score = Column(Float, default=90.0)# 三好實踐活躍度 (1-100)
    cadre_satisfaction_score = Column(Float, default=92.0) # 幹部溝通滿意度 (1-100)
    composite_health_index = Column(Float, default=88.75)  # 綜合向心力指數
    status_level = Column(String(30), default="excellent") # excellent (綠燈), attention (黃燈), warning (紅燈)
    leadership_recommendation = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

class VegetarianRecipe(Base):
    """【功能 99】佛門茶水點心與蔬食環保無肉菜單食譜庫"""
    __tablename__ = "vegetarian_recipes"

    id = Column(Integer, primary_key=True, index=True)
    dish_name = Column(String(150), nullable=False)
    category = Column(String(50), default="tea_snack")     # tea_snack, main_dish, beverage, dessert
    ingredients = Column(Text, nullable=False)
    steps = Column(Text, nullable=False)
    dietary_tags = Column(String(100), default="全素,無五辛")
    carbon_offset_kg = Column(Float, default=1.8)          # 相比葷食每份減碳千克數
    prep_difficulty = Column(String(20), default="easy")   # easy, medium, advanced
    created_at = Column(DateTime, default=datetime.utcnow)

class CentenaryMilestoneWhitepaper(Base):
    """【功能 100】佛光青年分團年度弘法成效大數據全景總覽與百年弘法白皮書"""
    __tablename__ = "centenary_milestone_whitepapers"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), default="國際佛光會新竹青年分團 100 項數位弘法創新成效白皮書")
    version = Column(String(20), default="v1.0-Centenary")
    summary = Column(Text, default="")
    total_features_count = Column(Integer, default=100)
    metrics_snapshot_json = Column(Text, default="{}")
    vision_statement = Column(Text, default="")
    published_by = Column(String(100), default="新竹佛光青年分團秘書處")
    created_at = Column(DateTime, default=datetime.utcnow)


class YouthWish(Base):
    """【青年心願牆】青年心願許願卡片、分類、預算、點讚集氣與圓滿狀態"""
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
    """【社群與活動爬蟲】外部社群與公開活動爬蟲抓取紀錄與匯入佐證清冊"""
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
