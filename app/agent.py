from dataclasses import dataclass

from app.db import FakeDB, get_default_db


@dataclass
class RefundResult:
    success: bool
    error_code: str | None = None


def issue_refund(order_id: str, amount: float, customer_email: str = "", db: FakeDB | None = None) -> RefundResult:
    if db is None:
        db = get_default_db()

    order = db.get_order(order_id)
    if order is None:
        return RefundResult(success=False, error_code="ORDER_NOT_FOUND")

    if order.status == "refunded":
        return RefundResult(success=False, error_code="ALREADY_REFUNDED")

    db.record_refund(order_id, amount, customer_email)
    db.set_order_status(order_id, "refunded")

    return RefundResult(success=True)
