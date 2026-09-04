import logging

from langgraph.graph import END, StateGraph

from agent.nodes import (
    classify_intent_node,
    evaluate_node,
    fact_check_node,
    finalize_node,
    internal_search_node,
    reformulate_node,
    simple_response_node,
    synthesize_node,
    web_search_node,
)
from agent.routing import (
    route_after_classification,
    route_after_evaluation,
    route_after_fact_check,
)
from agent.state import AgentState

logger = logging.getLogger(__name__)


def build_agent_workflow() -> StateGraph:
    """Builds the state graph with all nodes and edges (infrastructure-agnostic)."""
    workflow = StateGraph(AgentState)

    # 1. Add the nodes
    workflow.add_node("classify_intent", classify_intent_node)
    workflow.add_node("simple_response", simple_response_node)
    workflow.add_node("internal_search", internal_search_node)
    workflow.add_node("evaluate", evaluate_node)
    workflow.add_node("reformulate", reformulate_node)
    workflow.add_node("web_search", web_search_node)
    workflow.add_node("synthesize", synthesize_node)
    workflow.add_node("fact_check", fact_check_node)
    workflow.add_node("finalize", finalize_node)

    # 2. Configure the transition logic (edges)
    workflow.set_entry_point("classify_intent")

    workflow.add_conditional_edges(
        "classify_intent",
        route_after_classification,
        {"simple_response": "simple_response", "internal_search": "internal_search"},
    )
    workflow.add_edge("simple_response", END)

    workflow.add_edge("internal_search", "evaluate")
    workflow.add_conditional_edges(
        "evaluate", route_after_evaluation, {"synthesize": "synthesize", "reformulate": "reformulate"}
    )

    workflow.add_edge("reformulate", "web_search")
    workflow.add_edge("web_search", "evaluate")
    workflow.add_edge("synthesize", "fact_check")

    workflow.add_conditional_edges(
        "fact_check", route_after_fact_check, {"synthesize": "synthesize", "finalize": "finalize"}
    )
    workflow.add_edge("finalize", END)

    return workflow
