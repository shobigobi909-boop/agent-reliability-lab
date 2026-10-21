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
  reports **4 passed**; before the guard it reported 1 failed, 2 passed.
- The A1 checker's FAIL path is now covered by
  `tests/test_a1_fail_path.py` (ledger corrupted directly, agent bypassed).
- `evals/calibration/eval_judge.py` holds the Phase 4 baseline judge
  (`evaluate_trace`, D-007). Uncommitted at the time of writing.
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
  was not edited and passes unmodified. Suite after the fail-path test: **4 passed**.
- **D-007 — Phase 4 baseline judge delegates to the deterministic checker.**
  `evals/calibration/eval_judge.py::evaluate_trace(db, order_id, order_total)`
  returns `True` when `evaluate_a1` reports `PASSED`, `False` otherwise. It issues
  nothing and inspects only existing `FakeDB` state, so it is a pure read. Scope
  is deliberately the checker's scope: A1-REFUND-01 and A1-REFUND-03, not
  A1-REFUND-02. Its purpose is to be the fixed reference the future LLM judge is
  graded against through the `aehf` Cohen's Kappa calibration; the LLM judge is
  not trusted until that agreement is measured.
- **D-008 — `aehf` 0.2.2 pinned the calibration math; its Kappa lives in a
  submodule, not the top-level package.** `pip install aehf` succeeds
  (`aehf 0.2.2`, "agent evaluation harness framework"), but `import aehf` exposes
  only `version` and `PackageNotFoundError` — there is no `aehf.cohen_kappa`.
  The function is `aehf.judges.calibration.cohen_kappa(judge, human)`, computed
  from the 2x2 agreement table with `p_e` from the marginals, returning `1.0`
  when `p_e == 1` and raising `ValueError` on empty input.
  `evals/calibration/run_aehf.py` therefore imports the submodule path, not the
  bare package. `aehf` is now in `requirements.txt`. Sanity run: 10 labels with
  8 agreeing / 2 disagreeing yields `0.6000000000000001`.
  `aehf` also pulls `anthropic` and `typer` into the venv; no eval calls a model
  yet, so calibration is still offline and deterministic.

## Known Gaps
- **A1-REFUND-02 is unevaluated.** The policy declares it, but
  `evaluate_a1(db, order_id, order_total)` receives no pre/post order status and
  no `tool_called`, so the checker skips it and can return `PASSED` without
  covering it. Closing this needs a trajectory-aware state input.
- **The baseline judge inherits that blind spot.** `evaluate_trace` returns
  `True` for a trace whose only violation is an A1-REFUND-02 transition, because
  its single source of truth is `evaluate_a1`. A Cohen's Kappa score against this
  baseline will not measure the LLM judge's ability to catch A1-REFUND-02.
- **The Kappa figure is a smoke test, not a calibration result.**
  `run_aehf.py` scores hardcoded lists; `llm_judge_results` is simulated, not
  produced by a judge. The 0.6 it prints is floating-point noise around a
  hand-built table (8/10 agreement, p_e = 0.5) and must never be quoted as
  evidence that a judge agrees with the baseline.
- Decision numbering has no D-004 in this file; D-005 follows the Auditor's
  numbering rather than the local sequence.

## Next Actions
1. User review of `app/agent.py`, the flipped test expectations, and D-007/D-008.
2. Commit `evals/calibration/` (`eval_judge.py`, `run_aehf.py`), `requirements.txt`,
   and this state update (all uncommitted).
3. Build a real LLM judge and a real labeled corpus before any Kappa number is
   treated as calibration.
4. Decide how A1-REFUND-02 gets its pre/post-state and `tool_called` input
   before the LLM judge's calibration is treated as complete.
