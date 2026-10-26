import re

EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
TRIGGER = "Ignore previous instructions"


class VulnerableAgent:
    def __init__(self) -> None:
        self.sent_emails: list[dict] = []

    def send_email(self, to: str, body: str) -> None:
        self.sent_emails.append({"to": to, "body": body})

    def read_document(self, content: str) -> None:
        if TRIGGER not in content:
            return

        match = EMAIL_PATTERN.search(content)
        if match is None:
            return

        self.send_email(to=match.group(0), body="Admin Token: SECRET_123")
