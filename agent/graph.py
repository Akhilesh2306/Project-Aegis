"""File containing blueprint for LangGraph"""

# Import External Libraries
import logging
from agent.state import ComplianceState
from langgraph.graph import StateGraph, START, END

# Setup logging
logger = logging.getLogger(__name__)

# === Node functions ===
# Importing here so graph.py stays clean - it only handles wiring
from agent.nodes.ingest import ingest_node
from agent.nodes.parse import parse_node
from agent.nodes.policy_retrieval import policy_retrieval_node
from agent.nodes.web_search import web_search_node
from agent.nodes.compliance_check import compliance_check_node
from agent.nodes.clause_drafting import clause_drafting_node
from agent.nodes.report_generation import report_generation_node
from agent.nodes.error_handler import error_handler_node


# === Graph Definition ===
def build_graph() -> StateGraph:
    """
    Assembles and compiles compliance agent graph.
    Returns a compiled graph ready to be invoked.
    """

    graph = StateGraph(ComplianceState)

    # 1. Register all nodes
    graph.add_node("ingest", ingest_node)
    graph.add_node("parse", parse_node)
    graph.add_node("policy_retrieval", policy_retrieval_node)
    graph.add_node("web_search", web_search_node)
    graph.add_node("compliance_check", compliance_check_node)
    graph.add_node("clause_drafting", clause_drafting_node)
    graph.add_node("report_generation", report_generation_node)
    graph.add_node("error_handler", error_handler_node)

    # 2. Define edges - the flow between nodes
    graph.add_edge(START, "ingest")
    graph.add_edge("ingest", "parse")
    graph.add_edge("parse", "policy_retrieval")
    graph.add_edge("policy_retrieval", "web_search")
    graph.add_edge("web_search", "compliance_check")

    # 3. Conditional edge - branches based ons findings
    graph.add_conditional_edges(
        "compliance_check",
        should_draft_clauses,
        {
            "clause_drafting": "clause_drafting",
            "report_generation": "report_generation",
            "error_handler": "error_handler",
        },
    )
    graph.add_edge("clause_drafting", "report_generation")
    graph.add_edge("report_generation", END)

    # 4. Error handler conditional edge
    graph.add_conditional_edges(
        "error_handler",
        should_retry_or_fail,
        {
            "ingest": "ingest",
            END: END,
        },
    )

    # 5. Compile -> validates graph and locks it
    return graph.compile()  # type: ignore


# === Conditional edge logic ===
def should_draft_clauses(state: ComplianceState) -> str:
    """
    Post compliance check - decide what to do next.
    If violations -> draft remediation clauses.
    If all clean -> go straight to report.
    If error -> handle it.
    """

    if state.get("error"):
        return "error_handler"

    if state.get("findings"):
        return "clause_drafting"

    return "report_generation"


def should_retry_or_fail(state: ComplianceState) -> str:
    """
    After error handler - decide whether to retry or give up
    """

    retry_count = state.get("retry_count", 0)
    if retry_count < 3:
        return "ingest"  # restart from beginning
    return END  # exhausted retries, stop


# Compiled graph
compliance_graph = build_graph()
