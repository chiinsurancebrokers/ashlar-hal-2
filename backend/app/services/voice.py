import httpx
from backend.app.core.config import get_settings


def _select_voice_id(settings, language: str="en") -> str | None:
    # HAL uses one consistent multilingual male voice in both Greek and English.
    # Railway can override HAL_MALE_VOICE_ID at any time.
    if getattr(settings, "hal_male_voice_id", None):
        return settings.hal_male_voice_id
    if settings.elevenlabs_voice_id:
        return settings.elevenlabs_voice_id
    if language.lower().startswith("el"):
        return settings.elevenlabs_voice_id_el
    return settings.elevenlabs_voice_id_en


async def elevenlabs_tts(text: str, language: str = "en") -> bytes:
    settings = get_settings()
    if not settings.elevenlabs_api_key:
        raise RuntimeError("ELEVENLABS_API_KEY is not configured.")

    voice_id = _select_voice_id(settings, language)
    if not voice_id:
        raise RuntimeError(
            "No ElevenLabs voice ID is configured. Set HAL_MALE_VOICE_ID "
            "or ELEVENLABS_VOICE_ID."
        )

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": settings.elevenlabs_api_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            # Calm, confident adviser delivery rather than dramatic narration.
            "stability": 0.58,
            "similarity_boost": 0.78,
            "style": 0.12,
            "use_speaker_boost": True,
            "speed": 0.96,
        },
    }

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.content
