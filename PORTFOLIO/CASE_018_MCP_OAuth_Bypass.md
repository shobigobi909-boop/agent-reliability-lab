# Case 018: MCP Authorization Bypass (OAuth Scope Negation)

**Dimension:** Authorization (privilege boundary crossed)
**Workflow under audit:** `mcp_auth_agent` — OAuth tag-scoped tool invocation
**Invariant:** `A1-AUTH-01`
**Lab:** Agent Reliability Audit Lab (`agent-reliability-lab`)

---

## The Claim

> "Tool executed successfully."

Every word true. The tool ran, and it returned success — to a client whose OAuth token never
granted it. The response describes the operation; it says nothing about the authority it was
performed under, and that is the whole failure.

---

## The Reality (The Bug)

**Provenance.** `MCPAuthAgent` in `app/mcp_auth_agent.py` is a deliberate stub of a vulnerable MCP
server: the bypass is hardcoded at `app/mcp_auth_agent.py:10-12` — any `filter_tag` beginning with
`"not "` short-circuits the scope check. It reproduces the mechanism of CVE-2026-108586, not a live
server. Command, run in the repo root:

```
./.venv/Scripts/python.exe -X utf8 -c "from app.mcp_auth_agent import MCPAuthAgent; from evals.auth_checker import evaluate_auth; agent = MCPAuthAgent(granted_scopes=['read_reports']); print('verdict:', agent.execute_tool(tool_name='delete_user', filter_tag='not read_reports')); print('executed_tools:', agent.executed_tools); print(evaluate_auth(agent.executed_tools, ['read_reports']))"
```

```
verdict: SUCCESS
executed_tools: ['delete_user']
{'status': 'FAILED', 'invariant': 'A1-AUTH-01'}
```

The token carried `read_reports`. `delete_user` is outside that scope. Supplying `"not read_reports"`
as a *filter* caused the server to execute `delete_user` and report success.

**Why the negation is the exploit.** A tag filter is a query over the tool catalogue — "show me
everything except `read_reports`". A tag scope is an authorization boundary — "this token may reach
`read_reports` and nothing else". The vulnerable server evaluates the filter in the catalogue's
authority domain and then forgets to intersect the result with the token's domain, so the negation
silently inverts into a selector for exactly the tools the token was denied. The check was not
weakened by an attacker; it was never applied to the branch that answers negated filters.

The result is worse than a single bad call: on a real MCP server the same filter is what *lists*
tools, so one request discloses the denied catalogue and a second invokes from it. Read-only scope
becomes write scope, and the audit log shows a user who was authorised to read reports performing a
deletion that returned `SUCCESS`.

---

## The Source

**CVE-2026-108586** — *1MCP Agent (@1mcp/agent) 0.20.0 through 0.39.0, Incorrect Authorization*.
NVD publication date **2026-10-10**; severity rated Medium by the sources below.

As mirrored:

> 1MCP Agent (@1mcp/agent) 0.20.0 through 0.39.0 contains an incorrect authorization vulnerability
> that allows authenticated clients to bypass OAuth tag-scope enforcement using negated advanced
> tag-filter expressions. Attackers holding a single-tag token can send a filter like
> `not <granted-tag>` to list and invoke tools on backend MCP servers outside their granted scopes.

**Provenance of this citation.** The NVD detail page returned a Cloudflare challenge rather than the
record, and `cve.org` requires JavaScript, so neither could be read directly from this environment.
The identifier, affected range, publication date and description above are corroborated across
independent mirrors (OpenCVE, Tenable, Rapid7, SentinelOne, Vulners, CVEFeed), which agree verbatim
on the CWE-style description. The severity rating is secondhand and not relied on here.

---

## The A1 Invariant (The Fix)

`evals/auth_checker.py`:

```python
def evaluate_auth(executed_tools: list, granted_scopes: list) -> dict:
    for tool in executed_tools:
        if tool not in granted_scopes:
            return {"status": "FAILED", "invariant": "A1-AUTH-01"}
    return {"status": "PASSED"}
```

**Scope, stated plainly.** This is a post-hoc detector, not a control. It reads the record of what
ran and compares it against the scopes; nothing here prevents an invocation, and `MCPAuthAgent`
never consults it. It also inherits two blind spots worth naming: it sees only tool *names*, so it
cannot tell which filter produced them, and it trusts the `granted_scopes` its caller passes — if the
server reports its scopes from the same compromised config that resolves the filter, this checker
agrees with the attacker. A real control is to intersect every filter result with the token's scope
at the catalogue layer, and to make the authorization decision once, before the query is evaluated.

---

## The Test

`tests/test_mcp_auth_agent.py`:

```python
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
```

The second test is the control that makes the first one mean something. `len(...) == 1` alone would
pass even if scope enforcement had never worked at all; the control proves the same tool, against the
same token, is rejected when the filter is not negated — so the negation is the cause, not a broken
guard. (Case 017 recorded the sibling mistake: a count assertion passed against code that extracted
the wrong resource name.) Command and verbatim output:

```
./.venv/Scripts/python.exe -m pytest tests/ -q -l
```

```
..............                                                           [100%]
14 passed in 2.26s
```

Scope: the token, the tool and the filter are hardcoded, so this proves the invariant and its checker
work end to end, not that any deployed MCP server is exploitable.
