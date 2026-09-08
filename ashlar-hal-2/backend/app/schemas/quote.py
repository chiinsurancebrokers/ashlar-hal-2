from pydantic import BaseModel, Field


class QuoteResult(BaseModel):
    insurer: str
    product_code: str
    product_name: str
    eligible: bool
    premium: float | None = Field(default=None, ge=0)
    currency: str = "EUR"
    rate_version: str
    deductible: float | None = None
    reasons: list[str] = []
    warnings: list[str] = []
