"""
app.py
------
AutoStream AI Agent — CLI Entry Point (Gemini Version)

Run with:
    python app.py
"""

import os
import sys
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

# ── Load environment variables ──
load_dotenv(override=True)

# ── Rich terminal UI ──
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich.rule import Rule
    from rich.markdown import Markdown
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from agent import agent_graph
from agent.state import AgentState

console = Console() if RICH_AVAILABLE else None


# ─────────────────────────────────────────────
# Initial State
# ─────────────────────────────────────────────

def create_initial_state() -> AgentState:
    return {
        "messages": [],
        "intent": "other",
        "lead_info": {"name": None, "email": None, "platform": None},
        "lead_captured": False,
        "awaiting_field": None,
        "rag_context": "",
        "plan_interest": None,
    }


# ─────────────────────────────────────────────
# UI Helpers
# ─────────────────────────────────────────────

def print_banner():
    if RICH_AVAILABLE:
        banner = Text()
        banner.append("\n  ▶  AutoStream", style="bold cyan")
        banner.append("  AI Sales & Support Agent\n", style="bold white")
        banner.append("  Powered by Gemini + LangGraph\n", style="dim")

        console.print(Panel(banner, border_style="cyan", padding=(0, 2)))
        console.print(
            "  Type 'quit' or 'exit' to end.\n",
            style="dim"
        )
    else:
        print("\n" + "="*55)
        print("  AutoStream — AI Sales & Support Agent")
        print("  Powered by Gemini + LangGraph")
        print("="*55)
        print("  Type 'quit' or 'exit' to end.\n")


def print_user(text: str):
    if RICH_AVAILABLE:
        console.print(f"\n[bold green]You:[/] {text}")
    else:
        print(f"\nYou: {text}")


def print_agent(text: str):
    if RICH_AVAILABLE:
        console.print(f"\n[bold cyan]Maya:[/] ", end="")
        console.print(Markdown(text))
    else:
        print(f"\nMaya: {text}")


def print_status(label: str, value: str):
    if RICH_AVAILABLE:
        console.print(f"[dim]{label}: {value}[/dim]")


def print_separator():
    if RICH_AVAILABLE:
        console.print(Rule(style="dim cyan"))
    else:
        print("-" * 50)


# ─────────────────────────────────────────────
# Main Loop
# ─────────────────────────────────────────────

def run():
    print_banner()

    state = create_initial_state()

    while True:
        try:
            user_input = console.input("You › ").strip() if RICH_AVAILABLE else input("You › ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit", "bye"):
            print("\nThanks for using AutoStream!")
            break

        print_separator()
        print_user(user_input)

        # Add user message
        state["messages"] = state["messages"] + [HumanMessage(content=user_input)]

        # Run agent
        try:
            state = agent_graph.invoke(state)
        except Exception as e:
            print(f"\n❌ Error: {e}")
            continue

        # Debug info (optional but useful)
        print_status("Intent", state.get("intent"))
        if state.get("awaiting_field"):
            print_status("Awaiting", state.get("awaiting_field"))

        if state.get("lead_captured"):
            print_status("Status", "Lead Captured ✅")

        # Print last AI response
        ai_messages = [m for m in state["messages"] if getattr(m, "type", "") == "ai"]
        if ai_messages:
            print_agent(ai_messages[-1].content)


# ─────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────

if __name__ == "__main__":
    if not os.environ.get("GOOGLE_API_KEY"):
        print("\n❌ ERROR: GOOGLE_API_KEY not set.")
        print("👉 Add this to your .env file:")
        print("GOOGLE_API_KEY=your_key_here\n")
        sys.exit(1)

    run()