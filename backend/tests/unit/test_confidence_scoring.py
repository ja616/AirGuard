import pytest
from backend.investigation.stages.confidence import run
from backend.investigation.models import RCAHypothesis, CorrelatedFinding
from backend.core.constants import ConfidenceLevel
import datetime

def make_finding(severity, source="airflow"):
    return CorrelatedFinding(
        source=source,
        event="test",
        timestamp=datetime.datetime.now().isoformat(),
        severity=severity,
        relevance_score=1.0,
        description="test"
    )

def make_rca():
    return RCAHypothesis(
        root_cause="Test",
        contributing_factors=[],
        certainty=0.5
    )

def test_confidence_0_findings():
    rca = make_rca()
    res = run(rca, [])
    assert res.score == 0.3 # 0.5 - 0.2
    assert res.level == ConfidenceLevel.LOW

def test_confidence_1_low():
    res = run(make_rca(), [make_finding("low")])
    assert res.score == 0.5 # 0.5 + 0.05 - 0.05
    assert res.level == ConfidenceLevel.MEDIUM

def test_confidence_1_med():
    res = run(make_rca(), [make_finding("medium")])
    assert res.score == 0.55 # 0.5 + 0.1 - 0.05
    assert res.level == ConfidenceLevel.MEDIUM

def test_confidence_1_high():
    res = run(make_rca(), [make_finding("high")])
    assert res.score == 0.65 # 0.5 + 0.2 - 0.05
    assert res.level == ConfidenceLevel.MEDIUM

def test_confidence_2_low_same():
    res = run(make_rca(), [make_finding("low"), make_finding("low")])
    assert res.score == 0.55 # 0.5 + 0.05 + 0.05 - 0.05
    assert res.level == ConfidenceLevel.MEDIUM

def test_confidence_2_med_same():
    res = run(make_rca(), [make_finding("medium"), make_finding("medium")])
    assert res.score == 0.65 # 0.5 + 0.2 - 0.05
    assert res.level == ConfidenceLevel.MEDIUM

def test_confidence_2_high_same():
    res = run(make_rca(), [make_finding("high"), make_finding("high")])
    assert res.score == 0.85 # 0.5 + 0.4 - 0.05
    assert res.level == ConfidenceLevel.HIGH

def test_confidence_2_low_diff():
    res = run(make_rca(), [make_finding("low", "a"), make_finding("low", "b")])
    assert res.score == 0.75 # 0.5 + 0.1 + 0.15
    assert res.level == ConfidenceLevel.MEDIUM

def test_confidence_2_med_diff():
    res = run(make_rca(), [make_finding("medium", "a"), make_finding("medium", "b")])
    assert res.score == 0.85 # 0.5 + 0.2 + 0.15
    assert res.level == ConfidenceLevel.HIGH

def test_confidence_2_high_diff():
    res = run(make_rca(), [make_finding("high", "a"), make_finding("high", "b")])
    assert res.score == 1.0 # 0.5 + 0.4 + 0.15 = 1.05 -> 1.0
    assert res.level == ConfidenceLevel.HIGH

def test_confidence_low_med_diff():
    res = run(make_rca(), [make_finding("low", "a"), make_finding("medium", "b")])
    assert res.score == 0.8 # 0.5 + 0.05 + 0.1 + 0.15
    assert res.level == ConfidenceLevel.HIGH

def test_confidence_low_high_diff():
    res = run(make_rca(), [make_finding("low", "a"), make_finding("high", "b")])
    assert res.score == 0.9 # 0.5 + 0.05 + 0.2 + 0.15
    assert res.level == ConfidenceLevel.HIGH

def test_confidence_med_high_diff():
    res = run(make_rca(), [make_finding("medium", "a"), make_finding("high", "b")])
    assert res.score == 0.95 # 0.5 + 0.1 + 0.2 + 0.15
    assert res.level == ConfidenceLevel.HIGH

def test_confidence_3_same():
    res = run(make_rca(), [make_finding("medium")] * 3)
    assert res.score == 0.75 # 0.5 + 0.3 - 0.05
    assert res.level == ConfidenceLevel.MEDIUM

def test_confidence_3_diff():
    res = run(make_rca(), [make_finding("medium", "a"), make_finding("medium", "b"), make_finding("low", "c")])
    assert res.score == 0.9 # 0.5 + 0.1 + 0.1 + 0.05 + 0.15
    assert res.level == ConfidenceLevel.HIGH
