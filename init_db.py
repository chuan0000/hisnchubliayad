import os
import sys
from datetime import datetime

from app.database import engine, Base, SessionLocal
from app.models import User, SiteBlock, EvidenceItem, TeamMember, HealthLog
from app.auth import hash_password

def init_database():
    print("=" * 60)
    print("🚀 正在初始化「國際佛光會新竹青年分團」動態成果管理資料庫...")
    print("=" * 60)

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. 建立預設使用者
        if db.query(User).count() == 0:
            print("👤 正在建立預設管理員與幹部帳號...")
            admin_user = User(
                username="admin",
                hashed_password=hash_password("blia123456"),
                full_name="分團長 / 評鑑秘書",
                role="super_admin",
                is_active=True
            )
            cadre_user = User(
                username="cadre",
                hashed_password=hash_password("blia123456"),
                full_name="活動總召幹部",
                role="cadre",
                is_active=True
            )
            db.add(admin_user)
            db.add(cadre_user)
            db.commit()
            print("   ✅ 已建立超級管理員: admin / blia123456")
            print("   ✅ 已建立活動幹部: cadre / blia123456")

        # 2. 建立全站動態區塊內容 (Site Blocks)
        if db.query(SiteBlock).count() == 0:
            print("🌐 正在初始化全站動態區塊內容（首頁標題、看板數值、簡介）...")
            blocks_data = [
                ("site_title", "網站名稱", "國際佛光會新竹青年分團", "header", "text"),
                ("site_subtitle", "副標題", "佛教青年的活力新基地・以智慧生活・用慈悲行願", "header", "text"),
                ("hero_badge", "首頁宣傳徽章", "2026 年度成果評鑑暨動態管理系統", "hero", "text"),
                ("hero_heading", "首頁主標題", "凝聚青年力量・實踐三好四給", "hero", "text"),
                ("hero_description", "首頁簡介說明", "深耕新竹在地，連結大專青年與科技新貴。秉持佛光山星雲大師四大宗旨「以文化弘揚佛法、以教育培養人才、以慈善福利社會、以共修淨化人心」，展現新竹青年的蓬勃朝氣與實踐行動。", "hero", "markdown"),
                ("hero_banner_image", "首頁頂部主視覺圖片", "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?auto=format&fit=crop&w=1600&q=80", "hero", "image_url"),
                ("announcement_enabled", "最新公告開關 (true/false)", "true", "announcement", "boolean"),
                ("announcement_text", "公告跑馬燈文字", "📢 2026 年度「VEGRUN 全民蔬食路跑」與「新竹青年生活禪」現正熱烈打卡報名中，歡迎青年朋友踴躍登錄！", "announcement", "text"),
                ("announcement_link", "公告連結按鈕", "#health", "announcement", "text"),
                ("stat_youth_members", "看板：活躍青年團員數", "86", "stats", "number"),
                ("stat_total_events", "看板：年度主辦活動場次", "34", "stats", "number"),
                ("stat_service_hours", "看板：公益服務總時數", "1280", "stats", "number"),
                ("stat_vegrun_km", "看板：蔬食健走累積里程 (KM)", "520", "stats", "number"),
                ("four_aims_intro", "四大宗旨專區前言", "依循星雲大師創會宗旨，將人間佛教落實在生活每處細節，以下為分團各項具體推動成果、評鑑指標代碼與公文檔案歸檔。", "aims", "text"),
                ("contact_temple", "輔導道場名稱", "佛光山新竹法寶寺", "contact", "text"),
                ("contact_address", "道場聯絡地址", "新竹市東區民族路 241 巷 1 號", "contact", "text"),
                ("contact_email", "公務電子郵件", "hsinchu.blia.youth@gmail.com", "contact", "text"),
                ("contact_phone", "道場聯絡電話", "03-5325566", "contact", "text"),
                ("podcast_name", "特色專案名稱", "《新竹佛光青年X竹光三參》", "podcast", "text"),
                ("podcast_description", "特色專案簡介", "專屬新竹青年的生活思辨與心靈加油站，用幽默接地氣的視角聊佛法、談職場、玩生活。", "podcast", "text"),
                ("footer_copyright", "頁腳版權宣告", "© 2026 國際佛光會中華青年總會 新竹青年分團 版權所有", "footer", "text"),
            ]
            for key, title, val, cat, vtype in blocks_data:
                db.add(SiteBlock(block_key=key, block_title=title, block_value=val, category=cat, value_type=vtype))
            db.commit()

        # 3. 建立示範四大宗旨佐證資料 (含評鑑代碼、年度、量化指標、多附件)
        if db.query(EvidenceItem).count() <= 10:
            print("📂 正在更新四大宗旨佐證庫（建立評鑑代碼、年度切換與量化指標）...")
            evidence_data = [
                # 2026 年度成果
                ("culture", "《新竹佛光青年X竹光三參》Podcast 影音企劃與錄製推廣", "2026-03-15", "2026", "A-1-2", "新竹法寶寺數位錄音室", "青年團隊自主策劃，引導在地青年將《星雲說喻》連結職場與人際溝通，累積錄製 12 集，突破萬次線上收聽。", 12000, 15, 180.0, 98, "https://images.unsplash.com/photo-1590602847861-f357a9332bbc?auto=format&fit=crop&w=800&q=80", "image", "podcast_episodes_log.jpg", '[{"name":"Podcast企劃簽呈.pdf","url":"/uploads/sample_plan.pdf","type":"pdf"}]'),
                ("culture", "人間佛教文化沙龍：青年墨寶文創設計與互動拓印展", "2026-05-04", "2026", "A-1-1", "新竹法寶寺一樓文化長廊", "結合青年文創設計，將大師法語轉化為現代手繪明信片與拓印體驗，活動期間共吸引 650 位社區民眾與大學生參訪交流。", 650, 22, 120.0, 96, "https://images.unsplash.com/photo-1455390582262-044cdead277a?auto=format&fit=crop&w=800&q=80", "image", "culture_exhibition_report.jpg", "[]"),
                ("education", "科技新貴與心靈中道：竹科青年一日生活禪修營", "2026-04-20", "2026", "B-1-1", "新竹法寶寺般若堂 / 禪堂", "針對新竹科學園區工程師與大專青年舉辦，講授正念呼吸、步行禪與壓力調適，參與學員 45 位，滿意度達 98%。", 45, 12, 96.0, 98, "https://images.unsplash.com/photo-1506126613408-eca07ce68773?auto=format&fit=crop&w=800&q=80", "image", "tech_zen_retreat_2026.jpg", "[]"),
                ("education", "新竹青年幹部領導力培訓暨教案破冰工作坊", "2026-02-18", "2026", "B-1-2", "新竹法寶寺會議室", "邀請總會講師指導青年帶領技巧、團體動力破冰遊戲與活動風險防範，全面提升幹部團隊企劃與執行力。", 28, 8, 56.0, 95, "https://images.unsplash.com/photo-1531482615713-2afd69097998?auto=format&fit=crop&w=800&q=80", "image", "cadre_leadership_training.pdf", "[]"),
                ("cultivation", "青年菩提讀書會：雙週星雲法語實踐座談共修", "2026-06-10", "2026", "C-1-2", "新竹青年分團部", "定期研讀大師著作與經典智慧，青年夥伴輪流擔任帶領人，落實佛法在生活中的反思與實踐，出席穩定且凝聚力極佳。", 35, 6, 70.0, 97, "https://images.unsplash.com/photo-1497633762265-9d179a990aa6?auto=format&fit=crop&w=800&q=80", "image", "reading_circle_notes.jpg", "[]"),
                ("cultivation", "新竹法寶寺晨鐘暮鼓青年共修暨三皈五戒願力分享", "2026-01-08", "2026", "C-1-1", "法寶寺大雄寶殿", "青年幹部自主承擔法會引禮、梵唄與行堂執事，以恭敬心體驗寺院修行生活，淨化身心靈。", 60, 16, 80.0, 99, "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=800&q=80", "image", "buddhist_cultivation_assembly.jpg", "[]"),
                ("charity", "寒冬送暖：新竹偏鄉獨居長者探訪與臘八粥結緣善行", "2026-01-15", "2026", "D-1-1", "新竹縣五峰鄉與竹東鎮", "法寶節青年動員熬煮並親送熱騰騰的臘八粥及保暖物資包至獨居長輩家中，共傳遞 300 份溫暖與星雲大師墨寶春聯。", 300, 25, 150.0, 98, "https://images.unsplash.com/photo-1593113598332-cd288d649433?auto=format&fit=crop&w=800&q=80", "image", "charity_warmth_service.jpg", "[]"),
                ("charity", "地球淨心：新竹南寮漁港海岸環保淨灘與減塑推廣", "2026-07-12", "2026", "D-1-2", "新竹南寮海岸", "落實「環保與心保」，號召青年志工 35 人清除 180 公斤海洋塑膠廢棄物，還給海洋清淨面貌。", 35, 35, 140.0, 96, "https://images.unsplash.com/photo-1618477461853-cf6ed80faba5?auto=format&fit=crop&w=800&q=80", "image", "beach_cleanup_action.jpg", "[]"),
                
                # 2025 歷史封存示範成果
                ("culture", "2025 人間音緣青年歌唱大賽新竹區初賽", "2025-10-20", "2025", "A-1-1", "新竹市文化局演藝廳", "青年用歌聲傳遞真善美，共有 220 位青年與社區觀眾到場支持，圓滿完成賽事承辦。", 220, 18, 90.0, 94, "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?auto=format&fit=crop&w=800&q=80", "image", "2025_singing_contest.jpg", "[]"),
                ("charity", "2025 歲末獨居榮民與弱勢家庭關懷送暖行動", "2025-12-14", "2025", "D-1-1", "新竹市東區榮民之家", "青年志工關懷訪視 250 位榮民長者，致贈禦寒物資與慰問禮品，傳遞三好溫暖。", 250, 20, 100.0, 97, "https://images.unsplash.com/photo-1582213782179-e0d53f98f2ca?auto=format&fit=crop&w=800&q=80", "image", "2025_veterans_service.jpg", "[]"),
            ]

            for cat, title, dt, yr, code, loc, summ, part, vol, hrs, sat, url, ftype, orig, att in evidence_data:
                db.add(EvidenceItem(
                    category=cat,
                    title=title,
                    event_date=dt,
                    year=yr,
                    evaluation_code=code,
                    location=loc,
                    summary=summ,
                    participants_count=part,
                    volunteers_count=vol,
                    service_hours=hrs,
                    satisfaction_rate=sat,
                    file_url=url,
                    file_type=ftype,
                    original_filename=orig,
                    attachments=att,
                    created_by="分團長 / 評鑑秘書",
                    is_published=True
                ))
            db.commit()

        # 4. 建立幹部團隊名冊
        if db.query(TeamMember).count() == 0:
            team_data = [
                ("林冠宇", "分團長", "第十二屆", "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=400&q=80", "以願力取代壓力，攜手新竹青年深耕在地、開創現代人間淨土！", "hsinchu.leader@blia.org", 1),
                ("陳思妤", "副團長", "第十二屆", "https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=400&q=80", "給人歡喜是最大的福報，用心陪伴每一位初入道場的新夥伴。", "vice.hsinchu@blia.org", 2),
                ("張宏睿", "執行秘書", "第十二屆", "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=400&q=80", "落實行政制度與評鑑數位化，為新竹青年分團奠定厚實基石。", "secretary.hsinchu@blia.org", 3),
                ("黃鈺婷", "財務長", "第十二屆", "https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=400&q=80", "珍惜每一分大眾善款，以嚴謹透明的財務守護活動資源運作。", "finance.hsinchu@blia.org", 4),
                ("李家豪", "活動總召", "第十二屆", "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=400&q=80", "設計有溫度、有活力的青年營隊，讓佛法在歡樂與感動中滋潤心田！", "event.hsinchu@blia.org", 5),
                ("王沛恩", "宣傳資訊組長", "第十二屆", "https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=400&q=80", "善用自媒體與新媒體視覺，把三好的美好力量散播到數位雲端。", "media.hsinchu@blia.org", 6),
            ]
            for name, pos, term, avatar, bio, contact, order in team_data:
                db.add(TeamMember(name=name, position=pos, term=term, avatar_url=avatar, bio=bio, contact=contact, sort_order=order, is_active=True))
            db.commit()

        # 5. 建立健康打卡
        if db.query(HealthLog).count() == 0:
            health_data = [
                ("林冠宇", "run", "2026-10-14", 5.2, 7200, "https://images.unsplash.com/photo-1476480862126-209bfaa8edc8?auto=format&fit=crop&w=400&q=80", "晨光十八尖山慢跑，為 VEGRUN 蔬食路跑累積里程！"),
                ("陳思妤", "walk", "2026-10-13", 3.5, 5100, "", "青草湖環湖步道健走，心存好心、步步輕安。"),
                ("李家豪", "run", "2026-10-12", 6.8, 9400, "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?auto=format&fit=crop&w=400&q=80", "頭前溪河濱公園夜跑，運動健身亦能推廣蔬食愛地球。"),
                ("王沛恩", "walk", "2026-10-11", 4.0, 5800, "", "下班後漫步新竹護城河畔，舒緩緊繃身心。"),
                ("張宏睿", "walk", "2026-10-10", 3.0, 4500, "", "法寶寺周邊步道巡禮，日行萬步健康加分。"),
            ]
            for name, atype, dt, km, steps, img, note in health_data:
                db.add(HealthLog(participant_name=name, activity_type=atype, log_date=dt, distance_km=km, steps=steps, proof_image_url=img, note=note))
            db.commit()

        print("=" * 60)
        print("✨ 新竹佛光青年分團資料庫升級完畢（已注入 5 大新功能支援示範資料）！")
        print("=" * 60)
    except Exception as e:
        db.rollback()
        print(f"❌ 初始化發生錯誤: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    init_database()
