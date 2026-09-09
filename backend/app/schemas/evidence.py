from enum import Enum
from pydantic import BaseModel


class EvidenceStatus(str, Enum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    CONTRADICTED = "contradicted"
    AMBIGUOUS = "ambiguous"


class EvidenceClaim(BaseModel):
    claim_id: str
    claim: str
    status: EvidenceStatus
    insurer: str | None = None
    product_code: str | None = None
    source_document: str | None = None
    document_sha256: str | None = None
    page: int | None = None
    clause: str | None = None
    excerpt: str | None = None
    allow_generation: bool = False
