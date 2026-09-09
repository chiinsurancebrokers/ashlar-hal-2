from types import SimpleNamespace
from backend.app.services.voice import _select_voice_id
from backend.app.core.config import Settings

def test_default_hal_voice_is_male_adam():
    s=Settings()
    assert s.hal_male_voice_id=="pNInz6obpgDQGcFmaJgB"

def test_hal_male_voice_has_priority():
    s=SimpleNamespace(
        hal_male_voice_id="male-hal",
        elevenlabs_voice_id="shared-old",
        elevenlabs_voice_id_en="english",
        elevenlabs_voice_id_el="greek",
    )
    assert _select_voice_id(s,"en")=="male-hal"
    assert _select_voice_id(s,"el")=="male-hal"

def test_shared_voice_remains_fallback():
    s=SimpleNamespace(
        hal_male_voice_id=None,
        elevenlabs_voice_id="shared-old",
        elevenlabs_voice_id_en="english",
        elevenlabs_voice_id_el="greek",
    )
    assert _select_voice_id(s,"en")=="shared-old"
