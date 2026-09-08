from dataclasses import dataclass
from backend.app.insurers.base import InsurerAdapter
from backend.app.schemas.applicant import Applicant
from backend.app.schemas.quote import QuoteResult


@dataclass(frozen=True)
class RateRow:
    age_min: int
    age_max: int
    area: str
    product_code: str
    product_name: str
    annual_premium: float
    currency: str = "EUR"


class TableRateAdapter(InsurerAdapter):
    def __init__(self, carrier_code: str, carrier_name: str, version: str, rows: list[RateRow]):
        self.carrier_code = carrier_code
        self.carrier_name = carrier_name
        self.version = version
        self.rows = rows

    def supported_rate_versions(self) -> list[str]:
        return [self.version]

    def quote(self, applicant: Applicant) -> list[QuoteResult]:
        matches = [
            row for row in self.rows
            if row.age_min <= applicant.age <= row.age_max
            and row.area == applicant.coverage_area
        ]

        return [
            QuoteResult(
                insurer=self.carrier_name,
                product_code=row.product_code,
                product_name=row.product_name,
                eligible=True,
                premium=row.annual_premium,
                currency=row.currency,
                rate_version=self.version,
                deductible=applicant.deductible,
                warnings=["Indicative rate pending final insurer eligibility/underwriting checks."],
            )
            for row in matches
        ]
