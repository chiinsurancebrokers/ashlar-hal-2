from backend.app.rates.registry import quote_current
from backend.app.schemas.applicant import Applicant

def _find(quotes, insurer_contains, code):
    return [q for q in quotes if insurer_contains in q.insurer and q.product_code == code][0]

def test_mp_official_area1_age40_standard():
    q=_find(quote_current(Applicant(age=40,residence_country="Greece",coverage_area="area1")),"Morgan Price","standard")
    assert q.premium == 1490.80
    assert q.official_rate is True
    assert q.rate_version == "morgan_price_europe_2026_official"

def test_mp_official_area4_age50_elite():
    q=_find(quote_current(Applicant(age=50,residence_country="Greece",coverage_area="area4")),"Morgan Price","elite")
    assert q.premium == 19464.47

def test_area3_does_not_mix_legacy_carriers():
    qs=quote_current(Applicant(age=40,residence_country="Greece",coverage_area="area3"))
    assert qs
    assert all("Morgan Price" in q.insurer for q in qs)

def test_mp_evidence_attached():
    q=_find(quote_current(Applicant(age=40,residence_country="Greece",coverage_area="area1")),"Morgan Price","premium")
    assert q.evidence_status == "verified_2026_tob_and_policy"
    assert any("Annual limit" in f for f in q.verified_facts)

def test_non_greece_not_quoted():
    assert quote_current(Applicant(age=40,residence_country="France",coverage_area="area1")) == []


def test_mp_maternity_requirement_ranks_premium_or_elite_first():
    qs=quote_current(Applicant(age=40,residence_country="Greece",coverage_area="area1",maternity_required=True))
    assert qs[0].product_code in {"premium","elite"}
    assert qs[0].requirements_score == 1.0

def test_mp_standard_fails_dental_requirement_with_verified_evidence():
    qs=quote_current(Applicant(age=40,residence_country="Greece",coverage_area="area1",dental_required=True))
    std=_find(qs,"Morgan Price","standard")
    assert std.requirements_score == 0.0
    assert "Routine dental" in std.unmatched_requirements
