from __future__ import annotations

from backend.app.rates.registry import quote_shortlist, quote_exclusions
from backend.app.schemas.applicant import Applicant

COMPARISON_ROWS=[
    ("Annual premium","premium"),
    ("Monthly premium","monthly"),
    ("Coverage","card_coverage"),
    ("Annual limit","card_annual_limit"),
    ("Deductible","card_deductible"),
    ("Evacuation","card_evacuation"),
    ("Why it fits","card_why"),
]


def plan_to_client_dict(q) -> dict:
    annual=float(q.premium or 0)
    return {
        "plan_key":q.plan_key,
        "insurer":q.insurer,
        "product_name":q.product_name,
        "currency":q.currency,
        "premium":annual,
        "monthly":round(annual/12,2),
        "card_badge":q.card_badge,
        "card_coverage":q.card_coverage,
        "card_annual_limit":q.card_annual_limit,
        "card_deductible":q.card_deductible,
        "card_evacuation":q.card_evacuation,
        "card_why":q.card_why,
        "fit_badges":q.fit_badges,
        "must_have_checks":q.must_have_checks,
        "client_note":q.client_note,
        "recommended":q.recommended,
    }


def build_comparison(applicant: Applicant, selected_keys: list[str] | None = None) -> dict:
    shortlist=quote_shortlist(applicant,limit=5)
    selected=set(selected_keys or [])
    plans=[q for q in shortlist if not selected or q.plan_key in selected]
    return {
        "plans":[plan_to_client_dict(q) for q in plans],
        "excluded":quote_exclusions(applicant),
        "rows":[label for label,_ in COMPARISON_ROWS],
    }
