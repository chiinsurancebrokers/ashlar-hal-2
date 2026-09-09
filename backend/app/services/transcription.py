from __future__ import annotations

import httpx

from backend.app.core.config import get_settings

ALLOWED_AUDIO_TYPES = {
    "audio/webm",
    "audio/ogg",
    "audio/mpeg",
    "audio/mp4",
    "audio/x-m4a",
    "audio/wav",
    "audio/x-wav",
}

async def transcribe_audio(
    content: bytes,
    filename: str,
    content_type: str | None = None,
) -> dict:
    settings = get_settings()

    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured.")

    max_bytes = settings.max_audio_upload_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise ValueError(
            f"Audio file exceeds the {settings.max_audio_upload_mb} MB HAL limit."
        )

    if not content:
        raise ValueError("The recording is empty.")

    safe_type = content_type or "audio/webm"
    if safe_type.split(";")[0].lower() not in ALLOWED_AUDIO_TYPES:
        # Browsers can report variations; the OpenAI endpoint ultimately validates
        # the file too. Reject obviously non-audio uploads here.
        if not safe_type.lower().startswith("audio/"):
            raise ValueError("Unsupported audio type.")

    files = {
        "file": (filename or "hal-recording.webm", content, safe_type),
    }
    data = {
        "model": settings.openai_transcribe_model,
        # Helps preserve insurance vocabulary without forcing a language.
        "prompt": (
            "International health insurance conversation. Preserve insurer names, "
            "medical terminology, country names, ages, currencies, deductibles, "
            "policy terms, and numbers accurately. Greek and English may both occur."
        ),
    }

    async with httpx.AsyncClient(timeout=90) as client:
        response = await client.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            data=data,
            files=files,
        )
        response.raise_for_status()
        payload = response.json()

    text = str(payload.get("text", "")).strip()
    if not text:
        raise RuntimeError("The transcription service returned no text.")

    return {
        "text": text,
        "model": settings.openai_transcribe_model,
    }
