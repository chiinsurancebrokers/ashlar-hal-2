from fastapi import APIRouter
from backend.app.schemas.applicant import Applicant
from backend.app.rates.registry import quote_current, quote_shortlist

router=APIRouter(prefix="/quotes",tags=["quotes"])

@router.post("/preview")
def quote_preview(applicant:Applicant):
    quotes=quote_current(applicant)
    shortlist=quote_shortlist(applicant,limit=5)
    if applicant.residence_country.strip().lower() not in {"greece","gr","hellas","ελλάδα","ellada"}:
        return {"applicant":applicant.model_dump(),"quotes":[],"status":"rate_unavailable","message":"The currently loaded rate datasets are configured for Greece-based applicants.","evidence_mode":"locked"}
    has_req=any([applicant.outpatient_required, applicant.maternity_required, applicant.dental_required, applicant.mental_health_required, applicant.wellness_required, applicant.optical_required, applicant.evacuation_required, applicant.chronic_required])
    recommendation=None
    if has_req:
        recommendation=next((q.model_dump() for q in quotes if q.requirements_score==1.0 and q.evidence_confidence==1.0),None)
    return {
        "applicant":applicant.model_dump(),"quotes":[q.model_dump() for q in quotes],"shortlist":[q.model_dump() for q in shortlist],"status":"ok",
        "message":"Morgan Price uses the official 2026 workbook; other carriers remain on labelled legacy datasets until replaced.",
        "evidence_mode":"locked","verified_recommendation":recommendation
    }
