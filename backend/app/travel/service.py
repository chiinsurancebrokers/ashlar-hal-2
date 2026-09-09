from __future__ import annotations

import json
from typing import Any

from backend.app.core.config import get_settings
from backend.app.services.openai_adviser import openai_adviser_response
from backend.app.travel.discovery import (
    apply_travel_updates,
    deterministic_travel_updates,
    long_term_mismatch,
    next_travel_question,
    travel_progress,
)
from backend.app.travel.europesure import recommend_tier


ALLOWED_OPENAI_TRAVEL_KEYS={
    "travel_trip_type","travel_destination","travel_age","age","travel_cover_preference",
    "travel_tier_preference","travel_travellers","travel_duration_days",
    "travel_winter_sports","travel_business_cover","travel_gadget_cover",
    "travel_covid_extension","travel_car_hire_excess",
}


def _is_greek(text: str) -> bool:
    import re
    return bool(re.search(r"[\u0370-\u03ff]", text or ""))


def _extract_json(text: str) -> dict:
    raw=(text or "").strip()
    try:
        parsed=json.loads(raw)
        return parsed if isinstance(parsed,dict) else {}
    except Exception:
        pass
    import re
    m=re.search(r"\{.*\}",raw,flags=re.S)
    if m:
        try:
            parsed=json.loads(m.group(0))
            return parsed if isinstance(parsed,dict) else {}
        except Exception:
            pass
    return {}


def _clean_openai_updates(updates: dict) -> dict:
    clean={}
    for key,value in (updates or {}).items():
        if key not in ALLOWED_OPENAI_TRAVEL_KEYS or value is None:
            continue
        if key in {"travel_winter_sports","travel_business_cover","travel_gadget_cover","travel_covid_extension","travel_car_hire_excess"}:
            clean[key]=bool(value)
        elif key in {"travel_age","age","travel_travellers","travel_duration_days"}:
            try:
                n=int(value)
                if 0<=n<=10000:
                    clean[key]=n
            except Exception:
                pass
        elif key=="travel_trip_type" and str(value).lower() in {"single","annual"}:
            clean[key]=str(value).lower()
        elif key=="travel_cover_preference" and str(value).lower() in {"budget","balanced","highest"}:
            clean[key]=str(value).lower()
        elif key=="travel_tier_preference" and str(value).lower() in {"silver","gold","platinum"}:
            clean[key]=str(value).lower()
        else:
            clean[key]=str(value)[:120]
    return clean


async def _openai_travel_intake(message: str, state: dict, history: list[dict] | None, greek: bool) -> dict:
    settings=get_settings()
    if not settings.openai_api_key:
        return {"acknowledgement":"","updates":{}}

    instructions=f"""
You are HAL's travel-insurance applicant understanding layer for Ashlar Assurance.
The quoted travel product family in this journey is Europesure.

Return JSON only:
{{
  "acknowledgement":"one short natural acknowledgement, never a question",
  "updates":{{}}
}}

Language: {"Greek" if greek else "English"}.

Extract only facts explicitly stated or clearly confirmed by the applicant.
Do not invent a destination, age, dates, benefits, price, eligibility or recommendation.
Do not choose the next question; HAL's deterministic travel discovery engine does that.

Allowed updates:
- travel_trip_type: single | annual
- travel_destination: free text destination actually stated
- travel_age: integer age of the oldest traveller when stated
- age: same integer when appropriate
- travel_cover_preference: budget | balanced | highest
- travel_tier_preference: silver | gold | platinum only if explicitly requested
- travel_travellers: integer
- travel_duration_days: integer only if duration is clear
- travel_winter_sports, travel_business_cover, travel_gadget_cover,
  travel_covid_extension, travel_car_hire_excess: true only when explicitly requested

Current travel state:
{json.dumps(state,ensure_ascii=False)}
"""
    try:
        raw=await openai_adviser_response(
            instructions=instructions,
            message=message,
            history=history,
            json_mode=True,
            max_output_tokens=500,
        )
        parsed=_extract_json(raw)
        return {
            "acknowledgement":str(parsed.get("acknowledgement") or "").strip(),
            "updates":_clean_openai_updates(parsed.get("updates") or {}),
        }
    except Exception:
        return {"acknowledgement":"","updates":{}}


def _summary_ack(state: dict, greek: bool) -> str:
    bits=[]
    if state.get("travel_trip_type"):
        bits.append("ετήσια πολλαπλά ταξίδια" if greek and state["travel_trip_type"]=="annual" else
                    "ένα ταξίδι" if greek else
                    "annual multi-trip cover" if state["travel_trip_type"]=="annual" else "single-trip cover")
    if state.get("travel_destination"):
        bits.append(str(state["travel_destination"]))
    if state.get("travel_age") is not None:
        bits.append(("ηλικία " if greek else "age ")+str(state["travel_age"]))
    if not bits:
        return ""
    return ("Έχω σημειώσει: " if greek else "I’ve noted: ")+", ".join(bits)+". "


def _recommendation_reply(result: dict, greek: bool) -> str:
    if not result.get("eligible_on_legacy_data"):
        return (
            "Με βάση τα legacy στοιχεία που έχουν φορτωθεί στον HAL, η Europesure είχε ανώτατη ηλικία τα 79. "
            "Δεν θα σας προτείνω πρόγραμμα ως επιλέξιμο χωρίς επιβεβαίωση των σημερινών όρων."
            if greek else
            "Based on the legacy Europesure data loaded into HAL, the maximum age was 79. "
            "I won’t present a plan as eligible until the current terms are confirmed."
        )
    name=result["plan_name"]
    if greek:
        return (
            f"Με βάση όσα μου είπατε, θα ξεκινούσα από το {name}. {result['reason']} "
            "Τα στοιχεία παροχών είναι από το legacy HAL dataset, οπότε η τελική τρέχουσα κάλυψη και τιμή πρέπει να επιβεβαιωθούν στο Europesure portal."
        )
    return (
        f"Based on what you’ve told me, I’d start with {name}. {result['reason']} "
        "The benefit figures come from HAL’s legacy Europesure dataset, so current cover and price must be confirmed in the Europesure portal."
    )


async def travel_turn(message: str, state: dict, history: list[dict] | None=None) -> dict[str,Any]:
    greek=_is_greek(message)
    merged=apply_travel_updates(state,deterministic_travel_updates(message,state))
    ai=await _openai_travel_intake(message,merged,history,greek)
    merged=apply_travel_updates(merged,ai["updates"])

    mismatch=long_term_mismatch(message,merged)
    if mismatch and not merged.get("travel_long_term_warning_shown"):
        merged["travel_long_term_warning_shown"]=True
        q=next_travel_question(merged,greek)
        if q:
            merged["travel_pending_question"]=q["key"]
        warning=(
            "Αυτό ακούγεται περισσότερο σαν μακροχρόνια διαμονή/εργασία στο εξωτερικό παρά σαν προσωρινό ταξίδι. "
            "Σε αυτή την περίπτωση το International Health Insurance πιθανότατα ταιριάζει καλύτερα· μπορούμε όμως να συνεχίσουμε στο Travel αν αυτό θέλετε."
            if greek else
            "That sounds more like long-term living or working abroad than a temporary trip. "
            "International Health Insurance is probably the better fit, although we can continue with Travel if that is what you want."
        )
        if q:
            warning+=" "+q["reply"]
        return {
            "reply":warning,
            "state":merged,
            "quotes":[],
            "excluded_plans":[],
            "travel_result":None,
            "ai_status":"travel_product_fit_warning",
            "provider_sources_used":[],
            "knowledge_sources_used":[],
            "journey":"travel",
            "lead_cta":{"show":False,"journey":"travel","label":"Request a travel insurance proposal"},
            "open_application_form":False,
            "quick_replies":q["quick_replies"] if q else [],
            "travel_discovery":travel_progress(merged),
        }

    q=next_travel_question(merged,greek)
    if q:
        merged["travel_pending_question"]=q["key"]
        merged["travel_discovery_complete"]=False
        ack=ai["acknowledgement"] or _summary_ack(merged,greek)
        reply=((ack.rstrip()+" "+q["reply"]) if ack else q["reply"]).strip()
        return {
            "reply":reply,
            "state":merged,
            "quotes":[],
            "excluded_plans":[],
            "travel_result":None,
            "ai_status":"openai_travel_discovery" if ai["acknowledgement"] else "deterministic_travel_discovery",
            "provider_sources_used":[],
            "knowledge_sources_used":[],
            "journey":"travel",
            "lead_cta":{"show":False,"journey":"travel","label":"Request a travel insurance proposal"},
            "open_application_form":False,
            "quick_replies":q["quick_replies"],
            "travel_discovery":travel_progress(merged),
        }

    merged["travel_pending_question"]=None
    merged["travel_discovery_complete"]=True
    result=recommend_tier(merged)
    return {
        "reply":_recommendation_reply(result,greek),
        "state":merged,
        "quotes":[],
        "excluded_plans":[],
        "travel_result":result,
        "ai_status":"europesure_deterministic_match",
        "provider_sources_used":[],
        "knowledge_sources_used":[],
        "journey":"travel",
        "lead_cta":{"show":True,"journey":"travel","label":"Request broker help"},
        "open_application_form":False,
        "quick_replies":[],
        "travel_discovery":travel_progress(merged),
    }
