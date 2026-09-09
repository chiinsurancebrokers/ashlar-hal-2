from backend.app.services.chat import (
    _extract_json,
    _deterministic_updates,
    _greece_direct_answer,
    _provider_direct_answer,
)

def test_plain_text_response_does_not_crash_parser():
    parsed=_extract_json("This is a normal answer.")
    assert parsed["reply"]=="This is a normal answer."

def test_empty_response_does_not_crash_parser():
    parsed=_extract_json("")
    assert parsed["reply"]==""

def test_bare_age_is_extracted_without_llm():
    updates=_deterministic_updates("51",{},[])
    assert updates["age"]==51

def test_outpatient_and_mental_health_are_extracted():
    updates=_deterministic_updates(
        "I need strong outpatient and mental health cover.",{},[]
    )
    assert updates["outpatient_required"] is True
    assert updates["mental_health_required"] is True

def test_greece_direct_answer_contains_real_data():
    reply,sources=_greece_direct_answer(False)
    assert "27%" in reply
    assert "12.1%" in reply
    assert len(sources)>=1

def test_morgan_price_direct_answer_not_ellipsis():
    reply,sources=_provider_direct_answer(False)
    assert reply.strip() not in {"...","…",""}
    assert any("morgan-price.eu/about-us" in s for s in sources)
