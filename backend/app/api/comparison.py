from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.core.config import get_settings
from backend.app.schemas.applicant import Applicant
from backend.app.services.comparison import build_comparison
from backend.app.services.leads import send_gmail_comparison

router=APIRouter(prefix="/comparison",tags=["comparison"])

class CompareRequest(BaseModel):
    applicant_state: dict[str,Any]
    selected_keys: list[str] = []

class ComparisonEmailRequest(CompareRequest):
    name: str = Field(default="",max_length=120)
    email: str = Field(min_length=5,max_length=180)
    consent: bool = True

@router.get("/config")
def config():
    return {"policy_analyzer_url":get_settings().policy_analyzer_url}

@router.post("/preview")
def preview(req:CompareRequest):
    try:
        applicant=Applicant(**req.applicant_state)
        return build_comparison(applicant,req.selected_keys)
    except Exception as exc:
        raise HTTPException(status_code=400,detail=f"Could not build comparison: {str(exc)[:180]}") from exc

@router.post("/email")
async def email_comparison(req:ComparisonEmailRequest):
    if "@" not in req.email or "." not in req.email.split("@")[-1]:
        raise HTTPException(status_code=400,detail="Please enter a valid email address.")
    if not req.consent:
        raise HTTPException(status_code=400,detail="Consent is required to send the comparison.")
    try:
        applicant=Applicant(**req.applicant_state)
        data=build_comparison(applicant,req.selected_keys)
        plans=data["plans"]
        if len(plans)<1:
            raise HTTPException(status_code=400,detail="No valid selected plans were found.")
        result=await send_gmail_comparison(req.name.strip(),req.email.strip(),plans)
        return {**result,"plans_sent":len(plans)}
    except HTTPException:
        raise
    except RuntimeError as exc:
        raise HTTPException(status_code=503,detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502,detail=f"Comparison delivery failed: {str(exc)[:180]}") from exc
