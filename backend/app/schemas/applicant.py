from pydantic import BaseModel, Field
class Applicant(BaseModel):
    age: int = Field(ge=0, le=120)
    residence_country: str = "Greece"
    nationality: str | None = None
    coverage_area: str = Field(default="area1", pattern="^(area1|area2|area3|area4)$")
    currency: str = "EUR"
    deductible: float | None = Field(default=None, ge=0)
    outpatient_required: bool = False
    maternity_required: bool = False
    dental_required: bool = False
    mental_health_required: bool = False
    wellness_required: bool = False
    optical_required: bool = False
    evacuation_required: bool = False
    chronic_required: bool = False
    budget_annual: float | None = Field(default=None, ge=0)
