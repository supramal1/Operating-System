"""Synthetic case runner. Constructs source-adapter dataclasses directly from
case JSON; never invokes live calendar/cornerstone/drive fetchers. Used to
produce briefs for hand-scoring against the rubric.

Hard guarantees:
    - We import ONLY the dataclasses (CalendarRead, CalendarEvent,
      CornerstoneRead, DriveDeltaRead) from lookout.sources.*. The fetcher
      functions (fetch_today_events, query, fetch_delta) are NEVER imported,
      referenced, or called. Importing a frozen dataclass cannot initiate a
      network call.
    - The case-runner mirrors run.py's call into agent.generate_brief so the
      SDK boundary (allowed_tools=[]) is preserved unchanged. AC-1 holds.
    - All payloads are synthesised from the case JSON in cases.jsonl. No live
      Calendar API, no Cornerstone HTTP, no Drive sweep.

Output: one rendered markdown brief per case, written to --output-dir, plus
a summary table on stdout. The runner DOES NOT attempt to retry failed cases;
a contract failure writes the failed brief with marker `[VALIDATION FAILED]`
in the front-matter and returns FAILED in the summary so the orchestrator can
decide what to do.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import asdict
from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import Any

# IMPORTANT: only the dataclasses are imported here. The fetcher functions
# (calendar.fetch_today_events, cornerstone.query, drive_delta.fetch_delta)
# are NOT imported and NOT referenced anywhere in this module.
from .agent import generate_brief, load_output_spec, load_system_prompt
from .contracts import OutputContractError, validate_output
from .render import render_brief_file
from .run_context import RunContext
from .sources.calendar import CalendarEvent, CalendarRead
from .sources.cornerstone import CornerstoneRead
from .sources.drive_delta import DriveDeltaRead
from . import __version__


DEFAULT_CASES_FILE = (
    Path.home()
    / "Desktop" / "Charlie-Oscar-OS-Prep" / "co-platform"
    / "agents" / "lookout" / "doc-store" / "evals" / "cases.jsonl"
)
DEFAULT_SPECS_DIR = (
    Path.home()
    / "Desktop" / "Charlie-Oscar-OS-Prep" / "co-platform"
    / "agents" / "lookout" / "doc-store" / "specs"
)
DEFAULT_OUTPUT_BASE = (
    Path.home()
    / "Desktop" / "Charlie-Oscar-OS-Prep" / "co-platform"
    / "agents" / "lookout" / "doc-store" / "evals" / "runs"
)
DEFAULT_STATE_DIR = (
    Path.home()
    / "Desktop" / "Charlie-Oscar-OS-Prep" / "co-platform"
    / "agents" / "lookout" / "state" / "cases-runner"
)
DEFAULT_MODEL = "claude-opus-4-8"
DEFAULT_PRINCIPAL = "malik.roberts@essencemediacom.com"


# --- case loading ----------------------------------------------------------


def load_cases(path: Path) -> list[dict]:
    """Read cases.jsonl. Each non-empty line is one JSON object.

    Raises ValueError with the line number on malformed JSON.
    """
    cases: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for lineno, raw in enumerate(f, start=1):
            stripped = raw.strip()
            if not stripped:
                continue
            try:
                cases.append(json.loads(stripped))
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"Malformed JSON in {path} on line {lineno}: {e}"
                ) from e
    return cases


# --- dataclass builders ----------------------------------------------------


def case_to_calendar_read(case: dict) -> CalendarRead:
    """Convert case['input']['calendar'] into a CalendarRead.

    Window spans 00:00 -> 23:59 (UTC) on the case date. Missing fields on
    each event default sensibly (empty strings, empty lists, all_day False,
    hangout_link "").
    """
    raw_events = case.get("input", {}).get("calendar", []) or []
    events: list[CalendarEvent] = []
    for ev in raw_events:
        events.append(
            CalendarEvent(
                id=ev.get("id", ""),
                summary=ev.get("summary", ""),
                description=ev.get("description", ""),
                start=ev.get("start", ""),
                end=ev.get("end", ""),
                attendees=list(ev.get("attendees", []) or []),
                organizer_email=ev.get("organizer_email", ""),
                location=ev.get("location", ""),
                all_day=bool(ev.get("all_day", False)),
                hangout_link=ev.get("hangout_link", ""),
            )
        )

    case_date = date.fromisoformat(case["input"]["date"])
    window_start = datetime.combine(case_date, time.min, tzinfo=timezone.utc)
    window_end = datetime.combine(case_date, time.max, tzinfo=timezone.utc)
    return CalendarRead(
        events=events,
        window_start=window_start,
        window_end=window_end,
        errors=[],
    )


def case_to_cornerstone_read(case: dict) -> CornerstoneRead:
    """Convert case['input']['cornerstone_state'] into a CornerstoneRead.

    Pass ALL items regardless of scope. The eval intentionally stress-tests
    Lookout's judgment by handing it everything; production filtering happens
    upstream at the wrapper edge.
    """
    items = case.get("input", {}).get("cornerstone_state", []) or []
    case_id = case.get("case_id", "unknown-case")

    blob_lines: list[str] = ["=== CORNERSTONE CONTEXT ===", f"[items_retrieved: {len(items)}]", ""]
    for i, item in enumerate(items, start=1):
        blob_lines.append(f"--- ITEM {i} ---")
        blob_lines.append(f"key: {item.get('key', '')}")
        blob_lines.append(f"type: {item.get('type', '')}")
        blob_lines.append(f"client_scope: {item.get('client_scope', '')}")
        blob_lines.append(f"topic: {item.get('topic', '')}")
        blob_lines.append(f"body: {item.get('body', '')}")
        blob_lines.append("")
    blob_lines.append("=== END CORNERSTONE CONTEXT ===")

    return CornerstoneRead(
        text="\n".join(blob_lines),
        items_retrieved=len(items),
        context_request_id=f"synthetic-{case_id}",
        errors=[],
    )


def case_to_drive_delta_read(case: dict) -> DriveDeltaRead:
    """Convert case['input']['drive_delta'] into a DriveDeltaRead."""
    delta = case.get("input", {}).get("drive_delta", {}) or {}
    return DriveDeltaRead(
        added=list(delta.get("added", []) or []),
        modified=list(delta.get("modified", []) or []),
        removed=list(delta.get("removed", []) or []),
        unchanged_count=0,
        errors=[],
    )


def case_to_run_context(case: dict, state_dir: Path, output_dir: Path) -> RunContext:
    """Build a synthetic RunContext from the case JSON.

    client_scope rule:
        - distinct scopes across cornerstone_state items
        - if every item shares one scope -> use that
        - otherwise (mixed, or "agency-wide" present) -> "agency-wide"
    """
    items = case.get("input", {}).get("cornerstone_state", []) or []
    scopes = {item.get("client_scope", "") for item in items if item.get("client_scope")}
    if len(scopes) == 1:
        client_scope = next(iter(scopes))
    else:
        client_scope = "agency-wide"

    return RunContext(
        run_id=case["case_id"],
        date=date.fromisoformat(case["input"]["date"]),
        principal_id=DEFAULT_PRINCIPAL,
        client_scope=client_scope,
        cornerstone_namespace="default",
        drive_root_folder_id=None,
        state_dir=state_dir,
        output_dir=output_dir,
        calendar_time_zone="Europe/London",
    )


# --- payload formatting (mirrors run.py exactly) ---------------------------


def _calendar_payload(read: CalendarRead) -> dict[str, Any]:
    return {
        "window_start": read.window_start.isoformat(),
        "window_end": read.window_end.isoformat(),
        "events": [asdict(e) for e in read.events],
        "errors": list(read.errors),
    }


def _cornerstone_payload(read: CornerstoneRead) -> dict[str, Any]:
    return {
        "text": read.text,
        "items_retrieved": read.items_retrieved,
        "context_request_id": read.context_request_id,
        "errors": list(read.errors),
    }


def _drive_delta_payload(read: DriveDeltaRead) -> dict[str, Any]:
    return {
        "added": list(read.added),
        "modified": list(read.modified),
        "removed": list(read.removed),
        "unchanged_count": read.unchanged_count,
        "errors": list(read.errors),
    }


# --- per-case orchestration ------------------------------------------------


def run_case(
    case: dict,
    *,
    model: str,
    output_dir: Path,
    state_dir: Path,
    specs_dir: Path,
) -> dict:
    """Generate one brief for one case. Returns a result row.

    Result schema:
        {
            "case_id": str,
            "brief_path": Path,
            "validation": "PASS" | "FAILED",
            "error": str | None,
            "model": str,
            "langfuse_trace_id": str | None,
        }
    """
    case_id = case["case_id"]
    case_date = date.fromisoformat(case["input"]["date"])
    case_date_iso = case_date.isoformat()

    cal_read = case_to_calendar_read(case)
    cs_read = case_to_cornerstone_read(case)
    dd_read = case_to_drive_delta_read(case)
    run_context = case_to_run_context(case, state_dir=state_dir, output_dir=output_dir)

    system_prompt = load_system_prompt(specs_dir)
    output_spec_text = load_output_spec(specs_dir)

    output_dir.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)

    # Mirror run.py's generate_brief call site exactly. AC-1 holds because
    # we use the same agent.generate_brief, which keeps allowed_tools=[].
    generation = asyncio.run(generate_brief(
        system_prompt=system_prompt,
        output_spec_text=output_spec_text,
        calendar_payload=_calendar_payload(cal_read),
        cornerstone_payload=_cornerstone_payload(cs_read),
        drive_delta_payload=_drive_delta_payload(dd_read),
        run_id=run_context.run_id,
        date_iso=case_date_iso,
        principal_id=run_context.principal_id,
        client_scope=run_context.client_scope,
        cornerstone_namespace=run_context.cornerstone_namespace,
        model=model,
        cwd=output_dir,
    ))

    validation_status = "PASS"
    error_msg: str | None = None
    try:
        validated_text = validate_output(
            generation.text, expected_run_id=run_context.run_id
        ).text
    except OutputContractError as e:
        validation_status = "FAILED"
        error_msg = str(e)
        validated_text = generation.text  # write the failed brief anyway

    rendered = render_brief_file(
        run_id=run_context.run_id,
        brief_date=case_date_iso,
        lookout_output=validated_text,
        model=model,
        agent_version=__version__,
        trace_id="synthetic-no-trace",
        principal_id=run_context.principal_id,
        client_scope=run_context.client_scope,
    )

    brief_path = output_dir / rendered.filename
    if validation_status == "FAILED":
        # Mark on the disk file so a reader knows this brief is suspect.
        marker = (
            "---\n"
            f"[VALIDATION FAILED] {error_msg}\n"
            "---\n\n"
        )
        brief_path.write_text(marker + rendered.content, encoding="utf-8")
    else:
        brief_path.write_text(rendered.content, encoding="utf-8")

    return {
        "case_id": case_id,
        "brief_path": brief_path,
        "validation": validation_status,
        "error": error_msg,
        "model": model,
        "langfuse_trace_id": None,
    }


# --- CLI -------------------------------------------------------------------


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="lookout-cases",
        description=(
            "Synthetic case runner for Lookout. Generates briefs from cases.jsonl "
            "WITHOUT calling Calendar / Cornerstone / Drive — all source payloads "
            "are constructed from the case JSON. Used to produce briefs for "
            "hand-scoring against the rubric."
        ),
    )
    p.add_argument("--cases-file", type=Path, default=DEFAULT_CASES_FILE)
    p.add_argument("--case", type=str, default=None, help="Single case_id to run.")
    p.add_argument("--all", action="store_true", help="Run every case in the file.")
    p.add_argument("--model", type=str, default=DEFAULT_MODEL)
    p.add_argument(
        "--output-dir", type=Path, default=None,
        help="Where briefs are written. Defaults to runs/<today-iso>/.",
    )
    p.add_argument("--state-dir", type=Path, default=DEFAULT_STATE_DIR)
    p.add_argument("--specs-dir", type=Path, default=DEFAULT_SPECS_DIR)
    return p.parse_args(argv)


def _summary_table(rows: list[dict]) -> str:
    if not rows:
        return "(no cases run)"
    case_w = max(len(r["case_id"]) for r in rows)
    file_w = max(len(r["brief_path"].name) for r in rows)
    out: list[str] = []
    header = f"{'case_id'.ljust(case_w)}  {'status'.ljust(7)}  {'brief'.ljust(file_w)}  error"
    out.append(header)
    out.append("-" * len(header))
    for r in rows:
        out.append(
            f"{r['case_id'].ljust(case_w)}  "
            f"{r['validation'].ljust(7)}  "
            f"{r['brief_path'].name.ljust(file_w)}  "
            f"{(r['error'] or '')[:120]}"
        )
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)

    if not args.all and not args.case:
        print("Must pass --all OR --case <case_id>.", file=sys.stderr)
        return 2

    if args.output_dir is None:
        args.output_dir = DEFAULT_OUTPUT_BASE / date.today().isoformat()

    try:
        all_cases = load_cases(args.cases_file)
    except (OSError, ValueError) as e:
        print(f"[cases] failed to load {args.cases_file}: {e}", file=sys.stderr)
        return 2

    if args.case:
        cases = [c for c in all_cases if c.get("case_id") == args.case]
        if not cases:
            print(f"[cases] no case with case_id={args.case!r} in {args.cases_file}.",
                  file=sys.stderr)
            return 2
    else:
        cases = all_cases

    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.state_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    for i, case in enumerate(cases, start=1):
        case_id = case.get("case_id", "<missing-case_id>")
        print(f"[{i}/{len(cases)}] {case_id} ... ", end="", flush=True)
        try:
            row = run_case(
                case,
                model=args.model,
                output_dir=args.output_dir,
                state_dir=args.state_dir,
                specs_dir=args.specs_dir,
            )
        except Exception as e:
            row = {
                "case_id": case_id,
                "brief_path": args.output_dir / f"{case_id}_ERROR.md",
                "validation": "FAILED",
                "error": f"runner-exception: {e}",
                "model": args.model,
                "langfuse_trace_id": None,
            }
            print(f"ERROR ({e!r})")
        else:
            if row["validation"] == "PASS":
                print(f"PASS (validation OK) -> {row['brief_path'].name}")
            else:
                print(f"FAILED ({row['error']}) -> {row['brief_path'].name}")
        rows.append(row)

    print()
    print(_summary_table(rows))
    print()
    print(f"Output dir: {args.output_dir}")
    n_pass = sum(1 for r in rows if r["validation"] == "PASS")
    n_fail = sum(1 for r in rows if r["validation"] == "FAILED")
    print(f"Summary: {n_pass} PASS, {n_fail} FAILED, {len(rows)} total")
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
