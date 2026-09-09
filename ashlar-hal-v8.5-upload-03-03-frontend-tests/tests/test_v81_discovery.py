from backend.app.services.discovery import apply_discovery_answer, next_discovery_question
from backend.app.services.chat import _quote_payload


def test_no_quotes_before_discovery_complete():
    state={"age":51,"residence_country":"Greece","coverage_area":"area1"}
    assert _quote_payload(state)==[]
    assert next_discovery_question(state)["key"]=="deductible"


def test_outpatient_answer_is_explicit():
    state={"pending_question":"outpatient"}
    u=apply_discovery_answer("Hospital only",state)
    assert u["outpatient_required"] is False
    assert u["outpatient_answered"] is True


def test_outpatient_yes():
    u=apply_discovery_answer("Include outpatient cover",{"pending_question":"outpatient"})
    assert u["outpatient_required"] is True


def test_maternity_question_for_age_35():
    s={"age":35,"residence_country":"Greece","coverage_area":"area1","deductible_answered":True,"outpatient_answered":True}
    assert next_discovery_question(s)["key"]=="maternity"


def test_maternity_skipped_for_age_51():
    s={"age":51,"residence_country":"Greece","coverage_area":"area1","deductible_answered":True,"outpatient_answered":True}
    assert next_discovery_question(s)["key"]=="dental"


def test_final_discovery_reaches_none():
    s={"age":51,"residence_country":"Greece","coverage_area":"area1","deductible_answered":True,"outpatient_answered":True,"maternity_answered":True,"dental_answered":True,"mental_health_answered":True,"evacuation_answered":True,"budget_answered":True}
    assert next_discovery_question(s) is None
