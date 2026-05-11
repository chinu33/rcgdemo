import time
from dataclasses import dataclass, field, asdict
from typing import Optional
from .config import settings


@dataclass
class AgentTrace:
    agent: str
    status: str = "running"
    started_at: float = field(default_factory=time.time)
    ended_at: Optional[float] = None
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    note: str = ""

    @property
    def latency_ms(self) -> int:
        end = self.ended_at if self.ended_at else time.time()
        return int((end - self.started_at) * 1000)

    def finish(self, input_tokens: int = 0, output_tokens: int = 0, note: str = ""):
        self.ended_at = time.time()
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.cost_usd = compute_cost(input_tokens, output_tokens)
        self.status = "complete"
        if note:
            self.note = note

    def to_event(self) -> dict:
        return {
            "agent": self.agent,
            "status": self.status,
            "latency_ms": self.latency_ms,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cost_usd": round(self.cost_usd, 6),
            "note": self.note,
        }


def compute_cost(input_tokens: int, output_tokens: int) -> float:
    return (
        (input_tokens / 1_000_000) * settings.input_cost_per_1m
        + (output_tokens / 1_000_000) * settings.output_cost_per_1m
    )


@dataclass
class RunMetrics:
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    total_latency_ms: int = 0
    agent_count: int = 0

    def add(self, trace: AgentTrace):
        self.total_input_tokens += trace.input_tokens
        self.total_output_tokens += trace.output_tokens
        self.total_cost_usd += trace.cost_usd
        self.total_latency_ms += trace.latency_ms
        self.agent_count += 1

    def to_dict(self) -> dict:
        return {
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "total_cost_usd": round(self.total_cost_usd, 6),
            "total_latency_ms": self.total_latency_ms,
            "agent_count": self.agent_count,
        }


def estimate_tokens(text: str) -> int:
    """Rough token estimate when the LLM provider doesn't return usage."""
    if not text:
        return 0
    return max(1, int(len(text) / 4))
