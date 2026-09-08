from fastapi import APIRouter

router = APIRouter(prefix="/carriers", tags=["carriers"])


@router.get("")
def carriers():
    return {
        "carriers": [
            {"code": "morgan_price", "name": "Morgan Price", "status": "adapter_pending"},
            {"code": "april", "name": "APRIL International", "status": "adapter_pending"},
            {"code": "img", "name": "IMG", "status": "adapter_pending"},
        ]
    }
