from backend.app.knowledge.service import ipmi_value_proposition, ipmi_value_context
from backend.app.services.chat import _education_direct_answer, _hnwi_direct_answer

def test_outpatient_priority():
    data=ipmi_value_proposition()
    assert any(x["id"]=="outpatient_choice" for x in data["pillars"])
    assert "outpatient" in ipmi_value_context().lower()

def test_physician_fee_gap():
    data=ipmi_value_proposition()
    p=next(x for x in data["pillars"] if x["id"]=="inpatient_fee_design")
    assert "fee schedules" in p["argument"].lower()
    assert "balance" in p["sales_translation"].lower()

def test_vitamins_are_guarded():
    assert "never promise routine vitamins" in ipmi_value_context().lower()

def test_morgan_examples():
    text=" ".join(ipmi_value_proposition()["morgan_price_2026_verified_examples"]["examples"]).lower()
    for term in ["full refund","mri/ct/pet","outpatient psychiatric","normal maternity","rehabilitation","evacuation"]:
        assert term in text

def test_direct_answer_pro_ipmi():
    reply,_=_education_direct_answer(False)
    assert "stronger solution" in reply.lower()
    assert "outpatient" in reply.lower()
    assert "fee schedules" in reply.lower()

def test_hnwi_premium_solution():
    reply,_=_hnwi_direct_answer(False)
    assert "premium solution" in reply.lower()
