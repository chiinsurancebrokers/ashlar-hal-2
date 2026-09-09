from pathlib import Path

from backend.app.travel.discovery import (
    apply_travel_updates,
    deterministic_travel_updates,
    long_term_mismatch,
    next_travel_question,
    travel_progress,
)
from backend.app.travel.europesure import public_catalog, recommend_tier


def test_legacy_catalog_matches_uploaded_hal_source():
    c=public_catalog()
    by={x["tier"]:x for x in c["plans"]}
    assert c["verification_status"]=="legacy_unverified_current"
    assert c["current_terms_confirmed"] is False
    assert c["max_age_legacy"]==79
    assert by["silver"]["emergency_medical"]=="€1,000,000"
    assert by["silver"]["cancellation"]=="€1,500"
    assert by["silver"]["baggage"]=="€750"
    assert by["gold"]["emergency_medical"]=="€3,500,000"
    assert by["gold"]["cancellation"]=="€3,000"
    assert by["gold"]["baggage"]=="€5,000"
    assert by["platinum"]["emergency_medical"]=="€10,000,000"
    assert by["platinum"]["cancellation"]=="€10,000"
    assert by["platinum"]["baggage"]=="€7,500"


def test_worldwide_defaults_to_platinum():
    r=recommend_tier({
        "travel_trip_type":"single",
        "travel_destination":"Japan",
        "travel_destination_scope":"worldwide",
        "travel_age":51,
        "travel_cover_preference":"balanced",
    })
    # Explicit balanced preference wins over geographic positioning.
    assert r["tier"]=="gold"

    r2=recommend_tier({
        "travel_trip_type":"single",
        "travel_destination":"Japan",
        "travel_destination_scope":"worldwide",
        "travel_age":51,
    })
    assert r2["tier"]=="platinum"


def test_budget_europe_maps_to_silver():
    r=recommend_tier({
        "travel_destination":"Italy",
        "travel_destination_scope":"europe",
        "travel_age":40,
        "travel_cover_preference":"budget",
    })
    assert r["tier"]=="silver"


def test_age_over_79_is_not_presented_as_eligible():
    r=recommend_tier({
        "travel_destination":"France",
        "travel_destination_scope":"europe",
        "travel_age":80,
        "travel_cover_preference":"balanced",
    })
    assert r["eligible_on_legacy_data"] is False
    assert r["recommended"] is False


def test_travel_discovery_sequence_is_separate():
    s={"journey":"travel"}
    q=next_travel_question(s,False)
    assert q["key"]=="travel_trip_type"
    s=apply_travel_updates(s,{"travel_trip_type":"single"})
    assert next_travel_question(s,False)["key"]=="travel_destination"
    s=apply_travel_updates(s,{"travel_destination":"Japan","travel_destination_scope":"worldwide"})
    assert next_travel_question(s,False)["key"]=="travel_age"
    s=apply_travel_updates(s,{"travel_age":50,"age":50})
    assert next_travel_question(s,False)["key"]=="travel_cover_preference"
    s=apply_travel_updates(s,{"travel_cover_preference":"balanced"})
    assert next_travel_question(s,False) is None
    assert travel_progress(s)["complete"] is True


def test_free_form_travel_extraction():
    u=deterministic_travel_updates(
        "We are a family of 4 travelling to Japan for 18 days. I am 51 and want annual multi-trip cover.",
        {"journey":"travel"},
    )
    assert u["travel_trip_type"]=="annual"
    assert u["travel_age"]==51
    assert u["travel_duration_days"]==18
    assert u["travel_travellers"]==4
    assert "Japan" in u["travel_destination"]


def test_long_term_product_fit_guard():
    assert long_term_mismatch("I am relocating to Singapore for work",{"journey":"travel"})
    assert long_term_mismatch("",{"journey":"travel","travel_duration_days":200})


def test_frontend_contains_travel_card_and_exact_quote_cta():
    html=(Path(__file__).resolve().parents[1]/"frontend"/"index.html").read_text(encoding="utf-8")
    assert "function renderTravelResult" in html
    assert "Get exact Europesure quote" in html
    assert "/api/v1/travel/europesure/recommend" in html


def test_health_advertises_travel_engine():
    main=(Path(__file__).resolve().parents[1]/"backend/app/main.py").read_text(encoding="utf-8")
    assert '"version":"8.5.2"' in main
    assert '"europesure_travel_engine":"active"' in main
    assert '"europesure_data_status":"legacy_unverified_current"' in main
