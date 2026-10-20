#!/usr/bin/env bash
set -e

echo "============================================================"
echo "  國際佛光會新竹青年分團 - 動態成果管理系統 (跨平台啟動中...)"
echo "============================================================"
echo ""

# 檢查 Python 3 命令
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    if command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        echo "[錯誤] 系統中未檢測到 Python 3！"
        echo "請先至 https://www.python.org 或透過 Homebrew (brew install python) 安裝。"
        exit 1
    fi
fi

# 顯示系統環境架構
ARCH=$(uname -m 2>/dev/null || echo "Unknown")
OS=$(uname -s 2>/dev/null || echo "Unknown")
echo "🖥️  作業系統：$OS | 硬體架構：$ARCH ($($PYTHON_CMD --version))"
echo ""

# 建立虛擬環境 (若尚未建立)
if [ ! -d "venv" ]; then
    echo "[步驟 1/3] 正在建立 Python 虛擬環境 (venv)..."
    $PYTHON_CMD -m venv venv || {
        echo "⚠️  venv 建立遇到問題，嘗試直接使用系統環境執行..."
    }
fi

# 啟用虛擬環境 (若存在)
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    PIP_CMD="pip"
    RUN_PYTHON="python"
else
    PIP_CMD="$PYTHON_CMD -m pip"
    RUN_PYTHON="$PYTHON_CMD"
fi

# 安裝依賴
echo "[步驟 2/3] 檢查並安裝必要套件 (純 Python 與跨平台二進位相容)..."
$PIP_CMD install -r requirements.txt

# 初始化資料庫
echo "[步驟 3/3] 檢查資料庫狀態..."
$RUN_PYTHON -c "
import init_db
from app.database import Base, SessionLocal, engine
from app.models import User
Base.metadata.create_all(bind=engine)
db = SessionLocal()
if db.query(User).count() == 0:
    print('   正在建立預設管理員與示範成果...')
    init_db.init_database()
else:
    print('   ✅ 資料庫已就緒。')
db.close()
"

echo ""
echo "============================================================"
echo "  ✅ 系統已成功啟動！"
echo "  🌐 前台展示首頁：http://localhost:8000"
echo "  ⚙️ 後台管理系統：http://localhost:8000/admin"
echo "  📑 API 文件文件：http://localhost:8000/docs"
echo "  (相容：x86_64、ARM64、Apple Silicon Mac、Windows 與 Linux)"
echo "  按下 Ctrl+C 即可終止服務"
echo "============================================================"
echo ""

$RUN_PYTHON -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
