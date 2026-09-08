from dataclasses import dataclass


@dataclass(frozen=True)
class RequirementResult:
    requirement: str
    mandatory: bool
    matched: bool
    evidence_confidence: float


def score_requirements(results: list[RequirementResult]) -> tuple[float, float]:
    if not results:
        return 0.0, 0.0

    mandatory_failed = any(r.mandatory and not r.matched for r in results)
    matched = sum(1 for r in results if r.matched)
    requirements_score = 0.0 if mandatory_failed else matched / len(results)
    evidence_confidence = sum(r.evidence_confidence for r in results) / len(results)

    return round(requirements_score, 4), round(evidence_confidence, 4)
