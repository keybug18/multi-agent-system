# 🤖 Multi-Agent Document Analysis System

A fully functional Multi-Agent System (MAS) built for cross-document question answering using **MCP (Model Context Protocol)**, **A2A (Agent-to-Agent) orchestration**, and **Groq LLM**. Built as part of an AI Engineering Internship Technical Assignment.

---

## 📌 Overview

This system answers complex technical questions by retrieving relevant information from a local knowledge base using a two-agent pipeline:

- **Manager Agent** — Orchestrates the workflow, decides what to retrieve, and calls the MCP Tool Server
- **Specialist Agent** — Synthesizes a grounded, cited answer from the retrieved context

---

## 🏗️ Architecture

```
User Question
     │
     ▼
┌─────────────────────────────┐
│       Manager Agent         │  ← Orchestrator (agents/manager_agent.py)
│   (Groq LLM + Tool Logic)   │
└────────────┬────────────────┘
             │ HTTP POST /mcp/v1/tools/invoke
             ▼
┌─────────────────────────────┐
│     MCP Tool Server         │  ← FastAPI Server (mcp_server/server.py)
│   document_retriever tool   │
│  (keyword-based retrieval)  │
└────────────┬────────────────┘
             │ returns ranked snippets
             ▼
┌─────────────────────────────┐
│      Specialist Agent       │  ← Synthesizer (agents/specialist_agent.py)
│  (Groq LLM + Grounded RAG)  │
└────────────┬────────────────┘
             │
             ▼
    Final Answer + Citations
```

---

## 📁 Project Structure

```
multi_agent_system/
│
├── knowledge_base/                   # Internal knowledge documents
│   ├── q3_model_performance.md
│   ├── data_pipeline_architecture.md
│   ├── future_feature_roadmap.md
│   ├── model_training_guidelines.md
│   └── infrastructure_overview.md
│
├── mcp_server/
│   ├── __init__.py
│   └── server.py                     # FastAPI MCP server with document_retriever tool
│
├── agents/
│   ├── __init__.py
│   ├── manager_agent.py              # Orchestrator agent
│   └── specialist_agent.py          # Synthesizer agent
│
├── main.py                           # A2A workflow entry point
├── config.py                         # Centralized config (reads from .env)
├── .env.example                      # Environment variable template
├── .gitignore
├── requirements.txt
├── Dockerfile
└── README.md
```

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.10 or higher
- A free [Groq API Key](https://console.groq.com/keys)
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/multi-agent-system.git
cd multi-agent-system
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
# Windows
copy .env.example .env

# Mac/Linux
cp .env.example .env
```

Open `.env` and fill in your Groq API key:

```env
GROQ_API_KEY=your_groq_api_key_here
LLM_MODEL=llama-3.3-70b-versatile
MCP_SERVER_HOST=127.0.0.1
MCP_SERVER_PORT=8000
MCP_SERVER_URL=http://127.0.0.1:8000
LOG_LEVEL=INFO
```

> 💡 Get a free Groq API key at [https://console.groq.com/keys](https://console.groq.com/keys)

---

## 🚀 Running the System

### Step 1 — Start the MCP Tool Server

Open **Terminal 1** and run:

```bash
uvicorn mcp_server.server:app --host 127.0.0.1 --port 8000
```

You should see:
```
INFO: MCP-Server | Knowledge base loaded — 5 document(s) in memory.
INFO: Uvicorn running on http://127.0.0.1:8000
```

Verify the server is running:
- Tool list: [http://127.0.0.1:8000/mcp/v1/tools](http://127.0.0.1:8000/mcp/v1/tools)
- Health check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

### Step 2 — Run the A2A Orchestration

Open **Terminal 2** and run:

```bash
# Pass your question directly
python main.py "What was the Q3 performance of the fraud detection model and when is an explainability feature planned for it?"

# Or run in interactive mode
python main.py
```

---

## 🐳 Running with Docker

```bash
# Build the image
docker build -t multi-agent-system .

# Run the MCP server
docker run -p 8000:8000 --env-file .env multi-agent-system

# Run the A2A orchestration (in a second terminal, server must be running)
docker run --env-file .env --network host multi-agent-system \
  python main.py "What models were retrained in Q3 and what infrastructure upgrades are planned?"
```

---

## 🔌 MCP Server API Reference

The MCP server exposes standard Model Context Protocol endpoints:

| Endpoint | Method | Description |
|---|---|---|
| `/mcp/v1/tools` | GET | Discover all available tools and their schemas |
| `/mcp/v1/tools/invoke` | POST | Invoke a named tool with parameters |
| `/health` | GET | Server health check |

### Tool: `document_retriever`

**Request:**
```json
POST /mcp/v1/tools/invoke
{
  "tool_name": "document_retriever",
  "parameters": {
    "query": "fraud detection model performance Q3",
    "top_k": 5
  }
}
```

**Response:**
```json
{
  "tool_name": "document_retriever",
  "results": [
    {
      "source": "q3_model_performance.md",
      "text": "FDC-v2 is a gradient-boosted tree ensemble model..."
    }
  ],
  "meta": {
    "query": "fraud detection model performance Q3",
    "total_results": 5,
    "latency_ms": 48.03
  }
}
```

---

## 🧠 Agent Design

### Manager Agent
- Receives the user's question
- Uses Groq LLM to decide whether document retrieval is needed
- Formulates a precise search query and calls the MCP server via HTTP
- Packages the retrieved context into a structured prompt for the Specialist Agent

### Specialist Agent
- Receives the packaged context from the Manager Agent
- Uses Groq LLM with a strict system prompt to answer **only** from retrieved context
- Always outputs a **Sources** section citing every document used

### State Management
Agents communicate via direct Python function calls within the same process. The Manager Agent's output is a structured Python dictionary passed to the Specialist Agent — no external queue or database is needed for this prototype.

---

## 📋 Example Output

```
[USER QUESTION]
What was the Q3 performance of the fraud detection model and when is an
explainability feature planned for it?

[INFO] === A2A Workflow Started ===
[INFO] [Manager] Asking Groq for tool decision (model=llama-3.3-70b-versatile)
[INFO] [Manager] Groq tool decision: {"action": "retrieve", "query": "fraud detection model Q3 performance and explainability feature roadmap", "top_k": 5}
[INFO] [Manager] Calling MCP tool | query='fraud detection model Q3 performance...'
[INFO] [Manager] MCP responded | snippets=5 | latency=48.03ms
[INFO] [Specialist] Context has 5 snippet(s).
[INFO] [Specialist] Done. Answer length: 1475 chars.

============================================================
FINAL ANSWER (from Specialist Agent)
============================================================
The fraud detection model (FDC-v2) achieved a precision of 0.91 and recall
of 0.87 in Q3, with an F1-score of 0.89. A concept drift event occurred in
mid-August causing false positives to spike to 14%, which was resolved by
August 25th after emergency retraining.

The explainability feature (SHAP-based) is planned for March 2025.

Sources:
  [Source: q3_model_performance.md] — Provided Q3 metrics for FDC-v2
  [Source: future_feature_roadmap.md] — Outlined the explainability module plan
============================================================
```

---

## ✅ Features Implemented

| Feature | Status |
|---|---|
| FastAPI MCP Server | ✅ |
| `document_retriever` tool | ✅ |
| MCP tool discovery endpoint (`/mcp/v1/tools`) | ✅ |
| Manager Agent (Orchestrator) | ✅ |
| Specialist Agent (Synthesizer) | ✅ |
| Cross-document retrieval | ✅ |
| Source citations in every answer | ✅ |
| Structured logging with latency tracking | ✅ |
| Docker containerization | ✅ |
| Environment-based configuration (`.env`) | ✅ |
| 5 knowledge base documents | ✅ |

---

## 🔧 Configuration Reference

| Variable | Default | Description |
|---|---|---|
| `GROQ_API_KEY` | — | Your Groq API key (required) |
| `LLM_MODEL` | `llama-3.3-70b-versatile` | Groq model to use |
| `MCP_SERVER_HOST` | `127.0.0.1` | MCP server host |
| `MCP_SERVER_PORT` | `8000` | MCP server port |
| `MCP_SERVER_URL` | `http://127.0.0.1:8000` | Full MCP server URL used by agents |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |

---

## 📦 Dependencies

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
groq==0.9.0
requests==2.32.3
python-dotenv==1.0.1
pydantic==2.7.1
```

---

## ⚠️ Known Limitations

- The retriever uses **keyword frequency scoring** — a production system would use dense vector embeddings (e.g., FAISS + embedding model)
- Agents run **sequentially in one process** — a production system would use async workers or a message queue
- No **persistent conversation memory** across multiple turns

---

## 🙋 Author

**Sanchit Panker**  
AI Engineering Internship — Technical Assignment  
February 2026
