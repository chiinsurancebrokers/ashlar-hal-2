from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field

from backend.app.services.voice import elevenlabs_tts

router = APIRouter(prefix="/voice", tags=["voice"])


class VoiceRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2500)
    language: str = "en"


@router.post("/tts")
async def text_to_speech(req: VoiceRequest):
    try:
        audio = await elevenlabs_tts(req.text, req.language)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="ElevenLabs request failed.") from exc
    return Response(content=audio, media_type="audio/mpeg")
