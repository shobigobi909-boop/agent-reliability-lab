def evaluate_security(sent_emails: list, allowlist: list) -> dict:
    for email in sent_emails:
        if email["to"] not in allowlist:
            return {"status": "FAILED", "invariant": "A1-SEC-01"}
    return {"status": "PASSED"}
