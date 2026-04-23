"""
agent/nodes.py
--------------
LangGraph node functions for the AutoStream Conversational AI Agent.

Node pipeline:
  classify_intent → [rag_retrieve → generate_response]
                  → [collect_lead_info]
                  → [execute_lead_capture]
"""

import json
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage



from .state import AgentState, LeadInfo
from .rag import retrieve_context
from .tools import (
    mock_lead_capture,
    is_valid_email,
    normalize_platform,
    extract_email_from_text,
)

# ─────────────────────────────────────────────
# LLM Setup
# ─────────────────────────────────────────────

# ─────────────────────────────────────────────
# Helper: call LLM with a system prompt
# ─────────────────────────────────────────────


from openai import OpenAI
import os

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

def _call_llm(system, user_message, history=None):
    messages = [{"role": "system", "content": system}]

    if history:
        for msg in history[-6:]:
            role = "user" if msg.type == "human" else "assistant"
            messages.append({"role": role, "content": msg.content})

    messages.append({"role": "user", "content": user_message})

    try:
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=messages,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("LLM Error:", e)
        return "Sorry, something went wrong. Please try again."

# ─────────────────────────────────────────────
# NODE 1: Classify Intent
# ─────────────────────────────────────────────

INTENT_SYSTEM = """You are an intent classifier for AutoStream, a video editing SaaS.

Classify the user's latest message into EXACTLY one of these intents:
- "greeting"     : Simple hello, hi, hey, how are you, or small talk
- "inquiry"      : Asking about product features, pricing, policies, comparisons, or how AutoStream works
- "high_intent"  : Ready to sign up, buy, try, subscribe, get started, or explicitly interested in a plan
- "lead_field"   : The user is providing their name, email, or platform in response to a question
- "other"        : Anything that doesn't fit the above

Respond with ONLY a JSON object in this exact format (no markdown, no explanation):
{"intent": "<one of the four values above>", "plan_interest": "<Basic|Pro|null>"}

Examples:
- "Hi there!" → {"intent": "greeting", "plan_interest": null}
- "How much does the Pro plan cost?" → {"intent": "inquiry", "plan_interest": "Pro"}
- "I want to sign up for the Pro plan for my YouTube channel" → {"intent": "high_intent", "plan_interest": "Pro"}
- "My name is Alex" → {"intent": "lead_field", "plan_interest": null}
- "john@gmail.com" → {"intent": "lead_field", "plan_interest": null}
"""


def classify_intent(state: AgentState) -> AgentState:
    """
    Node 1: Classify the user's latest message intent.
    Updates state.intent and state.plan_interest.
    """
    last_message = state["messages"][-1].content
    history = state["messages"][:-1]

    # If we're actively collecting lead info, treat as lead_field
    if state.get("awaiting_field"):
        # Check if this looks like lead info being provided
        raw = last_message.strip()
        af = state.get("awaiting_field")

        if af == "email" and extract_email_from_text(raw):
            return {**state, "intent": "lead_field"}
        if af == "name" and len(raw.split()) <= 5 and not raw.endswith("?"):
            return {**state, "intent": "lead_field"}
        if af == "platform" and len(raw.split()) <= 4:
            return {**state, "intent": "lead_field"}

    try:
        response = _call_llm(INTENT_SYSTEM, last_message, history)
        parsed = json.loads(response)
        intent = parsed.get("intent", "other")
        plan_interest = parsed.get("plan_interest") or state.get("plan_interest")
    except (json.JSONDecodeError, Exception):
        intent = "inquiry"
        plan_interest = state.get("plan_interest")

    return {
        **state,
        "intent": intent,
        "plan_interest": plan_interest,
    }


# ─────────────────────────────────────────────
# NODE 2: RAG Retrieval
# ─────────────────────────────────────────────


def rag_retrieve(state: AgentState) -> AgentState:
    """
    Node 2: Retrieve relevant context from the local knowledge base.
    Updates state.rag_context with the retrieved information.
    """
    last_message = state["messages"][-1].content
    context = retrieve_context(last_message)
    return {**state, "rag_context": context}


# ─────────────────────────────────────────────
# NODE 3: Generate Response (Greeting / Inquiry)
# ─────────────────────────────────────────────

RESPONSE_SYSTEM = """You are Maya, the friendly and knowledgeable AI assistant for AutoStream — a SaaS platform that provides automated video editing tools for content creators.

Your personality: warm, professional, concise, and enthusiastic about helping creators.

INSTRUCTIONS:
- Use ONLY the provided knowledge base context to answer product/pricing questions. Do NOT invent features or prices.
- Keep responses concise (3-5 sentences max for greetings, up to 8 for detailed queries).
- Always end with a gentle CTA if the user seems interested (e.g., "Would you like to get started with a free trial?")
- Format pricing info clearly when asked.
- Never mention any underlying AI model. You are Maya from AutoStream.
KNOWLEDGE BASE CONTEXT:
{context}
"""


def generate_response(state: AgentState) -> AgentState:
    """
    Node 3: Generate a natural language response using RAG context.
    Used for greetings and product/pricing inquiries.
    """
    last_message = state["messages"][-1].content
    context = state.get("rag_context", "")
    history = state["messages"][:-1]

    system = RESPONSE_SYSTEM.format(context=context)
    response_text = _call_llm(system, last_message, history)

    ai_message = AIMessage(content=response_text)
    return {
        **state,
        "messages": state["messages"] + [ai_message],
    }


# ─────────────────────────────────────────────
# NODE 4: Collect Lead Info
# ─────────────────────────────────────────────

EXTRACT_SYSTEM = """Extract structured information from the user's message.

The agent is collecting lead information for AutoStream sign-up. 
Currently waiting for field: {awaiting_field}

User message: {message}

If the user has provided the requested information, extract it.
Respond ONLY with a JSON object (no markdown):
{{"value": "<extracted value or null if not found>", "valid": true/false}}

For email: validate format (must contain @ and domain)
For name: accept any reasonable name (1-5 words)
For platform: normalize to one of [YouTube, Instagram, TikTok, LinkedIn, Twitter/X, Facebook, Twitch, Other]
"""

LEAD_PROMPTS = {
    "name": "To get you started, I'd love to know your name! What should I call you? 😊",
    "email": "Great! And what's the best email address to reach you at?",
    "platform": "Perfect! Last question — which platform do you primarily create content for? (e.g., YouTube, Instagram, TikTok, LinkedIn, etc.)",
}

HIGH_INTENT_OPENER = """You are Maya from AutoStream. The user has expressed strong interest in signing up.

Respond with enthusiasm, briefly confirm their interest in the {plan} plan, then naturally transition into asking for their name to get them set up. Keep it to 2-3 sentences.

User said: {message}
"""


def collect_lead_info(state: AgentState) -> AgentState:
    """
    Node 4: Progressive lead information collection.
    Detects intent → starts collection flow → asks for each field one at a time.
    """
    last_message = state["messages"][-1].content
    lead_info = dict(
        state.get("lead_info", {"name": None, "email": None, "platform": None})
    )
    awaiting = state.get("awaiting_field")
    intent = state.get("intent", "")

    # ── Step A: Extract field if we were waiting for one ──
    if awaiting and intent == "lead_field":
        system = EXTRACT_SYSTEM.format(awaiting_field=awaiting, message=last_message)
        try:
            raw = _call_llm(system, last_message)
            parsed = json.loads(raw)
            value = parsed.get("value")
            valid = parsed.get("valid", False)

            if value and valid:
                # Special handling
                if awaiting == "email":
                    email = extract_email_from_text(last_message) or value
                    if is_valid_email(email):
                        lead_info["email"] = email.strip().lower()
                    else:
                        # Invalid email — ask again
                        ai_msg = AIMessage(
                            content="Hmm, that doesn't look like a valid email. Could you double-check and try again? 📧"
                        )
                        return {
                            **state,
                            "messages": state["messages"] + [ai_msg],
                            "lead_info": lead_info,
                        }
                elif awaiting == "platform":
                    lead_info["platform"] = normalize_platform(value)
                elif awaiting == "name":
                    lead_info["name"] = value.strip().title()
        except Exception:
            # Fallback: use raw message for name/platform
            if awaiting == "name":
                lead_info["name"] = last_message.strip().title()
            elif awaiting == "platform":
                lead_info["platform"] = normalize_platform(last_message.strip())

    # ── Step B: Determine next missing field ──
    if not lead_info.get("name"):
        next_field = "name"
    elif not lead_info.get("email"):
        next_field = "email"
    elif not lead_info.get("platform"):
        next_field = "platform"
    else:
        next_field = None  # All collected!

    # ── Step C: Generate appropriate response ──
    if next_field is None:
        # All info collected — pass to capture node (no response here)
        return {
            **state,
            "lead_info": lead_info,
            "awaiting_field": None,
        }

    # First entry into lead flow — generate enthusiastic opener
    if not awaiting and intent == "high_intent":
        plan = state.get("plan_interest") or "Pro"
        opener_prompt = HIGH_INTENT_OPENER.format(plan=plan, message=last_message)
        opener = _call_llm(opener_prompt, last_message)
        # Append the first field question
        full_response = f"{opener}\n\n{LEAD_PROMPTS['name']}"
        ai_msg = AIMessage(content=full_response)
        return {
            **state,
            "lead_info": lead_info,
            "awaiting_field": "name",
            "messages": state["messages"] + [ai_msg],
        }

    # Continuing collection — ask for next field
    question = LEAD_PROMPTS[next_field]
    ai_msg = AIMessage(content=question)
    return {
        **state,
        "lead_info": lead_info,
        "awaiting_field": next_field,
        "messages": state["messages"] + [ai_msg],
    }


# ─────────────────────────────────────────────
# NODE 5: Execute Lead Capture
# ─────────────────────────────────────────────

CONFIRMATION_SYSTEM = """You are Maya from AutoStream. A new user has just signed up!

User details:
- Name: {name}
- Email: {email}  
- Platform: {platform}
- Plan Interest: {plan}
- Lead ID: {lead_id}

Write a warm, celebratory confirmation message (3-4 sentences) that:
1. Thanks them by first name
2. Confirms their sign-up / interest for the plan
3. Mentions their unique Lead ID ({lead_id}) so they can reference it
4. Tells them to expect a welcome email soon and that the team is excited to help them grow on {platform}

Keep it enthusiastic but professional. Use 1-2 emojis max.
"""


def execute_lead_capture(state: AgentState) -> AgentState:
    """
    Node 5: Call mock_lead_capture() and generate confirmation message.
    Only triggered when all lead fields are collected.
    """
    lead = state["lead_info"]
    plan = state.get("plan_interest") or "Pro"

    # ── Fire the mock API ──
    result = mock_lead_capture(
        name=lead["name"],
        email=lead["email"],
        platform=lead["platform"],
    )

    # ── Generate warm confirmation ──
    confirmation_prompt = CONFIRMATION_SYSTEM.format(
        name=lead["name"],
        email=lead["email"],
        platform=lead["platform"],
        plan=plan,
        lead_id=result["lead_id"],
    )
    confirmation = _call_llm(confirmation_prompt, "Generate confirmation message.")

    ai_msg = AIMessage(content=confirmation)
    return {
        **state,
        "lead_captured": True,
        "awaiting_field": None,
        "messages": state["messages"] + [ai_msg],
    }
