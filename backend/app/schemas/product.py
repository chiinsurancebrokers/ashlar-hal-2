from datetime import date
from pydantic import BaseModel, Field


class Benefit(BaseModel):
    code: str
    label: str
    covered: bool | None = None
    limit: float | None = Field(default=None, ge=0)
    currency: str | None = None
    notes: str | None = None


class ProductVersion(BaseModel):
    insurer: str
    product_code: str
    product_name: str
    rate_version: str
    effective_from: date | None = None
    effective_to: date | None = None
    currency: str = "EUR"
    benefits: list[Benefit] = []
