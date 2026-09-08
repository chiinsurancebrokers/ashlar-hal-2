from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from backend.app.core.config import get_settings
from backend.app.api.carriers import router as carriers_router
from backend.app.api.quotes import router as quotes_router
from backend.app.api.rates import router as rates_router
from backend.app.api.voice import router as voice_router
from backend.app.api.evidence import router as evidence_router

settings=get_settings()
BASE_DIR=Path(__file__).resolve().parents[2]
FRONTEND_DIR=BASE_DIR/"frontend"
app=FastAPI(title=settings.app_name,version="2.0.0-v4-mp2026")
app.include_router(carriers_router,prefix=settings.api_prefix)
app.include_router(quotes_router,prefix=settings.api_prefix)
app.include_router(rates_router,prefix=settings.api_prefix)
app.include_router(voice_router,prefix=settings.api_prefix)
app.include_router(evidence_router,prefix=settings.api_prefix)
app.mount("/static",StaticFiles(directory=str(FRONTEND_DIR)),name="static")

@app.get("/",include_in_schema=False)
def homepage(): return FileResponse(FRONTEND_DIR/"index.html")

@app.get("/health")
def health():
    return {"status":"ok","service":settings.app_name,"environment":settings.app_env,"version":"2.0.0-v4-mp2026","quotation_engine":"active","morgan_price_rates":"official_2026","evidence_mode":"locked"}
