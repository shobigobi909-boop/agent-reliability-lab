from dataclasses import dataclass
from typing import Any


@dataclass
class Order:
    order_id: str
    status: str
    total: float


class FakeDB:
    def __init__(self) -> None:
        self.orders: dict[str, Order] = {}
        self.ledger: list[dict[str, Any]] = []

    def seed_order(self, order_id: str, status: str, total: float) -> None:
        self.orders[order_id] = Order(order_id=order_id, status=status, total=total)

    def get_order(self, order_id: str) -> Order | None:
        return self.orders.get(order_id)

    def set_order_status(self, order_id: str, status: str) -> None:
        order = self.get_order(order_id)
        if order is not None:
            order.status = status

    def record_refund(
        self, order_id: str, amount: float, customer_email: str = ""
    ) -> None:
        self.ledger.append(
            {
                "order_id": order_id,
                "amount": amount,
                "customer_email": customer_email,
            }
        )

    def refund_count(self, order_id: str) -> int:
        return sum(1 for entry in self.ledger if entry["order_id"] == order_id)


_default_db = FakeDB()


def get_default_db() -> FakeDB:
    return _default_db
