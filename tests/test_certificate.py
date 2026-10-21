from evals.certificate import band_for, generate_certificate


def test_failed_a1_forces_adverse_verdict() -> None:
    certificate = generate_certificate(
        "Refund Agent",
        "Mock Refund Workflow",
        0.61,
        band_for(0.61),
        a1_outcome=False,
    )

    assert "**ADVERSE**" in certificate
    assert "**CLEAN**" not in certificate
    assert "**FAILED**" in certificate


def test_passing_a1_keeps_the_kappa_verdict() -> None:
    certificate = generate_certificate(
        "Refund Agent",
        "Mock Refund Workflow",
        0.61,
        band_for(0.61),
        a1_outcome=True,
    )

    assert "**CLEAN**" in certificate
    assert "**ADVERSE**" not in certificate
    assert "**PASSED**" in certificate