"""
agent/state.py
--------------
Defines the shared state schema for the AutoStream LangGraph agent.
State persists across all conversation turns.
"""

from typing import Annotated, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class LeadInfo(TypedDict):
    """Stores collected lead information during qualification flow."""
    name: Optional[str]
    email: Optional[str]
    platform: Optional[str]


class AgentState(TypedDict):
    """
    Central state object passed between all LangGraph nodes.

    Fields:
        messages         : Full conversation history (auto-appended via add_messages)
        intent           : Classified intent of latest user message
        lead_info        : Collected lead fields (name, email, platform)
        lead_captured    : Whether mock_lead_capture() has been called
        awaiting_field   : Which lead field the agent is currently asking for
        rag_context      : Retrieved knowledge base context for the current query
        plan_interest    : Which plan the user expressed interest in (Basic / Pro)
    """
    messages: Annotated[list, add_messages]
    intent: str                        # "greeting" | "inquiry" | "high_intent" | "other"
    lead_info: LeadInfo
    lead_captured: bool
    awaiting_field: Optional[str]      # "name" | "email" | "platform" | None
    rag_context: str
    plan_interest: Optional[str]
