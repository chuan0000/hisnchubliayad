with open('app/routers/blocks.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update models import
if 'SurveyCustomQuestion' not in text:
    old_models = 'LostAndFoundItem, CarpoolTrip, PodcastEpisode, TeaCeremonyBooking'
    new_models = 'LostAndFoundItem, CarpoolTrip, PodcastEpisode, TeaCeremonyBooking, SurveyCustomQuestion, VendorDirectory, PriceComparison'
    text = text.replace(old_models, new_models, 1)
    print('Imported models in blocks.py for R19')

# 2. Update schemas import
if 'SurveyCustomQuestionResponse' not in text:
    old_schemas = 'TeaCeremonyBookingCreate, TeaCeremonyBookingResponse'
    new_schemas = 'TeaCeremonyBookingCreate, TeaCeremonyBookingResponse, SurveyCustomQuestionCreate, SurveyCustomQuestionResponse, VendorDirectoryCreate, VendorDirectoryResponse, PriceComparisonCreate, PriceComparisonResponse'
    text = text.replace(old_schemas, new_schemas, 1)
    print('Imported schemas in blocks.py for R19')

r19_blocks_code = '''
# ==============================================================================
# 【功能 91】活動滿意度問卷自訂題目設計器 API
# ==============================================================================
custom_survey_router = APIRouter(prefix="/api/custom-surveys", tags=["問卷題目自訂設計器 (Survey Builder)"])

@custom_survey_router.get("/{evidence_id}", response_model=List[SurveyCustomQuestionResponse])
def list_custom_survey_questions(evidence_id: int, db: Session = Depends(get_db)):
    """【公開/青年】調閱指定活動專屬自訂問卷題目"""
    items = db.query(SurveyCustomQuestion).filter(SurveyCustomQuestion.evidence_id == evidence_id).order_by(SurveyCustomQuestion.sort_order.asc(), SurveyCustomQuestion.id.asc()).all()
    if not items:
        # Default baseline question if none customized yet
        return [
            SurveyCustomQuestion(id=1, evidence_id=evidence_id, question_text="您對本次青年活動整體安排滿意度？", question_type="rating", options_json="[1,2,3,4,5]", sort_order=1, is_required=True),
            SurveyCustomQuestion(id=2, evidence_id=evidence_id, question_text="今日課程或走讀活動最讓您有啟發的內容是？", question_type="text", options_json="[]", sort_order=2, is_required=True)
        ]
    return items

@custom_survey_router.post("", response_model=SurveyCustomQuestionResponse)
def create_custom_survey_question(
    q_in: SurveyCustomQuestionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_cadre)
):
    """【幹部後台】為活動動態新增自訂問卷題目"""
    new_q = SurveyCustomQuestion(
        evidence_id=q_in.evidence_id or 0,
        question_text=q_in.question_text,
        question_type=q_in.question_type or "rating",
        options_json=q_in.options_json or "[]",
        sort_order=q_in.sort_order or 0,
        is_required=q_in.is_required if q_in.is_required is not None else True
    )
    db.add(new_q)
    db.commit()
    db.refresh(new_q)
    return new_q

@custom_survey_router.delete("/{q_id}")
def delete_custom_survey_question(
    q_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_cadre)
):
    """【幹部後台】刪除自訂問卷題目"""
    q = db.query(SurveyCustomQuestion).filter(SurveyCustomQuestion.id == q_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="找不到此題目")
    db.delete(q)
    db.commit()
    return {"status": "success", "message": "問卷題目已刪除"}


# ==============================================================================
# 【功能 92】三好微行持功德回向文疏高畫質列印排版 API
# ==============================================================================
liturgy_router = APIRouter(prefix="/api/liturgy", tags=["回向文疏排版列印 (Dharma Liturgy)"])

@liturgy_router.get("/print-slip")
def generate_liturgy_slip(
    donor_name: str = "陳冠宇",
    target: str = "闔家眷屬與法界眾生",
    prayer_text: str = "願以此行善功德，回向十方眾生身心康泰、智慧如海、吉祥如意！",
    date: str = "2026-10-16"
):
    """【功能 92】動態產製典雅直排佛教回向文疏（高畫質向量 SVG，支援 A4 / 斗方列印）"""
    cert_id = f"BLIA-HCY-LITURGY-{abs(hash(donor_name + date)) % 9000 + 1000:04d}"

    svg_markup = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 840" width="100%" height="100%" style="background-color: #FEF3C7; font-family: serif;">
      <!-- 外框雙層祥雲紋理飾條 -->
      <rect x="20" y="20" width="560" height="800" rx="16" fill="none" stroke="#B45309" stroke-width="4" />
      <rect x="30" y="30" width="540" height="780" rx="12" fill="none" stroke="#D97706" stroke-width="1.5" stroke-dasharray="6,3" />

      <!-- 頂部文疏全銜 -->
      <text x="300" y="75" font-size="13" font-weight="bold" fill="#78350F" text-anchor="middle" letter-spacing="4">國際佛光會中華青年總會・新竹青年分團</text>
      <text x="300" y="115" font-size="24" font-weight="900" fill="#451A03" text-anchor="middle" letter-spacing="3">三好微行持功德回向文疏</text>
      <line x1="180" y1="130" x2="420" y2="130" stroke="#B45309" stroke-width="2" />

      <!-- 疏文字號 -->
      <text x="530" y="70" font-size="10" font-family="monospace" fill="#78350F" text-anchor="end">{cert_id}</text>

      <!-- 核心文疏內容 (經典古樸直排版式體驗) -->
      <foreignObject x="60" y="170" width="480" height="460">
        <div xmlns="http://www.w3.org/1999/xhtml" style="font-size: 16px; line-height: 2.2; color: #451A03; text-align: justify; text-indent: 2em; writing-mode: vertical-rl; height: 420px; font-weight: 500;">
          伏以 佛光普照，法水長流。大德發菩提心，實踐三好四給行願。
          弟子【{donor_name}】誠惶誠恐，至誠稽首，於人間佛道精進不懈。
          謹將今日身做好事、口說好話、心存好心之微善功德，
          悉皆回向於【{target}】。
          祈願佛光注照，消災免難，福慧增長，善根日茂。
          疏文祈願：『{prayer_text}』
          四恩總報，三有齊資；普願法界，同證菩提！
        </div>
      </foreignObject>

      <!-- 用印蓋章 -->
      <rect x="80" y="660" width="70" height="70" fill="#DC2626" opacity="0.85" rx="6" />
      <text x="115" y="692" font-size="11" font-weight="bold" fill="#FFFFFF" text-anchor="middle">佛光青年</text>
      <text x="115" y="710" font-size="11" font-weight="bold" fill="#FFFFFF" text-anchor="middle">回向用印</text>

      <!-- 落款日期與道場 -->
      <text x="500" y="730" font-size="12" fill="#78350F" text-anchor="end">佛光山新竹法寶寺 監院法師 慈悲印可</text>
      <text x="500" y="755" font-size="12" fill="#78350F" text-anchor="end">公曆 {date} 歲次丙午年吉日 敬疏</text>
    </svg>"""

    return {
        "status": "success",
        "cert_id": cert_id,
        "donor_name": donor_name,
        "target": target,
        "svg_markup": svg_markup
    }


# ==============================================================================
# 【功能 93】活動物資採購比價清單與廠商名錄 API
# ==============================================================================
procurement_router = APIRouter(prefix="/api/procurement", tags=["採購比價與廠商名冊 (Procurement & Vendors)"])

@procurement_router.get("/vendors", response_model=List[VendorDirectoryResponse])
def list_procurement_vendors(category: Optional[str] = None, db: Session = Depends(get_db)):
    """【幹部後台】調閱活動物資合作特約廠商名冊"""
    query = db.query(VendorDirectory)
    if category:
        query = query.filter(VendorDirectory.category == category)
    return query.order_by(VendorDirectory.id.desc()).all()

@procurement_router.post("/vendors", response_model=VendorDirectoryResponse)
def create_procurement_vendor(
    v_in: VendorDirectoryCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_cadre)
):
    """【幹部後台】登記新合作物資廠商"""
    new_v = VendorDirectory(
        vendor_name=v_in.vendor_name,
        category=v_in.category or "印刷文宣",
        contact_person=v_in.contact_person or "",
        phone=v_in.phone or "",
        address=v_in.address or "",
        rating_score=v_in.rating_score or 5.0,
        notes=v_in.notes or ""
    )
    db.add(new_v)
    db.commit()
    db.refresh(new_v)
    return new_v

@procurement_router.get("/comparisons", response_model=List[PriceComparisonResponse])
def list_price_comparisons(db: Session = Depends(get_db)):
    """【幹部後台】調閱採購三家比價單紀錄"""
    return db.query(PriceComparison).order_by(PriceComparison.id.desc()).all()

@procurement_router.post("/comparisons", response_model=PriceComparisonResponse)
def create_price_comparison(
    p_in: PriceComparisonCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_cadre)
):
    """【幹部後台】建立三家比價審核單"""
    new_p = PriceComparison(
        item_title=p_in.item_title,
        category=p_in.category or "團服製衣",
        vendor_a=p_in.vendor_a or "",
        price_a=p_in.price_a or 0.0,
        vendor_b=p_in.vendor_b or "",
        price_b=p_in.price_b or 0.0,
        vendor_c=p_in.vendor_c or "",
        price_c=p_in.price_c or 0.0,
        selected_vendor=p_in.selected_vendor or "",
        rationale=p_in.rationale or ""
    )
    db.add(new_p)
    db.commit()
    db.refresh(new_p)
    record_audit_log(db, user.username, "新增物資比價單", target=new_p.item_title)
    return new_p
'''

if 'custom_survey_router' not in text:
    text += '\n' + r19_blocks_code
    with open('app/routers/blocks.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print('R19 routers appended to blocks.py!')

# Mount in main.py
with open('app/main.py', 'r', encoding='utf-8') as f:
    text_main = f.read()

if 'blocks.custom_survey_router' not in text_main:
    target_main = 'app.include_router(blocks.milestone_chart_router)'
    replacement_main = target_main + '''
app.include_router(blocks.custom_survey_router)
app.include_router(blocks.liturgy_router)
app.include_router(blocks.procurement_router)'''
    text_main = text_main.replace(target_main, replacement_main)
    with open('app/main.py', 'w', encoding='utf-8') as f:
        f.write(text_main)
    print('Mounted custom_survey, liturgy, procurement routers in main.py!')
