from fastapi import APIRouter, HTTPException
from backend.app.knowledge.service import international_vs_local, destination, hnwi_ipmi, ipmi_value_proposition

router=APIRouter(prefix="/knowledge",tags=["knowledge"])

@router.get("/international-vs-local")
def get_international_vs_local():
    return international_vs_local()

@router.get("/ipmi-value")
def get_ipmi_value():
    return ipmi_value_proposition()

@router.get("/hnwi-ipmi")
def get_hnwi_ipmi():
    return hnwi_ipmi()

@router.get("/destinations/{country_code}")
def get_destination(country_code:str):
    data=destination(country_code)
    if not data:
        raise HTTPException(status_code=404,detail="Destination knowledge is not yet curated for this country.")
    return data
