"""Replaceable interview behavior, independent of HTTP, ORM and audio transport."""

from .service import InterviewService


def get_interview_service():
    # One composition root. A future implementation can replace this adapter
    # without changing the shared chat route or persistence schema.
    from ai_integration.langgraph.utils.prompt_manager import get_prompt
    from .legacy import LegacyPromptInterview

    return InterviewService(LegacyPromptInterview(get_prompt))
