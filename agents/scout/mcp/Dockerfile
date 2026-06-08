# Scout MCP server container — slice-1 gateway integration.
#
# Runs Scout as an HTTP/SSE MCP server. Obot registers it as a remote MCP
# server on the same docker network and proxies Claude Desktop requests
# through audit + auth before they reach Scout.
#
# Build context: co-platform/agents/scout/
# Build command (on VPS):  docker build -t scout-mcp:slice1 -f mcp/Dockerfile .

FROM python:3.12-slim

# Node + Claude Code CLI: claude-agent-sdk spawns `claude` as a subprocess for
# the actual LLM call. Without this, Scout's generate_brief fails immediately.
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates gnupg && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    npm install -g @anthropic-ai/claude-code && \
    apt-get purge -y curl gnupg && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Scout's source (read-only at runtime) and the consolidated doc-store.
# Build context root is co-platform/agents/scout/, so doc-store/ is at top of
# context; Scout source is copied from outside the context via build args or
# a pre-build staging step (see build-image.sh).
COPY scout-src/ /app/scout-src/
COPY doc-store/ /app/doc-store/
COPY mcp/server.py /app/server.py

# Python deps: Scout's runtime deps + MCP SDK with FastMCP.
RUN pip install --no-cache-dir \
        "claude-agent-sdk>=0.2.87" \
        "langfuse>=4.7.0" \
        "mcp[cli]>=1.0.0"

ENV PYTHONPATH=/app/scout-src/src \
    PYTHONUNBUFFERED=1 \
    SCOUT_USE_API_KEY=1 \
    SCOUT_SPECS_DIR=/app/doc-store/specs \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=8000

EXPOSE 8000

CMD ["python", "/app/server.py"]
