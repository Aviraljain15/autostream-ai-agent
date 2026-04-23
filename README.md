# ▶ AutoStream — Conversational AI Sales Agent

> An intelligent AI agent for AutoStream's video editing SaaS platform.
> Built using **LangGraph + OpenRouter (GPT-4o-mini)** for stateful multi-turn conversations.

---

## 📁 Project Structure

```
autostream-ai-agent/
│
├── agent/
│   ├── __init__.py
│   ├── nodes.py          # Core agent logic (intent, response, lead flow)
│   ├── graph.py          # LangGraph workflow
│   ├── rag.py            # Knowledge retrieval (RAG)
│   ├── state.py          # Agent state schema
│   ├── tools.py          # Lead capture + validation
│
├── knowledge_base/
│   └── autostream_kb.json
│
├── app.py                # CLI entry point
├── requirements.txt
├── README.md
```

---

## 🧠 Architecture Explanation

This project is built using **LangGraph** to create a structured, stateful conversational AI agent.

LangGraph was chosen because it enables precise control over multi-step workflows such as intent detection, retrieval, and tool execution. Unlike simple chatbots, it allows conditional routing between nodes based on user intent.

The system follows a pipeline:

* Intent classification
* RAG-based retrieval
* Response generation
* Lead collection
* Tool execution

State is maintained using a shared `AgentState` object that stores:

* Conversation history
* Current intent
* Lead information (name, email, platform)
* Flow progress (awaiting fields, completion status)

This ensures continuity across multiple turns.

The RAG system uses a local JSON knowledge base to provide grounded answers for pricing and features.

The lead capture tool is only triggered after all required fields are collected, ensuring correct execution logic.

---

## 🚀 How to Run

### 1. Clone the repository

```
git clone <your-repo-link>
cd autostream-ai-agent
```

---

### 2. Install dependencies

```
pip install -r requirements.txt
```

---

### 3. Add API key

Create a `.env` file:

```
OPENROUTER_API_KEY=your_api_key_here
```

---

### 4. Run the app

```
python app.py
```

---

## 💬 Example Flow

```
User: hi
→ greeting detected

User: tell me about pricing
→ RAG response

User: i want pro plan for youtube
→ high intent detected

User: Aviral Jain
User: aviral@gmail.com
User: youtube
→ lead captured successfully
```

---

## 🤖 Agent Capabilities

### Intent Detection

* greeting
* inquiry
* high_intent
* lead_field

---

### RAG (Retrieval-Augmented Generation)

* Uses local JSON knowledge base
* Provides accurate pricing & features
* Avoids hallucination

---

### Lead Capture Tool

* Collects Name → Email → Platform
* Validates email
* Executes only after full data collection
* Generates Lead ID

---

## 📱 WhatsApp Integration (Using Webhooks)

To integrate this agent with WhatsApp:

1. Use WhatsApp Business API
2. Set up a backend (FastAPI/Flask)
3. Create a webhook endpoint to receive messages
4. Pass incoming messages to the LangGraph agent
5. Return generated responses via WhatsApp API

User sessions can be tracked using phone numbers to maintain state across conversations.

---

## 🔧 Tech Stack

* Python
* LangGraph
* OpenRouter (GPT-4o-mini)
* Local JSON (RAG)
* Rich (CLI UI)

---

## 📄 License

MIT — Built for AutoStream internship evaluation
