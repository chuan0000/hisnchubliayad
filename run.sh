#!/bin/bash
set -e

echo "============================================================"
echo "  國際佛光會新竹青年分團 - 動態成果管理系統 (啟動中...)"
echo "============================================================"
echo ""

# 檢查 Python
if ! command -v python3 &> /dev/null; then
    echo "[錯誤] 系統中未檢測到 python3！請先至 python.org 安裝。"
    exit 1
fi

# 建立虛擬環境
if [ ! -d "venv" ]; then
    echo "[步驟 1/3] 正在建立 Python 虛擬環境 (venv)..."
    python3 -m venv venv
fi

# 啟用虛擬環境
source venv/bin/activate

# 安裝依賴
echo "[步驟 2/3] 檢查並安裝必要套件..."
pip install -r requirements.txt

# 初始化資料庫
if [ ! -f "hsinchu_youth.db" ]; then
    echo "[步驟 3/3] 初次啟動：初始化 SQLite 資料庫與示範成果資料..."
    python3 init_db.py
else
    echo "[步驟 3/3] 資料庫檔案 hsinchu_youth.db 已存在。"
fi

echo ""
echo "============================================================"
echo "  ✅ 系統已成功啟動！"
echo "  🌐 前台展示首頁：http://localhost:8000"
echo "  ⚙️ 後台管理系統：http://localhost:8000/admin"
echo "  📑 API 文件文件：http://localhost:8000/docs"
echo "  按下 Ctrl+C 即可終止服務"
echo "============================================================"
echo ""

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload 
