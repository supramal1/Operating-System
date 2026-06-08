"""Render the final decision-brief file from Scout's validated output.

Thin on purpose. Scout produces the markdown body itself (it has prose to write
in Parts 1, 2, 4 and prose-with-template-blocks in Part 3). This module prepends
a small YAML front-matter for traceability and computes the canonical filename.

Headings and the JSON footer come straight from Scout; they pass through
`contracts.validate_output` unchanged. We never rewrite Scout's body - if a
heading is wrong, validation has already rejected the run.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class RenderedBrief:
    filename: str
    content: str


def render_brief_file(
    brief_id: str,
    brief_date: str,
    scout_output: str,
    *,
    model: str,
    agent_version: str,
    trace_id: str,
) -> RenderedBrief:
    """Build the final on-disk file: front-matter + Scout's validated body.

    Filename pattern from 06-build-notes.md:
        <brief_id>_<YYYY-MM-DD>_decision-brief.md
    """
    yyyy_mm_dd = _normalise_date(brief_date)
    front_matter = (
        "---\n"
        f"brief_id: {brief_id}\n"
        f"date: {yyyy_mm_dd}\n"
        f"agent: Scout\n"
        f"agent_version: {agent_version}\n"
        f"model: {model}\n"
        f"langfuse_trace_id: {trace_id}\n"
        "---\n\n"
    )
    filename = f"{brief_id}_{yyyy_mm_dd}_decision-brief.md"
    return RenderedBrief(filename=filename, content=front_matter + scout_output)


def _normalise_date(raw: str) -> str:
    raw = raw.strip()
    # If the brief used a literal "[today]" placeholder or anything non-ISO,
    # fall back to today's date so the filename is always well-formed.
    try:
        return date.fromisoformat(raw).isoformat()
    except ValueError:
        return date.today().isoformat()
