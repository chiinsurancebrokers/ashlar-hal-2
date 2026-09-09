from backend.app.schemas.applicant import Applicant
from backend.app.rates.registry import quote_shortlist, quote_exclusions
from backend.app.services.comparison import build_comparison
from backend.app.services.leads import _build_comparison_message


def test_v8_maternity_exclusions_are_explained():
    app=Applicant(age=35,residence_country="Greece",coverage_area="area1",maternity_required=True)
    excluded=quote_exclusions(app)
    names={x["product_name"] for x in excluded}
    assert "Morgan Price Standard" in names
    assert "Morgan Price Comprehensive" in names
    assert any("Routine maternity" in x["gaps"] for x in excluded)


def test_v8_shortlist_has_keys_badges_and_checks():
    app=Applicant(age=35,residence_country="Greece",coverage_area="area1",maternity_required=True)
    qs=quote_shortlist(app)
    premium=next(q for q in qs if q.product_code=="premium" and "Morgan Price" in q.insurer)
    assert premium.plan_key=="morgan_price:premium"
    assert "Routine maternity" in premium.must_have_checks
    assert any("Maternity" in x for x in premium.fit_badges)


def test_quick_comparison_selects_requested_keys():
    app=Applicant(age=51,residence_country="Greece",coverage_area="area1")
    qs=quote_shortlist(app)
    keys=[q.plan_key for q in qs[:2]]
    data=build_comparison(app,keys)
    assert len(data["plans"])==2
    assert {p["plan_key"] for p in data["plans"]}==set(keys)


def test_comparison_email_contains_plans_and_bcc():
    plans=[{"product_name":"Plan A","insurer":"Provider A","currency":"EUR","premium":1200,"monthly":100,"card_annual_limit":"1,000,000","card_why":"Fits your needs","fit_badges":["Best value"]}]
    msg=_build_comparison_message("Alex","alex@example.com",plans,"sender@example.com","broker@example.com")
    assert msg["To"]=="alex@example.com"
    assert msg["Bcc"]=="broker@example.com"
    assert "Your Ashlar" in msg["Subject"]
    assert "Plan A" in msg.as_string()
