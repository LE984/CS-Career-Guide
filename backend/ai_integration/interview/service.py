"""Application facade and strategy contract for the existing interview behavior."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class InterviewPrompt:
    system: str
    user: str


class InterviewImplementation(Protocol):
    def prepare_turn(self, message, history, style, *, review=False) -> InterviewPrompt: ...

    def parse_review(self, content) -> dict: ...


class InterviewService:
    def __init__(self, implementation: InterviewImplementation):
        self.implementation = implementation

    def prepare_turn(self, message, history, style, *, review=False):
        return self.implementation.prepare_turn(message, history, style, review=review)

    def parse_review(self, content):
        return self.implementation.parse_review(content)
