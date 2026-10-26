from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "dashboard" / "app.py"

CASE_NAMES = [
    "Case 014: Duplicate Refund",
    "Case 015: Infinite Loop",
    "Case 016: Prompt Injection",
    "Case 017: GhostJacking",
    "Case 018: OAuth Bypass",
]


def run_app() -> AppTest:
    return AppTest.from_file(str(APP), default_timeout=30).run()


def test_dashboard_renders_both_top_level_tabs():
    at = run_app()

    assert not at.exception
    labels = [tab.label for tab in at.tabs]
    assert "Live Audit" in labels
    assert "Portfolio Case Studies" in labels


def test_portfolio_tab_offers_every_case():
    at = run_app()

    assert not at.exception
    assert at.selectbox(key="portfolio_case").options == CASE_NAMES


def test_selecting_a_case_renders_its_writeup():
    at = run_app()

    at.selectbox(key="portfolio_case").select("Case 018: OAuth Bypass").run()

    assert not at.exception
    rendered = "\n".join(block.value for block in at.markdown)
    assert "Case 018: MCP Authorization Bypass (OAuth Scope Negation)" in rendered


def test_running_a_case_test_shows_pytest_output():
    at = run_app()

    at.selectbox(key="portfolio_case").select("Case 015: Infinite Loop").run()
    at.button(key="portfolio_run_test").click().run()

    assert not at.exception
    assert at.success
    output = "\n".join(block.value for block in at.code)
    assert "1 passed" in output


def test_live_audit_button_still_produces_the_audit():
    at = run_app()

    at.button(key="run_live_audit").click().run()

    audit = at.session_state.audit
    assert not at.exception
    assert audit["a1_status"] == "PASSED"
    assert audit["refund_count"] == 1
    assert audit["verdict"] in {"CLEAN", "QUALIFIED", "DISCLAIMER"}
    assert "§1.1" in audit["certificate"] or "1.1" in audit["certificate"]
