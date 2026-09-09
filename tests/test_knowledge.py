from backend.app.knowledge.service import international_vs_local, destination, education_context, destination_context

def test_education_has_balanced_rules():
    data=international_vs_local()
    assert any("Never say international insurance is always better" in x for x in data["argumentation_rules"])
    assert len(data["principles"]) >= 6

def test_greece_destination_profile():
    gr=destination("GR")
    assert gr["country"]=="Greece"
    facts={x["id"]:x for x in gr["facts"]}
    assert facts["unmet_needs_oecd"]["value"].startswith("12.1%")
    assert facts["unmet_needs_need_population"]["value"].startswith("21.9%")
    assert "denominator_note" in facts["unmet_needs_oecd"]
    assert facts["oop"]["value"]=="34%"

def test_context_contains_sources():
    assert "APRIL International" in education_context()
    assert "OECD" in destination_context("GR")
