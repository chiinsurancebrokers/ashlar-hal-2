from backend.app.evidence.morgan_price_2026 import benefit_value
from backend.app.rates.registry import quote_current
from backend.app.schemas.applicant import Applicant

def test_tob_key_values():
    assert benefit_value("premium","normal_maternity") == "7,500"
    assert benefit_value("elite","normal_maternity") == "10,000"
    assert benefit_value("standard_plus","routine_dental") == "Not covered"
    assert benefit_value("comprehensive","routine_dental") == "750"
    assert benefit_value("standard_plus","outpatient_psychiatric") == "Full refund – max 5 visits"
    assert benefit_value("standard","outpatient_mri_ct_pet") == "Not covered"

def test_verified_matching_routine_dental():
    a=Applicant(age=40,residence_country="Greece",coverage_area="area1",dental_required=True)
    mp={q.product_code:q for q in quote_current(a) if "Morgan Price" in q.insurer}
    assert mp["standard"].requirements_score == 0.0
    assert mp["standard_plus"].requirements_score == 0.0
    assert mp["comprehensive"].requirements_score == 1.0

def test_verified_matching_routine_maternity():
    a=Applicant(age=35,residence_country="Greece",coverage_area="area1",maternity_required=True)
    mp={q.product_code:q for q in quote_current(a) if "Morgan Price" in q.insurer}
    assert mp["comprehensive"].requirements_score == 0.0
    assert mp["premium"].requirements_score == 1.0
    assert mp["elite"].requirements_score == 1.0
