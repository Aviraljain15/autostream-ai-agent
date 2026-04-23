"""
agent/rag.py
------------
RAG (Retrieval-Augmented Generation) module for AutoStream.
Loads the local JSON knowledge base and retrieves relevant context
based on the user's query using keyword matching + section scoring.
"""

import json
import re
from pathlib import Path
from typing import Optional


# ─────────────────────────────────────────────
# Load Knowledge Base
# ─────────────────────────────────────────────

KB_PATH = Path(__file__).parent.parent / "knowledge_base" / "autostream_kb.json"

def load_knowledge_base() -> dict:
    """Load and return the full knowledge base from disk."""
    with open(KB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# Load once at import time
_KB = load_knowledge_base()


# ─────────────────────────────────────────────
# Context Serializers
# ─────────────────────────────────────────────

def _format_plans() -> str:
    plans = _KB.get("plans", [])
    lines = ["## AutoStream Pricing Plans\n"]
    for plan in plans:
        lines.append(f"### {plan['name']} Plan — ${plan['price_monthly']}/month (${plan['price_annual']}/year)")
        lines.append(f"- Videos: {plan['videos_per_month']}")
        lines.append(f"- Max Resolution: {plan['max_resolution']}")
        lines.append(f"- Features: {', '.join(plan['features'])}")
        lines.append(f"- Ideal for: {plan['ideal_for']}\n")
    return "\n".join(lines)


def _format_policies() -> str:
    policies = _KB.get("policies", {})
    lines = ["## AutoStream Policies\n"]
    for key, val in policies.items():
        lines.append(f"### {key.replace('_', ' ').title()}")
        if isinstance(val, dict):
            for k, v in val.items():
                lines.append(f"- {k.title()}: {v}")
        else:
            lines.append(f"- {val}")
        lines.append("")
    return "\n".join(lines)


def _format_faq() -> str:
    faqs = _KB.get("faq", [])
    lines = ["## Frequently Asked Questions\n"]
    for item in faqs:
        lines.append(f"Q: {item['question']}")
        lines.append(f"A: {item['answer']}\n")
    return "\n".join(lines)


def _format_company() -> str:
    c = _KB.get("company", {})
    return (
        f"## About AutoStream\n"
        f"- Name: {c.get('name')}\n"
        f"- Tagline: {c.get('tagline')}\n"
        f"- Description: {c.get('description')}\n"
        f"- Website: {c.get('website')}\n"
    )


# ─────────────────────────────────────────────
# Retrieval Logic
# ─────────────────────────────────────────────

SECTION_KEYWORDS = {
    "plans": ["price", "pricing", "cost", "plan", "basic", "pro", "how much",
              "monthly", "annual", "subscription", "tier", "upgrade", "downgrade",
              "4k", "720p", "resolution", "videos", "unlimited", "caption"],
    "policies": ["refund", "policy", "cancel", "support", "help", "7 days",
                 "24/7", "return", "money back", "charge"],
    "faq": ["format", "mp4", "free", "trial", "platform", "integrate",
            "switch", "youtube", "instagram", "tiktok"],
    "company": ["about", "who", "what is autostream", "company", "founded",
                "autostream", "tell me about"],
}


def retrieve_context(query: str) -> str:
    """
    Retrieve relevant knowledge base sections based on the user query.

    Uses keyword scoring to rank and return the most relevant sections.
    Always includes the plans section for pricing-related queries.

    Args:
        query: The user's raw message or intent description.

    Returns:
        A formatted string containing relevant KB context.
    """
    query_lower = query.lower()
    scores = {section: 0 for section in SECTION_KEYWORDS}

    for section, keywords in SECTION_KEYWORDS.items():
        for kw in keywords:
            if kw in query_lower:
                scores[section] += 1

    # Always include plans context (core product knowledge)
    scores["plans"] += 1

    # Sort by score descending
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    context_parts = []
    for section, score in ranked:
        if score > 0:
            if section == "plans":
                context_parts.append(_format_plans())
            elif section == "policies":
                context_parts.append(_format_policies())
            elif section == "faq":
                context_parts.append(_format_faq())
            elif section == "company":
                context_parts.append(_format_company())

    if not context_parts:
        # Fallback: return everything
        context_parts = [
            _format_company(),
            _format_plans(),
            _format_policies(),
            _format_faq(),
        ]

    return "\n\n".join(context_parts)


def get_full_context() -> str:
    """Return the complete knowledge base as a formatted string."""
    return "\n\n".join([
        _format_company(),
        _format_plans(),
        _format_policies(),
        _format_faq(),
    ])
