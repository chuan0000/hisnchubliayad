@echo off
chcp 65001 >nul
echo ============================================================
echo   國際佛光會新竹青年分團 - 動態成果管理系統 (啟動中...)
echo ============================================================
echo.

REM 檢查 Python 命令 (優先 python，備援 py)
set PYTHON_CMD=python
python --version >nul 2>&1
if errorlevel 1 (
    py -3 --version >nul 2>&1
    if errorlevel 1 (
        echo [錯誤] 系統中未檢測到 Python 3！
        echo 請先安裝 Python 3.9 以上版本，並記得勾選 "Add Python to PATH"。
        echo 下載網址：https://www.python.org/downloads/
        pause
        exit /b
    ) else (
        set PYTHON_CMD=py -3
    )
)

echo [系統資訊] 正在使用 %PYTHON_CMD% 執行...
echo.

REM 建立虛擬環境 (若不存在)
if not exist "venv" (
    echo [步驟 1/3] 建立 Python 虛擬環境 (venv)...
    %PYTHON_CMD% -m venv venv
)

REM 啟動虛擬環境並安裝依賴
echo [步驟 2/3] 檢查並安裝必要套件 (跨平台相容)...
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    set RUN_PY=python
    pip install -r requirements.txt
) else (
    set RUN_PY=%PYTHON_CMD%
    %PYTHON_CMD% -m pip install -r requirements.txt
)

REM 檢查並初始化資料庫
echo [步驟 3/3] 檢查 SQLite 資料庫狀態...
%RUN_PY% -c "import init_db; from app.database import Base, SessionLocal, engine; from app.models import User; Base.metadata.create_all(bind=engine); db = SessionLocal(); user_count = db.query(User).count(); db.close(); sys_exit = 0 if user_count > 0 else 1; import sys; sys.exit(sys_exit)"
if errorlevel 1 (
    echo    初次啟動：正在初始化資料庫與示範成果資料...
    %RUN_PY% init_db.py
) else (
    echo    資料庫已就緒。
)

echo.
echo ============================================================
echo   ✅ 系統已成功啟動！
echo   🌐 前台展示首頁：http://localhost:8000
echo   ⚙️ 後台管理系統：http://localhost:8000/admin
echo   📑 API 文件文件：http://localhost:8000/docs
echo   (支援架構：x86_64、ARM64、Windows、macOS、Linux)
echo   關閉此視窗或按下 Ctrl+C 即可停止伺服器
echo ============================================================
echo.

%RUN_PY% -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pause
