import pytest

from datetime import date

from evals.certificate import band_for, generate_certificate

AUDITED_ON = "2026-10-26"


def build(kappa: float, a1_outcome: bool = True) -> str:
    return generate_certificate(
        "Live Gemini Agent",
        "Real LLM refund workflow",
        kappa,
        band_for(kappa),
        a1_outcome=a1_outcome,
        audit_date=date.fromisoformat(AUDITED_ON),
    )


def test_failed_invariant_forces_fail_verdict() -> None:
    certificate = build(0.61, a1_outcome=False)

    assert "## 1. Verdict: FAIL" in certificate
    assert "## 1. Verdict: QUALIFIED" not in certificate
    assert "| A1-REFUND-01 | An order may be refunded at most once | Failed |" in certificate
    assert "| A1-REFUND-03 | Total refunded must not exceed the order total | Not evaluated |" in certificate


def test_indicative_kappa_qualifies_the_report() -> None:
    certificate = build(0.56)

    assert "## 1. Verdict: QUALIFIED" in certificate
    assert "| Cohen's Kappa (judge vs. baseline checker) | 0.56 |" in certificate
    assert "| Agreement band | Moderate (0.43-0.60) |" in certificate
    assert "| Evidence label | Indicative |" in certificate
    assert "| Sample size | 50 |" in certificate
    assert "| A1-REFUND-02 | A refunded order must not transition to refunded again | Not evaluated |" in certificate
    assert "**Judge provenance.**" in certificate


def test_audit_grade_kappa_with_a_passing_invariant_passes() -> None:
    certificate = build(0.85)

    assert "## 1. Verdict: PASS" in certificate
    assert "| Evidence label | Confirmatory |" in certificate
    assert "| A1-REFUND-01 | An order may be refunded at most once | Passed |" in certificate


def test_report_carries_named_signer_scope_and_date() -> None:
    certificate = build(0.56)

    assert "# Agent Reliability Audit Report — Live Gemini Agent" in certificate
    assert "**Auditor:** Shoaib Hussain, AI Reliability Engineer" in certificate
    assert "**System under test:** Live Gemini agent" in certificate
    assert "**Workflow:** Real LLM refund workflow" in certificate
    assert "**Model version:** gemini-3.8-flash" in certificate
    assert f"**Audit date:** {AUDITED_ON}" in certificate
    assert "**Invariant spec:** refund_a1 v0.1" in certificate
    assert "[QA Auditor]" not in certificate
    assert "| **Date** | 2026-10-26 |" in certificate
    for section in (
        "## 2. Scope and methodology",
        "## 3. Invariant results",
        "## 4. Statistical claims",
        "## 5. MCP supply-chain review",
        "## 6. Framework mapping",
        "## 7. Recommendations",
        "## 8. Auditor sign-off",
    ):
        assert section in certificate


def test_supply_chain_count_comes_from_the_scanner() -> None:
    certificate = build(0.56)

    assert "in the tool descriptions reviewed (3 tools)" in certificate


def test_a_supplied_verdict_that_contradicts_the_kappa_raises() -> None:
    with pytest.raises(ValueError, match="contradicts"):
        generate_certificate(
            "Live Gemini Agent",
            "Real LLM refund workflow",
            0.56,
            "AUDIT-GRADE",
        )
