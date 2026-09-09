from pathlib import Path


def test_v8_frontend_has_ultimate_ux_elements():
    html=(Path(__file__).resolve().parents[1]/"frontend"/"index.html").read_text(encoding="utf-8")
    for term in ["Your needs","Compare selected plans","Send me this comparison","progressFill","compareTray","localStorage"]:
        assert term in html
