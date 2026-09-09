from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[3]
DATA_FILE = BASE_DIR / "data" / "travel" / "europesure" / "plans.json"


@lru_cache
def europesure_data() -> dict[str, Any]:
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def _money(value: int | float) -> str:
    return f"€{value:,.0f}"


def destination_scope(destination: str | None) -> str | None:
    text=(destination or "").strip().lower()
    if not text:
        return None
    usa_terms=("usa","u.s.","united states","america","ηνωμένες πολιτείες","ηνωμενες πολιτειες")
    europe_terms=(
        "europe","eu ","europa","ευρώπη","ευρωπη","european union","ευρωπαϊκή ένωση","ευρωπαικη ενωση",
        "greece","greek","italy","italian","france","french","spain","spanish","germany","german",
        "portugal","netherlands","belgium","austria","switzerland","cyprus","malta","croatia",
    )
    if any(x in text for x in usa_terms):
        return "usa"
    if any(x in text for x in europe_terms):
        return "europe"
    if any(x in text for x in ("worldwide","world wide","global","παγκόσμια","παγκοσμια")):
        return "worldwide"
    return "worldwide"


def recommend_tier(state: dict) -> dict[str, Any]:
    """Conservative deterministic tier recommendation from the legacy HAL positioning."""
    data=europesure_data()
    plans=data["plans"]
    age=state.get("travel_age") or state.get("age")
    scope=state.get("travel_destination_scope") or destination_scope(state.get("travel_destination"))
    preference=str(state.get("travel_cover_preference") or "").lower()
    explicit=str(state.get("travel_tier_preference") or "").lower()

    eligible=True
    eligibility_note=None
    if age is not None:
        try:
            if int(age) > int(data["dataset"]["max_age_legacy"]):
                eligible=False
                eligibility_note=(
                    "The uploaded legacy Europesure data states a maximum age of 79. "
                    "Current eligibility must be confirmed before proceeding."
                )
        except Exception:
            pass

    if explicit in plans:
        tier=explicit
        reason="You explicitly asked to look at this Europesure tier."
    elif preference in {"highest","maximum","premium","strongest"}:
        tier="platinum"
        reason="You prioritised the strongest legacy limits."
    elif preference in {"balanced","balance","value"}:
        tier="gold"
        reason="You prioritised a balanced level of cover, which matches the legacy positioning of Gold."
    elif preference in {"budget","basic","price","economy"} and scope=="europe":
        tier="silver"
        reason="The legacy source positions Silver as the entry-level option for short European trips and budget-conscious travellers."
    elif scope in {"worldwide","usa"}:
        tier="platinum"
        reason="The legacy source positions Platinum as the premium option for worldwide travel."
    else:
        tier="gold"
        reason="The legacy source positions Gold as the balanced, most-popular option."

    plan=dict(plans[tier])
    result={
        "provider":"Europesure",
        "tier":tier,
        "plan_name":f"Europesure {plan['name']}",
        "recommended":eligible,
        "eligible_on_legacy_data":eligible,
        "eligibility_note":eligibility_note,
        "reason":reason,
        "trip_type":state.get("travel_trip_type"),
        "destination":state.get("travel_destination"),
        "destination_scope":scope,
        "emergency_medical_eur":plan["emergency_medical_eur"],
        "cancellation_eur":plan["cancellation_eur"],
        "baggage_eur":plan["baggage_eur"],
        "positioning":plan["positioning"],
        "legacy_fit":plan["legacy_fit"],
        "common_benefits_legacy":data["dataset"]["common_benefits_legacy"],
        "optional_addons_legacy":data["dataset"]["optional_addons_legacy"],
        "portal_url":data["dataset"]["portal_url"],
        "verification_status":data["dataset"]["verification_status"],
        "current_terms_confirmed":False,
        "client_note":data["dataset"]["client_use"],
        "alternatives":[
            {
                "tier":k,
                "name":v["name"],
                "emergency_medical_eur":v["emergency_medical_eur"],
                "cancellation_eur":v["cancellation_eur"],
                "baggage_eur":v["baggage_eur"],
            }
            for k,v in plans.items()
        ],
    }
    return result


def public_catalog() -> dict[str, Any]:
    data=europesure_data()
    return {
        "provider":data["dataset"]["provider"],
        "verification_status":data["dataset"]["verification_status"],
        "current_terms_confirmed":False,
        "max_age_legacy":data["dataset"]["max_age_legacy"],
        "annual_multi_trip_from_eur_legacy":data["dataset"]["annual_multi_trip_from_eur_legacy"],
        "trip_types":data["dataset"]["trip_types"],
        "common_benefits_legacy":data["dataset"]["common_benefits_legacy"],
        "optional_addons_legacy":data["dataset"]["optional_addons_legacy"],
        "plans":[
            {
                "tier":key,
                "name":value["name"],
                "emergency_medical":_money(value["emergency_medical_eur"]),
                "cancellation":_money(value["cancellation_eur"]),
                "baggage":_money(value["baggage_eur"]),
                "positioning":value["positioning"],
                "legacy_fit":value["legacy_fit"],
            }
            for key,value in data["plans"].items()
        ],
        "client_note":data["dataset"]["client_use"],
    }
