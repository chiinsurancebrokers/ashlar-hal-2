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
from backend.app.api.providers import router as providers_router
from backend.app.api.chat import router as chat_router
from backend.app.api.transcribe import router as transcribe_router

settings=get_settings()
BASE_DIR=Path(__file__).resolve().parents[2]
FRONTEND_DIR=BASE_DIR/"frontend"

app=FastAPI(title=settings.app_name,version="2.0.0-v6-provider-aware")
app.include_router(carriers_router,prefix=settings.api_prefix)
app.include_router(quotes_router,prefix=settings.api_prefix)
app.include_router(rates_router,prefix=settings.api_prefix)
app.include_router(voice_router,prefix=settings.api_prefix)
app.include_router(evidence_router,prefix=settings.api_prefix)
app.include_router(providers_router,prefix=settings.api_prefix)
app.include_router(chat_router,prefix=settings.api_prefix)
app.include_router(transcribe_router,prefix=settings.api_prefix)

app.mount("/static",StaticFiles(directory=str(FRONTEND_DIR)),name="static")

@app.get("/",include_in_schema=False)
def homepage():
    return FileResponse(FRONTEND_DIR/"index.html")

@app.get("/health")
def health():
    return {
        "status":"ok",
        "service":settings.app_name,
        "environment":settings.app_env,
        "version":"2.0.0-v6-voice-input",
        "quotation_engine":"active",
        "conversational_ai":"configured" if settings.anthropic_api_key else "not_configured",
        "provider_knowledge":"auto_refresh",
        "speech_to_text":"configured" if settings.openai_api_key else "not_configured",
        "morgan_price_rates":"official_2026",
        "morgan_price_benefits":"verified_04_26",
        "evidence_mode":"locked",
    }
