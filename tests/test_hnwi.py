from backend.app.knowledge.service import hnwi_ipmi, hnwi_context, destination

def test_hnwi_local_national_is_supported():
    data=hnwi_ipmi()
    assert any("local national" in x["argument"].lower() for x in data["core_value_dimensions"])

def test_hnwi_has_fairness_boundary():
    data=hnwi_ipmi()
    assert any("local plan can never" in x.lower() for x in data["what_not_to_say"])

def test_greece_oop_is_not_claim_denial_metric():
    gr=destination("GR")
    oop=gr["oop_interpretation"]
    assert any("insurer" in x.lower() and "claim" in x.lower() for x in oop["not_proven_by_metric"])
    assert oop["greece_2023_oop_distribution"]["inpatient_care"]=="34%"
