from backend.app.schemas.applicant import Applicant
from backend.app.rates.registry import quote_shortlist
from backend.app.services.plan_details import explain_plan


def test_morgan_tell_me_more_returns_verified_detail():
    app=Applicant(age=35,residence_country="Greece",coverage_area="area1",maternity_required=True)
    qs=quote_shortlist(app,limit=8)
    q=next(x for x in qs if x.plan_key=="morgan_price:premium")
    d=explain_plan(app,q.plan_key)
    labels={x["label"] for x in d["details"]}
    assert "Normal pregnancy and childbirth" in labels
    assert any("waiting period" in x.lower() for x in d["caveats"])
