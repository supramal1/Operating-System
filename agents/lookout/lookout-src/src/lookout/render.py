"""Render the final daily-brief file from Lookout's validated output.

Thin on purpose. Lookout produces the markdown body itself. This module
prepends a small YAML front-matter for traceability and computes the
canonical filename.

Headings and the JSON footer come straight from Lookout; they pass through
`contracts.validate_output` unchanged. We never rewrite Lookout's body — if
something is wrong, validation has already rejected the run.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class RenderedBrief:
    filename: str
    content: str


def render_brief_file(
    *,
    run_id: str,
    brief_date: str,
    lookout_output: str,
    model: str,
    agent_version: str,
    trace_id: str,
    principal_id: str,
    client_scope: str,
) -> RenderedBrief:
    """Build the final on-disk file: front-matter + Lookout's validated body.

    Filename pattern:
        <run_id>_<YYYY-MM-DD>_daily-brief.md
    """
    yyyy_mm_dd = _normalise_date(brief_date)
    front_matter = (
        "---\n"
        f"run_id: {run_id}\n"
        f"date: {yyyy_mm_dd}\n"
        f"agent: Lookout\n"
        f"agent_version: {agent_version}\n"
        f"model: {model}\n"
        f"langfuse_trace_id: {trace_id}\n"
        f"principal_id: {principal_id}\n"
        f"client_scope: {client_scope}\n"
        "---\n\n"
    )
    filename = f"{run_id}_{yyyy_mm_dd}_daily-brief.md"
    return RenderedBrief(filename=filename, content=front_matter + lookout_output)


def _normalise_date(raw: str) -> str:
    raw = raw.strip()
    try:
        return date.fromisoformat(raw).isoformat()
    except ValueError:
        return date.today().isoformat()
