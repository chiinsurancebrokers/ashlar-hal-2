from backend.app.services.leads import _build_message, _subject


def _payload():
    return {
        "insurance_interest":"International Health Insurance",
        "first_name":"Alex",
        "last_name":"Test",
        "email":"applicant@example.com",
        "phone":"",
        "residence_country":"Greece",
        "nationality":"Greek",
        "age":"51",
        "coverage_area":"Europe",
        "family_members":"",
        "budget":"",
        "preferred_contact":"Email",
        "message":"Please contact me.",
        "hal_applicant_state":"{}",
        "hal_conversation":"Applicant: test",
        "hal_quotes":"",
        "consent":True,
    }


def test_gmail_message_reply_to_applicant():
    msg=_build_message(_payload(),"HAL-TEST","sender@example.com","leads@example.com")
    assert msg["From"]=="sender@example.com"
    assert msg["To"]=="leads@example.com"
    assert msg["Reply-To"]=="applicant@example.com"
    assert "New HAL Lead" in msg["Subject"]


def test_subject_contains_reference():
    s=_subject("Travel Insurance","Greece","40","HAL-ABC")
    assert "HAL-ABC" in s
    assert "Travel Insurance" in s
