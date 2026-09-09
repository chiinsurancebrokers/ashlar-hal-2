from backend.app.knowledge.service import destination_context, destination

def test_greece_has_private_insurance_argumentation():
    gr=destination("GR")
    ia=gr["insurance_argumentation"]
    assert ia["waiting_lists"]["priority"]=="high"
    assert any("public healthcare system" in x.lower() for x in ia["balanced_structure"])
    assert any("private health plan" in x.lower() for x in ia["balanced_structure"])

def test_greece_context_translates_evidence_to_insurance():
    ctx=destination_context("GR")
    assert "EVIDENCE → INSURANCE ARGUMENT" in ctx
    assert "WAITING LISTS — HIGH PRIORITY" in ctx
    assert "private insurance" in ctx.lower()
