from app.db import FakeDB
from evals.invariant_checker import evaluate_a1


def test_a1_refund_01_fails_on_corrupted_ledger(fake_db: FakeDB) -> None:
    order_id = "ORD-2002"
    fake_db.seed_order(order_id, status="refunded", total=100.00)

    fake_db.ledger.append(
        {"order_id": order_id, "amount": 50.00, "customer_email": "qa@example.com"}
    )
    fake_db.ledger.append(
        {"order_id": order_id, "amount": 50.00, "customer_email": "qa@example.com"}
    )

    assert fake_db.refund_count(order_id) == 2

    result = evaluate_a1(fake_db, order_id, 100.00)

    assert result == {"status": "FAILED", "invariant": "A1-REFUND-01"}
