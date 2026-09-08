from fastapi import APIRouter
from backend.app.schemas.applicant import Applicant

router = APIRouter(prefix="/quotes", tags=["quotes"])


@router.post("/preview")
def quote_preview(applicant: Applicant):
    # HAL 2.0 intentionally does not let an LLM invent or calculate a premium.
    # Carrier adapters will be registered here after current rates are imported.
    return {
        "applicant": applicant.model_dump(),
        "quotes": [],
        "message": "Carrier adapters are ready to be connected to versioned current-rate data.",
    }
