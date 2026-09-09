from __future__ import annotations
import json
from functools import lru_cache
from pathlib import Path
BASE = Path(__file__).resolve().parents[3] / "data" / "evidence" / "morgan_price_2026"
@lru_cache
def load_manifest() -> dict: return json.loads((BASE / "documents.json").read_text(encoding="utf-8"))
@lru_cache
def load_claims() -> dict: return json.loads((BASE / "claims.json").read_text(encoding="utf-8"))
@lru_cache
def load_table_of_benefits() -> dict: return json.loads((BASE / "table_of_benefits.json").read_text(encoding="utf-8"))
def verified_claims(product_code: str | None = None) -> list[dict]:
    result=[]
    for c in load_claims()["claims"]:
        if c.get("status") != "verified" or not c.get("allow_generation"): continue
        if product_code is not None and c.get("product_code") not in (None, product_code): continue
        result.append(c)
    return result
def benefits_for_plan(product_code: str) -> list[dict]:
    if product_code not in {"standard","standard_plus","comprehensive","premium","elite"}: return []
    return [{"benefit_code":b["benefit_code"],"section":b["section"],"category":b["category"],"label":b["label"],"value":b["values"][product_code],"page":b["page"],"source_page_sha256":b["source_page_sha256"],"waiting_period":b.get("waiting_period"),"coinsurance":b.get("coinsurance"),"pre_authorisation_required":b.get("pre_authorisation_required",False),"note":b.get("note"),"status":"verified"} for b in load_table_of_benefits()["benefits"]]
def benefit_value(product_code: str, benefit_code: str) -> str | None:
    for b in load_table_of_benefits()["benefits"]:
        if b["benefit_code"] == benefit_code: return b["values"].get(product_code)
    return None
def covered(product_code: str, benefit_code: str) -> bool:
    value=benefit_value(product_code,benefit_code)
    return value is not None and not value.lower().startswith("not covered")
def verified_fact_texts(product_code: str, limit: int = 10) -> list[str]:
    selected=["overall_maximum","cancer_treatment","outpatient_services_combined","outpatient_psychiatric","routine_dental","normal_maternity","medical_evacuation_transport","out_of_area_emergency"]
    index={b["benefit_code"]:b for b in load_table_of_benefits()["benefits"]}; tob=[]
    for code in selected:
        b=index.get(code)
        if b: tob.append(f'{b["label"]}: {b["values"][product_code]} (Table of Benefits p.{b["page"]}).')
    policy_specific=[c["claim"] for c in verified_claims(product_code) if c.get("product_code")==product_code]
    policy_general=[c["claim"] for c in verified_claims(product_code) if c.get("product_code") is None]
    return (tob+policy_specific+policy_general)[:limit]
