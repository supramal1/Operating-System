"""Scout batch runner.

Runs Scout across a named set of briefs in one command. Three things happen per brief:

  1. Scout generates the brief and writes it to the outputs folder (same as a single
     `scout` run). Structural hard-checks fire automatically — those are mechanics and
     are safe to automate.
  2. The LLM judge produces DRAFT scores against the case's rubric dimensions. Draft
     scores are written to `goldens/drafts/<brief_id>_<date>_judge.json`.
  3. A combined batch results file is written to
     `drive/.../outputs/_batch/<timestamp>_<set>_results.json`.

What this runner DOES NOT do:
  - Mark any judge score as final.
  - Move briefs from outputs/ to reviewed/.
  - Post scores back to Langfuse as final (they live as draft files on disk; trace
     scoring is left to Mal's review).
  - Close any loop without Mal's review.

Until the judge-agreement gate is hit (see 09-scout_rubric.md), every score is DRAFT.

Usage:
    scout-batch --briefs opmodel-001 llm-gov-001 knowledge-001 \\
                --set calibration --no-judge      # hard-checks only
    scout-batch --briefs opmodel-001 --set adhoc  # one brief + judge draft
    scout-batch --list-sets                       # show named sets

Brief inputs are looked up at:
    drive/Charlie Oscar AI Ops/Agents/Scout/inbox/<brief_id>_brief.md
    drive/Charlie Oscar AI Ops/Agents/Scout/inbox/<brief_id>_material.md

If either is missing, that brief is skipped with a clear message and the batch
continues with the rest.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import __version__
from .agent import generate_brief, load_output_spec, load_system_prompt
from .contracts import (
    BriefError,
    OutputContractError,
    parse_brief,
    validate_output,
)
from .evals import load_jsonl, llm_judge
from .langfuse_trace import ScoutTrace, get_langfuse_client
from .render import render_brief_file


# --- Locations ---

HERE = Path(__file__).resolve().parents[2]
DOC_STORE = (
    Path.home()
    / "Desktop" / "Charlie-Oscar-OS-Prep" / "co-platform"
    / "agents" / "scout" / "doc-store"
)
DEFAULT_DRIVE_ROOT = HERE / "drive" / "Charlie Oscar AI Ops"
DEFAULT_SPECS_DIR = DOC_STORE / "specs"
DEFAULT_CASES = DOC_STORE / "evals" / "cases.jsonl"
DEFAULT_RUBRIC = DOC_STORE / "evals" / "rubric.md"
DEFAULT_GOLDENS_DIR = HERE / "goldens"
DEFAULT_DRAFTS_DIR = DEFAULT_GOLDENS_DIR / "drafts"
DEFAULT_MODEL = "claude-opus-4-7"


# --- Named sets ---
#
# A named set is just a list of brief_ids the runner can take in one command. New
# sets are added here, deliberately, so the set definitions live in code under git
# rather than a config file the runner could be tricked into expanding.
#
# Mal supplies the briefs and materials; the runner just knows the names.

NAMED_SETS: dict[str, list[str]] = {
    "calibration": [
        "opmodel-001",
        "llm-gov-001",
        "knowledge-001",
        "adoption-001",
        "agent-strategy-001",
        "messy-001",
    ],
}


# --- Per-brief results ---

@dataclass
class BriefResult:
    brief_id: str
    case_id: str | None = None
    status: str = "pending"          # pending | brief_missing | material_missing |
                                     # brief_invalid | output_invalid | ok
    output_path: str | None = None
    trace_id: str | None = None
    trace_url: str | None = None
    hard_check_errors: list[str] = field(default_factory=list)
    judge_scores: dict[str, int] | None = None
    judge_rationale: dict[str, str] | None = None
    judge_status: str = "skipped"    # skipped | draft | error
    notes: str = ""


# --- Loading helpers ---

def _outputs_dir(drive_root: Path) -> Path:
    return drive_root / "Agents" / "Scout" / "outputs"


def _inbox_dir(drive_root: Path) -> Path:
    return drive_root / "Agents" / "Scout" / "inbox"


def _batch_dir(drive_root: Path) -> Path:
    return _outputs_dir(drive_root) / "_batch"


def _case_for(brief_id: str, cases_path: Path) -> dict[str, Any] | None:
    """Find the eval case whose case id matches scout-<brief_id> (best-effort)."""
    try:
        cases = load_jsonl(cases_path)
    except SystemExit:
        return None
    candidate = f"scout-{brief_id}"
    for c in cases:
        if c.get("id") == candidate or c.get("brief", {}).get("brief_id") == brief_id:
            return c
    return None


# --- The per-brief pipeline (single Scout run + optional draft judge) ---

async def _run_one(
    brief_id: str,
    *,
    drive_root: Path,
    specs_dir: Path,
    model: str,
    cases_path: Path,
    rubric_text: str | None,
    drafts_dir: Path,
    langfuse,
) -> BriefResult:
    result = BriefResult(brief_id=brief_id)
    inbox = _inbox_dir(drive_root)
    brief_path = inbox / f"{brief_id}_brief.md"
    material_path = inbox / f"{brief_id}_material.md"

    if not brief_path.is_file():
        result.status = "brief_missing"
        result.notes = f"Expected at {brief_path}"
        return result
    if not material_path.is_file():
        result.status = "material_missing"
        result.notes = f"Expected at {material_path}"
        return result

    brief_text = brief_path.read_text(encoding="utf-8")
    material_text = material_path.read_text(encoding="utf-8")

    try:
        brief = parse_brief(brief_text)
    except BriefError as e:
        result.status = "brief_invalid"
        result.notes = str(e)
        return result

    system_prompt = load_system_prompt(specs_dir)
    output_spec = load_output_spec(specs_dir)
    outputs_dir = _outputs_dir(drive_root)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    case = _case_for(brief_id, cases_path)
    if case:
        result.case_id = case.get("id")

    with ScoutTrace(brief_id=brief.brief_id, langfuse=langfuse) as trace:
        result.trace_id = trace.trace_id
        result.trace_url = trace.trace_url

        with trace.span("input_load", input={"brief_path": str(brief_path), "material_path": str(material_path)}):
            pass

        with trace.generation(
            "scout_generate",
            model=model,
            input={"brief_chars": len(brief_text), "material_chars": len(material_text)},
            metadata={"tools": "disabled", "batch": True},
        ) as gen:
            run = await generate_brief(
                brief_text=brief_text,
                material_text=material_text,
                system_prompt=system_prompt,
                output_spec_text=output_spec,
                model=model,
                cwd=drive_root,
            )
            gen.update(output=run.text)

        with trace.span("validate") as s:
            try:
                validated = validate_output(run.text, expected_brief_id=brief.brief_id)
            except OutputContractError as e:
                result.status = "output_invalid"
                result.hard_check_errors.append(str(e))
                s.update(level="ERROR", status_message=str(e))
                trace.record_output({"status": "rejected", "reason": str(e)})
                return result

        with trace.span("render"):
            rendered = render_brief_file(
                brief_id=brief.brief_id,
                brief_date=brief.fields["DATE"],
                scout_output=validated.text,
                model=model,
                agent_version=__version__,
                trace_id=trace.trace_id or "unknown",
            )

        output_path = outputs_dir / rendered.filename
        with trace.span("file_write", input={"path": str(output_path)}):
            output_path.write_text(rendered.content, encoding="utf-8")

        result.status = "ok"
        result.output_path = str(output_path)

        # Draft judge (only if rubric provided and we have a case to score against).
        if rubric_text is not None and case is not None:
            try:
                j = await llm_judge(case, run.text, rubric_text)
                result.judge_scores = j.get("scores", {})
                result.judge_rationale = j.get("rationale", {})
                result.judge_status = "draft"
                _write_draft_judge(drafts_dir, brief_id, j, case_id=case.get("id"))
            except Exception as e:  # pragma: no cover (network/path issues)
                result.judge_status = "error"
                result.notes = f"judge error: {e}"

        trace.record_output({
            "status": result.status,
            "output_path": result.output_path,
            "judge_status": result.judge_status,
        })

    return result


def _write_draft_judge(
    drafts_dir: Path,
    brief_id: str,
    j: dict[str, Any],
    case_id: str | None,
) -> None:
    drafts_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).date().isoformat()
    path = drafts_dir / f"{brief_id}_{today}_judge.json"
    payload = {
        "brief_id": brief_id,
        "case_id": case_id,
        "status": "DRAFT — not final until reviewed by Mal",
        "scored_against": "09-scout_rubric.md",
        "calibration_gate": "75-90% agreement target with hand-scores; not yet reached",
        "scores": j.get("scores", {}),
        "rationale": j.get("rationale", {}),
        "should_surface_hits": j.get("should_surface_hits", []),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


# --- CLI ---

def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="scout-batch",
        description=(
            "Run Scout across a named set of briefs in one command. Produces a "
            "spec-compliant brief per task and DRAFT judge scores. Never marks "
            "scores final and never closes a loop without Mal's review."
        ),
    )
    p.add_argument("--briefs", nargs="*", default=None,
                   help="One or more brief_ids to run (looked up in inbox).")
    p.add_argument("--set", dest="set_name", default=None,
                   help=f"Name of a predefined set. Available: {', '.join(NAMED_SETS) or '(none)'}.")
    p.add_argument("--list-sets", action="store_true",
                   help="Print named sets and exit.")
    p.add_argument("--no-judge", action="store_true",
                   help="Skip the LLM judge; run Scout + hard-checks only.")
    p.add_argument("--drive-root", type=Path, default=DEFAULT_DRIVE_ROOT)
    p.add_argument("--specs-dir", type=Path, default=DEFAULT_SPECS_DIR)
    p.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    p.add_argument("--rubric", type=Path, default=DEFAULT_RUBRIC)
    p.add_argument("--drafts-dir", type=Path, default=DEFAULT_DRAFTS_DIR)
    p.add_argument("--model", default=DEFAULT_MODEL)
    return p.parse_args(argv)


def _collect_brief_ids(args: argparse.Namespace) -> list[str]:
    ids: list[str] = []
    if args.set_name:
        if args.set_name not in NAMED_SETS:
            sys.exit(f"Unknown set {args.set_name!r}. Known: {', '.join(NAMED_SETS) or '(none)'}.")
        ids.extend(NAMED_SETS[args.set_name])
    if args.briefs:
        for b in args.briefs:
            if b not in ids:
                ids.append(b)
    if not ids:
        sys.exit("No briefs to run. Pass --briefs <id> [...] or --set <name>.")
    return ids


def _print_summary(results: list[BriefResult]) -> None:
    print("\n=== Batch summary ===")
    for r in results:
        status_tag = r.status if r.status == "ok" else f"FAIL: {r.status}"
        judge_tag = "" if r.judge_status == "skipped" else f"  judge=DRAFT {r.judge_scores or {}}"
        print(f"  {r.brief_id:24s} {status_tag}{judge_tag}")
        if r.hard_check_errors:
            for e in r.hard_check_errors:
                print(f"      hard-check: {e}")
        if r.notes:
            print(f"      note: {r.notes}")
    print("\nALL judge scores are DRAFT until the 75-90% agreement gate is reached.")
    print("Review every draft before treating it as a real score.")


def _write_batch_report(
    results: list[BriefResult],
    drive_root: Path,
    set_name: str | None,
) -> Path:
    batch_dir = _batch_dir(drive_root)
    batch_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    name = set_name or "adhoc"
    path = batch_dir / f"{ts}_{name}_results.json"
    payload = {
        "timestamp": ts,
        "set": set_name,
        "calibration_gate": "judge scores are DRAFT; 75-90% hand-score agreement target not yet reached",
        "results": [asdict(r) for r in results],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


async def _main_async(args: argparse.Namespace) -> int:
    if args.list_sets:
        print("Named sets:")
        for name, ids in NAMED_SETS.items():
            print(f"  {name}: {', '.join(ids)}")
        return 0

    brief_ids = _collect_brief_ids(args)
    rubric_text = None if args.no_judge else args.rubric.read_text(encoding="utf-8")
    langfuse = get_langfuse_client()

    results: list[BriefResult] = []
    for bid in brief_ids:
        print(f"[batch] running {bid} ...")
        r = await _run_one(
            bid,
            drive_root=args.drive_root,
            specs_dir=args.specs_dir,
            model=args.model,
            cases_path=args.cases,
            rubric_text=rubric_text,
            drafts_dir=args.drafts_dir,
            langfuse=langfuse,
        )
        results.append(r)

    report_path = _write_batch_report(results, args.drive_root, args.set_name)
    _print_summary(results)
    print(f"\nBatch report: {report_path}")
    return 0 if all(r.status == "ok" for r in results) else 1


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    return asyncio.run(_main_async(args))


if __name__ == "__main__":
    raise SystemExit(main())
