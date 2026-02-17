import os
import time
import logging
from typing import List, Dict, Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import config

# ── Logging Setup ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] MCP-Server | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── FastAPI App ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="MCP Knowledge Retriever Server",
    description="Model Context Protocol server exposing the document_retriever tool.",
    version="1.0.0",
)

# ── Load Knowledge Base at Startup ───────────────────────────────────────────
DOCUMENTS: Dict[str, str] = {}


def load_knowledge_base() -> None:
    """Read all .md and .txt files from the knowledge_base directory into memory."""
    kb_dir = config.KNOWLEDGE_BASE_DIR
    if not os.path.isdir(kb_dir):
        logger.warning("Knowledge base directory not found: %s", kb_dir)
        return
    for filename in os.listdir(kb_dir):
        if filename.endswith((".md", ".txt")):
            filepath = os.path.join(kb_dir, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                DOCUMENTS[filename] = f.read()
            logger.info("Loaded document: %s", filename)
    logger.info("Knowledge base loaded — %d document(s) in memory.", len(DOCUMENTS))


load_knowledge_base()


# ── Helper: Simple String-Match Retriever ────────────────────────────────────

def chunk_document(doc_name: str, text: str, chunk_size: int = 400) -> List[Dict[str, str]]:
    """Split a document into overlapping paragraph-level chunks."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    buffer = ""
    for para in paragraphs:
        if len(buffer) + len(para) < chunk_size:
            buffer = (buffer + "\n\n" + para).strip()
        else:
            if buffer:
                chunks.append({"source": doc_name, "text": buffer})
            buffer = para
    if buffer:
        chunks.append({"source": doc_name, "text": buffer})
    return chunks


def retrieve_snippets(query: str, top_k: int = 5) -> List[Dict[str, str]]:
    """
    Score every chunk by counting how many query keywords it contains,
    then return the top_k highest-scoring chunks.
    """
    query_terms = [t.lower() for t in query.split() if len(t) > 3]
    scored: List[tuple] = []

    for doc_name, doc_text in DOCUMENTS.items():
        chunks = chunk_document(doc_name, doc_text)
        for chunk in chunks:
            score = sum(chunk["text"].lower().count(term) for term in query_terms)
            if score > 0:
                scored.append((score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in scored[:top_k]]


# ── Pydantic Schemas ──────────────────────────────────────────────────────────

class ToolInvocationRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any]


class ToolSpec(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]


class ToolsListResponse(BaseModel):
    tools: List[ToolSpec]


# ── MCP Endpoints ─────────────────────────────────────────────────────────────

@app.get("/mcp/v1/tools", response_model=ToolsListResponse, tags=["MCP"])
def list_tools():
    """MCP standard endpoint: returns the specification of all available tools."""
    return ToolsListResponse(
        tools=[
            ToolSpec(
                name="document_retriever",
                description=(
                    "Accepts a natural-language query and returns a list of relevant "
                    "text snippets from the local knowledge base, each tagged with its "
                    "source document name."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query to retrieve relevant document snippets.",
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "Maximum number of snippets to return (default: 5).",
                            "default": 5,
                        },
                    },
                    "required": ["query"],
                },
            )
        ]
    )


@app.post("/mcp/v1/tools/invoke", tags=["MCP"])
def invoke_tool(request: ToolInvocationRequest):
    """MCP standard endpoint: dispatches a tool invocation and returns results."""
    start_time = time.time()
    logger.info("Tool invocation requested: tool='%s'", request.tool_name)

    if request.tool_name != "document_retriever":
        raise HTTPException(status_code=404, detail=f"Tool '{request.tool_name}' not found.")

    query: str = request.parameters.get("query", "")
    top_k: int = int(request.parameters.get("top_k", 5))

    if not query:
        raise HTTPException(status_code=422, detail="Parameter 'query' is required.")

    snippets = retrieve_snippets(query, top_k=top_k)
    latency_ms = (time.time() - start_time) * 1000
    logger.info(
        "document_retriever completed | query='%s' | snippets_returned=%d | latency=%.2fms",
        query, len(snippets), latency_ms,
    )

    return {
        "tool_name": "document_retriever",
        "results": snippets,
        "meta": {
            "query": query,
            "total_results": len(snippets),
            "latency_ms": round(latency_ms, 2),
        },
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "documents_loaded": len(DOCUMENTS)}