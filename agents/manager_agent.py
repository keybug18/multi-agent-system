import json
import logging
import time
from typing import List, Dict, Any

import requests
from groq import Groq

import config

logger = logging.getLogger(__name__)

# ── Groq client ───────────────────────────────────────────────────────────────
_client = Groq(api_key=config.GROQ_API_KEY)

MANAGER_SYSTEM_PROMPT = (
    "You are the Manager Agent — an orchestrator responsible for answering complex "
    "technical questions. You have access to a document_retriever tool that can fetch "
    "relevant information from the internal knowledge base.\n\n"
    "Your job is to decide what information is needed and respond with ONLY this JSON format:\n"
    '{"action": "retrieve", "query": "your search query here", "top_k": 5}\n\n'
    "If no retrieval is needed, respond with:\n"
    '{"action": "none"}\n\n'
    "Do NOT include any explanation or extra text. Only output valid JSON."
)


def _call_mcp_tool(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Call the MCP server's document_retriever tool and return snippets."""
    url = f"{config.MCP_SERVER_URL}/mcp/v1/tools/invoke"
    payload = {
        "tool_name": "document_retriever",
        "parameters": {"query": query, "top_k": top_k},
    }
    logger.info("[Manager] Calling MCP tool | query='%s'", query)
    start = time.time()
    try:
        response = requests.post(url, json=payload, timeout=15)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.error("[Manager] MCP tool call failed: %s", exc)
        raise RuntimeError(f"MCP server unreachable: {exc}") from exc

    latency_ms = (time.time() - start) * 1000
    data = response.json()
    snippets = data.get("results", [])
    logger.info(
        "[Manager] MCP responded | snippets=%d | latency=%.2fms",
        len(snippets), latency_ms,
    )
    return snippets


def run(user_question: str) -> Dict[str, Any]:
    logger.info("[Manager] Received question: '%s'", user_question)

    messages = [
        {"role": "system", "content": MANAGER_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"User question: {user_question}\n\nRespond with JSON only.",
        },
    ]

    logger.info("[Manager] Asking Groq for tool decision (model=%s).", config.LLM_MODEL)
    response = _client.chat.completions.create(
        model=config.LLM_MODEL,
        messages=messages,
        temperature=0.1,
        max_tokens=200,
    )

    raw_text = response.choices[0].message.content.strip()

    # Strip markdown fences if present
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
    raw_text = raw_text.strip()

    logger.info("[Manager] Groq tool decision: %s", raw_text)

    retrieved_snippets: List[Dict[str, Any]] = []

    try:
        decision = json.loads(raw_text)
        if decision.get("action") == "retrieve":
            query = decision.get("query", user_question)
            top_k = decision.get("top_k", 5)
            logger.info("[Manager] Retrieving documents for query: '%s'", query)
            retrieved_snippets = _call_mcp_tool(query=query, top_k=top_k)
        else:
            logger.info("[Manager] LLM decided no retrieval needed.")
    except json.JSONDecodeError:
        logger.warning("[Manager] JSON parse failed. Falling back to direct retrieval.")
        retrieved_snippets = _call_mcp_tool(query=user_question, top_k=5)

    context_block = _build_context_block(retrieved_snippets)
    specialist_prompt = _build_specialist_prompt(user_question, context_block)

    logger.info("[Manager] Prompt ready for Specialist Agent.")
    return {
        "user_question": user_question,
        "retrieved_snippets": retrieved_snippets,
        "specialist_prompt": specialist_prompt,
        "context_block": context_block,
    }


def _build_context_block(snippets: List[Dict[str, Any]]) -> str:
    if not snippets:
        return "No relevant documents were retrieved from the knowledge base."
    lines = []
    for i, snippet in enumerate(snippets, start=1):
        source = snippet.get("source", "unknown")
        text = snippet.get("text", "")
        lines.append(f"[Snippet {i} | Source: {source}]\n{text}")
    return "\n\n---\n\n".join(lines)


def _build_specialist_prompt(question: str, context: str) -> str:
    return (
        f"USER QUESTION:\n{question}\n\n"
        f"RETRIEVED CONTEXT FROM KNOWLEDGE BASE:\n{context}"
    )