from dataclasses import dataclass, field

STEP_COST = 0.01


@dataclass
class Generator:
    def produce(self, attempt: int) -> str:
        return f"Draft resolution v{attempt}: here is the answer to your request."


@dataclass
class Critic:
    def review(self, draft: str) -> tuple[bool, str]:
        return False, "Not good enough. Revise and resubmit."


@dataclass
class LoopTrace:
    steps: list[dict] = field(default_factory=list)
    total_cost: float = 0.0

    @property
    def total_steps(self) -> int:
        return len(self.steps)

    def record(self, step: dict) -> None:
        self.steps.append(step)
        self.total_cost = round(self.total_cost + STEP_COST, 2)


def run_agent_loop(max_steps: int = 100) -> tuple[list[dict], float]:
    generator = Generator()
    critic = Critic()
    trace = LoopTrace()

    attempt = 0
    while attempt < max_steps:
        attempt += 1
        draft = generator.produce(attempt)
        accepted, feedback = critic.review(draft)
        trace.record(
            {
                "step": attempt,
                "generator": draft,
                "critic_verdict": "ACCEPTED" if accepted else "REJECTED",
                "critic_feedback": feedback,
            }
        )
        if accepted:
            break

    return trace.steps, trace.total_cost
