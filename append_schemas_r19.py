with open('app/schemas.py', 'r', encoding='utf-8') as f:
    text = f.read()

schemas_r19 = '''

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
'''

if 'SurveyCustomQuestionBase' not in text:
    text += schemas_r19
    with open('app/schemas.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('app/schemas.py updated with Round 19 schemas!')
else:
    print('Round 19 schemas already in app/schemas.py')
