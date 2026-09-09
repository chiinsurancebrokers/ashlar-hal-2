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
from backend.app.api.knowledge import router as knowledge_router
from backend.app.api.leads import router as leads_router
from backend.app.api.comparison import router as comparison_router
from backend.app.api.plans import router as plans_router
from backend.app.api.travel import router as travel_router

settings=get_settings()
BASE_DIR=Path(__file__).resolve().parents[2]
FRONTEND_DIR=BASE_DIR/"frontend"

app=FastAPI(title=settings.app_name,version="8.5.2")
app.include_router(carriers_router,prefix=settings.api_prefix)
app.include_router(quotes_router,prefix=settings.api_prefix)
app.include_router(rates_router,prefix=settings.api_prefix)
app.include_router(voice_router,prefix=settings.api_prefix)
app.include_router(evidence_router,prefix=settings.api_prefix)
app.include_router(providers_router,prefix=settings.api_prefix)
app.include_router(chat_router,prefix=settings.api_prefix)
app.include_router(transcribe_router,prefix=settings.api_prefix)
app.include_router(knowledge_router,prefix=settings.api_prefix)
app.include_router(leads_router,prefix=settings.api_prefix)
app.include_router(comparison_router,prefix=settings.api_prefix)
app.include_router(plans_router,prefix=settings.api_prefix)
app.include_router(travel_router,prefix=settings.api_prefix)

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
        "version":"8.5.2",
        "quotation_engine":"active",
        "conversational_ai":"openai_responses_api" if settings.openai_api_key else "not_configured",
        "conversational_model":settings.openai_chat_model if settings.openai_api_key else None,
        "openai_response_storage":"disabled",
        "conversation_control":"openai_language_plus_deterministic_insurance_engine",
        "provider_knowledge":"auto_refresh",
        "speech_to_text":"configured" if settings.openai_api_key else "not_configured",
        "voice_playback":"single_player",
        "hal_voice":"male_multilingual_adviser",
        "chat_fallback":"deterministic_and_curated",
        "private_insurance_argumentation":"active",
        "ipmi_value_positioning":"pro_comprehensive_ipmi",
        "lead_routing":"ipmi_travel_local_review",
        "shortlist_ui":"provider_cards",
        "must_have_filter":"active",
        "multi_provider_shortlist":"active",
        "ultimate_ui":"active",
        "intent_first_conversation":"active",
        "adaptive_voice_ui":"active",
        "single_interface":"active",
        "microphone_toggle":"record_stop_transcribe",
        "contextual_quick_replies":"active",
        "public_policy_analyzer":"hidden",
        "quick_compare":"active",
        "guided_discovery":"active",
        "plan_explanations":"deterministic",
        "send_comparison_gmail":"active",
        "advanced_policy_analyzer":settings.policy_analyzer_url,
        "gmail_lead_delivery":"configured" if all([settings.gmail_client_id,settings.gmail_client_secret,settings.gmail_refresh_token,settings.gmail_sender_email,settings.gmail_lead_recipient]) else "not_configured",
        "insurance_education":"active",
        "europesure_travel_engine":"active",
        "europesure_data_status":"legacy_unverified_current",
        "travel_ipmi_separation":"active",
        "journey_switch_reset":"active",
        "composer_position":"sticky_bottom",
        "automatic_tts":"active",
        "guided_short_answer_parser":"active",
        "guided_numeric_reply_parser":"fixed_v8_5_2",
        "destination_intelligence":["Greece"],
        "morgan_price_rates":"official_2026",
        "morgan_price_benefits":"verified_04_26",
        "evidence_mode":"locked",
    }
