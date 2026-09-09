import pytest

from backend.app.services.chat import _deterministic_updates, _intent_flags, chat_turn


def test_residence_greece_does_not_trigger_destination_intelligence():
    flags=_intent_flags(
        "Hi HAL, my name is Chris, I'm 51, I live in Greece, and I'm looking for international health insurance.",
        {}
    )
    assert flags["destination"] is False


def test_explicit_greece_healthcare_question_triggers_destination_intelligence():
    flags=_intent_flags("How is the healthcare system in Greece?",{})
    assert flags["destination"] is True


def test_name_age_and_residence_are_extracted():
    u=_deterministic_updates(
        "Hi HAL, my name is Chris, I'm 51, I live in Greece, and I'm looking for international health insurance.",
        {},
        []
    )
    assert u["first_name"]=="Chris"
    assert u["age"]==51
    assert u["residence_country"]=="Greece"


@pytest.mark.asyncio
async def test_first_ipmi_turn_is_warm_and_guided_not_country_profile():
    result=await chat_turn(
        "Hi HAL, my name is Chris, I'm 51, I live in Greece, and I'm looking for international health insurance.",
        {},
        []
    )
    reply=result["reply"].lower()
    assert "hi chris" in reply
    assert "nice to meet you" in reply
    assert "27%" not in reply
    assert "12.1%" not in reply
    assert "oecd" not in reply
    assert result["ai_status"]=="guided_discovery"
    # Age and residence are already known, so the next question should move forward.
    assert result["state"]["pending_question"]=="coverage_area"
