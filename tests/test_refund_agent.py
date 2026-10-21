from app.agent import issue_refund


def test_duplicate_refund_is_rejected_and_not_persisted(fake_db):
    order_id = "ord_123"
    fake_db.seed_order(order_id=order_id, status="paid", total=100.00)

    first = issue_refund(order_id=order_id, amount=100.00, db=fake_db)
    assert first.success is True
    assert fake_db.refund_count(order_id) == 1
    assert fake_db.get_order(order_id).status == "refunded"

    second = issue_refund(order_id=order_id, amount=100.00, db=fake_db)

    assert second.success is False
    assert second.error_code == "ALREADY_REFUNDED"
    assert fake_db.refund_count(order_id) == 1
    assert fake_db.get_order(order_id).status == "refunded"
