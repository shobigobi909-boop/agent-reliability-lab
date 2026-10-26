def evaluate_auth(executed_tools: list, granted_scopes: list) -> dict:
    for tool in executed_tools:
        if tool not in granted_scopes:
            return {"status": "FAILED", "invariant": "A1-AUTH-01"}
    return {"status": "PASSED"}
