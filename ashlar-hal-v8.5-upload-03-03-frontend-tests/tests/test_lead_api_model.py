from backend.app.api.leads import LeadRequest

def test_lead_request_model():
    r=LeadRequest(
        insurance_interest="International Health Insurance",
        first_name="Test",
        last_name="Applicant",
        email="test@example.com",
        consent=True,
    )
    assert r.email=="test@example.com"
    assert r.consent is True
