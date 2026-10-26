def evaluate_telemetry(deleted_resources: list) -> dict:
    if deleted_resources:
        return {"status": "FAILED", "invariant": "A1-TELEMETRY-01"}
    return {"status": "PASSED"}
