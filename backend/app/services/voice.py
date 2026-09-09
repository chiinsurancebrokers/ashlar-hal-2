import httpx
from backend.app.core.config import get_settings


def _select_voice_id(settings, language: str="en") -> str | None:
    # Prefer ONE shared multilingual voice when configured.
    # Language-specific IDs are only fallbacks if the shared ID is absent.
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
            "No ElevenLabs voice ID is configured. Set ELEVENLABS_VOICE_ID "
            "(recommended) or one language-specific voice ID."
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
    }

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.content
