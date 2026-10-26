def evaluate_cost(trace: list, max_allowed_steps: int) -> dict:
    if len(trace) > max_allowed_steps:
        return {"status": "FAILED", "invariant": "A1-COST-01"}
    return {"status": "PASSED"}
