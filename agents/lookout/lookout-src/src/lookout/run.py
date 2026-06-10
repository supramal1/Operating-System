"""Lookout v1 CLI entry point.

One run:
    1. Compose RunContext from CLI args.
    2. Pull three live sources: calendar, cornerstone, drive delta.
    3. Generate the daily brief via Claude Agent SDK (no tools).
    4. Structurally validate the output (raises if it fails the contract).
    5. Render the file with front-matter + canonical filename.
    6. Write the file to the output folder.
    7. Stop.

There is no step 8. Nothing consumes the output automatically. Mal's review
IS the next step.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import uuid
from dataclasses import asdict
from datetime import date, datetime
from pathlib import Path

from . import __version__
from .agent import generate_brief, load_output_spec, load_system_prompt
from .contracts import OutputContractError, validate_output
from .langfuse_trace import LookoutTrace, get_langfuse_client
from .render import render_brief_file
from .run_context import RunContext
from .sources import calendar as calendar_source
from .sources import cornerstone as cornerstone_source
from .sources import drive_delta as drive_delta_source


DEFAULT_SPECS_DIR = (
    Path.home()
    / "Desktop" / "Charlie-Oscar-OS-Prep" / "co-platform"
    / "agents" / "lookout" / "doc-store" / "specs"
)
DEFAULT_STATE_DIR = (
    Path.home()
    / "Desktop" / "Charlie-Oscar-OS-Prep" / "co-platform"
    / "agents" / "lookout" / "state"
)
DEFAULT_OUTPUT_DIR = (
    Path.home()
    / "Desktop" / "Charlie-Oscar-OS-Prep" / "co-platform"
    / "agents" / "lookout" / "drive" / "Charlie Oscar AI Ops"
    / "Agents" / "Lookout" / "outputs"
)
DEFAULT_MODEL = "claude-opus-4-8"


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="lookout",
        description=(
            "Lookout v1: daily-summary agent. Pulls calendar + cornerstone + "
            "drive delta for a date, writes a spec-compliant brief to the "
            "outputs folder, then stops."
        ),
    )
    p.add_argument(
        "--date", required=True, type=_iso_date,
        help="Date the brief is for, YYYY-MM-DD.",
    )
    p.add_argument(
        "--principal-id", required=True,
        help="Whose calendar to read (Google account email).",
    )
    p.add_argument(
        "--client-scope", required=True,
        help=(
            "MC-6 scope. Single client id (e.g. 'acme') OR 'agency-wide'. "
            "Every cornerstone read carries this."
        ),
    )
    p.add_argument(
        "--cornerstone-namespace", required=True,
        help="Cornerstone namespace to query against.",
    )
    p.add_argument(
        "--drive-root-folder-id", default="",
        help=(
            "Optional Google Drive folder id to narrow the drive sweep. "
            "Empty string means walk the whole Drive."
        ),
    )
    p.add_argument(
        "--state-dir", type=Path, default=DEFAULT_STATE_DIR,
        help=(
            "Lookout-private state dir (coverage-index, delta, library-mirror). "
            f"Default: {DEFAULT_STATE_DIR}. NEVER point at "
            "platform/stewardship/."
        ),
    )
    p.add_argument(
        "--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR,
        help=f"Where to write the rendered brief. Default: {DEFAULT_OUTPUT_DIR}.",
    )
    p.add_argument(
        "--specs-dir", type=Path, default=DEFAULT_SPECS_DIR,
        help="Directory containing system-prompt.md and output-spec.md.",
    )
    p.add_argument(
        "--model", default=DEFAULT_MODEL,
        help=f"Claude model id (default: {DEFAULT_MODEL}).",
    )
    p.add_argument(
        "--dry-run", action="store_true",
        help="Pull sources and compose the prompt, but do not call the model.",
    )
    return p.parse_args(argv)


def _iso_date(raw: str) -> date:
    try:
        return date.fromisoformat(raw)
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"--date {raw!r} must be ISO YYYY-MM-DD") from e


def _make_run_id(d: date) -> str:
    """`lookout_<YYYYMMDD>_<short-uuid>` — filesystem safe, unique per run."""
    return f"lookout_{d.strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}"


def _calendar_event_to_dict(ev: object) -> dict:
    return asdict(ev) if hasattr(ev, "__dataclass_fields__") else dict(vars(ev))


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)

    try:
        run_context = RunContext(
            run_id=_make_run_id(args.date),
            date=args.date,
            principal_id=args.principal_id,
            client_scope=args.client_scope,
            cornerstone_namespace=args.cornerstone_namespace,
            drive_root_folder_id=(args.drive_root_folder_id or None),
            state_dir=args.state_dir,
            output_dir=args.output_dir,
        )
    except (ValueError, TypeError) as e:
        print(f"[run-context] {e}", file=sys.stderr)
        return 2

    if not run_context.client_scope:
        # argparse already requires this, but enforce here for symmetry with MC-6.
        print("[run-context] --client-scope is required (MC-6).", file=sys.stderr)
        return 2

    system_prompt = load_system_prompt(args.specs_dir)
    output_spec = load_output_spec(args.specs_dir)

    run_context.output_dir.mkdir(parents=True, exist_ok=True)
    run_context.state_dir.mkdir(parents=True, exist_ok=True)

    langfuse = get_langfuse_client()

    with LookoutTrace(run_id=run_context.run_id, langfuse=langfuse) as trace:
        with trace.span(
            "input_load",
            input={
                "run_id": run_context.run_id,
                "date": run_context.date.isoformat(),
                "principal_id": run_context.principal_id,
                "client_scope": run_context.client_scope,
                "cornerstone_namespace": run_context.cornerstone_namespace,
                "drive_root_folder_id": run_context.drive_root_folder_id,
            },
        ):
            pass

        with trace.span("calendar_pull") as s:
            cal_read = calendar_source.fetch_today_events(run_context)
            s.update(output={"events": len(cal_read.events), "errors": cal_read.errors})

        with trace.span("cornerstone_pull") as s:
            try:
                cs_read = cornerstone_source.query(
                    run_context,
                    ask=(
                        f"What is worth knowing for {run_context.principal_id} on "
                        f"{run_context.date.isoformat()} in scope "
                        f"{run_context.client_scope!r}? Surface decisions, "
                        f"commitments, and context relevant to today's meetings."
                    ),
                )
            except ValueError as e:
                cs_read = cornerstone_source.CornerstoneRead(
                    text="", items_retrieved=0, context_request_id=None,
                    errors=[f"cornerstone-edge-error: {e}"],
                )
            s.update(output={
                "items_retrieved": cs_read.items_retrieved,
                "errors": cs_read.errors,
            })

        with trace.span("drive_delta") as s:
            dd_read = drive_delta_source.fetch_delta(run_context)
            s.update(output={
                "added": len(dd_read.added),
                "modified": len(dd_read.modified),
                "removed": len(dd_read.removed),
                "errors": dd_read.errors,
            })

        calendar_payload = {
            "window_start": cal_read.window_start.isoformat(),
            "window_end": cal_read.window_end.isoformat(),
            "events": [_calendar_event_to_dict(e) for e in cal_read.events],
            "errors": cal_read.errors,
        }
        cornerstone_payload = {
            "text": cs_read.text,
            "items_retrieved": cs_read.items_retrieved,
            "context_request_id": cs_read.context_request_id,
            "errors": cs_read.errors,
        }
        drive_delta_payload = {
            "added": dd_read.added,
            "modified": dd_read.modified,
            "removed": dd_read.removed,
            "unchanged_count": dd_read.unchanged_count,
            "errors": dd_read.errors,
        }

        if args.dry_run:
            print("[dry-run] Source reads complete:")
            print(f"  calendar: {len(cal_read.events)} events, errors={cal_read.errors}")
            print(f"  cornerstone: {cs_read.items_retrieved} items, errors={cs_read.errors}")
            print(f"  drive: +{len(dd_read.added)} ~{len(dd_read.modified)} -{len(dd_read.removed)}, errors={dd_read.errors}")
            print("[dry-run] Skipping model call. Done.")
            return 0

        with trace.generation(
            "lookout_generate",
            model=args.model,
            input={
                "calendar_events": len(cal_read.events),
                "cornerstone_items": cs_read.items_retrieved,
                "drive_added": len(dd_read.added),
                "drive_modified": len(dd_read.modified),
            },
            metadata={"tools": "disabled (allowed=[] + disallowed=builtins)"},
        ) as gen:
            result = asyncio.run(generate_brief(
                system_prompt=system_prompt,
                output_spec_text=output_spec,
                calendar_payload=calendar_payload,
                cornerstone_payload=cornerstone_payload,
                drive_delta_payload=drive_delta_payload,
                run_id=run_context.run_id,
                date_iso=run_context.date.isoformat(),
                principal_id=run_context.principal_id,
                client_scope=run_context.client_scope,
                cornerstone_namespace=run_context.cornerstone_namespace,
                model=args.model,
                cwd=run_context.output_dir,
            ))
            gen.update(output=result.text)

        with trace.span("validate", input={"chars": len(result.text)}) as s:
            try:
                validated = validate_output(result.text, expected_run_id=run_context.run_id)
            except OutputContractError as e:
                s.update(level="ERROR", status_message=str(e))
                print(f"[output-contract] {e}", file=sys.stderr)
                print(
                    "Lookout produced output but it failed structural validation. "
                    "Not writing to outputs. See Langfuse trace (if configured) "
                    "for full text.",
                    file=sys.stderr,
                )
                trace.record_output({"status": "rejected", "reason": str(e)})
                return 3
            s.update(output={
                "calendar_events": validated.footer["source_counts"]["calendar_events"],
                "gaps": validated.footer["gaps"],
            })

        with trace.span("render") as s:
            rendered = render_brief_file(
                run_id=run_context.run_id,
                brief_date=run_context.date.isoformat(),
                lookout_output=validated.text,
                model=args.model,
                agent_version=__version__,
                trace_id=trace.trace_id or "unknown",
                principal_id=run_context.principal_id,
                client_scope=run_context.client_scope,
            )
            s.update(output={"filename": rendered.filename})

        output_path = run_context.output_dir / rendered.filename
        with trace.span("file_write", input={"path": str(output_path)}) as s:
            output_path.write_text(rendered.content, encoding="utf-8")
            s.update(output={"bytes": output_path.stat().st_size})

        trace.record_output({
            "status": "ok",
            "output_path": str(output_path),
            "gaps": validated.footer["gaps"],
        })

    print(f"Wrote: {output_path}")
    if trace.trace_id:
        print(f"Langfuse trace id:  {trace.trace_id}")
    if trace.trace_url:
        print(f"Langfuse trace url: {trace.trace_url}")
    print("Lookout stops here. Review the brief before treating any item as actionable.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
