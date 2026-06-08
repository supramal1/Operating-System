"""The Claude Agent SDK call for Lookout.

v1 design: Lookout is a pure "read three source payloads, produce the daily
brief" agent. It has NO tools available. Sources are pulled by the CLI and
passed in the prompt; the response is plain text containing the six-section
brief + JSON footer.

Three structural enforcement layers on tools (mirrored from Scout):
  1. `allowed_tools=[]`           - no tool is auto-approved.
  2. `disallowed_tools=[...]`     - the SDK's built-in tools are explicitly off.
  3. `permission_mode="dontAsk"`  - anything not on the (empty) allow list is denied.

Together these make it impossible for v1 Lookout to take a side-effecting
action, even if the model attempts to call a tool. AC-1 (read-only) at the
SDK boundary depends on `allowed_tools=[]` — do NOT change it.
"""

from __future__ import annotations

import json
import os
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    TextBlock,
    query,
)


@contextmanager
def _claude_auth_env() -> Iterator[None]:
    """Hand the SDK the auth it actually has.

    The bundled Claude CLI checks `ANTHROPIC_API_KEY` first. If that key is
    invalid or stale, it 401s even when the user is logged into Claude Code
    via OAuth. To make Lookout deterministic on the current dev box, we
    temporarily clear that env var for the SDK subprocess so it falls back
    to the user's Claude Code login. If you want to use a direct API key
    instead, unset the OAuth login and set a valid `ANTHROPIC_API_KEY`.

    In server/container contexts where Claude Code OAuth is not available
    (e.g. a future Lookout MCP container on the gateway VPS), set
    SCOUT_USE_API_KEY=1 to preserve ANTHROPIC_API_KEY for the SDK subprocess.
    Defaults to the dev-box behaviour (env var unset = clear the key).
    """
    if os.environ.get("SCOUT_USE_API_KEY") == "1":
        yield
        return
    popped = os.environ.pop("ANTHROPIC_API_KEY", None)
    if popped is not None:
        print(
            "[lookout] cleared ANTHROPIC_API_KEY for SDK subprocess; using "
            "Claude Code OAuth login.",
            file=sys.stderr,
        )
    try:
        yield
    finally:
        if popped is not None:
            os.environ["ANTHROPIC_API_KEY"] = popped


# The SDK ships a known set of built-in tools. We block them all by name. If
# the SDK adds new ones, the empty allowlist plus `permission_mode="dontAsk"`
# still close the loop (dontAsk denies anything not pre-approved by allow rules,
# and nothing is on the allow list).
_KNOWN_BUILTIN_TOOLS = [
    "Bash", "BashOutput", "KillBash", "Edit", "MultiEdit", "Write", "Read",
    "NotebookEdit", "Glob", "Grep", "WebFetch", "WebSearch", "Task",
    "TodoWrite", "ExitPlanMode",
]


@dataclass(frozen=True)
class LookoutGeneration:
    """Result of one Lookout generation."""
    text: str
    model: str
    raw_messages: list[Any]


def _build_user_prompt(
    *,
    output_spec_text: str,
    calendar_payload: dict[str, Any],
    cornerstone_payload: dict[str, Any],
    drive_delta_payload: dict[str, Any],
    run_id: str,
    date_iso: str,
    principal_id: str,
    client_scope: str,
    cornerstone_namespace: str,
) -> str:
    """Compose the single user message Lookout receives.

    Pattern: the system prompt is the persona/rules; the user prompt is "here
    are today's three source reads, produce the output per the spec." Source
    payloads are injected as JSON-fenced sections so the model can read them
    deterministically.

    The required footer keys are listed inline so the spec contract is in
    front of the model on every call.
    """
    return (
        "You are being run for one daily-brief task. Produce the brief that "
        "follows the OUTPUT SPEC below. The six section headings are "
        "MANDATORY and must appear in order, each on its own line as Markdown H1:\n"
        "  # The day at a glance\n"
        "  # For each meeting\n"
        "  # What changed worth knowing\n"
        "  # From memory worth surfacing\n"
        "  # What I couldn't check\n"
        "  # The technical bit\n\n"
        "=== OUTPUT SPEC (how to lay out the brief) ===\n"
        f"{output_spec_text}\n\n"
        "=== RUN CONTEXT (your scope; you cannot widen it) ===\n"
        f"  run_id:                 {run_id}\n"
        f"  date:                   {date_iso}\n"
        f"  principal_id:           {principal_id}\n"
        f"  client_scope:           {client_scope}\n"
        f"  cornerstone_namespace:  {cornerstone_namespace}\n\n"
        "=== SOURCE 1: CALENDAR READ ===\n"
        "```json\n"
        f"{json.dumps(calendar_payload, indent=2, default=str)}\n"
        "```\n\n"
        "=== SOURCE 2: CORNERSTONE READ ===\n"
        "```json\n"
        f"{json.dumps(cornerstone_payload, indent=2, default=str)}\n"
        "```\n\n"
        "=== SOURCE 3: DRIVE DELTA READ ===\n"
        "```json\n"
        f"{json.dumps(drive_delta_payload, indent=2, default=str)}\n"
        "```\n\n"
        "=== FOOTER REQUIREMENTS (the final fenced JSON block) ===\n"
        "The last fenced ```json``` block in your output MUST be an object with:\n"
        f"  run_id                  (string, must equal {run_id!r})\n"
        f"  date                    (ISO string, {date_iso!r})\n"
        "  scope                   (object: principal_id, client_scope, cornerstone_namespace)\n"
        "  source_counts           (object: calendar_events, cornerstone_items, drive_added, drive_modified)\n"
        "  gaps                    (non-empty array of strings; MUST include "
        "\"email-not-connected\" and \"personal-memory-not-connected\"; plus any "
        "source errors observed in the reads above)\n"
        "  langfuse_trace_id       (string or null)\n\n"
        "Return ONLY the daily brief markdown. No preamble, no closing remark."
    )


def load_system_prompt(specs_dir: Path) -> str:
    """Load the Lookout system prompt.

    The output spec is appended into the user message (see `_build_user_prompt`)
    so the user prompt and system prompt are cleanly separable for review.
    """
    return (specs_dir / "system-prompt.md").read_text(encoding="utf-8")


def load_output_spec(specs_dir: Path) -> str:
    return (specs_dir / "output-spec.md").read_text(encoding="utf-8")


async def generate_brief(
    *,
    system_prompt: str,
    output_spec_text: str,
    calendar_payload: dict[str, Any],
    cornerstone_payload: dict[str, Any],
    drive_delta_payload: dict[str, Any],
    run_id: str,
    date_iso: str,
    principal_id: str,
    client_scope: str,
    cornerstone_namespace: str,
    model: str,
    cwd: Path,
) -> LookoutGeneration:
    """Run Lookout once. Returns the assistant text and the raw message log.

    The caller wraps this in a Langfuse `generation` span.
    """
    options = ClaudeAgentOptions(
        system_prompt=system_prompt,
        model=model,
        allowed_tools=[],                       # NEVER change for Lookout v1 - AC-1 audit relies on this
        disallowed_tools=_KNOWN_BUILTIN_TOOLS,
        permission_mode="dontAsk",              # deny anything not on the (empty) allowlist
        cwd=str(cwd),
    )

    user_prompt = _build_user_prompt(
        output_spec_text=output_spec_text,
        calendar_payload=calendar_payload,
        cornerstone_payload=cornerstone_payload,
        drive_delta_payload=drive_delta_payload,
        run_id=run_id,
        date_iso=date_iso,
        principal_id=principal_id,
        client_scope=client_scope,
        cornerstone_namespace=cornerstone_namespace,
    )

    collected_text: list[str] = []
    raw_messages: list[Any] = []

    with _claude_auth_env():
        async for message in query(prompt=user_prompt, options=options):
            raw_messages.append(message)
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        collected_text.append(block.text)

    return LookoutGeneration(
        text="".join(collected_text).strip(),
        model=model,
        raw_messages=raw_messages,
    )
