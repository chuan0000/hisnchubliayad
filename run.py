#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
國際佛光會新竹青年分團 - 成果展示與動態管理系統 (BLIA Hsinchu Youth CMS)
跨平台一鍵啟動執行檔 (Universal Cross-Platform Launcher: x86 / ARM / macOS / Windows / Linux)

執行方式：
    python3 run.py    (macOS / Linux / ARM)
    python run.py     (Windows)
"""

import os
import sys
import time
import platform
import threading
import webbrowser

# 設定系統編碼與路徑，確保跨平台環境正常引用
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

HOST = "0.0.0.0"
PORT = 8000
LOCAL_URL = f"http://localhost:{PORT}"
ADMIN_URL = f"http://localhost:{PORT}/admin"
DOCS_URL = f"http://localhost:{PORT}/docs"


def print_system_info():
    """輸出當前硬體架構與作業系統資訊"""
    arch = platform.machine()
    system = platform.system()
    py_ver = platform.python_version()
    print(f"🖥️  偵測系統環境：{system} ({arch}) | Python {py_ver}")


def check_and_init_db():
    """檢查並自動初始化 SQLite 資料庫與預設成果、幹部、打卡資料"""
    try:
        from app.database import Base, SessionLocal, engine
        from app.models import User
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        user_count = db.query(User).count()
        db.close()
        
        if user_count == 0:
            print("[步驟 1/3] 偵測到初次啟動，正在初始化 SQLite 資料庫與示範成果...")
            import init_db
            init_db.init_database()
            print("   ✅ 資料庫與四大宗旨示範成果建立完成！")
        else:
            print("[步驟 1/3] ✅ 資料庫已就緒。")
    except Exception as e:
        print(f"   ⚠️ 初始化資料庫檢查提示: {e}")
        try:
            import init_db
            init_db.init_database()
        except Exception:
            pass


def open_browser():
    """延遲 1.5 秒伺服器啟動後自動開啟預設瀏覽器"""
    time.sleep(1.5)
    try:
        print(f"[步驟 3/3] 🌐 正在為您自動開啟系統首頁：{LOCAL_URL}")
        webbrowser.open(LOCAL_URL)
    except Exception:
        print(f"   ⚠️ 請在瀏覽器網址列輸入開啟：{LOCAL_URL}")


def main():
    print("=" * 66)
    print("   國際佛光會新竹青年分團 - 成果展示與動態管理系統")
    print("   凝聚青年力量・實踐三好四給・四大宗旨成果評鑑")
    print("=" * 66)
    print_system_info()
    print()

    # 1. 檢查並初始化資料庫
    check_and_init_db()

    # 2. 顯示連線資訊
    print()
    print("[步驟 2/3] 🚀 正在啟動 Web 伺服器...")
    print("-" * 66)
    print(f"   🌐 前台公開首頁：{LOCAL_URL}")
    print(f"   ⚙️ 幹部管理後台：{ADMIN_URL}")
    print(f"   📑 官方 API 文件：{DOCS_URL}")
    print()
    print("   🔑 預設管理員帳號：admin  /  密碼：blia123456")
    print("   💡 同一道場區域網路內之手機，可透過 [本機IP]:8000 瀏覽與打卡")
    print("   ⛔ 欲停止伺服器，請在此終端機視窗按下 Ctrl + C")
    print("-" * 66)
    print()

    # 3. 背景執行緒延遲開啟瀏覽器
    threading.Thread(target=open_browser, daemon=True).start()

    # 4. 啟動 Uvicorn 伺服器
    try:
        import uvicorn
        uvicorn.run("app.main:app", host=HOST, port=PORT, reload=False)
    except ImportError:
        print()
        print("❌ 錯誤：尚未安裝 uvicorn！")
        print("請在終端機或命令提示字元執行安裝指令：")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 伺服器已安全停止，感謝您的使用！吉祥圓滿！")


if __name__ == "__main__":
    main()
