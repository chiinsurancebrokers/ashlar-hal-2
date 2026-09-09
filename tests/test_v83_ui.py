from pathlib import Path

HTML=(Path(__file__).resolve().parents[1]/"frontend"/"index.html").read_text(encoding="utf-8")

def test_adaptive_landing_exists():
    assert 'id="welcomeStage"' in HTML
    assert 'id="halOrb"' in HTML
    assert 'Health Insurance' in HTML
    assert 'Travel Insurance' in HTML

def test_contextual_quick_replies_are_rendered():
    assert "guided-choices" in HTML
    assert "sendGuidedChoice" in HTML

def test_legacy_permanent_shortcuts_not_public():
    assert 'About Morgan Price</button>' not in HTML
    assert 'Healthcare in Greece</button>' not in HTML
    assert 'HNWI / comprehensive</button>' not in HTML

def test_public_policy_analyzer_not_linked():
    assert "Advanced Policy Analyzer" not in HTML
