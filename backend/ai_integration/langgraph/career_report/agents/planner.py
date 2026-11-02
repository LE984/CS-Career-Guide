from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, TypedDict
from django.conf import settings

from langgraph.graph import END, StateGraph

from ai_integration.langgraph.career_report.agents.growth_agent import run_growth_agent
from ai_integration.langgraph.career_report.agents.market_agent import run_market_agent
from ai_integration.langgraph.career_report.agents.profile_agent import run_profile_agent
from ai_integration.langgraph.career_report.agents.strategy_agent import run_strategy_agent


class PlannerState(TypedDict):
    user_profile: Dict[str, Any]
    target_job: str
    partials: Dict[str, Any]
    report: Dict[str, Any]
    errors: Dict[str, str]


def _run_agents_node(state: PlannerState) -> PlannerState:
    user_profile = state["user_profile"]
    target_job = state["target_job"]

    jobs = {
        "profile": lambda: run_profile_agent(user_profile, target_job),
        "growth": lambda: run_growth_agent(user_profile, target_job),
        "market": lambda: run_market_agent(user_profile, target_job),
        "strategy": lambda: run_strategy_agent(user_profile, target_job),
    }

    partials: Dict[str, Any] = {}
    errors: Dict[str, str] = {}

    with ThreadPoolExecutor(max_workers=settings.CAREER_REPORT_MAX_WORKERS) as executor:
        future_map = {executor.submit(fn): key for key, fn in jobs.items()}
        for future in as_completed(future_map):
            key = future_map[future]
            try:
                partials[key] = future.result()
            except Exception as exc:
                errors[key] = str(exc)
                partials[key] = {}

    state["partials"] = partials
    state["errors"] = errors
    return state


def _merge_report_node(state: PlannerState) -> PlannerState:
    partials = state.get("partials", {})
    profile = partials.get("profile", {}).get("profile", {})
    growth_root = partials.get("growth", {})
    market = partials.get("market", {}).get("market", {})
    strategy = partials.get("strategy", {}).get("strategy", {})

    report = {
        "summary": {
            "target_job": state.get("target_job"),
            "profile_highlight": profile.get("talent_portrait", ""),
            "market_heat": market.get("market_heat", ""),
            "key_risk": (strategy.get("risk_alerts") or [""])[0],
        },
        "profile": profile,
        "growth_plan": growth_root.get("growth_plan", {}),
        "market": market,
        "strategy": strategy,
        "weekly_plan": growth_root.get("weekly_plan", {}),
        "monthly_plan": growth_root.get("monthly_plan", {}),
    }

    state["report"] = report
    return state


def create_planner_graph():
    graph = StateGraph(PlannerState)
    graph.add_node("planner_run_agents", _run_agents_node)
    graph.add_node("report_merge", _merge_report_node)
    graph.set_entry_point("planner_run_agents")
    graph.add_edge("planner_run_agents", "report_merge")
    graph.add_edge("report_merge", END)
    return graph.compile()
