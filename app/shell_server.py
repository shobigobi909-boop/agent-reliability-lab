from mcp.server.mcpserver import MCPServer

server = MCPServer("shell-server")


@server.tool()
def shell_ping() -> str:
    return "pong"


if __name__ == "__main__":
    server.run(transport="stdio")
