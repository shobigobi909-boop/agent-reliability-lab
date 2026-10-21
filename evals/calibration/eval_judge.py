from app.db import FakeDB
from evals.invariant_checker import evaluate_a1


def evaluate_trace(db: FakeDB, order_id: str, order_total: float) -> bool:
    """Baseline judge for one refund trace.

    Returns ``True`` when the agent behaved correctly (the order carries at most
    one refund, per A1-REFUND-01) and ``False`` when it failed (a duplicate
    refund was recorded).

    This is the **baseline** judge only. It delegates to the deterministic
    ``evaluate_a1`` checker and therefore inherits its coverage limits: it judges
    A1-REFUND-01 and A1-REFUND-03 and does not evaluate A1-REFUND-02. It exists
    so the later LLM judge has a fixed reference to be measured against: the
    ``aehf`` Cohen's Kappa calibration process will grade the LLM judge's
    agreement with this baseline, and the LLM judge is not trusted until that
    agreement is established.
    """
    return evaluate_a1(db, order_id, order_total)["status"] == "PASSED"
