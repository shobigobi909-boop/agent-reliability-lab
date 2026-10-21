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
  are uncommitted.## 2026-10-21 — Phase 5: ADVERSE path, certificate sections, Streamlit dashboard

### Added
- `generate_certificate(..., a1_outcome: bool = True)` — `a1_outcome=False`
  forces **ADVERSE** over the Kappa band and renders §1.3 as **FAILED**; the
  label-contradiction `ValueError` still runs first.
- §1.4 AIUC-1 mapping appendix, §1.6 professional accountability, §1.7 MCP
  supply-chain attestation.
- `band_for` is public (was `_band`) so the dashboard passes a consistent label
  instead of duplicating thresholds.
- `tests/test_certificate.py` — ADVERSE and CLEAN paths.
- `dashboard/app.py` — Streamlit UI: Run Calibration button, Kappa metric,
  Generate Certificate button.
- `streamlit` 1.66.0 in `.venv` and `requirements.txt`. Streamlit was named in
  the project stack but had never been installed; the dashboard could not run
  before this.

### Verified
- `streamlit.testing.v1.AppTest`: title renders, both buttons present, the
  calibration click sets the Kappa metric to 0.56, the certificate click renders
  all seven sections (§1.1-§1.7).
- `pytest tests/ -q -l` → **9 passed**.

### Recorded
- **D-011**, superseding D-010's "ADVERSE is unreachable" clause.

### Open
- Band-derivation edge cases (contradiction `ValueError`, 0.60/0.43 boundaries,
  §1.2/§1.5 rendered text) remain untested.
- `dashboard/app.py` has no automated test in the suite; it was exercised with
  AppTest by hand, not committed as a pytest.## 2026-10-21 — Phase 5 exit criterion: end-to-end audit orchestrator

### Added
- `scripts/run_full_audit.py` — start banner, `run_calibration()`,
  `generate_certificate(..., verdict=band_for(kappa), a1_outcome=True)`,
  certificate, completion banner (D-012). Inserts the repo root on `sys.path` for
  the same reason as `harness.py`.

### Verified
- `./.venv/Scripts/python.exe -X utf8 scripts/run_full_audit.py` →
  `Kappa: 0.56`, `INDICATIVE`, **QUALIFIED** certificate with §1.1-§1.7,
  `--- AUDIT RUN COMPLETE ---`.
- `pytest tests/ -q -l` → **9 passed**.

### Committed
- `47f0f0c` — Phase 5: Complete Streamlit dashboard and Certificate sections.

### Open
- The Kappa in the certificate is the simulated judge's agreement (D-009), not a
  calibrated model. The pipeline is proven; the statistic is not evidence.
- `dashboard/app.py` and the certificate edge cases still have no pytest coverage.

## 2026-10-21 — Phase 6: Live Gemini integration (real LLM, traced tool calls)

### Added
- `google-genai` 2.32.0 in `.venv` and `requirements.txt`. Install downgraded
  `websockets` 17.3 → 16.1.1 (`google-genai` pins `<17`); nothing in the suite
  imports it. Verification: `from google import genai` →
  `SDK installed successfully`.
- `app/llm_agent.py` — module-level client, `types.Tool` declaring `issue_refund`
  (`order_id` string, `amount` number, `customer_email` string, all required), and
  `GeminiAgent(db)` around `client.chats.create(...)` with a dispatch loop that
  calls the real `issue_refund` and answers the model through
  `types.Part.from_function_response` (D-013, D-014, D-015).
- `scripts/run_live_audit.py` — two-turn live run over a seeded `FakeDB`, printing
  both replies, `evaluate_a1`, `refund_count`, the raw ledger and the call trace.
- `scripts/run_live_certificate.py` — same two turns, `evaluate_a1` feeds
  `a1_outcome`, and the certificate is rendered with `run_calibration()` as the
  Kappa source (D-016).

### Verified
- SDK surface read from the installed package, not from memory:
  `Part.from_function_response` (`types.py:2536`), `FunctionDeclaration.parameters`
  as `Schema` (`types.py:4872`), `Tool.function_declarations` (`types.py:5401`),
  keyword-only `Chats.create` (`chats.py:590`).
- `genai.Client(api_key=None)` raises `ValueError: No API key was provided.`, so
  the module-level client fails closed when `GEMINI_API_KEY` is unset.
- Run 1 (no email in the prompt): no `function_call` on either turn, empty ledger,
  `evaluate_a1` → `{'status': 'PASSED'}`. Vacuous PASS, reported as such.
- Run 2 (system instruction + email): refund issued, `refund_count == 1`, one
  ledger entry, `{'status': 'PASSED'}`.
- Run 3 (trace): turn 1 `tool_called='issue_refund'` with
  `{'customer_email': 'customer@example.com', 'order_id': 'ORD-9999', 'amount': 100}`;
  turn 2 `tool_called=None`. The model refused the duplicate natively; the D-006
  guard was not exercised.
- `pytest tests/ -q -l` → **9 passed** throughout.

### Recorded
- **D-013** (model `gemini-2.5-flash` → `gemini-3.8-flash`, provider 404),
  **D-014** (system instruction), **D-015** (`self.trace`), **D-016** (live
  certificate uses `run_calibration()`).

### Committed
- `d3ebda0` — Phase 6: Gemini live agent integration and function trace.

### Open
- `GeminiAgent.chat` discards the `RefundResult`, so the trace shows the call but
  not the guard's answer.
- `app/llm_agent.py` has no pytest coverage; all four live runs were manual.
- The live certificate's Kappa is still the D-009 simulated judge, and its
  `a1_outcome` comes from a single live session (n = 1).