import httpx
from backend.app.core.config import get_settings


async def elevenlabs_tts(text: str, language: str = "en") -> bytes:
    settings = get_settings()
    if not settings.elevenlabs_api_key:
        raise RuntimeError("ELEVENLABS_API_KEY is not configured.")

    voice_id = (
        (settings.elevenlabs_voice_id_el or settings.elevenlabs_voice_id)
        if language.lower().startswith("el")
        else (settings.elevenlabs_voice_id_en or settings.elevenlabs_voice_id)
    )
    if not voice_id:
        raise RuntimeError("No ElevenLabs voice ID is configured. Set ELEVENLABS_VOICE_ID or a language-specific voice ID.")

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
