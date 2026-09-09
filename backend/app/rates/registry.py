from __future__ import annotations
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import csv

from backend.app.schemas.applicant import Applicant
from backend.app.schemas.quote import QuoteResult
from backend.app.evidence.morgan_price_2026 import verified_fact_texts, load_manifest

RATE_DIR = Path(__file__).resolve().parents[3] / "data" / "rates"
LEGACY_FILE = RATE_DIR / "legacy_april_img_2025.csv"
MP_2026_FILE = RATE_DIR / "morgan_price_2026_official.csv"
CARD_META_FILE = Path(__file__).resolve().parents[3] / "data" / "ui" / "plan_cards.json"

@dataclass(frozen=True)
class RateRecord:
    carrier: str
    carrier_name: str
    rate_version: str
    area: str
    area_label: str
    age_min: int
    age_max: int
    product_code: str
    product_name: str
    annual_premium: float
    currency: str
    official: bool
    source: str

@lru_cache
def load_card_meta() -> dict:
    import json
    return json.loads(CARD_META_FILE.read_text(encoding="utf-8"))

@lru_cache
def load_rates() -> tuple[RateRecord, ...]:
    records=[]
    with MP_2026_FILE.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            records.append(RateRecord(
                carrier=row["carrier"], carrier_name=row["carrier_name"], rate_version=row["rate_version"],
                area=row["area"], area_label=row["area_label"], age_min=int(row["age_min"]), age_max=int(row["age_max"]),
                product_code=row["product_code"], product_name=row["product_name"], annual_premium=float(row["annual_premium"]),
                currency=row["currency"], official=True, source=row["source"]
            ))
    with LEGACY_FILE.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            records.append(RateRecord(
                carrier=row["carrier"], carrier_name=row["carrier_name"], rate_version=row["rate_version"],
                area=row["area"], area_label=row["area"], age_min=int(row["age_min"]), age_max=int(row["age_max"]),
                product_code=row["product_code"], product_name=row["product_name"], annual_premium=float(row["annual_premium"]),
                currency=row["currency"], official=False, source="Legacy HAL rate table"
            ))
    return tuple(records)

def current_versions() -> list[dict]:
    seen={}
    for r in load_rates():
        key=(r.carrier,r.rate_version)
        if key not in seen:
            seen[key]={
                "carrier":r.carrier,"carrier_name":r.carrier_name,"rate_version":r.rate_version,
                "status":"official_2026" if r.official else "legacy_current",
                "source":r.source
            }
    return list(seen.values())

def _requirement_match(applicant: Applicant, carrier: str, product_code: str) -> tuple[float | None, list[str], list[str], float]:
    selected=[]
    if applicant.outpatient_required: selected.append(("Out-patient cover", "outpatient"))
    if applicant.maternity_required: selected.append(("Routine maternity", "maternity"))
    if applicant.dental_required: selected.append(("Routine dental", "dental"))
    if applicant.mental_health_required: selected.append(("Mental health", "mental_health"))
    if applicant.wellness_required: selected.append(("Wellness screening", "wellness"))
    if applicant.optical_required: selected.append(("Optical benefits", "optical"))
    if applicant.evacuation_required: selected.append(("Medical evacuation", "evacuation"))
    if applicant.chronic_required: selected.append(("Chronic condition cover", "chronic"))
    if not selected: return None, [], [], 1.0 if carrier == "morgan_price" else 0.0
    if carrier != "morgan_price": return None, [], [], 0.0
    from backend.app.evidence.morgan_price_2026 import covered
    checks={
        "outpatient": product_code in {"standard_plus","comprehensive","premium","elite"},
        "maternity": covered(product_code,"normal_maternity"),
        "dental": covered(product_code,"routine_dental"),
        "mental_health": covered(product_code,"outpatient_psychiatric") and covered(product_code,"inpatient_psychiatric"),
        "wellness": covered(product_code,"wellness_screening"),
        "optical": covered(product_code,"optical_eye_test"),
        "evacuation": covered(product_code,"medical_evacuation_transport"),
        "chronic": covered(product_code,"inpatient_chronic_conditions"),
    }
    matched=[]; unmatched=[]
    for label,key in selected: (matched if checks[key] else unmatched).append(label)
    return len(matched)/len(selected), matched, unmatched, 1.0

def quote_current(applicant: Applicant) -> list[QuoteResult]:
    residence=applicant.residence_country.strip().lower()
    if residence not in {"greece","gr","hellas","ελλάδα","ellada"}:
        return []
    quotes=[]
    has_requirements=any([applicant.outpatient_required, applicant.maternity_required, applicant.dental_required, applicant.mental_health_required, applicant.wellness_required, applicant.optical_required, applicant.evacuation_required, applicant.chronic_required])
    for r in load_rates():
        if r.area != applicant.coverage_area:
            continue
        # For Area 2/3/4, only Morgan Price has a verified 2026 geographic definition.
        if applicant.coverage_area in {"area2","area3","area4"} and r.carrier != "morgan_price":
            continue
        if not (r.age_min <= applicant.age <= r.age_max):
            continue
        req_score, matched, unmatched, evidence_conf = _requirement_match(applicant, r.carrier, r.product_code)
        if r.official:
            warnings=[
                "Official Morgan Price Europe 2026 rate from the supplied workbook.",
                "Final premium and acceptance remain subject to insurer eligibility, underwriting and confirmation."
            ]
            facts=verified_fact_texts(r.product_code)
            docs=[d["official_url"] for d in load_manifest()["documents"] if d["document_type"] in {"policy_wording","table_of_benefits"}]
            evidence_status="verified_2026_tob_and_policy"
        else:
            warnings=[
                "Indicative quotation using HAL's legacy current rate dataset for this carrier.",
                "Benefit matching is intentionally not scored until this carrier's new official documents are loaded."
            ]
            facts=[]; docs=[]; evidence_status="legacy_unverified_benefits"
        reasons=[]
        if matched:
            reasons.append("Verified match: " + ", ".join(matched))
        if unmatched:
            reasons.append("Verified gap: " + ", ".join(unmatched))
        quotes.append(QuoteResult(
            insurer=r.carrier_name,product_code=r.product_code,product_name=r.product_name,eligible=True,
            premium=r.annual_premium,currency=r.currency,rate_version=r.rate_version,deductible=applicant.deductible,
            coverage_area_label=r.area_label if r.official else f"{r.area} (legacy definition)",official_rate=r.official,
            evidence_status=evidence_status,evidence_confidence=evidence_conf,requirements_score=req_score,
            matched_requirements=matched,unmatched_requirements=unmatched,
            verified_facts=facts,source_documents=docs,reasons=reasons,warnings=warnings
        ))
    if has_requirements:
        def requirement_rank(q: QuoteResult):
            if q.requirements_score == 1.0 and q.evidence_confidence == 1.0: cls=0
            elif q.requirements_score is not None and q.requirements_score > 0: cls=1
            elif q.requirements_score is None: cls=2
            else: cls=3
            budget_gap=abs((q.premium or 0)-(applicant.budget_annual or q.premium or 0))
            over=bool(applicant.budget_annual and (q.premium or 0)>applicant.budget_annual)
            return (cls, over, budget_gap, q.premium or float("inf"))
        quotes.sort(key=requirement_rank)
    elif applicant.budget_annual:
        quotes.sort(key=lambda q:(q.premium > applicant.budget_annual, abs((q.premium or 0)-applicant.budget_annual)))
    else:
        quotes.sort(key=lambda q:q.premium or float("inf"))
    return quotes


def _client_card_meta(carrier: str, product_code: str) -> dict:
    data=load_card_meta().get(carrier,{}).get(product_code,{})
    return {
        "card_badge":data.get("badge"),
        "card_coverage":data.get("coverage"),
        "card_annual_limit":data.get("annual_limit"),
        "card_deductible":data.get("deductible"),
        "card_evacuation":data.get("evacuation"),
        "card_why":data.get("why"),
    }


def _has_must_haves(applicant: Applicant) -> bool:
    return any([
        applicant.outpatient_required, applicant.maternity_required,
        applicant.dental_required, applicant.mental_health_required,
        applicant.wellness_required, applicant.optical_required,
        applicant.evacuation_required, applicant.chronic_required,
    ])


def _carrier_key_from_quote(q: QuoteResult) -> str:
    if "Morgan Price" in q.insurer:
        return "morgan_price"
    if "APRIL" in q.insurer:
        return "april"
    if "IMG" in q.insurer:
        return "img"
    return q.insurer.lower().replace(" ","_")[:40]


def _smart_badges(applicant: Applicant, q: QuoteResult) -> list[str]:
    badges=[]
    if q.evidence_confidence==1.0 and q.requirements_score==1.0:
        if applicant.maternity_required:
            badges.append("Maternity fit")
        if applicant.outpatient_required:
            badges.append("Outpatient fit")
        if applicant.mental_health_required:
            badges.append("Mental health fit")
        if applicant.dental_required:
            badges.append("Dental fit")
        if applicant.evacuation_required:
            badges.append("Evacuation fit")
        if not badges and q.matched_requirements:
            badges.append("Needs matched")
    elif q.evidence_confidence < 1.0:
        badges.append("Alternative provider")
    if q.product_code=="elite" and "Morgan Price" in q.insurer:
        badges.append("Highest cover")
    return badges[:3]


def quote_exclusions(applicant: Applicant) -> list[dict]:
    """Client-safe explanation of verified plans removed by MUST-HAVE filters."""
    out=[]
    for q in quote_current(applicant):
        if q.evidence_confidence==1.0 and q.requirements_score is not None and q.requirements_score < 1.0:
            out.append({
                "plan_key":f"{_carrier_key_from_quote(q)}:{q.product_code}",
                "insurer":q.insurer,
                "product_name":q.product_name,
                "gaps":list(q.unmatched_requirements),
            })
    return out


def quote_shortlist(applicant: Applicant, limit: int = 5) -> list[QuoteResult]:
    """Premium client-facing shortlist with hard MUST-HAVE filtering."""
    candidates=quote_current(applicant)
    has_req=_has_must_haves(applicant)
    filtered=[]

    for q in candidates:
        # A verified failed MUST-HAVE is an absolute client-facing exclusion.
        if q.evidence_confidence==1.0 and q.requirements_score is not None and q.requirements_score < 1.0:
            continue

        carrier_key=_carrier_key_from_quote(q)
        for k,v in _client_card_meta(carrier_key,q.product_code).items():
            setattr(q,k,v)

        q.plan_key=f"{carrier_key}:{q.product_code}"
        q.fit_badges=_smart_badges(applicant,q)
        q.must_have_checks=list(q.matched_requirements) if q.evidence_confidence==1.0 else []

        if q.card_badge is None:
            q.card_badge=(q.insurer.split()[0][:3] if q.insurer else "PLAN").upper()
        q.card_coverage=q.card_coverage or "International medical cover"
        q.card_annual_limit=q.card_annual_limit or "See plan schedule"
        q.card_deductible=q.card_deductible or "See selected option"
        q.card_evacuation=q.card_evacuation or "Subject to plan terms"

        if q.evidence_confidence==1.0 and q.matched_requirements:
            q.card_why="Matches your priorities: " + ", ".join(q.matched_requirements[:3]) + "."
            q.client_note=None
        elif q.evidence_confidence < 1.0:
            q.card_why=q.card_why or "Alternative provider option."
            q.client_note="Current benefits should be confirmed before proposal."
        else:
            q.card_why=q.card_why or "International health insurance option."

        filtered.append(q)

    def client_rank(q: QuoteResult):
        if has_req:
            if q.requirements_score==1.0 and q.evidence_confidence==1.0: cls=0
            elif q.requirements_score is None: cls=1
            else: cls=2
        else: cls=0
        over=bool(applicant.budget_annual and (q.premium or 0)>applicant.budget_annual)
        gap=abs((q.premium or 0)-(applicant.budget_annual or q.premium or 0))
        return (cls,over,gap,q.premium or float("inf"))

    filtered.sort(key=client_rank)

    shortlist=[]; seen=set()
    for q in filtered:
        key=_carrier_key_from_quote(q)
        if key in seen: continue
        shortlist.append(q); seen.add(key)
        if len(shortlist)>=min(3,limit): break
    for q in filtered:
        if q in shortlist: continue
        shortlist.append(q)
        if len(shortlist)>=limit: break

    # Add smart ranking badges after final shortlist is known.
    lowest=min((q.premium for q in shortlist if q.premium is not None),default=None)
    for i,q in enumerate(shortlist):
        q.recommended=(i==0)
        q.recommendation_rank=i+1
        if lowest is not None and q.premium==lowest and "Best value" not in q.fit_badges:
            q.fit_badges=(q.fit_badges+["Best value"])[:3]
    return shortlist
