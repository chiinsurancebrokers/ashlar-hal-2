from fastapi import APIRouter
import json
from pathlib import Path
from backend.app.rates.registry import current_versions

router=APIRouter(prefix="/rates", tags=["rates"])
RATE_DIR=Path(__file__).resolve().parents[3]/"data"/"rates"

@router.get("/versions")
def rate_versions():
    return {"active_versions":current_versions(),"policy":"Official versions supersede legacy versions without overwriting historical source data."}

@router.get("/morgan-price/2026/source")
def morgan_price_source():
    return json.loads((RATE_DIR/"morgan_price_2026_source.json").read_text(encoding="utf-8"))
