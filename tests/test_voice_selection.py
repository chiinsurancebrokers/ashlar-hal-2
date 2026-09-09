from types import SimpleNamespace
from backend.app.services.voice import _select_voice_id

def test_shared_voice_has_priority():
    s=SimpleNamespace(
        elevenlabs_voice_id="shared",
        elevenlabs_voice_id_en="english",
        elevenlabs_voice_id_el="greek",
    )
    assert _select_voice_id(s,"en")=="shared"
    assert _select_voice_id(s,"el")=="shared"

def test_language_voice_is_fallback_only():
    s=SimpleNamespace(
        elevenlabs_voice_id=None,
        elevenlabs_voice_id_en="english",
        elevenlabs_voice_id_el="greek",
    )
    assert _select_voice_id(s,"en")=="english"
    assert _select_voice_id(s,"el")=="greek"
