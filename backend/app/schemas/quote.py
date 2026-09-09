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
    coverage_area_label: str | None = None
    official_rate: bool = False
    evidence_status: str = "unverified"
    evidence_confidence: float = Field(default=0.0, ge=0, le=1)
    requirements_score: float | None = Field(default=None, ge=0, le=1)
    matched_requirements: list[str] = []
    unmatched_requirements: list[str] = []
    verified_facts: list[str] = []
    source_documents: list[str] = []
    reasons: list[str] = []
    warnings: list[str] = []
