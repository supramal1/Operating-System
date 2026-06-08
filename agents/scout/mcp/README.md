# Scout MCP server

Thin MCP wrapper that exposes Scout's `generate_brief` as a single tool. Runs in a container alongside Obot on the slice-1 VPS; Obot registers it as a remote MCP server and proxies Claude Desktop traffic to it.

## Why a wrapper, not Scout's CLI

Scout's CLI writes files to disk. The MCP contract returns the brief content directly to the caller. Wrapping `generate_brief` (the in-process function) bypasses the file-write step — the brief content is the same, no Drive folder needed in the container.

## Architecture

```
Claude Desktop                        Obot                 Scout MCP container
─────────────       MCP/SSE        ────────       MCP/SSE       ─────────────
              ─────────────────▶  Auth+Audit ─────────────▶
                                  Caddy:443         scout-mcp:8000
                                                            │
                                                            ▼
                                                     claude-agent-sdk
                                                            │
                                                            ▼
                                                  https://api.anthropic.com
```

The Scout container has no public exposure — only Obot reaches it via the `obot-net` docker network.

## What this container needs

- **Scout source** (`co-platform/agents/scout/scout-src/` — staged at build time from `…/01-scout/src/`)
- **Doc-store** (`co-platform/agents/scout/doc-store/` — already populated, T1)
- **`ANTHROPIC_API_KEY`** env (injected by docker-compose from `/srv/obot/.env`)
- **`SCOUT_USE_API_KEY=1`** (set in the Dockerfile — bypasses Scout's `_claude_auth_env` Claude Code OAuth fallback)

## Files in this dir

- `Dockerfile` — multi-step build (Node + Claude Code CLI + Python + Scout)
- `server.py` — MCP wrapper (~70 lines, imports Scout's `generate_brief`)
- `README.md` — this file
- (added in T4c) `build-image.sh` — stages Scout's source into the build context, builds image on VPS

## What Scout's container does NOT have

- No Drive folder (the wrapper doesn't write files; MCP returns text)
- No goldens / hand-scores (calibration history stays on the Mac repo; not needed at runtime)
- No Langfuse keys yet — added at T4c if we want gateway-mediated calls traced

## Test plan (T4f)

| Test | Pass condition |
|---|---|
| Container builds | `docker build` exit 0 |
| Container starts | `docker logs scout-mcp` shows "Uvicorn running on …" or equivalent |
| MCP tool list | `curl https://srv1665188.hstgr.cloud/<obot-route>/tools` returns `generate_decision_brief` |
| Direct CLI brief on Mac | `uv run scout --brief X --material Y` writes brief to outputs/ |
| Gateway brief via MCP | Claude Desktop calls `generate_decision_brief(brief, material)`, returns the same content |
| Byte-diff | Content of CLI brief == gateway brief (modulo run-specific fields: trace_id, timestamps) |
| Audit row | New row in Obot's audit log for the gateway call, attributed to the GitHub-OAuth-authenticated user |
