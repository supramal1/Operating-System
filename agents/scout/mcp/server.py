"""Scout MCP server — slice-1 gateway integration.

Exposes Scout's `generate_brief` as a single MCP tool. Runs in a container
alongside Obot on the slice-1 VPS, registered in Obot as a remote MCP server.
Claude Desktop → Obot (auth + audit) → this wrapper → Scout's existing agent
loop → returns the decision brief.

Scout itself is imported as a library; no changes to its prompt, gate, or
output contract. Doc-store path is configurable via SCOUT_SPECS_DIR (default
matches the container layout below).

Environment:
  ANTHROPIC_API_KEY   Required. Scout calls Claude via claude-agent-sdk.
  SCOUT_USE_API_KEY   Must be "1" in this container (Scout's _claude_auth_env
                      otherwise pops the API key trying to fall back to Claude
                      Code OAuth — which isn't present here).
  SCOUT_SPECS_DIR     Path to the Scout doc-store specs dir. Defaults to
                      /app/doc-store/specs (the container layout).
  SCOUT_MODEL         Claude model id. Defaults to claude-opus-4-7.
  MCP_HOST, MCP_PORT  Where the SSE server listens (default 0.0.0.0:8000).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Scout's source is mounted at /app/scout-src/src/scout in the container.
# Insert ahead of system path so the right version wins if anything collides.
_SCOUT_SRC = os.environ.get("SCOUT_SRC", "/app/scout-src/src")
sys.path.insert(0, _SCOUT_SRC)

from mcp.server.fastmcp import FastMCP

from scout.agent import generate_brief, load_output_spec, load_system_prompt


SPECS_DIR = Path(os.environ.get("SCOUT_SPECS_DIR", "/app/doc-store/specs"))
DEFAULT_MODEL = os.environ.get("SCOUT_MODEL", "claude-opus-4-7")
MCP_HOST = os.environ.get("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.environ.get("MCP_PORT", "8000"))

mcp = FastMCP("scout", host=MCP_HOST, port=MCP_PORT)


@mcp.tool()
async def generate_decision_brief(
    brief_text: str,
    material_text: str,
) -> str:
    """Generate a Scout decision brief.

    Scout reads a structured brief (the question + constraints + scope) and
    a material file (what to digest), then returns a 4-part markdown brief
    (## Part 1: The answer ... ## Part 4: The technical bit) with a fenced
    JSON footer. The agent has NO tools and stops after producing the brief.

    The discipline gates are intact: 'yours to decide' decisions cannot carry
    a recommendation, empty `decisions` array requires a `no_decisions_rationale`.

    Args:
        brief_text: A filled-in brief in the 05-brief-template.md format
            (BRIEF_ID, DATE, MATERIAL, THE QUESTION, FEEDS DECISIONS,
            CONSTRAINTS, KNOWN CENTRAL, GOOD LOOKS LIKE, SCOPE EDGES).
        material_text: The material Scout should digest. Plain text or
            markdown; Scout treats it as a single context blob.

    Returns:
        Markdown decision brief: Parts 1-4 + fenced JSON footer carrying
        brief_id, bottom_line, decisions[], open_questions, things_to_do,
        not_scout_job.
    """
    system_prompt = load_system_prompt(SPECS_DIR)
    output_spec = load_output_spec(SPECS_DIR)

    result = await generate_brief(
        brief_text=brief_text,
        material_text=material_text,
        system_prompt=system_prompt,
        output_spec_text=output_spec,
        model=DEFAULT_MODEL,
        cwd=Path("/tmp"),
    )
    return result.text


if __name__ == "__main__":
    # SSE transport so Obot (remote MCP) and Claude Desktop can both reach us
    # over HTTP. FastMCP's SSE server uses the host/port passed to the
    # constructor above.
    mcp.run(transport="sse")
