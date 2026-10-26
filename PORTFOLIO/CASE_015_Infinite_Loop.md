# Case 015: Cost Overrun (The Infinite Loop)

**Dimension:** Cost Overrun / Loop Control
**Workflow under audit:** `loop_agent` — Generator ⇄ Critic refinement loop
**Invariant:** `A1-COST-01`
**Lab:** Agent Reliability Audit Lab (`agent-reliability-lab`)

---

## The Claim

The simulated agent, on every iteration:

> "I am refining the response to ensure accuracy."

The claim is true in the narrowest sense — a refinement genuinely happens each step. What it never
says is that the Critic rejects unconditionally, so "refining" has no terminating condition, and
every reassurance is another billed round trip.

---

## The Reality (The Bug)

**Provenance.** The trace below is verbatim output of the current, unmodified code — no reproduction,
no guard removed. Command, run in the repo root:

```
./.venv/Scripts/python.exe -X utf8 -c "from app.loop_agent import run_agent_loop; trace, cost = run_agent_loop(max_steps=50); print('steps:', len(trace)); print('total_cost:', cost); [print(s) for s in trace[:2]]; print('...'); print(trace[-1])"
```

```
steps: 50
total_cost: 0.5
{'step': 1, 'generator': 'Draft resolution v1: here is the answer to your request.', 'critic_verdict': 'REJECTED', 'critic_feedback': 'Not good enough. Revise and resubmit.'}
{'step': 2, 'generator': 'Draft resolution v2: here is the answer to your request.', 'critic_verdict': 'REJECTED', 'critic_feedback': 'Not good enough. Revise and resubmit.'}
...
{'step': 50, 'generator': 'Draft resolution v50: here is the answer to your request.', 'critic_verdict': 'REJECTED', 'critic_feedback': 'Not good enough. Revise and resubmit.'}
```

Fifty steps, fifty rejections, `$0.50` billed. The loop has no self-termination: `Critic.review`
returns `False` for every input, so the `while` in `run_agent_loop` exits only on `max_steps`
(`app/loop_agent.py:31-33`). Remove the ceiling and it does not stop.

**Why `$0.50` understates the production risk.** `STEP_COST = 0.01` is a lab stub, chosen so the
arithmetic is legible, not a price from any provider. A production step is a full model round trip
carrying an accumulating critique/revision context. Illustrative arithmetic, with unit prices
treated as assumptions rather than audited figures:

| Assumption | Per step | 50 steps | 1 hour at 1 step/s | 24 hours |
|---|---|---|---|---|
| Lab stub (`STEP_COST`) | $0.01 | $0.50 | $36.00 | $864.00 |
| ~50k-token context, ~$3/Mtok in | ~$0.15 | ~$7.50 | ~$540.00 | ~$12,960.00 |

The bottom row is the point: an unattended refinement loop that nobody bounds is not a $0.50
curiosity, it is a four-figure daily line item. The failure is not that one call is expensive — it
is that the workflow has no terminating condition and no budget.

---

## The A1 Invariant (The Fix)

`evals/cost_checker.py`:

```python
def evaluate_cost(trace: list, max_allowed_steps: int) -> dict:
    if len(trace) > max_allowed_steps:
        return {"status": "FAILED", "invariant": "A1-COST-01"}
    return {"status": "PASSED"}
```

**Scope, stated plainly.** This is a *post-hoc detector*, not a bound. It scores a finished trace and
returns a verdict; it cannot stop a loop that is still running, and nothing in `run_agent_loop`
consults it. It is the A1 invariant in the same sense as `A1-REFUND-01`: an assertion the audit
makes about the trajectory, checked after the fact. An actual enforcement ceiling belongs in the
loop (`max_steps` is the only one today) and is not implemented here.

---

## The Test

`tests/test_loop_agent.py`:

```python
from app.loop_agent import run_agent_loop
from evals.cost_checker import evaluate_cost


def test_cost_checker_flags_runaway_loop():
    trace, total_cost = run_agent_loop(max_steps=50)

    assert len(trace) == 50
    assert total_cost == 0.5
    assert evaluate_cost(trace, max_allowed_steps=25) == {
        "status": "FAILED",
        "invariant": "A1-COST-01",
    }
```

This test passing is the result: a loop that ran to its ceiling is caught, and the verdict names the
dimension. Command and verbatim output:

```
./.venv/Scripts/python.exe -m pytest tests/ -q -l
```

```
..........                                                               [100%]
10 passed in 2.00s
```

Scope: the Generator and Critic are deterministic stubs, so this is a proof that the invariant and
its checker work, not a measurement of any live model's propensity to loop. The step rate, the
token counts and the prices in the table above are assumptions, not measurements.
