# ▶ AutoStream — Conversational AI Sales Agent

> An intelligent AI agent for AutoStream's video editing SaaS platform.
> Built with **Gemini 1.5 Flash** + **LangGraph** for stateful multi-turn conversations.

---

## 📁 Project Structure

```
autostream-agent/
│
├── knowledge_base/
│   └── autostream_kb.json       # RAG knowledge base (pricing, features, policies)
│
├── agent/
│   ├── __init__.py              # Package exports
│   ├── state.py                 # LangGraph AgentState schema
│   ├── rag.py                   # Knowledge retrieval module
│   ├── tools.py                 # mock_lead_capture() + validation helpers
│   ├── nodes.py                 # All 5 LangGraph node functions
│   └── graph.py                 # StateGraph definition + conditional routing
│
├── app.py                       # CLI entry point (rich terminal UI)
├── streamlit_app.py             # Web UI entry point
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variable template
└── README.md                    # This file
```

---

## 🏗️ Architecture

```
User Input
    │
    ▼
┌─────────────────────┐
│   classify_intent   │  ← Gemini classifies: greeting | inquiry | high_intent | lead_field
└─────────┬───────────┘
          │
    ┌─────┴──────────────────────────┐
    │                                │
    ▼                                ▼
┌──────────────┐          ┌─────────────────────┐
│  rag_retrieve │          │  collect_lead_info  │◄──┐
└──────┬───────┘          └──────────┬──────────┘   │
       │                             │               │
       ▼                    all fields?              │
┌──────────────────┐         YES │    NO             │
│ generate_response│             ▼    └──────── (loop, wait for user)
└──────────────────┘   ┌─────────────────────┐
                        │ execute_lead_capture │
                        │  → mock_lead_capture()│
                        └─────────────────────┘
```

---

## 🧠 Key Design Decisions

| Decision  | Choice                       | Why                                            |
| --------- | ---------------------------- | ---------------------------------------------- |
| LLM       | Gemini 1.5 Flash             | Free-tier, fast, reliable for real-time agents |
| Framework | LangGraph                    | Native state management, conditional routing   |
| RAG       | Local JSON + keyword scoring | Lightweight, fast, no vector DB needed         |
| State     | TypedDict                    | Clean multi-turn memory handling               |

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone <your-repo>
cd autostream-agent

pip install -r requirements.txt
```

---

### 2. Set API Key (Gemini)

```bash
cp .env.example .env
```

Edit `.env`:

```env
GOOGLE_API_KEY=your_api_key_here
```

---

### 3. Run (CLI)

```bash
python app.py
```

---

### 4. Run (Web UI)

```bash
streamlit run streamlit_app.py
```

---

## 💬 Example Conversation Flow

```
You  › Hi! Tell me about your pricing.
Maya › AutoStream offers two plans:
       • Basic — $29/month: 10 videos, 720p resolution
       • Pro   — $79/month: Unlimited videos, 4K, AI captions
       Would you like to try Pro free for 14 days?

You  › That sounds great! I want to sign up for Pro for my YouTube channel.
Maya › Amazing! YouTube creators love AutoStream Pro 🚀
       Let's get you set up — what's your name?

You  › Alex Johnson
Maya › Great! And what's the best email address to reach you at?

You  › alex@example.com
Maya › Perfect! Last question — which platform do you primarily create for?

You  › YouTube
Maya › 🎉 You're all set, Alex! Your lead ID is AS-84201.
       Expect a welcome email at alex@example.com shortly!
```

---

## 🧠 Agent Capabilities

### 1. Intent Classification

* **greeting** → small talk
* **inquiry** → pricing, features, policies (RAG)
* **high_intent** → ready to sign up (lead flow)
* **lead_field** → user providing details

---

### 2. RAG Knowledge Retrieval

* Local JSON knowledge base
* Keyword-based retrieval (fast, no embeddings needed)
* Responses grounded strictly in retrieved context

---

### 3. Lead Capture Tool

* Step-by-step collection:

  * Name → Email → Platform
* Email validation + retry
* Tool executes ONLY after all fields collected
* Generates unique Lead ID

---

## 📋 Evaluation Checklist

| Criterion          | Implementation                    |
| ------------------ | --------------------------------- |
| ✅ Intent detection | LLM-based classifier (`nodes.py`) |
| ✅ RAG              | Local JSON + retrieval (`rag.py`) |
| ✅ State management | LangGraph `AgentState`            |
| ✅ Tool calling     | Proper gated execution            |
| ✅ Code structure   | Modular & scalable                |
| ✅ Deployability    | CLI + Streamlit UI                |

---

## 🔧 Tech Stack

* **Language**: Python 3.9+
* **LLM**: Gemini 1.5 Flash (`langchain-google-genai`)
* **Framework**: LangGraph
* **RAG**: Local JSON knowledge base
* **UI**: Rich (CLI), Streamlit (Web)

---

## 📄 License

MIT — Built for AutoStream internship assessment.
