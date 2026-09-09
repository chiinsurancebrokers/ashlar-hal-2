from __future__ import annotations
from backend.app.schemas.applicant import Applicant
from backend.app.rates.registry import quote_shortlist
from backend.app.evidence.morgan_price_2026 import benefits_for_plan

DISPLAY_CODES=[
    "overall_maximum","hospital_accommodation","surgeons_fees","cancer_treatment",
    "outpatient_services_combined","outpatient_mri_ct_pet","outpatient_physiotherapy",
    "outpatient_psychiatric","routine_dental","normal_maternity","inpatient_rehabilitation",
    "medical_evacuation_transport","complementary_therapies","wellness_screening",
]

def _money(v,c):
    return f"{c} {float(v):,.2f}" if v is not None else "—"

def explain_plan(applicant: Applicant, plan_key: str) -> dict:
    quotes=quote_shortlist(applicant,limit=8)
    q=next((x for x in quotes if x.plan_key==plan_key),None)
    if q is None:
        raise ValueError("Selected plan is not in the current shortlist.")
    details=[]
    caveats=[]
    if plan_key.startswith("morgan_price:"):
        by_code={b["benefit_code"]:b for b in benefits_for_plan(q.product_code)}
        for code in DISPLAY_CODES:
            b=by_code.get(code)
            if not b: continue
            value=b.get("value") or "—"
            details.append({"label":b.get("label"),"value":value})
            if b.get("waiting_period") and not str(value).lower().startswith("not covered"):
                caveats.append(f'{b.get("label")}: waiting period {b.get("waiting_period")}')
            if b.get("coinsurance") and not str(value).lower().startswith("not covered"):
                caveats.append(f'{b.get("label")}: {b.get("coinsurance")}')
        headline=f"{q.product_name} is a Morgan Price Evolution plan with an annual premium of {_money(q.premium,q.currency)} for the current quotation inputs."
        if q.matched_requirements:
            fit="It matches your selected priorities: " + ", ".join(q.matched_requirements) + "."
        else:
            fit=q.card_why or "It is one of the plans available for your current quotation inputs."
        limitations="Benefits remain subject to the policy wording, annual maximum, network/pre-authorisation rules and underwriting."
    else:
        headline=f"{q.product_name} from {q.insurer} has an indicative annual premium of {_money(q.premium,q.currency)} for the current quotation inputs."
        fit=q.card_why or "It is included as an alternative provider option."
        details=[
            {"label":"Coverage summary","value":q.card_coverage or "International medical cover"},
            {"label":"Annual limit","value":q.card_annual_limit or "See plan schedule"},
            {"label":"Deductible","value":q.card_deductible or "See selected option"},
            {"label":"Evacuation","value":q.card_evacuation or "Subject to plan terms"},
        ]
        limitations="HAL does not yet have the same current verified benefit depth for this carrier. Detailed benefits must be confirmed before proposal."
    return {
        "plan_key":q.plan_key,"insurer":q.insurer,"product_name":q.product_name,
        "headline":headline,"fit":fit,"details":details,"caveats":caveats[:8],
        "limitations":limitations,"premium":q.premium,"currency":q.currency,
    }
