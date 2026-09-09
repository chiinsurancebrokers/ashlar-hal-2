from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.services.leads import send_gmail_lead

router=APIRouter(prefix="/leads",tags=["leads"])


class LeadRequest(BaseModel):
    insurance_interest: str = Field(max_length=80)
    first_name: str = Field(min_length=1,max_length=80)
    last_name: str = Field(min_length=1,max_length=80)
    email: str = Field(min_length=5,max_length=180)
    phone: str = Field(default="",max_length=60)
    residence_country: str = Field(default="",max_length=100)
    nationality: str = Field(default="",max_length=100)
    age: str = Field(default="",max_length=10)
    coverage_area: str = Field(default="",max_length=120)
    family_members: str = Field(default="",max_length=120)
    budget: str = Field(default="",max_length=80)
    preferred_contact: str = Field(default="Email",max_length=40)
    message: str = Field(default="",max_length=2500)
    hal_applicant_state: str = Field(default="",max_length=5000)
    hal_conversation: str = Field(default="",max_length=12000)
    hal_quotes: str = Field(default="",max_length=6000)
    consent: bool
    website: str = Field(default="",max_length=200)  # honeypot


@router.post("")
async def create_lead(req:LeadRequest):
    if "@" not in req.email or "." not in req.email.split("@")[-1]:
        raise HTTPException(status_code=400,detail="Please enter a valid email address.")

    if req.website.strip():
        # Return success-like response to bots but do not send anything.
        return {"status":"accepted","reference":"HAL-SPAM-FILTERED"}

    if not req.consent:
        raise HTTPException(status_code=400,detail="Consent is required before sending the enquiry.")

    try:
        result=await send_gmail_lead(req.model_dump())
        return result
    except RuntimeError as exc:
        raise HTTPException(status_code=503,detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502,detail=f"Lead delivery failed: {str(exc)[:180]}") from exc
