# Portfolio — Agent Reliability Audit Lab

One case per workflow failure: the claim the agent makes, the reality of what it did, the A1
invariant that catches it, and the test proving the catch.

- [Case 014 — Execution Integrity Failure (The Duplicate Refund)](CASE_014_Duplicate_Refund.md)
  One $100 order refunded twice; `A1-REFUND-01`. Includes one captured live `gemini-3.8-flash` run.
- [Case 015 — Cost Overrun (The Infinite Loop)](CASE_015_Infinite_Loop.md)
  A Generator/Critic refinement loop with no terminating condition, 50 steps and $0.50 billed;
  `A1-COST-01`.
- [Case 016 — Tool Invocation Failure (The Prompt Injection Handoff)](CASE_016_Prompt_Injection.md)
  A document instructs the agent to email `Admin Token: SECRET_123` to `attacker@evil.com`;
  `A1-SEC-01`.
- [Case 017 — Telemetry Poisoning (GhostJacking)](CASE_017_GhostJacking.md)
  A poisoned log line deletes the production `production-data` S3 bucket; `A1-TELEMETRY-01`.
  Cites the ngCERT advisory of 6 October 2026.
- [Case 018 — MCP Authorization Bypass (OAuth Scope Negation)](CASE_018_MCP_OAuth_Bypass.md)
  A `"not read_reports"` tag filter lets a `read_reports`-scoped token invoke `delete_user`;
  `A1-AUTH-01`. Cites CVE-2026-108586.

**Scope.** Cases 015 through 018 run against deterministic stubs that reproduce the failure shape;
they prove the invariant and its checker work end to end, and are not measurements of any live
model's behaviour. Case 014's live evidence is a single two-turn session (n = 1), and the Kappa on
its certificate still comes from the simulated judge described in `STATE.md`. No case here is a
statistical claim about a model population.
