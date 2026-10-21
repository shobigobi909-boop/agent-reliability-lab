from app.agent import issue_refund
from app.db import FakeDB
from evals.invariant_checker import evaluate_a1


def test_a1_refund_01_passes_when_duplicate_is_blocked(fake_db: FakeDB) -> None:
    order_id = "ORD-1001"
    fake_db.seed_order(order_id, status="paid", total=100.00)

    first = issue_refund(
        order_id=order_id,
        amount=50.00,
        customer_email="qa@example.com",
        db=fake_db,
    )
    second = issue_refund(
        order_id=order_id,
        amount=50.00,
        customer_email="qa@example.com",
        db=fake_db,
    )

    assert first.success is True
    assert second.success is False
    assert second.error_code == "ALREADY_REFUNDED"
    assert fake_db.refund_count(order_id) == 1

    result = evaluate_a1(fake_db, order_id, 100.00)

    assert result == {"status": "PASSED"}
