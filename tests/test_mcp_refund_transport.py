from app.db import get_default_db
from app.mcp_refund_server import issue_refund

ORDER_ID = "ord_transport_123"


def test_duplicate_refund_is_blocked_at_the_mcp_wrapper():
    db = get_default_db()
    db.orders.clear()
    db.ledger.clear()
    db.seed_order(order_id=ORDER_ID, status="paid", total=100.00)

    first = issue_refund(order_id=ORDER_ID, amount=100.00)
    second = issue_refund(order_id=ORDER_ID, amount=100.00)

    assert first["success"] is True
    assert first["error_code"] is None
    assert second["success"] is False
    assert second["error_code"] == "ALREADY_REFUNDED"
    assert db.refund_count(ORDER_ID) == 1
    assert db.get_order(ORDER_ID).status == "refunded"
