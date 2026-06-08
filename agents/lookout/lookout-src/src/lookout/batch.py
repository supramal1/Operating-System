"""Lookout batch runner — multi-date version of `lookout run`.

Mirrors Scout's batch.py shape (minimal). One `lookout` run per date in the
supplied range, in order, writing each brief to the same output folder. No
LLM judge step in v1 (the eval rubric is being authored in parallel by
another agent — see doc-store/evals/).

Usage:
    lookout-batch --start 2026-06-01 --end 2026-06-03 \\
                  --principal-id you@example.com \\
                  --client-scope agency-wide \\
                  --cornerstone-namespace charlie-oscar-job-canonical-memory

Failures on one date do not stop the batch — the runner records the per-date
exit code and continues. Final exit code is 0 only if every date succeeded.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

from .run import (
    DEFAULT_MODEL,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_SPECS_DIR,
    DEFAULT_STATE_DIR,
    main as run_main,
)


def _iso_date(raw: str) -> date:
    try:
        return date.fromisoformat(raw)
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"{raw!r} must be ISO YYYY-MM-DD") from e


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="lookout-batch",
        description=(
            "Run Lookout across a date range, one brief per day. Per-date "
            "failures do not stop the batch."
        ),
    )
    p.add_argument("--start", required=True, type=_iso_date,
                   help="First date in the range (inclusive), YYYY-MM-DD.")
    p.add_argument("--end", required=True, type=_iso_date,
                   help="Last date in the range (inclusive), YYYY-MM-DD.")
    p.add_argument("--principal-id", required=True)
    p.add_argument("--client-scope", required=True)
    p.add_argument("--cornerstone-namespace", required=True)
    p.add_argument("--drive-root-folder-id", default="")
    p.add_argument("--state-dir", type=Path, default=DEFAULT_STATE_DIR)
    p.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    p.add_argument("--specs-dir", type=Path, default=DEFAULT_SPECS_DIR)
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args(argv)


def _dates(start: date, end: date) -> list[date]:
    if end < start:
        return []
    out: list[date] = []
    d = start
    while d <= end:
        out.append(d)
        d = d + timedelta(days=1)
    return out


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    dates = _dates(args.start, args.end)
    if not dates:
        print(
            f"[lookout-batch] empty range: --start {args.start} must be <= --end {args.end}",
            file=sys.stderr,
        )
        return 2

    per_day_rc: dict[str, int] = {}
    for d in dates:
        print(f"[lookout-batch] {d.isoformat()} ...")
        sub_argv = [
            "--date", d.isoformat(),
            "--principal-id", args.principal_id,
            "--client-scope", args.client_scope,
            "--cornerstone-namespace", args.cornerstone_namespace,
            "--drive-root-folder-id", args.drive_root_folder_id,
            "--state-dir", str(args.state_dir),
            "--output-dir", str(args.output_dir),
            "--specs-dir", str(args.specs_dir),
            "--model", args.model,
        ]
        if args.dry_run:
            sub_argv.append("--dry-run")
        try:
            rc = run_main(sub_argv)
        except Exception as e:  # pragma: no cover (run.py already catches)
            print(f"[lookout-batch] {d.isoformat()} raised: {e}", file=sys.stderr)
            rc = 1
        per_day_rc[d.isoformat()] = rc

    print("\n=== Batch summary ===")
    for d_iso, rc in per_day_rc.items():
        tag = "ok" if rc == 0 else f"FAIL exit={rc}"
        print(f"  {d_iso}  {tag}")

    return 0 if all(rc == 0 for rc in per_day_rc.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
