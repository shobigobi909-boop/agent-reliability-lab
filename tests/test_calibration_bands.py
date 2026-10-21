import pytest

from evals.calibration import harness


@pytest.mark.parametrize(
    ("kappa", "expected"),
    [
        (0.61, "AUDIT-GRADE"),
        (0.56, "INDICATIVE"),
        (0.40, "NOT REPORTABLE"),
    ],
)
def test_verdict_bands(monkeypatch, capsys, kappa, expected) -> None:
    monkeypatch.setattr(harness, "cohen_kappa", lambda judge, human: kappa)

    harness.run_calibration()

    captured = capsys.readouterr().out
    assert f"Kappa: {kappa}" in captured
    assert expected in captured