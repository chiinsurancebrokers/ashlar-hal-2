from pydantic import BaseModel, Field


class Applicant(BaseModel):
    age: int = Field(ge=0, le=120)
    residence_country: str
    nationality: str | None = None
    coverage_area: str = "area1"
    currency: str = "EUR"
    deductible: float | None = Field(default=None, ge=0)
    outpatient_required: bool = False
    maternity_required: bool = False
    dental_required: bool = False
    budget_annual: float | None = Field(default=None, ge=0)
