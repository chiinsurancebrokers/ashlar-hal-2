from abc import ABC, abstractmethod
from backend.app.schemas.applicant import Applicant
from backend.app.schemas.quote import QuoteResult


class InsurerAdapter(ABC):
    carrier_code: str

    @abstractmethod
    def quote(self, applicant: Applicant) -> list[QuoteResult]:
        raise NotImplementedError

    @abstractmethod
    def supported_rate_versions(self) -> list[str]:
        raise NotImplementedError
