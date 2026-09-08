from __future__ import annotations

import json
import re
from typing import Any

import httpx

from backend.app.core.config import get_settings
from backend.app.providers.service import provider_context
from backend.app.schemas.applicant import Applicant
from backend.app.rates.registry import quote_current
from backend.app.knowledge.service import education_context, destination_context, international_vs_local, destination_sources, hnwi_context


BOOL_FIELDS = {
    "outpatient_required","maternity_required","dental_required",
    "mental_health_required","wellness_required","optical_required",
    "evacuation_required","chronic_required",
    "private_hospital_choice_required","cross_border_treatment_required",
    "home_country_treatment_required","continuity_portability_required",
    "high_annual_limit_required","private_room_required","direct_billing_required",
    "second_medical_opinion_required",
}
ALLOWED_FIELDS = {
    "age","residence_country","nationality","coverage_area","currency",
    "deductible","budget_annual","client_segment",*BOOL_FIELDS,
}

AREA_HELP = {
    "area1":"Europe",
    "area2":"Worldwide excluding USA, Singapore, Hong Kong and China",
    "area3":"Worldwide excluding USA",
    "area4":"Worldwide including USA",
}


def _extract_json(text: str) -> dict:
    text=text.strip()
    if text.startswith("```"):
        text=re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.I|re.S).strip()
    try:
        return json.loads(text)
    except Exception:
        m=re.search(r"\{.*\}", text, flags=re.S)
        if not m:
            raise
        return json.loads(m.group(0))


def _clean_updates(updates: dict[str, Any]) -> dict[str, Any]:
    clean={}
    for key,value in (updates or {}).items():
        if key not in ALLOWED_FIELDS or value is None:
            continue
        if key in BOOL_FIELDS:
            clean[key]=bool(value)
        elif key=="age":
            try:
                value=int(value)
                if 0 <= value <= 120: clean[key]=value
            except Exception: pass
        elif key in {"deductible","budget_annual"}:
            try:
                v=float(value)
                if v >= 0: clean[key]=v
            except Exception: pass
        elif key=="coverage_area":
            if value in AREA_HELP: clean[key]=value
        else:
            clean[key]=str(value)[:150]
    return clean


def _merge_state(state: dict, updates: dict) -> dict:
    merged=dict(state or {})
    merged.update(_clean_updates(updates))
    merged.setdefault("currency","EUR")
    return merged


def _complete_for_quote(state: dict) -> bool:
    return all(k in state and state[k] not in (None,"") for k in ("age","residence_country","coverage_area"))


def _fallback_reply(state: dict) -> str:
    if "age" not in state:
        return "How old is the person to be insured?"
    if "residence_country" not in state:
        return "Which country does the applicant normally reside in?"
    if "coverage_area" not in state:
        return ("Which area of cover do you need: Europe, worldwide excluding USA, "
                "or worldwide including USA?")
    return "I have enough information to calculate an indicative quotation. You can also tell me your budget and the benefits that matter most."


async def chat_turn(message: str, state: dict, history: list[dict] | None = None) -> dict:
    settings=get_settings()
    provider_needed=any(x in message.lower() for x in [
        "morgan","provider","company","insurer","εταιρ","πάροχ","ασφαλιστ"
    ])
    provider_text=""
    if provider_needed:
        provider_text=await provider_context("morgan_price", {"about","individual","group","downloads"}, char_limit=15000)

    lower=message.lower()
    education_needed=any(x in lower for x in [
        "international vs local","international or local","why international","local insurance",
        "travel insurance","ipmi","international health","global health",
        "διεθν","τοπικ","local","γιατί international","γιατι international","ταξιδιωτικ"
    ])
    destination_needed=any(x in lower for x in [
        "public hospital","public healthcare","health system","healthcare system","hospital system",
        "δημόσιο νοσοκομ","δημοσιο νοσοκομ","σύστημα υγείας","συστημα υγειας",
        "ελλάδα","ελλαδα","greece"
    ])
    edu_text=education_context() if education_needed else ""

    hnwi_needed=any(x in lower for x in [
        "hnwi","high net worth","high-net-worth","affluent","wealthy","premium client",
        "executive","business owner","entrepreneur","family office","comprehensive cover",
        "best coverage","maximum coverage","top hospitals","private hospitals",
        "ευκατάστα","ευκαταστα","εύπορ","ευπορ","πλούσι","πλουσι","επιχειρηματ",
        "πλήρη κάλυψη","πληρη καλυψη","comprehensive"
    ])
    hnwi_text=hnwi_context() if hnwi_needed else ""

    destination_code=None
    candidate=(state or {}).get("residence_country","")
    if any(x in lower for x in ["greece","ελλάδα","ελλαδα","hellas"]) or str(candidate).lower() in {"greece","gr","hellas","ελλάδα","ελλαδα"}:
        destination_code="GR"
    dest_text=destination_context(destination_code) if destination_needed and destination_code else ""

    if not settings.anthropic_api_key:
        # The application remains deterministic and usable without an LLM.
        return {
            "reply":_fallback_reply(state),
            "state":state,
            "quotes":[],
            "ai_status":"not_configured",
            "provider_sources_used":[],
            "knowledge_sources_used":[],
        }

    system=f"""
You are HAL, Ashlar Assurance's international health insurance assistant.

Your responsibilities:
1. Converse naturally in the user's language.
2. Extract applicant facts from conversation into structured updates.
3. Never calculate, estimate or invent a premium. Premiums are generated by HAL's deterministic rate engine after your turn.
4. Never invent a policy benefit, exclusion, waiting period, underwriting outcome, regulator or provider fact.
5. Provider/company facts may be stated only when supported by the OFFICIAL PROVIDER CONTEXT supplied below.
6. Morgan Price plan benefits are verified by a separate evidence engine. Do not invent details not supplied to you.
7. Do not claim a client is accepted or covered. Final acceptance is always subject to insurer underwriting/confirmation.
8. Ask only the most useful next question when information is missing.
9. When explaining INTERNATIONAL vs LOCAL insurance, be persuasive through relevant facts and trade-offs, but never use fear, disparage a public health system, or claim IPMI is always better.
10. Explicitly distinguish: public healthcare, local private health insurance, international private medical insurance (IPMI), and travel insurance.
11. Acknowledge genuine local-plan advantages such as lower cost, local-market expertise and suitability for people settled in one country.
12. Use destination health-system statistics only from DESTINATION HEALTHCARE INTELLIGENCE below, with the year/source context. Do not generalise from Europe-wide waiting-time articles to a country unless country-specific evidence is supplied.
13. If two statistics use different denominators, explain that difference rather than comparing them as if they were identical.
14. Never imply private insurance guarantees faster treatment everywhere. Explain that it may increase provider choice/access depending on network, policy and location.
15. If the user asks 'why do I need IPMI?', personalise the argument around mobility, geography, continuity, preferred providers, language/support, evacuation, financial protection and destination system access—not generic sales claims.
16. Recognise that an affluent LOCAL NATIONAL or HNWI may have a legitimate IPMI need even if they are not an expatriate. The need may be comprehensive provider choice, high limits, cross-border planned treatment, continuity, private-hospital access, direct billing or service—not merely geographic mobility.
17. Never infer HNWI status solely from a high budget; ask or infer only from explicit lifestyle/service preferences.
18. Do not say local insurance 'cannot' provide comprehensive protection as a universal claim. Say that some local plans may not combine the same international scope, portability, limits or service features, and compare actual products where available.
19. Out-of-pocket spending is not evidence that local insurers denied claims or that payers were uninsured. It is aggregate direct household healthcare spending, including co-payments and other direct payments where third-party financing does not pay the full cost.

Morgan Price coverage-area codes:
- area1: Europe
- area2: Worldwide excluding USA, Singapore, Hong Kong and China
- area3: Worldwide excluding USA
- area4: Worldwide including USA

Applicant update fields you may return:
age, residence_country, nationality, coverage_area, currency, deductible, budget_annual,
outpatient_required, maternity_required, dental_required, mental_health_required,
wellness_required, optical_required, evacuation_required, chronic_required,
client_segment, private_hospital_choice_required, cross_border_treatment_required,
home_country_treatment_required, continuity_portability_required, high_annual_limit_required,
private_room_required, direct_billing_required, second_medical_opinion_required.

Current applicant state:
{json.dumps(state or {}, ensure_ascii=False)}

OFFICIAL PROVIDER CONTEXT (may be empty if irrelevant to this message):
{provider_text}

INTERNATIONAL VS LOCAL EDUCATION CONTEXT (may be empty):
{edu_text}

DESTINATION HEALTHCARE INTELLIGENCE (may be empty):
{dest_text}

AFFLUENT / HNWI DECISION CONTEXT (may be empty):
{hnwi_text}

Return ONLY valid JSON with this exact shape:
{{
  "reply": "natural language answer/question",
  "applicant_updates": {{}},
  "provider_sources_used": ["official provider URL only if you actually used it"],
  "knowledge_sources_used": ["education or destination source URL only if you actually used it"]
}}
"""
    messages=[]
    for item in (history or [])[-8:]:
        role=item.get("role")
        content=item.get("content")
        if role in {"user","assistant"} and content:
            messages.append({"role":role,"content":str(content)[:5000]})
    messages.append({"role":"user","content":message[:8000]})

    async with httpx.AsyncClient(timeout=60) as client:
        response=await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key":settings.anthropic_api_key,
                "anthropic-version":"2023-06-01",
                "content-type":"application/json",
            },
            json={
                "model":settings.anthropic_model,
                "max_tokens":900,
                "temperature":0.2,
                "system":system,
                "messages":messages,
            },
        )
        response.raise_for_status()
        payload=response.json()

    text="".join(block.get("text","") for block in payload.get("content",[]) if block.get("type")=="text")
    parsed=_extract_json(text)
    merged=_merge_state(state, parsed.get("applicant_updates",{}))

    quotes=[]
    if _complete_for_quote(merged):
        try:
            applicant=Applicant(**merged)
            quotes=[q.model_dump() for q in quote_current(applicant)[:8]]
        except Exception:
            quotes=[]

    return {
        "reply":str(parsed.get("reply") or _fallback_reply(merged)),
        "state":merged,
        "quotes":quotes,
        "ai_status":"active",
        "provider_sources_used":[str(x) for x in parsed.get("provider_sources_used",[]) if isinstance(x,str)][:8],
        "knowledge_sources_used":[str(x) for x in parsed.get("knowledge_sources_used",[]) if isinstance(x,str)][:10],
    }
