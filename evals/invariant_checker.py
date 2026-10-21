from pathlib import Path

import yaml

from app.db import FakeDB, get_default_db

POLICY_PATH = Path(__file__).resolve().parent / "invariants" / "refund_a1_v0_1.yaml"


def load_invariants(path: Path = POLICY_PATH) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)["invariants"]


def evaluate_a1(db: FakeDB | None, order_id: str, order_total: float) -> dict:
    if db is None:
        db = get_default_db()

    for invariant in load_invariants():
        invariant_id = invariant["id"]

        if invariant_id == "A1-REFUND-01":
            passed = db.refund_count(order_id) <= 1
        elif invariant_id == "A1-REFUND-03":
            refunded_total = sum(
                entry["amount"] for entry in db.ledger if entry["order_id"] == order_id
            )
            passed = refunded_total <= order_total
        else:
            continue

        if not passed:
            return {"status": "FAILED", "invariant": invariant_id}

    return {"status": "PASSED"}
