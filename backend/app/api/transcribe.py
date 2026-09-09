from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.app.services.transcription import transcribe_audio

router = APIRouter(prefix="/transcribe", tags=["transcription"])


@router.post("")
async def transcribe(file: UploadFile = File(...)):
    try:
        content = await file.read()
        result = await transcribe_audio(
            content=content,
            filename=file.filename or "hal-recording.webm",
            content_type=file.content_type,
        )
        return {
            "status": "ok",
            **result,
            "audio_persisted_by_hal": False,
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Transcription request failed: {str(exc)[:180]}",
        ) from exc
