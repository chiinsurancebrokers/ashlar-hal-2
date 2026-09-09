from backend.app.services.leads import classify_journey, lead_intent, journey_cta

def test_travel_route():
    assert classify_journey("I need travel insurance for a 10 day trip",{})=="travel"

def test_local_route():
    assert classify_journey("I want local insurance in Greece",{})=="local_review"

def test_ipmi_route():
    assert classify_journey("I need international health insurance worldwide",{})=="ipmi"

def test_hnwi_state_routes_to_ipmi():
    assert classify_journey("",{"client_segment":"hnwi"})=="ipmi"

def test_lead_intent():
    assert lead_intent("Please send me a quote")
    assert lead_intent("Θέλω προσφορά")

def test_cta_labels():
    assert "travel" in journey_cta("travel",True)["label"].lower()
    assert journey_cta("local_review",True)["show"] is True
