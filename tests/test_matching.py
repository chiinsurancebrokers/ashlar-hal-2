from backend.app.matching.engine import RequirementResult, score_requirements


def test_mandatory_failure_zeroes_requirement_score():
    score, confidence = score_requirements([
        RequirementResult("Inpatient", True, True, 1.0),
        RequirementResult("Maternity", True, False, 0.8),
    ])
    assert score == 0.0
    assert confidence == 0.9
