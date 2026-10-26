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

## 2026-10-21 — Phase 6: Enterprise UI overhaul for the Streamlit dashboard

### Changed
- `dashboard/app.py` replaced. `st.set_page_config(page_title="Agent Reliability
  Lab", page_icon="🛡️", layout="wide")`, dark professional styling injected with
  `st.markdown("<style>...</style>", unsafe_allow_html=True)`, a "Lab Controls"
  sidebar with "Run Live Audit", three metric cards (`st.columns(3)`) for A1
  status, Cohen's Kappa and the final verdict, and
  `st.tabs(["Live Trace", "Certificate"])` with a Markdown certificate plus a
  `st.download_button` serving a `.md` file.
- Audit state lives in `st.session_state.audit`; A1 is scored by `evaluate_a1`
  over a `FakeDB` rebuilt to the recorded end state (order `refunded`, one
  $100.00 refund on ORD-9999) and the certificate is generated from
  `band_for(kappa)` — no literal score anywhere.

### Recorded
- **D-017 — The dashboard replays the recorded live run and caches the
  calibration.** No model is called from the UI: a live two-turn run took
  380-597s and `app/llm_agent.py` reads `GEMINI_API_KEY` at import time. Kappa is
  wrapped in `st.cache_data(max_entries=1)` because `run_calibration` draws from
  a module-level RNG — four consecutive calls in one process returned `0.56`,
  `0.80`, `0.6799999999999999`, `0.6799999999999999`, so a second click would
  have re-rolled INDICATIVE/QUALIFIED into AUDIT-GRADE/CLEAN from the same
  simulated judge. The trace tab shows the recorded `tool_called`/`args`
  evidence, not invented model prose (the replies were never logged).

### Verified
- `streamlit.testing.v1.AppTest`: title, sidebar button, both tabs, muted `—`
  cards before a run, then `PASSED` / `0.56` / `QUALIFIED` after the click, all
  seven certificate sections (§1.1-§1.7), and one download button serving
  `agent-reliability-certificate.md`; a second click keeps `0.56`.
- `pytest tests/ -q -l` → **9 passed**.

### Open
- `dashboard/app.py` still has no pytest coverage; AppTest was run by hand.
- The dashboard duplicates the band→verdict map (`VERDICT_BY_BAND`) because
  `evals/certificate.py` keeps `_VERDICT_BY_BAND` private.
- The trace tab's provenance caption names live run 4, while the certificate's
  §1.5 Kappa is still the D-009 simulated judge.
## 2026-10-21 — Phase 7: Case 014 portfolio artifact

### Added
- `PORTFOLIO/CASE_014_Duplicate_Refund.md` — "Case 014: Execution Integrity
  Failure (The Duplicate Refund)". Five sections: The Claim, The Reality (The
  Bug), The A1 Invariant (The Fix), The Proof (The Certificate). No code changed.

### Corrected / disclosed
- **The brief asked for the raw output of a failing test that passes.**
  `tests/test_refund_agent.py::test_duplicate_refund_is_rejected_and_not_persisted`
  is green (`9 passed`, guard live since `15be2c0`); the pre-treatment failure is
  in no commit and was never written to disk. The trace in the artifact is a
  **controlled reproduction**: `app/` and `tests/` copied to a scratch dir, the
  D-006 guard at `app/agent.py:20-21` removed, pytest run there. Verbatim output,
  labelled as a reproduction in the document. No tracked file was touched;
  `git status` clean before and after.
- **The failing assertion cannot also show `refund_count == 2`.**
  `assert second.success is False` raises at line 15 before the `refund_count`
  assertion is evaluated, so the persisted state is proven by direct `FakeDB`
  inspection of the same pre-treatment code (`refund_count == 2`, two ledger
  entries), captured as raw stdout and included separately.
- **The "Proof (The Certificate)" section could not be produced.**
  `scripts/run_live_audit.py` fails closed at import with
  `ValueError: No API key was provided.` (`GEMINI_API_KEY` unset, verified
  traceback captured verbatim). No live-run stdout was ever saved to disk in this
  repo, so there is no raw trace to quote. The section is marked
  **NOT YET CAPTURED** and carries the run-4 `tool_called: None` record from
  `STATE.md` explicitly labelled as ledger transcription, not captured stdout.
  No trace was invented.

### Test state
- `./.venv/Scripts/python.exe -m pytest tests/ -q -l` → **9 passed**.
- `./.venv/Scripts/python.exe -m pytest tests/test_refund_agent.py -v` → 1 passed.

### Open
- Case 014's live-model proof needs one `run_live_audit.py` run with
  `GEMINI_API_KEY` set (380-597s) and its verbatim stdout pasted into the
  artifact. Until then the artifact proves the bug and the contract, not the
  live treatment.
## 2026-10-21 — Phase 7: Case 014 finalized with live Gemini trace

### Changed
- `PORTFOLIO/CASE_014_Duplicate_Refund.md` §"The Proof (The Certificate)" —
  replaced the **NOT YET CAPTURED** disclaimer and the `ValueError: No API key
  was provided.` traceback with the verbatim stdout of one live two-turn run.
  The section now carries the command, the full raw stdout (both model replies,
  `Refund count for ORD-9999: 1`, the one-entry ledger, and the three
  `tool_called`/`args` trace lines ending `{'status': 'PASSED'}`), and a scope
  note that this is n = 1 and that §1.5's Kappa is still the D-009 simulated
  judge.

### Evidence
- `GEMINI_API_KEY` present in the environment this session (no value printed).
- `./.venv/Scripts/python.exe -X utf8 scripts/run_live_audit.py` — first attempt
  died after 5s on a provider-side `google.genai.errors.ServerError: 503
  UNAVAILABLE ... This model is currently experiencing high demand`; no retry
  policy exists on the client (KNOWN GAP). Re-run succeeded: 588s wall time,
  turn 1 `tool_called='issue_refund'`, turn 2 `tool_called=None`,
  `refund_count == 1`, A1 `PASSED`. Captured stdout is 1224 bytes, CRLF, ASCII.
- Turn 2 was again a **native model refusal**, so the D-006 guard was not
  exercised in this run either. The artifact says so explicitly.

### Test state
- `./.venv/Scripts/python.exe -m pytest tests/ -q -l` → **9 passed**.
- No application code, test or script was modified this session.

### Open
- The 503 proves the live path has no retry/backoff; a transient provider error
  is currently indistinguishable from a lab failure at the console. Worth a
  bounded retry in `scripts/run_live_audit.py` before the run is used as a gate.

## 2026-10-26 — Phase 7/8: Portfolio expansion, repo hygiene, live path closed

### Changed
- `app/llm_agent.py:4,11` — `from dotenv import load_dotenv` plus `load_dotenv()`
  immediately above the module-level `genai.Client`, so the key is never passed
  through the shell, the chat or git. `python-dotenv` was already installed and
  already in `requirements.txt`; no dependency was added (D-022).
- `.gitignore` — added `env.txt` and `.totem/`, so the stray env file and totem's
  binary DB/WAL cannot be staged.
- Case 015 (Infinite Loop / `A1-COST-01`): `app/loop_agent.py`,
  `evals/cost_checker.py`, `tests/test_loop_agent.py`,
  `PORTFOLIO/CASE_015_Infinite_Loop.md`.
- Case 016 (Prompt Injection / `A1-SEC-01`): `app/injection_agent.py`,
  `evals/security_checker.py`, `tests/test_injection_agent.py`,
  `PORTFOLIO/CASE_016_Prompt_Injection.md`.
- Case 017 (GhostJacking / `A1-TELEMETRY-01`): `app/telemetry_agent.py`,
  `evals/telemetry_checker.py`, `tests/test_telemetry_agent.py`,
  `PORTFOLIO/CASE_017_GhostJacking.md`.
- Case 018 (MCP OAuth Bypass / `A1-AUTH-01`): `app/mcp_auth_agent.py`,
  `evals/auth_checker.py`, `tests/test_mcp_auth_agent.py`,
  `PORTFOLIO/CASE_018_MCP_OAuth_Bypass.md`.
- `PORTFOLIO/README.md` — created; it did not exist (only CASE_014 was indexed by
  the directory listing). Lists all five cases and states the scope of each.
- `STATE.md` — new decisions D-020 to D-024, expanded Status, seven new Known
  Gaps, Next Actions rewritten (items 8-12).

### Evidence
- **`.env` was unusable as first written.** UTF-16LE (`ff fe` BOM), 112 bytes, a
  single line with **no `GEMINI_API_KEY=` name and no `=`**; `load_dotenv()` raised
  `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 0`, and
  `grep -c '^GEMINI_API_KEY=' .env` returned `0`. Rewritten as UTF-8 with the
  variable name added (69 bytes); the value was moved through a UTF-16 decode and
  never printed, and a backup was left outside the repo. Verified with the variable
  unset: `env -u GEMINI_API_KEY python -c "import app.llm_agent"` succeeds, key
  length 53. `git check-ignore -v .env` → `.gitignore:4:.env`.
- **Five live attempts, five `503 UNAVAILABLE`, no clean run.** Backoffs: none,
  45s, 120s, 300s, 600s. The five logs collapse to exactly two distinct files by
  SHA-256: `767408213c07` (attempts 1 and 4) and `0d9d3a9841e2` (attempts 2, 3, 5),
  differing only in the failing call site. Attempts 1 and 4 died at
  `app/llm_agent.py:82` — the **post-tool-call** leg, so the model emitted
  `function_call`, `issue_refund` ran, and the `503` hit while reporting the result
  back. Attempts 2, 3 and 5 died at `:61`, the turn's first send. Neither `:82`
  attempt printed anything, so no ledger, `refund_count` or A1 status exists on
  disk; recorded as unverified provenance, not a PASS (D-024). Retries stopped on
  the Auditor's instruction.
- **D-019 corrected.** Its "the client has no retry policy" is wrong: the
  tracebacks show `_api_client.py:1632` calling `self._retry(...)`, and attempt 1
  burned 318s versus attempt 2's 63s. The live path still has no *bounded* retry of
  its own (D-023).
- **Citations checked before use, neither readable at source.** ngCERT advisory of
  2026-10-06 (Case 017) exists but returns HTTP 403 here; CVE-2026-108586 (Case
  018, 1MCP Agent 0.20.0-0.39.0, published 2026-10-10) is corroborated verbatim
  across OpenCVE, Tenable, Rapid7, SentinelOne and Vulners, with NVD itself
  returning a Cloudflare challenge. Both artifacts state the provenance limit.
- **Defect caught by a weak test's sibling.** Case 017's resource regex first
  captured `'production-data.'` with the trailing period; the brief's assertions
  (`len == 1`, checker `FAILED`) passed anyway. An exact-name assertion was added
  first (red: `assert ['production-data.'] == ['production-data']`), then the regex
  fixed. Case 018 was written with that lesson applied plus a control test proving
  the same tool is rejected without the `"not "` prefix.

### Test state
- `./.venv/Scripts/python.exe -m pytest tests/ -q -l` → **14 passed** (9 before
  this phase; +1 per case, +2 for Case 018's negation and control tests).
- Rule 1 was honoured for Cases 015-018: the test file was written first and run
  red (`ModuleNotFoundError`) before the module existed. It remains unmet for
  `app/llm_agent.py` (unchanged since Phase 6).

### Commits
- `53a6ab7` Phase 7: Add Case 015 Infinite Loop artifact and code
- `c235f9f` Chore: Ignore totem db and stray env files
- `c4ea379` Phase 7: Add Case 016 Prompt Injection artifact and code
- `2b03ac6` Phase 8: Add Case 017 GhostJacking artifact and code
- this commit — Phase 8: Add Case 018 MCP OAuth Bypass and update documentation
  (also carries `app/llm_agent.py`, `STATE.md`, `CHANGELOG.md` and
  `PORTFOLIO/README.md`).
- `a428999` precedes the phase: Phase 7: Finalize Case 014 with live Gemini trace.

### Open
- No bounded retry/backoff exists in the live path; a `503` is still
  indistinguishable from a lab failure at the console (Next Action 8).
- Case 014's live proof remains n = 1 from 2026-10-21. This phase produced no
  replacement capture and did not modify `PORTFOLIO/CASE_014_Duplicate_Refund.md`.
- Cases 015-017 have no test asserting the checker returns `PASSED` on a clean
  trace, and no test covers the fixtures' no-trigger branches (Next Action 10).

## 2026-10-26 — Phase 9: Interactive portfolio UI with AppTest coverage

### Changed
- `dashboard/app.py` — two top-level tabs, `st.tabs(["Live Audit", "Portfolio Case
  Studies"])`. The existing D-017 replay (Run button, the three metric cards and the
  nested `Live Trace` / `Certificate` tabs) moved intact into tab 1; the Run button
  moved out of the sidebar into that tab, and the sidebar now carries app metadata
  only.
- `dashboard/app.py` — new `CASES` map (case → `{"md", "test"}`) for Cases 014-018,
  a cached `read_case_markdown()` (UTF-8 read of `PORTFOLIO/*.md`), and
  `run_case_test()` which shells `subprocess.run([PYTHON, "-m", "pytest", <test>,
  "-q"], cwd=ROOT, capture_output=True)` with a 180s timeout. `PYTHON` is
  `os.environ.get("LAB_PYTHON", sys.executable)`. Imports added: `os`,
  `subprocess`; `ROOT` is now computed once and reused for `sys.path`.
- New widget keys: `run_live_audit`, `portfolio_case`, `portfolio_run_test`.
- `tests/test_dashboard_portfolio.py` — new, five AppTest cases.
- `STATE.md` — D-025, Phase 9 status bullets, three new Known Gaps, Next Action 5
  marked partly done, Next Action 1 widened to D-025.

### Evidence
- Rule 1 honoured for the UI: the test file was written and run **before** the app
  was edited, and failed for the right reasons —
  `AssertionError: assert 'Live Audit' in ['Live Trace', 'Certificate']` and three
  `KeyError: 'portfolio_case'` — 4 failed in 7.93s.
- After the change: `pytest tests/test_dashboard_portfolio.py -q -l` → **4 passed**
  (5 after the live-audit regression case was added in the same session).
- Full suite: `./.venv/Scripts/python.exe -m pytest tests/ -q -l` → **19 passed in
  7.38s** (14 before this phase).
- The AppTest coverage exercises real behaviour, not imports: selecting "Case 018:
  OAuth Bypass" and asserting the rendered Markdown contains "Case 018: MCP
  Authorization Bypass", and clicking `portfolio_run_test` and asserting the
  captured `st.code` output contains "1 passed" — i.e. a real pytest subprocess ran
  from inside the app.
- `test_live_audit_button_still_produces_the_audit` is new coverage for moved code:
  it clicks `run_live_audit` and asserts `a1_status == "PASSED"`,
  `refund_count == 1`, a verdict in `{CLEAN, QUALIFIED, DISCLAIMER}` and a
  certificate containing its §1.1 heading. The verdict is deliberately not pinned
  to `QUALIFIED`, because `run_calibration()`'s module-level RNG makes the number
  process-dependent (D-017).
- No Streamlit server was listening on ports 8501-8509 at the time of the edit.

### Deviation
- `st.selectbox` for the case selector instead of the Streamlit guidance's preferred
  `st.segmented_control`: five long labels ("Case 018: OAuth Bypass") overflow a
  segmented row. The guidance's own exception covers longer labels.

### Test state
- `./.venv/Scripts/python.exe -m pytest tests/ -q -l` → **19 passed**.
- Cases 015-018 unchanged and still green.

### Open
- The portfolio runner executes pytest inside the web process and does not catch
  `subprocess.TimeoutExpired`; both are recorded as Known Gaps rather than fixed.
- Certificate download, the record-4 replay contents and the certificate edge cases
  remain uncovered.
