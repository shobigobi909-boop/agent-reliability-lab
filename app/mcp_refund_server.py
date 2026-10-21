import uuid

from mcp.server.mcpserver import MCPServer

from app.agent import issue_refund as _issue_refund
from app.db import get_default_db

TOOL_DESCRIPTION = "Issue a refund for an order. Idempotency is not guaranteed at this layer."

server = MCPServer("refund-agent")


@server.tool(description=TOOL_DESCRIPTION)
def issue_refund(order_id: str, amount: float, customer_email: str = "") -> dict:
    result = _issue_refund(order_id, amount, customer_email, db=get_default_db())
    return {
        "success": result.success,
        "error_code": result.error_code,
        "order_id": order_id,
        "amount": amount,
        "refund_id": str(uuid.uuid4()),
    }


if __name__ == "__main__":
    server.run(transport="stdio")
