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
