from app.database import engine, Base, SessionLocal
from app.models import SurveyCustomQuestion, VendorDirectory, PriceComparison, CadreNotice

Base.metadata.create_all(bind=engine)
db = SessionLocal()

try:
    if db.query(PriceComparison).count() == 0:
        p1 = PriceComparison(
            item_title="2026青年生活禪手冊印製 (200本)",
            category="文宣印刷",
            vendor_a="新竹光華數位印刷文創",
            price_a=7600.0,
            vendor_b="風城彩印行",
            price_b=8500.0,
            vendor_c="竹北快印輸出館",
            price_c=8200.0,
            selected_vendor="新竹光華數位印刷文創",
            rationale="全彩雪銅紙 150g，報價最優且配合法會日程準時交貨"
        )
        p2 = PriceComparison(
            item_title="青年幹部水陸法會餐盒 (80份)",
            category="餐飲外燴",
            vendor_a="竹北菩提素食工坊",
            price_a=8000.0,
            vendor_b="法喜健康素食",
            price_b=8800.0,
            vendor_c="慈心天然蔬食",
            price_c=9600.0,
            selected_vendor="竹北菩提素食工坊",
            rationale="食材新鮮，無五辛且配合熱食送達"
        )
        db.add(p1)
        db.add(p2)
        db.commit()
        print("Seeded PriceComparison!")

    if db.query(CadreNotice).count() == 0:
        n1 = CadreNotice(
            title="【常住重要】法寶寺週六水陸法會青年幹部動線確認會議",
            content="請各位幹部於本週五晚間 19:30 於 2F 青年團部集合，核對音控、知賓接待與行堂動線配置，並完成各組對講機頻率測試。",
            priority="urgent",
            publisher_name="分團長",
            target_roles="幹部/組長"
        )
        n2 = CadreNotice(
            title="【物資清點】夏令營隊物資設備歸還核銷提醒",
            content="請活動組與場務組幹部於明日下午前，將無線麥克風與活動背心全數歸還常住法寶庫房並完成線上物資核銷手續。",
            priority="normal",
            publisher_name="財務秘書",
            target_roles="活動組/場務組"
        )
        db.add(n1)
        db.add(n2)
        db.commit()
        print("Seeded CadreNotice!")

    print("All R19 seed data successfully committed!")
except Exception as e:
    db.rollback()
    print("Error seeding R19 data:", e)
finally:
    db.close()
