import logging
from typing import Dict, Any, List

from groq import Groq

import config

logger = logging.getLogger(__name__)

_client = Groq(api_key=config.GROQ_API_KEY)

SPECIALIST_SYSTEM_PROMPT = (
    "You are a meticulous technical analyst. Your job is to synthesize a clear, "
    "concise answer based ONLY on the provided context and the user's question. "
    "Do not use any external knowledge beyond what is explicitly stated in the context.\n\n"
    "CITATION REQUIREMENT:\n"
    "At the end of your answer, include a 'Sources' section that lists every document "
    "snippet you referenced, using the format:\n"
    "  [Source: <filename>] — <one-sentence summary of what that snippet contributed>\n\n"
    "If the context does not contain enough information to answer the question, "
    "clearly state that the information is not available in the knowledge base."
)


def run(manager_output: Dict[str, Any]) -> str:
    specialist_prompt: str = manager_output["specialist_prompt"]
    user_question: str = manager_output["user_question"]
    snippets: List[Dict[str, Any]] = manager_output.get("retrieved_snippets", [])

    logger.info("[Specialist] Synthesizing answer for: '%s'", user_question)
    logger.info("[Specialist] Context has %d snippet(s).", len(snippets))

    messages = [
        {"role": "system", "content": SPECIALIST_SYSTEM_PROMPT},
        {"role": "user", "content": specialist_prompt},
    ]

    response = _client.chat.completions.create(
        model=config.LLM_MODEL,
        messages=messages,
        temperature=0.2,
        max_tokens=1024,
    )

    answer = response.choices[0].message.content.strip()
    logger.info("[Specialist] Done. Answer length: %d chars.", len(answer))
    return answer