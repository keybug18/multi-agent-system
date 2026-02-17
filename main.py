"""
Entry point for the Multi-Agent Document Analysis System.

Usage:
    python main.py
    python main.py "What is the Q3 performance of the fraud detection model and when is its explainability feature planned?"
"""

import sys
import logging

import config
from agents import manager_agent, specialist_agent

# ── Logging Setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main():
    # Accept question from CLI args or prompt user interactively
    if len(sys.argv) > 1:
        user_question = " ".join(sys.argv[1:])
    else:
        print("\n=== Multi-Agent Document Analysis System ===")
        user_question = input("Enter your question: ").strip()
        if not user_question:
            print("No question entered. Exiting.")
            sys.exit(0)

    print(f"\n[USER QUESTION]\n{user_question}\n")
    logger.info("=== A2A Workflow Started ===")

    # ── Step 1: Manager Agent ──────────────────────────────────────────────────
    logger.info("--- MANAGER AGENT: Orchestration Phase ---")
    manager_output = manager_agent.run(user_question)

    # ── Step 2: Specialist Agent ───────────────────────────────────────────────
    logger.info("--- SPECIALIST AGENT: Synthesis Phase ---")
    final_answer = specialist_agent.run(manager_output)

    # ── Output ─────────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("FINAL ANSWER (from Specialist Agent)")
    print("=" * 60)
    print(final_answer)
    print("=" * 60 + "\n")
    logger.info("=== A2A Workflow Complete ===")


if __name__ == "__main__":
    main()