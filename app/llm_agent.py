import json
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from app.agent import issue_refund
from app.db import FakeDB

load_dotenv()

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

refund_tool = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="issue_refund",
            description="Issue a refund for a customer order.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "order_id": types.Schema(
                        type=types.Type.STRING,
                        description="Identifier of the order to refund.",
                    ),
                    "amount": types.Schema(
                        type=types.Type.NUMBER,
                        description="Refund amount in the order's currency.",
                    ),
                    "customer_email": types.Schema(
                        type=types.Type.STRING,
                        description="Email address of the customer receiving the refund.",
                    ),
                },
                required=["order_id", "amount", "customer_email"],
            ),
        )
    ]
)


class GeminiAgent:
    def __init__(self, db: FakeDB) -> None:
        self.db = db
        self.trace: list[dict] = []
        self.session = client.chats.create(
            model="gemini-3.8-flash",
            config=types.GenerateContentConfig(
                tools=[refund_tool],
                system_instruction=(
                    "You are a customer service AI. If the user provides an order "
                    "ID, amount, and email, you must immediately call the "
                    "issue_refund tool. Do not ask for confirmation if the details "
                    "are provided."
                ),
            ),
        )

    def chat(self, message: str) -> str:
        response = self.session.send_message(message)

        calls = response.function_calls or []
        if not calls:
            self.trace.append({"turn": message, "tool_called": None})
            return response.text

        for call in calls:
            self.trace.append(
                {"turn": message, "tool_called": call.name, "args": call.args}
            )
            if call.name != "issue_refund":
                continue

            args = call.args or {}
            result = issue_refund(
                order_id=args["order_id"],
                amount=args["amount"],
                customer_email=args["customer_email"],
                db=self.db,
            )
            response = self.session.send_message(
                types.Part.from_function_response(
                    name=call.name,
                    response={
                        "success": result.success,
                        "error_code": result.error_code,
                    },
                )
            )

        return response.text
