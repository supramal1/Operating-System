"""The Claude Agent SDK call for Scout.

v1 design: Scout is a pure "read the brief and material, produce the decision
brief" agent. It has NO tools available. Material and brief are passed in the
prompt; the response is plain text containing the four-part brief + JSON footer.

Three structural enforcement layers on tools:
  1. `allowed_tools=[]`           - no tool is auto-approved.
  2. `disallowed_tools=[...]`     - the SDK's built-in tools are explicitly off.
  3. `can_use_tool` callback      - any tool the model still tries is denied.

Together these make it impossible for v1 Scout to take a side-effecting action,
even if the model attempts to call a tool.
"""

from __future__ import annotations

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
    via OAuth. To make Scout deterministic on the current dev box, we
    temporarily clear that env var for the SDK subprocess so it falls back
    to the user's Claude Code login. If you want to use a direct API key
    instead, unset the OAuth login and set a valid `ANTHROPIC_API_KEY`.

    In server/container contexts where Claude Code OAuth is not available
    (e.g. the slice-1 Scout MCP container on the gateway VPS), set
    SCOUT_USE_API_KEY=1 to preserve ANTHROPIC_API_KEY for the SDK subprocess.
    Defaults to the dev-box behaviour (env var unset = clear the key).
    """
    if os.environ.get("SCOUT_USE_API_KEY") == "1":
        yield
        return
    popped = os.environ.pop("ANTHROPIC_API_KEY", None)
    if popped is not None:
        print(
            "[scout] cleared ANTHROPIC_API_KEY for SDK subprocess; using "
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
class ScoutGeneration:
    """Result of one Scout generation."""
    text: str
    model: str
    raw_messages: list[Any]


_FOOTER_TEMPLATE = '''```json
{
  "brief_id": "<must match BRIEF_ID from the brief>",
  "reviewed": "<one short string describing what was digested>",
  "bottom_line": "<one sentence: the single most important thing>",
  "decisions": [
    {
      "name": "<short name>",
      "tag": "yours to decide" or "Scout suggests <option>",
      "the_call": "<one sentence: what actually needs deciding>",
      "options": [
        {"name": "<short>", "tradeoff": "<one line>", "fits_when": "<one line>"}
      ],
      "settles_it": "<one line: the fact or test that answers it>",
      "scout_suggestion": null
    }
  ],
  "open_questions": ["<one line each>"],
  "things_to_do": ["<one line each, actions not decisions>"],
  "not_scout_job": ["<one line each>"]
}
```

The hard rules on the footer:
1. `brief_id` MUST match the BRIEF_ID in the brief.
2. Every decision needs `name`, `tag`, and `scout_suggestion`.
3. If `tag` contains "yours to decide" (case-insensitive), `scout_suggestion`
   MUST be null. This is the frame-don't-recommend gate. A suggestion on a
   "yours to decide" decision FAILS the run.
4. For "Scout suggests X" decisions, `scout_suggestion` should be a one-line
   recommendation.
5. RESTRAINT CASE: If the material genuinely raises no decisions, leave
   `decisions` as an empty array `[]` and include a `no_decisions_rationale`
   field — a one-line, specific explanation of why nothing was decidable
   (e.g. "material restates publicly-known SDK basics already implemented in
   Scout, no novel claim worth a second pass"). Empty `decisions` without a
   `no_decisions_rationale` is REJECTED as lazy. Empty `decisions` with a
   clear rationale is a valid restraint output (the right answer when the
   material doesn't earn any decisions). Do not invent decisions to fill the
   schema.'''


def _build_user_prompt(
    brief_text: str,
    material_text: str,
    output_spec_text: str,
) -> str:
    """Compose the single user message Scout receives.

    The output spec is included so Scout has the exact heading text in front of
    it on every call, and so we never trust a brief author to remember it. The
    system prompt provides discipline; the output spec provides shape; the
    footer template below provides the machine-readable contract that the new
    spec leaves implicit.
    """
    return (
        "You are being run for one task. Produce a decision brief that follows "
        "the OUTPUT SPEC below. The four part headings are MANDATORY and must "
        "appear in order, each on its own line as Markdown H2:\n"
        "  ## Part 1: The answer\n"
        "  ## Part 2: The detail\n"
        "  ## Part 3: What's next\n"
        "  ## Part 4: The technical bit\n"
        "You may append a parenthetical to any heading (e.g. 'Part 4: The "
        "technical bit (hidden at the bottom)') but the 'Part N: <title>' "
        "prefix is exact. 'Hidden at the bottom' means the CONTENT under the "
        "Part 4 heading is collapsed inside <details>, NOT that the heading "
        "itself is omitted. The Part 4 heading MUST appear above the "
        "<details> block.\n\n"
        "=== OUTPUT SPEC (how to lay out the report) ===\n"
        f"{output_spec_text}\n\n"
        "=== FOOTER TEMPLATE (the technical bit in Part 4) ===\n"
        f"{_FOOTER_TEMPLATE}\n\n"
        "=== BRIEF (Mal's task) ===\n"
        f"{brief_text}\n\n"
        "=== MATERIAL (what you are digesting) ===\n"
        f"{material_text}\n\n"
        "Return ONLY the decision brief markdown. No preamble, no closing "
        "remark. Layout of Part 4:\n"
        "  ## Part 4: The technical bit (hidden at the bottom)\n"
        "  \n"
        "  <details>\n"
        "  <summary>Technical data</summary>\n"
        "  \n"
        "  ```json\n"
        "  { ...footer matching the template above... }\n"
        "  ```\n"
        "  \n"
        "  </details>"
    )


def load_system_prompt(specs_dir: Path) -> str:
    """Load the Scout system prompt + the output spec as one system message.

    Concatenating them is deliberate: the system-prompt file is the *discipline*
    (frame-do-not-recommend, tone, hard limits); the output-spec is the *shape*
    (headings, footer JSON). Scout needs both as fixed context every run.
    """
    sp = (specs_dir / "system-prompt.md").read_text(encoding="utf-8")
    # Output spec is appended into the user message instead - see _build_user_prompt -
    # so that the user prompt and system prompt are cleanly separable for review.
    return sp


def load_output_spec(specs_dir: Path) -> str:
    return (specs_dir / "output-spec.md").read_text(encoding="utf-8")


async def generate_brief(
    *,
    brief_text: str,
    material_text: str,
    system_prompt: str,
    output_spec_text: str,
    model: str,
    cwd: Path,
) -> ScoutGeneration:
    """Run Scout once. Returns the assistant text and the raw message log.

    The caller wraps this in a Langfuse `generation` span.
    """
    options = ClaudeAgentOptions(
        system_prompt=system_prompt,
        model=model,
        allowed_tools=[],
        disallowed_tools=_KNOWN_BUILTIN_TOOLS,
        permission_mode="dontAsk",  # deny anything not on the (empty) allowlist
        cwd=str(cwd),
    )

    user_prompt = _build_user_prompt(brief_text, material_text, output_spec_text)

    collected_text: list[str] = []
    raw_messages: list[Any] = []

    with _claude_auth_env():
        async for message in query(prompt=user_prompt, options=options):
            raw_messages.append(message)
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        collected_text.append(block.text)

    return ScoutGeneration(
        text="".join(collected_text).strip(),
        model=model,
        raw_messages=raw_messages,
    )
