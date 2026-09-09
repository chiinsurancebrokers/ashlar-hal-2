import asyncio
from pathlib import Path

from backend.app.services.chat import chat_turn
from backend.app.services.discovery import apply_discovery_answer


def test_short_residence_answers_do_not_loop():
    assert apply_discovery_answer("Greece", {"pending_question":"residence"}) == {
        "residence_country":"Greece",
        "pending_question":None,
    }
    assert apply_discovery_answer("in greece", {"pending_question":"residence"})["residence_country"] == "Greece"


def test_short_age_and_area_answers():
    age=apply_discovery_answer("51", {"pending_question":"age"})
    assert age["age"] == 51
    assert age["pending_question"] is None

    europe=apply_discovery_answer("Europe", {"pending_question":"coverage_area"})
    assert europe["coverage_area"] == "area1"

    ww=apply_discovery_answer("Worldwide excluding USA", {"pending_question":"coverage_area"})
    assert ww["coverage_area"] == "area3"


def test_server_resets_travel_state_when_switching_to_ipmi():
    async def run():
        old={
            "journey":"travel",
            "travel_trip_type":"single",
            "travel_destination":"Greece",
            "travel_age":51,
            "travel_cover_preference":"budget",
        }
        d=await chat_turn("Hi, I'm looking for international health insurance.", old, [
            {"role":"assistant","content":"Old travel conversation"}
        ])
        return d

    d=asyncio.run(run())
    assert d["journey"] == "ipmi"
    assert d["state"]["journey"] == "ipmi"
    assert "travel_trip_type" not in d["state"]
    assert "travel_destination" not in d["state"]
    assert d["state"]["pending_question"] == "age"


def test_ipmi_greece_sequence_moves_forward():
    async def run():
        d1=await chat_turn("51", {"journey":"ipmi","pending_question":"age"}, [])
        d2=await chat_turn("Greece", d1["state"], [])
        return d1,d2

    d1,d2=asyncio.run(run())
    assert d1["state"]["age"] == 51
    assert d1["state"]["pending_question"] == "residence"
    assert d2["state"]["residence_country"] == "Greece"
    assert d2["state"]["pending_question"] == "coverage_area"


def test_frontend_moves_real_composer_and_autospeaks():
    html=(Path(__file__).resolve().parents[1]/"frontend"/"index.html").read_text(encoding="utf-8")
    assert 'id="stableComposerHost"' in html
    assert "composerHost.appendChild(composer)" in html
    assert "body.adviser-active .welcome-input-row," in html
    assert "explicitJourneyFromText" in html
    assert "startFreshJourney(requestedJourney,{announce:false})" in html
    assert "if(shouldSpeak)speakLast(true)" in html
    assert "recordingSurface=document.body.classList.contains('adviser-active')?'adviser':'welcome'" in html


def test_health_flags_show_stability_patch():
    main=(Path(__file__).resolve().parents[1]/"backend/app/main.py").read_text(encoding="utf-8")
    assert '"version":"8.5.2"' in main
    assert '"journey_switch_reset":"active"' in main
    assert '"composer_position":"sticky_bottom"' in main
    assert '"automatic_tts":"active"' in main
    assert '"guided_short_answer_parser":"active"' in main
