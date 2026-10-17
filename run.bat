@echo off
chcp 65001 >nul
echo ============================================================
echo   國際佛光會新竹青年分團 - 動態成果管理系統 (啟動中...)
echo ============================================================
echo.

REM 檢查 Python 是否已安裝
python --version >nul 2>&1
if errorlevel 1 (
    echo [錯誤] 系統中未檢測到 Python！
    echo 請先安裝 Python 3.9 以上版本，並記得勾選 "Add Python to PATH"。
    pause
    exit /b
)

REM 建立虛擬環境 (若不存在)
if not exist "venv" (
    echo [步驟 1/3] 建立 Python 虛擬環境 (venv)...
    python -m venv venv
)

REM 啟動虛擬環境並安裝依賴
echo [步驟 2/3] 檢查並安裝必要套件...
call venv\Scripts\activate.bat
pip install -r requirements.txt

REM 初始化資料庫 (若資料庫不存在)
if not exist "hsinchu_youth.db" (
    echo [步驟 3/3] 初次啟動：初始化 SQLite 資料庫與示範成果資料...
    python init_db.py
) else (
    echo [步驟 3/3] 資料庫檔案 hsinchu_youth.db 已就緒。
)

echo.
echo ============================================================
echo   ✅ 系統已成功啟動！
echo   🌐 前台展示首頁：http://localhost:8000
echo   ⚙️ 後台管理系統：http://localhost:8000/admin
echo   📑 API 文件文件：http://localhost:8000/docs
echo   (如需讓同一道場 Wi-Fi 的手機查看，可輸入本機區域 IP:8000)
echo   關閉此視窗或按下 Ctrl+C 即可停止伺服器
echo ============================================================
echo.

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload 
pause
