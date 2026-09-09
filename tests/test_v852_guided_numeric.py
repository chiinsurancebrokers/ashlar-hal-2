from pathlib import Path
from backend.app.services.discovery import apply_discovery_answer, next_discovery_question


def test_deductible_choices_advance():
    for message,expected in {
        "€0 deductible":0.0,
        "€500 deductible":500.0,
        "€1000 deductible":1000.0,
        "€1,000 deductible":1000.0,
        "500 deductible":500.0,
    }.items():
        out=apply_discovery_answer(message,{"pending_question":"deductible"})
        assert out["deductible"] == expected
        assert out["deductible_answered"] is True
        assert out["pending_question"] is None


def test_exact_live_sequence_advances_to_outpatient():
    state={
        "age":51,
        "residence_country":"Greece",
        "coverage_area":"area3",
        "pending_question":"deductible",
    }
    state.update(apply_discovery_answer("€500 deductible",state))
    assert next_discovery_question(state,False)["key"] == "outpatient"


def test_budget_choices_advance():
    for message,expected in {
        "Budget €3000":3000.0,
        "Budget €5,000":5000.0,
        "€8000":8000.0,
    }.items():
        out=apply_discovery_answer(message,{"pending_question":"budget"})
        assert out["budget_annual"] == expected
        assert out["budget_answered"] is True
        assert out["pending_question"] is None


def test_flexible_values_still_work():
    d=apply_discovery_answer("No preference on deductible",{"pending_question":"deductible"})
    assert d["deductible_preference"] == "flexible"
    b=apply_discovery_answer("No fixed budget",{"pending_question":"budget"})
    assert b["budget_preference"] == "flexible"


def test_health_version_flag():
    main=(Path(__file__).resolve().parents[1]/"backend/app/main.py").read_text(encoding="utf-8")
    assert '"version":"8.5.2"' in main
    assert '"guided_numeric_reply_parser":"fixed_v8_5_2"' in main
