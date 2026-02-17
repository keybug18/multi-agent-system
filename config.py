import os
from dotenv import load_dotenv

load_dotenv()

# LLM Configuration
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
LLM_MODEL: str = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")

# MCP Server Configuration
MCP_SERVER_HOST: str = os.getenv("MCP_SERVER_HOST", "127.0.0.1")
MCP_SERVER_PORT: int = int(os.getenv("MCP_SERVER_PORT", "8000"))
MCP_SERVER_URL: str = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8000")

# Logging
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

# Knowledge base path
KNOWLEDGE_BASE_DIR: str = os.path.join(os.path.dirname(__file__), "knowledge_base")