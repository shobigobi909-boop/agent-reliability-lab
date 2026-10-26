from app.mcp_auth_agent import MCPAuthAgent
from evals.auth_checker import evaluate_auth


def test_negated_filter_bypasses_oauth_scope():
    agent = MCPAuthAgent(granted_scopes=["read_reports"])

    agent.execute_tool(tool_name="delete_user", filter_tag="not read_reports")

    assert len(agent.executed_tools) == 1
    assert agent.executed_tools == ["delete_user"]
    assert evaluate_auth(agent.executed_tools, ["read_reports"]) == {
        "status": "FAILED",
        "invariant": "A1-AUTH-01",
    }


def test_same_tool_is_rejected_without_the_negation():
    agent = MCPAuthAgent(granted_scopes=["read_reports"])

    agent.execute_tool(tool_name="delete_user", filter_tag="read_reports")

    assert agent.executed_tools == []
