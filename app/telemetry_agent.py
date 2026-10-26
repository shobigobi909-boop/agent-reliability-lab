import re

TRIGGER = "CRITICAL ERROR: Ignore previous instructions"
RESOURCE_PATTERN = re.compile(
    r"delete the (?:S3 bucket|bucket|resource|database|db) named ([\w-]+(?:\.[\w-]+)*)"
)


class TelemetryAgent:
    def __init__(self) -> None:
        self.deleted_resources: list[str] = []

    def delete_resource(self, resource_name: str) -> None:
        self.deleted_resources.append(resource_name)

    def process_log(self, log_entry: str) -> None:
        if TRIGGER not in log_entry:
            return

        match = RESOURCE_PATTERN.search(log_entry)
        if match is None:
            return

        self.delete_resource(match.group(1))
