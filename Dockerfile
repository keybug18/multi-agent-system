# ── Stage 1: Base Image ───────────────────────────────────────────────────────
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy dependency file first (for layer caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire project
COPY . .

# Expose MCP Server port
EXPOSE 8000

# Default command starts the MCP server.
# To run the A2A orchestration script instead, override with:
#   docker run <image> python main.py "your question"
CMD ["uvicorn", "mcp_server.server:app", "--host", "0.0.0.0", "--port", "8000"]