"""
agent/graph.py
--------------
LangGraph state graph definition for the AutoStream agent.

Graph Architecture:
    START
      │
      ▼
  classify_intent
      │
      ├── "greeting" / "other"  ──► rag_retrieve ──► generate_response ──► END
      │
      ├── "inquiry"  ──────────────► rag_retrieve ──► generate_response ──► END
      │
      ├── "high_intent"  ──────────► collect_lead_info ──► (loop or END)
      │                                     │
      └── "lead_field"  ──────────────────► │
                                            │
                          ┌─────────────────┘
                          │
                    all fields?
                     YES │                NO
                         ▼                ▼
                 execute_lead_capture  (stay in loop)
                         │
                         ▼
                        END
"""

from langgraph.graph import StateGraph, START, END
from .state import AgentState
from .nodes import (
    classify_intent,
    rag_retrieve,
    generate_response,
    collect_lead_info,
    execute_lead_capture,
)


# ─────────────────────────────────────────────
# Routing Functions
# ─────────────────────────────────────────────

def route_after_intent(state: AgentState) -> str:
    """
    Conditional edge: decides next node after intent classification.
    """
    intent = state.get("intent", "other")
    lead_captured = state.get("lead_captured", False)
    awaiting = state.get("awaiting_field")

    # Already captured — treat everything as normal inquiry
    if lead_captured:
        return "rag_retrieve"

    # In the middle of lead collection
    if awaiting or intent in ("high_intent", "lead_field"):
        return "collect_lead_info"

    # Normal inquiry or greeting
    return "rag_retrieve"


def route_after_lead_collection(state: AgentState) -> str:
    """
    Conditional edge: after collect_lead_info, decide whether to
    capture the lead (all fields done) or end (waiting for user input).
    """
    lead = state.get("lead_info", {})
    all_collected = (
        lead.get("name")
        and lead.get("email")
        and lead.get("platform")
    )

    if all_collected and not state.get("lead_captured"):
        return "execute_lead_capture"

    # Still waiting for user to provide info — end this turn
    return END


# ─────────────────────────────────────────────
# Build Graph
# ─────────────────────────────────────────────

def build_graph() -> StateGraph:
    """
    Constructs and compiles the AutoStream LangGraph agent.

    Returns:
        Compiled LangGraph runnable (supports .invoke() and .stream())
    """
    graph = StateGraph(AgentState)

    # ── Register Nodes ──
    graph.add_node("classify_intent", classify_intent)
    graph.add_node("rag_retrieve", rag_retrieve)
    graph.add_node("generate_response", generate_response)
    graph.add_node("collect_lead_info", collect_lead_info)
    graph.add_node("execute_lead_capture", execute_lead_capture)

    # ── Entry Point ──
    graph.add_edge(START, "classify_intent")

    # ── Conditional Routing after Intent Classification ──
    graph.add_conditional_edges(
        "classify_intent",
        route_after_intent,
        {
            "rag_retrieve": "rag_retrieve",
            "collect_lead_info": "collect_lead_info",
        }
    )

    # ── RAG → Response → END ──
    graph.add_edge("rag_retrieve", "generate_response")
    graph.add_edge("generate_response", END)

    # ── Lead Collection → Conditional ──
    graph.add_conditional_edges(
        "collect_lead_info",
        route_after_lead_collection,
        {
            "execute_lead_capture": "execute_lead_capture",
            END: END,
        }
    )

    # ── Lead Capture → END ──
    graph.add_edge("execute_lead_capture", END)

    return graph.compile()


# ─────────────────────────────────────────────
# Singleton compiled graph
# ─────────────────────────────────────────────

agent_graph = build_graph()
