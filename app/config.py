import os
import sqlite3
import tempfile
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Database auto-detection:
# 在標準本機環境 (Windows/macOS/Linux，包含 x86 與 ARM 架構) 自動使用專案根目錄下的 hsinchu_youth.db
# 在部分檔案鎖定受限環境自動無縫相容系統暫存目錄 (跨平台 tempfile 相容)
local_db_path = BASE_DIR / "hsinchu_youth.db"
auto_db_url = f"sqlite:///{local_db_path}"

try:
    _test_conn = sqlite3.connect(str(local_db_path))
    _test_conn.execute("CREATE TABLE IF NOT EXISTS _test_lock (id int);")
    _test_conn.close()
except Exception:
    fallback_db = Path(tempfile.gettempdir()) / "hsinchu_youth.db"
    auto_db_url = f"sqlite:///{fallback_db}"

DATABASE_URL = os.getenv("DATABASE_URL", auto_db_url)

# Security & JWT
SECRET_KEY = os.getenv("SECRET_KEY", "blia-hsinchu-youth-secret-key-2026-buddhas-light-pure-land")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Upload limitations
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".pdf", ".mp4", ".mov", ".doc", ".docx"}
MAX_FILE_SIZE_MB = 50
