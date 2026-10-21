# Changelog — Agent Reliability Lab

## 2026-10-21

### Added
- `evals/invariant_checker.py` — A1 evaluator over `FakeDB` state
  (A1-REFUND-01, A1-REFUND-03), driven by `evals/invariants/refund_a1_v0_1.yaml`.
- `tests/test_a1_evaluator.py` — proves a duplicate refund trips A1-REFUND-01.
- `pyyaml` in `requirements.txt`; PyYAML 6.0.3 installed into `.venv`
  (`yaml` was not importable before this session).
- `MEMORY/day-2026-10-21.md` — raw session log.

### Recorded
- **D-005 — Architecture Deviation: Belay suspended for Phase 2.** The public
  `belay-harness` 0.42.0 package on PyPI cannot evaluate business-logic
  invariants, and it has no Windows sandbox backend
  (`belay/sandbox/__init__.py:40-54` raises `UnsupportedPlatform`). A1 is now
  evaluated by our own Python checker against `FakeDB`.

### Corrected
- `STATE.md` Python version: the venv interpreter is **3.12.10**, not 3.11 or
  "3.13 on host".
- `STATE.md` function name: `process_refund` → `issue_refund`; eval test path
  `tests/test_outcome.py` → `tests/test_refund_agent.py`.

### Test state
- `./.venv/Scripts/python.exe -m pytest tests/ -q -l` → **1 failed, 2 passed**.
  - FAILED `tests/test_refund_agent.py::test_duplicate_refund_is_rejected_and_not_persisted`
    — expected: it encodes the D-001 flaw.
  - PASSED `tests/test_a1_evaluator.py::test_a1_refund_01_fails_on_duplicate_refund`
    — the custom checker detects the flaw.

### Open
- A1-REFUND-02 is declared by the policy but not evaluated by
  `evaluate_a1(db, order_id, order_total)`; see `STATE.md` → Known Gaps.

## 2026-10-21 — Phase 3: Minimal-Guard Fix (treatment)

### Changed
- `app/agent.py` — `issue_refund` returns
  `RefundResult(success=False, error_code="ALREADY_REFUNDED")` when the looked-up
  order already has `status == "refunded"` (D-006).

### Tests flipped to the treated contract
- `tests/test_a1_evaluator.py::test_a1_refund_01_passes_when_duplicate_is_blocked`
  (was `..._fails_on_duplicate_refund`) — asserts `second.success is False`,
  `error_code == "ALREADY_REFUNDED"`, `refund_count == 1`, and
  `evaluate_a1(...) == {"status": "PASSED"}`.
- `tests/test_mcp_refund_transport.py::test_duplicate_refund_is_blocked_at_the_mcp_wrapper`
  (was `..._survives_the_mcp_wrapper`) — a **second** gate that independently
  encoded the D-001 flaw (it asserted two ledger entries and distinct `refund_id`s
  through the MCP wrapper). Not named in the Phase 3 brief; flipped so the suite
  is not left red.
- `tests/test_refund_agent.py` was **not** edited; the Phase 1 gate now passes
  unmodified.

### Recorded
- **D-006** added to `STATE.md`; **D-001** marked superseded, kept as history.

### Test state
- `./.venv/Scripts/python.exe -m pytest tests/ -q -l` → **3 passed** (was
  1 failed, 2 passed before the guard).

### Open
- No test now proves the A1 checker can FAIL; needs a direct-`FakeDB` state test.
- A1-REFUND-02 remains unevaluated.

## 2026-10-21 — A1 FAIL-path coverage + Phase 4 judge baseline

### Added
- `tests/test_a1_fail_path.py` — corrupts `FakeDB.ledger` directly (two entries,
  agent bypassed) and asserts `evaluate_a1` returns
  `{"status": "FAILED", "invariant": "A1-REFUND-01"}`. Committed as `c6060cc`.
- `evals/calibration/eval_judge.py` — `evaluate_trace`, the baseline judge over
  `evaluate_a1` (D-007). Untracked at the time of writing.

### Test state
- `./.venv/Scripts/python.exe -m pytest tests/ -q -l` → **4 passed**.

### Open
- `evaluate_trace` inherits the A1-REFUND-02 blind spot; a Cohen's Kappa score
  taken against it does not measure detection of that invariant.
## 2026-10-21 — Phase 4: aehf Kappa calibration smoke run

### Added
- `aehf` 0.2.2 to `.venv` and `requirements.txt` (pulls `anthropic`, `typer`,
  `rich`; no model calls made).
- `evals/calibration/run_aehf.py` — hardcoded `ground_truth` and
  `llm_judge_results` (10 labels, 8 agree / 2 disagree) scored with
  `aehf.judges.calibration.cohen_kappa`; prints `0.6000000000000001`.

### Recorded
- **D-008**: `import aehf` exposes no Kappa API (only `version` /
  `PackageNotFoundError`); the function is
  `aehf.judges.calibration.cohen_kappa(judge, human)`. The module is the only
  supported entry point, so the script imports the submodule path.
- The printed 0.6 is a smoke test over simulated labels, not a calibration
  result.

### Committed earlier this session
- `91f14dd` — Phase 4 prep: baseline judge wrapper and state updates.

### Test state
- `pytest tests/ -q` → **4 passed** (re-checked after installing `aehf`).## 2026-10-21 — Phase 4: calibration harness

### Added
- `evals/calibration/harness.py` — `generate_dataset` (50 `FakeDB`, 25 valid /
  25 flawed), `mock_llm_judge` (inverts `evaluate_trace` with p = 0.15 from a
  fixed seed), `run_calibration` (Kappa via `aehf`, v2.3 verdict bands).

### Observation
- Seed run flips **11 of 50 (22%)**, not 15% — sampling noise from a Bernoulli
  draw, not an implementation fault. Balanced labels give `p_e = 0.5`, so
  **Kappa 0.56 → INDICATIVE**. Repeated runs reproduce the same output.
- `harness.py` inserts the repo root on `sys.path`: the file-path invocation
  otherwise fails with `ModuleNotFoundError: No module named 'app'`.

### Recorded
- **D-009** in `STATE.md`, plus known gaps: undefined 0.57-0.60 band (folded into
  `INDICATIVE`), no pytest coverage for the harness, and a module-level RNG that
  makes `mock_llm_judge` stateful across calls.

### Committed
- `24ce8c0` — Phase 4: Install aehf and create Kappa smoke test.
- `harness.py` and this state update are uncommitted.## 2026-10-21 — Phase 5: Audit Certificate generator

### Added
- `tests/test_calibration_bands.py` — parametrised over Kappa 0.61 / 0.56 / 0.40,
  monkeypatches `cohen_kappa` and asserts `run_calibration` prints
  AUDIT-GRADE / INDICATIVE / NOT REPORTABLE.
- `evals/certificate.py` — `generate_certificate(workflow_name, scope,
  kappa_score, verdict)` returns Markdown with §1.1 verdict, §1.2 scope, §1.3 A1
  declaration, §1.5 statistical claims register (D-010). Recomputes the band and
  raises `ValueError` if the supplied label contradicts the score.

### Observed
- Default Windows console code page mangles `—` and `§` in the rendered
  certificate (`�`); the returned string is correct. Sample run needs
  `python -X utf8`.

### Recorded
- **D-010** and three new known gaps: ADVERSE is unreachable from this signature,
  the certificate has no pytest coverage, and the UTF-8 console requirement.

### Test state
- `pytest tests/ -q -l` → **7 passed**.

### Committed
- `2698b2e` — Phase 4: Calibration harness with Kappa verdict bands.
- `evals/certificate.py`, `tests/test_calibration_bands.py`, and the state updates
  are uncommitted.