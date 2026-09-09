from fastapi import APIRouter

router=APIRouter(prefix="/carriers", tags=["carriers"])

@router.get("")
def carriers():
    return {
        "carriers":[
            {"code":"morgan_price","name":"Morgan Price (Europe) ApS","rating":"active","rate_version":"morgan_price_europe_2026_official","rate_status":"official_2026","evidence":"official_2026_core_verified"},
            {"code":"april","name":"APRIL International","rating":"active","rate_version":"april_2025_current","rate_status":"legacy_current","evidence":"pending_new_documents"},
            {"code":"img","name":"IMG","rating":"active","rate_version":"img_europe_2025_current","rate_status":"legacy_current","evidence":"pending_new_documents"}
        ]
    }
