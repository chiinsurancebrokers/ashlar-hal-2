from backend.app.schemas.evidence import EvidenceClaim, EvidenceStatus


def generation_allowed(claim: EvidenceClaim) -> bool:
    return (
        claim.status == EvidenceStatus.VERIFIED
        and claim.allow_generation
    )


def safe_claim_text(claim: EvidenceClaim) -> str:
    if generation_allowed(claim):
        return claim.claim
    return "I cannot confirm this point from the available verified policy evidence."
