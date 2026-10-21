import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evals.calibration.harness import run_calibration
from evals.certificate import band_for, generate_certificate

WORKFLOW_NAME = "Refund Agent"
SCOPE = "Mock Refund Workflow"


def main() -> None:
    print("--- STARTING FULL AUDIT RUN ---")

    kappa = run_calibration()

    certificate = generate_certificate(
        workflow_name=WORKFLOW_NAME,
        scope=SCOPE,
        kappa_score=kappa,
        verdict=band_for(kappa),
        a1_outcome=True,
    )
    print(certificate)

    print("--- AUDIT RUN COMPLETE ---")


if __name__ == "__main__":
    main()