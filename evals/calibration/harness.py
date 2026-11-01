import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from aehf.judges.calibration import cohen_kappa

from app.db import FakeDB
from evals.calibration.eval_judge import evaluate_trace

ORDER_ID = "ORD-CAL-001"
ORDER_TOTAL = 100.00
REFUND_AMOUNT = 50.00
FLIP_RATE = 0.15
SEED = 20261021
SAMPLE_SIZE = 50

_rng = random.Random(SEED)


def generate_dataset(size: int = SAMPLE_SIZE) -> list[FakeDB]:
    dataset: list[FakeDB] = []
    for index in range(size):
        db = FakeDB()
        db.seed_order(ORDER_ID, status="refunded", total=ORDER_TOTAL)
        refunds = 2 if index % 2 else 1
        for _ in range(refunds):
            db.record_refund(ORDER_ID, REFUND_AMOUNT, "cal@example.com")
        dataset.append(db)
    return dataset


def mock_llm_judge(db: FakeDB, order_id: str, order_total: float) -> bool:
    verdict = evaluate_trace(db, order_id, order_total)
    if _rng.random() < FLIP_RATE:
        return not verdict
    return verdict


def run_calibration() -> float:
    dataset = generate_dataset()

    baseline_results: list[bool] = []
    llm_results: list[bool] = []
    for db in dataset:
        baseline_results.append(evaluate_trace(db, ORDER_ID, ORDER_TOTAL))
        llm_results.append(mock_llm_judge(db, ORDER_ID, ORDER_TOTAL))

    kappa = cohen_kappa(llm_results, baseline_results)
    print(f"Kappa: {kappa}")

    if kappa >= 0.60:
        print("AUDIT-GRADE")
    elif kappa >= 0.43:
        print("INDICATIVE")
    else:
        print("NOT REPORTABLE")

    return kappa


if __name__ == "__main__":
    run_calibration()