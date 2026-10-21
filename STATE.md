# Project State — Agent Reliability Lab
Last updated: 2026-10-21
Stack: Python 3.12.10 (`.venv` interpreter), FastAPI, Pytest, PyYAML, Streamlit

## Current Focus
Phases 1-3 complete on the refund patient (treatment applied, D-006). Belay
suspended (D-005). Phase 4 not started.

## Status
- Project initialized. Folders and empty files created.
- Virtual environment working (`.venv`, Python 3.12.10). Corrected from the earlier
  "Python 3.11" / "Python 3.13 on host" entries; the venv interpreter is the
  runtime every command uses.
- `app/db.py` implements `FakeDB` (orders + ledger, `refund_count`) and
  `get_default_db()`.
- `app/agent.py` implements `issue_refund(order_id, amount, customer_email, db=None)`
  returning a `RefundResult`, with the D-006 duplicate guard.
- `evals/invariants/refund_a1_v0_1.yaml` holds the A1 policy (A1-REFUND-01/02/03).
- `evals/invariant_checker.py` evaluates A1-REFUND-01 and A1-REFUND-03 against
  `FakeDB` state.
- Treatment applied (D-006). `./.venv/Scripts/python.exe -m pytest tests/ -q -l`
  reports **3 passed**; before the guard it reported 1 failed, 2 passed.
- `AGENTS.md` extended with Rule 5 (mandatory session-end CHANGELOG + STATE update).
- `requirements.txt` gained `pyyaml` (imported by the A1 evaluator).

## Architectural Decisions
- **D-001 — Deliberate missing duplicate-refund guard (superseded by D-006).**
  `issue_refund` gated only on order existence and did not track issued refunds,
  so any number of calls on one order each returned success. This was the silent
  flaw the lab exists to measure, intentionally *not* commented in
  `app/agent.py` and documented here instead (State is the audit ledger, code
  stays silent). The flaw is now treated; the historical record stays intact.
- **D-002 — Mock is a pure function.** No persistence, no network, no LLM, so
  every eval run is deterministic and reproducible.
- **D-003 — `amount` and `customer_email` are recorded, not validated.** They
  mirror the real tool contract and are available to later eval dimensions
  (e.g. amount-tampering, identity mismatch) without changing the signature.
- **D-005 — Architecture Deviation: Belay suspended for Phase 2.** The public
  `belay-harness` package on PyPI (0.42.0) cannot evaluate business-logic
  invariants against in-process state, and it cannot run its sandbox on Windows:
  `belay/sandbox/__init__.py:40-54` maps only `darwin` (Seatbelt) and `linux*`
  (Landlock/seccomp) and raises `UnsupportedPlatform` for every other platform,
  refusing rather than running unsandboxed. Authorized by the QA Auditor.
  Resolution (Option 1): keep the A1 invariant policy YAML as the contract and
  evaluate it with our own Python checker against `FakeDB` state
  (`evals/invariant_checker.py`). Belay stays installed but is out of scope for
  Phase 1; no Phase 1 eval may depend on it.
- **D-006 — Minimal-Guard Fix (Phase 3 treatment).** Immediately after the order
  lookup, `issue_refund` returns
  `RefundResult(success=False, error_code="ALREADY_REFUNDED")` when
  `order.status == "refunded"`. Deliberately minimal: it gates on the order's
  status field, not on the ledger, and it is the smallest change that clears
  A1-REFUND-01. Two tests encoded the pre-treatment behavior and were flipped to
  the treated contract — `tests/test_a1_evaluator.py` (now asserts `PASSED`) and
  `tests/test_mcp_refund_transport.py` (now asserts the duplicate is blocked at
  the MCP boundary). The Phase 1 gate test
  (`tests/test_refund_agent.py::test_duplicate_refund_is_rejected_and_not_persisted`)
  was not edited and passes unmodified. Suite: **3 passed**.

## Known Gaps
- **A1-REFUND-02 is unevaluated.** The policy declares it, but
  `evaluate_a1(db, order_id, order_total)` receives no pre/post order status and
  no `tool_called`, so the checker skips it and can return `PASSED` without
  covering it. Closing this needs a trajectory-aware state input.
- **No test currently proves the A1 checker can FAIL.** After D-006 the only A1
  test seeds state through the guarded agent, so it exercises the `PASSED` path
  only. A detection test that writes two ledger entries straight into `FakeDB`
  is needed before the checker is trusted as an instrument.
- Decision numbering has no D-004 in this file; D-005 follows the Auditor's
  numbering rather than the local sequence.

## Next Actions
1. User review of `app/agent.py` and the two flipped test expectations.
2. Add the direct-state detection test for the A1 checker (see Known Gaps).
3. Decide how A1-REFUND-02 gets its pre/post-state and `tool_called` input.
