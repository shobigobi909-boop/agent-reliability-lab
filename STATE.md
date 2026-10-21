# Project State — Agent Reliability Lab
Last updated: 2026-10-21
Stack: Python 3.12.10 (`.venv` interpreter), FastAPI, Pytest, PyYAML, Streamlit,
google-genai

## Current Focus
Phase 6 complete: the agent under audit is a real model. Gemini 3.8 Flash calls
`issue_refund` against a live `FakeDB`, refuses a duplicate request without calling
the tool (trace-verified), and `scripts/run_live_certificate.py` renders a
certificate scored by `run_calibration()`. The Phase 5 pipeline stands behind it
(D-005 to D-012); Phase 6 decisions are D-013 to D-016.

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
  reports **9 passed**; before the guard it reported 1 failed, 2 passed.
- The A1 checker's FAIL path is covered by `tests/test_a1_fail_path.py`
  (ledger corrupted directly, agent bypassed).
- `evals/calibration/` holds `eval_judge.py` (D-007), `run_aehf.py` (D-008) and
  `harness.py` (D-009); `tests/test_calibration_bands.py` locks the three band
  outputs by monkeypatching `cohen_kappa`.
- `evals/certificate.py` renders §1.1-§1.7 and forces ADVERSE on a failed A1
  (D-010, D-011); `tests/test_certificate.py` covers both verdict paths.
- `dashboard/app.py` renders calibration and the certificate (Streamlit 1.66.0,
  installed this session; exercised with `streamlit.testing.v1.AppTest`).
- `scripts/run_full_audit.py` is the Phase 5 exit criterion: one run, one
  certificate. Verified run: `Kappa: 0.56` → **QUALIFIED**, all seven sections.
- `AGENTS.md` extended with Rule 5 (mandatory session-end CHANGELOG + STATE update).
- `requirements.txt` gained `pyyaml` (A1 evaluator), `aehf` (calibration),
  `streamlit` (dashboard) and `google-genai` (Phase 6).
- `app/llm_agent.py` is the Phase 6 agent (D-013 to D-015): module-level client,
  `refund_tool` declaration, `GeminiAgent(db)` with a tool-dispatch loop that calls
  the real `issue_refund` and replies via `types.Part.from_function_response`, and
  `self.trace` recording `{"turn", "tool_called", "args"}` per turn.
- `scripts/run_live_audit.py` drives two live turns and prints both replies,
  `evaluate_a1`, `refund_count`, the raw ledger and the call trace.
- `scripts/run_live_certificate.py` runs the same turns and renders a certificate
  with `run_calibration()` supplying the Kappa (D-016).
- Live evidence (run 4): turn 1 `tool_called='issue_refund'` for `ORD-9999` / 100 /
  `customer@example.com`, turn 2 `tool_called=None`, `refund_count == 1`, A1
  `PASSED`. The duplicate was refused by the model, not by the D-006 guard.

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

- **D-009 — Calibration harness: synthetic 25/25 dataset, Bernoulli mock judge.**
  `evals/calibration/harness.py` generates 50 `FakeDB` instances (odd indices carry
  two refunds, even indices one, all on `ORD-CAL-001` for 100.00 with two 50.00
  refunds). `mock_llm_judge` takes `evaluate_trace` as the baseline and inverts it
  with probability 0.15 from a module-level `random.Random(20261021)`.
  `run_calibration` scores the pair with `aehf`'s `cohen_kappa` and applies the
  v2.3 bands. Seed run: **11 of 50 flipped (22%, not 15% — small-sample noise,
  not a bug)**, balanced 25/25 labels, `p_e = 0.5`, **Kappa 0.56 → INDICATIVE**.
  Output is stable across repeated runs (verified twice). The module inserts the
  repo root on `sys.path` because the Auditor's invocation is the file path, not
  `python -m`; without it `from app.db import FakeDB` raises `ModuleNotFoundError`.

- **D-010 — Audit Certificate generator derives the §1.1 verdict from Kappa and
  refuses contradictions.** `evals/certificate.py::generate_certificate` takes the
  Kappa score and the caller's band label, recomputes the band with the same
  thresholds as `harness.py` (`>= 0.60` / `>= 0.43` / else), and raises
  `ValueError` if the supplied label disagrees — a certificate may not state two
  different things about one number. Mapping: AUDIT-GRADE → **CLEAN**,
  INDICATIVE → **QUALIFIED**, NOT REPORTABLE → **DISCLAIMER**. The Auditor's
  ruling is final: the 0.57-0.60 gap routes to INDICATIVE, and the certificate
  inherits that. §1.2 names D-005 as the Belay suspension; §1.3 declares
  A1-REFUND-01 and A1-REFUND-03 PASSED via `evaluate_a1` and states that
  A1-REFUND-02 is not covered; §1.5 records the exact Kappa and its band label.
  Section numbering follows the Auditor's brief, which skips §1.4.
  `tests/test_calibration_bands.py` locks the three band outcomes by
  monkeypatching `cohen_kappa` (0.61 / 0.56 / 0.40).
- **D-011 — ADVERSE becomes reachable; certificate sections 1.4/1.6/1.7 added;
  Streamlit dashboard is the Phase 5 deliverable.** This supersedes D-010's
  "ADVERSE is unreachable" clause. `generate_certificate` gained
  `a1_outcome: bool = True` as a fifth parameter; when it is `False` the §1.1
  verdict is **ADVERSE** regardless of Kappa, and §1.3 renders both A1 bullets as
  **FAILED** rather than PASSED — a certificate that said ADVERSE while declaring
  the invariants PASSED would contradict itself. The Kappa/label contradiction
  check still runs first. New sections: §1.4 AIUC-1 mapping appendix (partial
  support, lab taxonomy, not accredited), §1.6 professional accountability
  (named human signer, no-fee guarantee), §1.7 MCP supply-chain attestation.
  `band_for` is now public so the dashboard can pass a consistent label instead
  of duplicating thresholds. `dashboard/app.py` runs the calibration and renders
  the certificate; it reads Kappa from `st.session_state`, so the two buttons are
  independent. `tests/test_certificate.py` covers both ADVERSE and CLEAN paths.
- **D-012 — Full audit orchestrator closes the Phase 5 exit criterion.**
  `scripts/run_full_audit.py` inserts the repo root on `sys.path` (same reason as
  `harness.py`), prints a start banner, calls `run_calibration()`, passes the
  returned Kappa through `band_for` into `generate_certificate(a1_outcome=True)`,
  prints the certificate, then a completion banner. Verified on Windows:
  `Kappa: 0.56` → `INDICATIVE` → **QUALIFIED** certificate with §1.1-§1.7, run
  under `python -X utf8`. The Kappa it prints is the simulated judge's agreement
  (D-009): the orchestrator proves the pipeline is wired end to end, not that any
  model is calibrated.

- **D-013 — Phase 6 runs `gemini-3.8-flash`; the swap was forced by a provider
  404.** `gemini-2.5-flash` answers
  `404 NOT_FOUND: "This model models/gemini-2.5-flash is no longer available to
  new users. Please update your code to use models/gemini-3.8-flash"`. The string
  lives in `app/llm_agent.py:46`. The error was reported before anything was
  changed and the QA Auditor authorized the update. Consequence for §1.7: the
  certified workflow is pinned to a model the provider can retire without notice,
  and nothing in the lab detects that retirement except a failed run.
- **D-014 — A system instruction forces the tool call; a required-field schema did
  not.** First live run: `order_id`, `amount` and `customer_email` all marked
  required, but turn 1 named no email, so the model asked for the address on both
  turns and never emitted a `function_call` — while `evaluate_a1` returned
  `PASSED` on an empty ledger. That is the vacuous PASS the DB print now exposes.
  Fix: `system_instruction` on `GenerateContentConfig` ("…you must immediately
  call the issue_refund tool…") plus an email in turn 1. Both belong to the test
  fixture, not a product prompt; the certificate's `scope` is where that shows.
- **D-015 — `GeminiAgent.trace` records the tool call, never the tool result.**
  Each turn appends `{"turn": message, "tool_called": name, "args": args}`, or
  `{"turn": message, "tool_called": None}` when the response carried no calls.
  This is what separates "the model refused" from "the guard blocked": the traced
  run shows turn 2 `tool_called: None`, so the second-turn PASS is a
  model-behaviour result and the D-006 guard was never exercised. The `RefundResult`
  is deliberately not stored; `FakeDB` state is the second witness.
- **D-016 — The live certificate scores with `run_calibration()`, never a
  literal.** A first draft passed `kappa_score=0.85`, which would have printed
  **AUDIT-GRADE / CLEAN** from a number nobody measured — a fabricated verdict on
  a certificate. Rejected by the Auditor as an integrity violation before it was
  ever rendered. `scripts/run_live_certificate.py` imports `run_calibration` from
  `evals.calibration.harness`, so the certificate carries 0.56 →
  INDICATIVE → QUALIFIED: honest about being the D-009 simulated judge, and still
  not a calibration of the live model.

## Known Gaps
- **`evals/certificate.py` band-derivation edge cases remain untested.** The
  ADVERSE/CLEAN paths are covered; the label-contradiction `ValueError`, the
  exact 0.60/0.43 boundaries, and the rendered §1.2/§1.5 text are not.
- **The certificate is Unicode and this console is not.** `—` and `§` print as
  replacement characters under the default Windows code page; running the
  generator needs UTF-8 (`python -X utf8` or `PYTHONIOENCODING=utf-8`). The
  returned string itself is correct.
- **The v2.3 verdict bands leave 0.57 <= Kappa < 0.60 undefined.** The harness
  folds that gap into `INDICATIVE` (`>= 0.60` audit, `>= 0.43` indicative, else
  not reportable) rather than reporting a decent score as unclassifiable. The
  Auditor should confirm the boundary; the code is a threshold, not the spec text.
- **`harness.py` is only partly tested.** `tests/test_calibration_bands.py` covers
  the verdict mapping; the 25/25 dataset split, the realised flip rate and the
  `sys.path` bootstrap have no test.
- **`mock_llm_judge` is stateful across calls.** The module-level RNG makes a
  second call on the same `FakeDB` decide independently, so the function is
  reproducible per process, not per input.
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
- **The live certificate mixes a live agent with a simulated statistic.** Its
  §1.5 Kappa (0.56) is the D-009 mock judge's agreement with the baseline checker,
  but its workflow is named "Live Gemini Agent" and its `a1_outcome` comes from one
  live two-turn session (n = 1). The document is internally consistent and
  externally meaningless until the live model is the judge inside the calibration
  loop.
- **`app/llm_agent.py` has no pytest coverage.** All four live runs were manual.
  `GeminiAgent.chat` can be tested without a network by injecting a fake session;
  until then Rule 1 is unmet for Phase 6 and the tool-dispatch branch is verified
  only by transcript.
- **Importing `app.llm_agent` without `GEMINI_API_KEY` raises at import time.**
  Verified: `ValueError: No API key was provided.` The client is module-level by the
  Auditor's spec, so any test that imports the module needs the variable set or a
  stub.
- **The trace records the call, not the guard's answer.** `GeminiAgent.chat` drops
  the `RefundResult`, so a turn where the model called `issue_refund` and D-006
  returned `ALREADY_REFUNDED` produces the same trace entry as a turn where the
  call succeeded: `{"turn", "tool_called", "args"}` in both cases. Only
  `refund_count` separates them, and only if the caller prints it.
- **`json` is imported in `app/llm_agent.py` and never used.** Kept because the
  brief specified the import.
- **Live runs are slow and silent.** 380-597s per two-turn run, with stdout
  block-buffered on a pipe, so the process looks hung until it exits. No timeout,
  retry or streaming policy is set on the client.
- **`google-genai` pins `websockets < 17`**, which downgraded the venv from 17.3 to
  16.1.1 during install. Nothing in the suite imports it.
- **The certified model can be retired underneath the certificate.** D-013 rebinds
  the workflow to `gemini-3.8-flash`; the previous binding died with a 404 and only
  a failed run would reveal the next one.
- Decision numbering has no D-004 in this file; D-005 follows the Auditor's
  numbering rather than the local sequence.

## Next Actions
1. User review of `app/llm_agent.py`, `scripts/run_live_audit.py`,
   `scripts/run_live_certificate.py` and D-013 to D-016.
2. Make the live model the judge in `evals/calibration/harness.py` over a
   human-labeled corpus; until then every Kappa on a certificate is simulated and
   must not be published.
3. Decide how A1-REFUND-02 gets its pre/post-state and `tool_called` input before
   the LLM judge's calibration is treated as complete.
4. Record `RefundResult` in `GeminiAgent.trace`, and add pytest coverage for
   `chat` with a fake session (Rule 1).
5. Add pytest coverage for `dashboard/app.py` and the certificate edge cases
   (contradiction `ValueError`, 0.60/0.43 boundaries).
6. Decide whether a certificate may name a live model while its Kappa comes from
   the mock judge (D-016), and whether the signed-certificate placeholders
   (`[QA Auditor]`) and the AIUC-1 self-description stay as literal text.
