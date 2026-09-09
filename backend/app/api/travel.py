from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from backend.app.travel.europesure import public_catalog, recommend_tier


router=APIRouter(prefix="/travel",tags=["travel"])


class TravelState(BaseModel):
    state: dict[str,Any] = {}


@router.get("/europesure")
def europesure_catalog():
    return public_catalog()


@router.post("/europesure/recommend")
def europesure_recommend(req: TravelState):
    return recommend_tier(req.state)
