"""The AC-4 boundary for Lookout.

`RunContext` is composed by the CALLER (CLI or orchestrator) once, and passed
into every step of a Lookout run unchanged. The agent NEVER mutates it. The
agent cannot widen it. Anything the agent would want to fetch must already be
in the run-context's scope; if not, the agent reports a gap and stops.

This file is the only place that should define the scope-bound boundary. Other
modules import `RunContext` from here.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class RunContext:
    """AC-4 boundary: composed by the caller, never widened by the agent.

    Fields:
        run_id: Unique id for this run (used in filenames + footer round-trip).
        date: The date the brief is for (Lookout is a daily summary).
        principal_id: Whose calendar is read (Google account email).
        client_scope: MC-6 scope. Either a single client_id (e.g. "acme") or
            the literal "agency-wide". Every cornerstone read carries this.
        cornerstone_namespace: The Cornerstone namespace to query against.
        drive_root_folder_id: Optional Google Drive folder id. None means the
            sweep walks the WHOLE Drive (drive_sweep's default).
        state_dir: Lookout's PRIVATE state dir. Holds coverage-index, delta,
            and library-mirror. NEVER points at platform/stewardship/ — that
            is owned by the stewardship sweep and sharing would race.
        output_dir: Where rendered briefs are written.
        calendar_time_zone: TZ used to bound the calendar day. Defaults to
            Europe/London (Mal's working TZ).
    """

    run_id: str
    date: date
    principal_id: str
    client_scope: str
    cornerstone_namespace: str
    drive_root_folder_id: str | None
    state_dir: Path
    output_dir: Path
    calendar_time_zone: str = "Europe/London"
