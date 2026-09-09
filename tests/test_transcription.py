import pytest
from backend.app.services.transcription import ALLOWED_AUDIO_TYPES

def test_common_browser_audio_types_are_allowed():
    assert "audio/webm" in ALLOWED_AUDIO_TYPES
    assert "audio/ogg" in ALLOWED_AUDIO_TYPES
    assert "audio/mp4" in ALLOWED_AUDIO_TYPES

def test_non_audio_not_allowed():
    assert "text/plain" not in ALLOWED_AUDIO_TYPES
