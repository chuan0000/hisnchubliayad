from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import UPLOAD_DIR, BASE_DIR
from app.database import engine, Base
from app.routers import auth, blocks, evidence, health, team, upload

# 建立資料庫表格結構
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="國際佛光會新竹青年分團 動態成果管理系統",
    description="專為道場與幹部本機運作打造的完全動態化 CMS 系統，涵蓋四大宗旨佐證歸檔、健康跑步打卡、Canva 簡報設計器與權限控管",
    version="1.2.0"
)

# 跨來源資源共享 (CORS) 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 掛載靜態檔案目錄
STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# 註冊 API 路由（涵蓋 100 項功能與四大進階模組）
app.include_router(auth.router)
app.include_router(blocks.router)
app.include_router(evidence.router)
app.include_router(health.router)
app.include_router(team.router)
app.include_router(upload.router)
app.include_router(upload.slides_router)
app.include_router(blocks.backup_router)
app.include_router(blocks.exam_router)
app.include_router(blocks.search_router)
app.include_router(blocks.inventory_router)
app.include_router(blocks.finance_router)
app.include_router(blocks.partner_router)
app.include_router(blocks.countdown_router)
app.include_router(blocks.faq_router)
app.include_router(blocks.audit_router)
app.include_router(blocks.budget_router)
app.include_router(blocks.roster_router)
app.include_router(blocks.announcement_router)
app.include_router(blocks.loan_router)
app.include_router(blocks.script_router)
app.include_router(blocks.poll_router)
app.include_router(blocks.study_router)
app.include_router(blocks.catering_router)
app.include_router(blocks.lamp_router)
app.include_router(blocks.film_router)
app.include_router(blocks.donation_router)
app.include_router(blocks.chanting_router)
app.include_router(blocks.export_pack_router)
app.include_router(blocks.venue_router)
app.include_router(blocks.library_router)
app.include_router(blocks.i18n_router)
app.include_router(blocks.lost_found_router)
app.include_router(blocks.carpool_router)
app.include_router(blocks.podcast_router)
app.include_router(blocks.exchange_router)
app.include_router(blocks.tea_router)
app.include_router(blocks.etiquette_router)
app.include_router(blocks.milestone_chart_router)
app.include_router(blocks.custom_survey_router)
app.include_router(blocks.liturgy_router)
app.include_router(blocks.procurement_router)
app.include_router(blocks.wisdom_router)
app.include_router(blocks.emergency_router)
app.include_router(blocks.recipe_router)
app.include_router(blocks.centenary_router)
app.include_router(blocks.wishlist_router)
app.include_router(blocks.crawler_router)

# 【功能 50】PWA Progressive Web App 漸進式網頁應用支援
@app.get("/manifest.json", include_in_schema=False)
def serve_manifest():
    return FileResponse(STATIC_DIR / "manifest.json", media_type="application/manifest+json")

@app.get("/sw.js", include_in_schema=False)
def serve_sw():
    return FileResponse(STATIC_DIR / "sw.js", media_type="application/javascript")

# 防快取標頭：確保瀏覽器永遠載入最新版頁面
NO_CACHE_HEADERS = {
    'Cache-Control': 'no-cache, no-store, must-revalidate',
    'Pragma': 'no-cache',
    'Expires': '0'
}

@app.get('/', summary='前台成果展示首頁')
def serve_frontend():
    return FileResponse(STATIC_DIR / 'index.html', headers=NO_CACHE_HEADERS)

@app.get('/admin', summary='後台 CMS 管理系統介面')
def serve_admin():
    return FileResponse(STATIC_DIR / 'admin.html', headers=NO_CACHE_HEADERS)

@app.get('/eval', summary='評審委員專用免登入審閱通道')
def serve_eval():
    return FileResponse(STATIC_DIR / 'eval.html', headers=NO_CACHE_HEADERS)

@app.get("/healthcheck", tags=["系統狀態"])
def healthcheck():
    return {
        "status": "healthy",
        "service": "BLIA Hsinchu Youth CMS",
        "database": "SQLite (Local)",
        "uploads_ready": UPLOAD_DIR.exists()
    }

if __name__ == '__main__':
    import uvicorn
    uvicorn.run('app.main:app', host='0.0.0.0', port=8000, reload=True)