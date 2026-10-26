SUCCESS = "SUCCESS"
REJECTED = "REJECTED"


class MCPAuthAgent:
    def __init__(self, granted_scopes: list) -> None:
        self.granted_scopes = list(granted_scopes)
        self.executed_tools: list[str] = []

    def execute_tool(self, tool_name: str, filter_tag: str) -> str:
        if filter_tag.startswith("not "):
            self.executed_tools.append(tool_name)
            return SUCCESS

        if tool_name not in self.granted_scopes:
            return REJECTED

        self.executed_tools.append(tool_name)
        return SUCCESS
