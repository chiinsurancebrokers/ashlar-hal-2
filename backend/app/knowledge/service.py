from __future__ import annotations
import json
from functools import lru_cache
from pathlib import Path

BASE = Path(__file__).resolve().parents[3] / "data"
EDU_PATH = BASE / "knowledge" / "international_vs_local.json"
HNWI_PATH = BASE / "knowledge" / "hnwi_ipmi.json"
DEST_DIR = BASE / "destinations"

@lru_cache
def international_vs_local() -> dict:
    return json.loads(EDU_PATH.read_text(encoding="utf-8"))

@lru_cache
def hnwi_ipmi() -> dict:
    return json.loads(HNWI_PATH.read_text(encoding="utf-8"))

@lru_cache
def destination(country_code: str) -> dict | None:
    mapping={"GR":"greece.json","GREECE":"greece.json","ΕΛΛΑΔΑ":"greece.json","HELLAS":"greece.json"}
    filename=mapping.get(country_code.strip().upper())
    if not filename:
        return None
    return json.loads((DEST_DIR/filename).read_text(encoding="utf-8"))

def source_urls(data: dict) -> list[str]:
    urls=[]
    for p in data.get("principles",[]):
        for s in p.get("sources",[]):
            if s.get("url") and s["url"] not in urls: urls.append(s["url"])
    for s in data.get("additional_sources",[]):
        if s.get("url") and s["url"] not in urls: urls.append(s["url"])
    return urls

def education_context() -> str:
    data=international_vs_local()
    parts=["INTERNATIONAL VS LOCAL HEALTH INSURANCE EDUCATION"]
    for p in data["principles"]:
        sources="; ".join(f'{s["name"]}: {s["url"]}' for s in p.get("sources",[]))
        parts.append(
            f'- {p["claim"]}\n  BALANCE: {p["balanced_note"]}\n  SOURCES: {sources}'
        )
    parts.append("ARGUMENTATION RULES:\n- " + "\n- ".join(data["argumentation_rules"]))
    return "\n\n".join(parts)

def destination_context(country_code: str) -> str:
    data=destination(country_code)
    if not data:
        return ""
    parts=[
        f'DESTINATION HEALTHCARE INTELLIGENCE: {data["country"]}',
        data["system_summary"]["balanced_overview"],
        data["system_summary"]["public_system_role"],
    ]
    for f in data["facts"]:
        line=f'- {f["claim"]}'
        if f.get("value"): line+=f' Value: {f["value"]}.'
        if f.get("period"): line+=f' Period: {f["period"]}.'
        if f.get("denominator_note"): line+=f' IMPORTANT DENOMINATOR NOTE: {f["denominator_note"]}'
        line+=f' Source: {f["source_name"]} — {f["source_url"]}'
        parts.append(line)
    if data.get("oop_interpretation"):
        oop=data["oop_interpretation"]
        parts.append("OOP INTERPRETATION:\n" + oop["correct_meaning"])
        parts.append("DO NOT INFER FROM OOP:\n- " + "\n- ".join(oop["not_proven_by_metric"]))
        if oop.get("greece_2023_oop_distribution"):
            d=oop["greece_2023_oop_distribution"]
            parts.append(
                "GREECE 2023 OOP DISTRIBUTION: "
                f'pharmaceuticals/medical aids {d["pharmaceuticals_and_medical_aids"]}; '
                f'inpatient {d["inpatient_care"]}; outpatient {d["outpatient_medical_care"]}; '
                f'dental {d["dental_care"]}; other {d["other"]}. '
                + d["interpretation"]
            )
    parts.append("SELLING / FAIRNESS BOUNDARY:\n- " + "\n- ".join(data["selling_boundary"]))
    return "\n\n".join(parts)

def destination_sources(country_code: str) -> list[str]:
    data=destination(country_code)
    if not data: return []
    urls=[]
    for f in data["facts"]:
        u=f.get("source_url")
        if u and u not in urls: urls.append(u)
    return urls


def hnwi_context() -> str:
    data=hnwi_ipmi()
    parts=[
        "AFFLUENT / HNWI IPMI NEED RECOGNITION",
        data["purpose"],
        "RECOGNITION SIGNALS:\n- " + "\n- ".join(data["recognition_signals"]),
    ]
    for d in data["core_value_dimensions"]:
        parts.append(
            f'{d["title"]}: {d["argument"]}\nCAUTION: {d["caveat"]}'
        )
    parts.append("DO NOT SAY:\n- " + "\n- ".join(data["what_not_to_say"]))
    parts.append("DISCOVERY QUESTIONS:\n- " + "\n- ".join(data["suggested_discovery_questions"]))
    parts.append("SOURCES:\n- " + "\n- ".join(f'{s["name"]}: {s["url"]}' for s in data["sources"]))
    return "\n\n".join(parts)
