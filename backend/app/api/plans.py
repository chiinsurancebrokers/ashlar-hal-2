from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.app.schemas.applicant import Applicant
from backend.app.services.plan_details import explain_plan

router=APIRouter(prefix="/plans",tags=["plans"])
class ExplainRequest(BaseModel):
    applicant_state: dict[str,Any]
    plan_key: str

@router.post("/explain")
def explain(req:ExplainRequest):
    try:
        return explain_plan(Applicant(**req.applicant_state),req.plan_key)
    except ValueError as exc:
        raise HTTPException(status_code=404,detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400,detail=f"Could not explain plan: {str(exc)[:180]}") from exc
