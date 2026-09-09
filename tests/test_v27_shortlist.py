from backend.app.schemas.applicant import Applicant
from backend.app.rates.registry import quote_current, quote_shortlist

def test_internal_quote_current_remains_complete():
    app=Applicant(age=35,residence_country="Greece",coverage_area="area1",maternity_required=True)
    codes={q.product_code for q in quote_current(app) if "Morgan Price" in q.insurer}
    assert "standard" in codes
    assert "comprehensive" in codes
    assert "premium" in codes

def test_client_shortlist_hard_filters_verified_maternity_gaps():
    app=Applicant(age=35,residence_country="Greece",coverage_area="area1",maternity_required=True)
    codes={q.product_code for q in quote_shortlist(app) if "Morgan Price" in q.insurer}
    assert "standard" not in codes
    assert "standard_plus" not in codes
    assert "comprehensive" not in codes
    assert "premium" in codes
    assert "elite" in codes

def test_area1_shortlist_is_multi_provider():
    app=Applicant(age=51,residence_country="Greece",coverage_area="area1")
    insurers={q.insurer for q in quote_shortlist(app)}
    assert any("Morgan Price" in x for x in insurers)
    assert any("APRIL" in x for x in insurers)
    assert any("IMG" in x for x in insurers)

def test_cards_have_client_metadata():
    app=Applicant(age=51,residence_country="Greece",coverage_area="area1")
    qs=quote_shortlist(app)
    assert qs
    assert all(q.card_badge for q in qs)
    assert all(q.card_coverage for q in qs)

def test_first_shortlist_card_is_recommended():
    app=Applicant(age=51,residence_country="Greece",coverage_area="area1")
    qs=quote_shortlist(app)
    assert qs[0].recommended is True
    assert qs[0].recommendation_rank==1
