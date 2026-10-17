with open('app/models.py', 'r', encoding='utf-8') as f:
    text = f.read()

models_r19 = '''

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
'''

if 'SurveyCustomQuestion' not in text:
    text += models_r19
    with open('app/models.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('app/models.py updated with Round 19 models!')
else:
    print('Round 19 models already in app/models.py')
