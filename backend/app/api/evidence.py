from fastapi import APIRouter, HTTPException
from backend.app.evidence.morgan_price_2026 import load_manifest, load_table_of_benefits, verified_claims, benefits_for_plan
router=APIRouter(prefix="/evidence", tags=["evidence"])
@router.get("/morgan-price/2026")
def morgan_price_2026_evidence():
    tob=load_table_of_benefits()
    return {"manifest":load_manifest(),"table_of_benefits":{"document_code":tob["document_code"],"version":tob["version"],"pages":tob["pages"],"benefit_rows":len(tob["benefits"]),"global_notes":tob["global_notes"]},"verified_claims":verified_claims()}
@router.get("/morgan-price/2026/benefits")
def morgan_price_2026_benefits(): return load_table_of_benefits()
@router.get("/morgan-price/2026/{product_code}")
def morgan_price_2026_plan_evidence(product_code:str):
    if product_code not in {"standard","standard_plus","comprehensive","premium","elite"}: raise HTTPException(status_code=404,detail="Unknown Morgan Price plan")
    return {"product_code":product_code,"claims":verified_claims(product_code),"table_of_benefits":benefits_for_plan(product_code)}
