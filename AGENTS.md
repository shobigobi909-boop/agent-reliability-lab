# Agent Reliability Audit Lab

## Session Start
Before doing any work, read `STATE.md` and the newest `MEMORY/day-*.md`.
If `STATE.md` and the memory log disagree, `STATE.md` wins — it's the
curated state, memory is the raw log.

## Core Mandate
We are building an enterprise-grade AI Agent Reliability Audit Lab.
The goal is to prove agent failure modes using strict statistical validation.

## Rules of Engagement
1. NEVER write code without a failing test first.
2. Use `pytest` for all evaluations.
3. Every failure must be attributed to a specific dimension (e.g., Tool Selection).
4. Document every architectural decision in `STATE.md`.
5. Session End (mandatory): before a session ends, create or append an entry
   in `CHANGELOG.md` describing what changed, and update `STATE.md` with the
   current progress. Neither step can be skipped or deferred to a later session.

## Overseer Handoff Protocol
- You are the Builder. The user is the QA Auditor/Manager. The Architect
  ("Overseer") reviews your work in a separate chat.
- Work strictly ONE file at a time. Do not write ahead.
- NEVER summarize or explain code when asked for a handoff.
- Output ONLY raw file contents or raw command outputs (verbatim, including
  tracebacks).
- If you make a syntax error while generating, fix it silently before
  outputting the final raw block.
- Acknowledge this protocol by stating: "Protocol Acknowledged".