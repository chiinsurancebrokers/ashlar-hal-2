from pathlib import Path
HTML=Path("frontend/index.html").read_text(encoding="utf-8")

def test_policy_analyzer_not_exposed_to_applicant():
    assert "Advanced Policy Analyzer" not in HTML

def test_tell_me_more_uses_plan_endpoint():
    assert "/api/v1/plans/explain" in HTML

def test_quick_reply_ui_present():
    assert "answer-option" in HTML
