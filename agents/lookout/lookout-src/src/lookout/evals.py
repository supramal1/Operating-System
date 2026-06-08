"""Lookout eval harness.

The rubric file and the cases file are being authored in parallel by another
agent (see `doc-store/evals/rubric.md` and `doc-store/evals/cases.jsonl`,
plus the schema at `doc-store/evals/cases-schema.json`). Until those land,
this harness can already:

  1. Schema-load the cases (light field check; no schema validation library
     required, schema lives next to the cases).
  2. Run the structural contract (`contracts.validate_output`) against
     pre-computed Lookout outputs in a `--score outputs.jsonl` file.

The LLM-judge pass is a TODO that the parallel agent's rubric format will
shape. The harness is laid out so the judge call can drop in next to
`hard_checks` without touching the CLI surface.

Usage:
    lookout-eval --validate                          # light schema check on cases
    lookout-eval --score outputs.jsonl              # structural check on outputs
    lookout-eval --score outputs.jsonl --case lookout-day-001

outputs.jsonl: one object per line, {"id": "<case_id>", "output": "<lookout output>"}
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contracts import OutputContractError, validate_output


HERE = Path(__file__).resolve().parents[2]
DOC_STORE = (
    Path.home()
    / "Desktop" / "Charlie-Oscar-OS-Prep" / "co-platform"
    / "agents" / "lookout" / "doc-store"
)
DEFAULT_CASES = DOC_STORE / "evals" / "cases.jsonl"
DEFAULT_SCHEMA = DOC_STORE / "evals" / "cases-schema.json"
DEFAULT_RUBRIC = DOC_STORE / "evals" / "rubric.md"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        sys.exit(f"File not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                sys.exit(f"Bad JSON in {path} line {i}: {e}")
    return rows


def validate_cases(cases: list[dict[str, Any]]) -> bool:
    """Light field-level check.

    The parallel agent owns `cases-schema.json`; once it lands, switch this to
    a real jsonschema validation. For now: every case must have a non-empty
    `id` and an `input` block.
    """
    id_re = re.compile(r"^lookout-[a-z0-9-]+-[0-9]{3}$")
    seen: set[str] = set()
    ok = True
    for c in cases:
        cid = c.get("id", "<missing>")
        if cid in seen:
            print(f"  DUPLICATE id: {cid}"); ok = False
        seen.add(cid)
        if not isinstance(cid, str) or not id_re.match(cid):
            print(f"  {cid}: id must match lookout-<slug>-<NNN>"); ok = False
        if not c.get("input"):
            print(f"  {cid}: missing input block"); ok = False
    print(f"Validated {len(cases)} cases. {'OK' if ok else 'PROBLEMS FOUND'}.")
    return ok


@dataclass
class StructuralResult:
    case_id: str
    ok: bool
    error: str | None = None


def _read_outputs_jsonl(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for row in load_jsonl(path):
        out[row["id"]] = row.get("output", "")
    return out


def _structural_check(case_id: str, output: str, expected_run_id: str | None) -> StructuralResult:
    try:
        validate_output(output, expected_run_id=expected_run_id or case_id)
        return StructuralResult(case_id=case_id, ok=True)
    except OutputContractError as e:
        return StructuralResult(case_id=case_id, ok=False, error=str(e))


def _argparse() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="lookout-eval", description="Lookout eval harness.")
    p.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    p.add_argument("--rubric", type=Path, default=DEFAULT_RUBRIC)
    p.add_argument("--validate", action="store_true",
                   help="Light schema check on the cases file.")
    p.add_argument("--score", type=Path, metavar="OUTPUTS_JSONL",
                   help="Run the structural contract against pre-computed outputs.")
    p.add_argument("--case", action="append", default=None,
                   help="Limit to specific case id(s). Repeatable.")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _argparse().parse_args(sys.argv[1:] if argv is None else argv)

    if args.validate or not args.score:
        cases = load_jsonl(args.cases) if args.cases.exists() else []
        if not cases:
            print(f"No cases at {args.cases}. The parallel agent owns this file.")
        ok = validate_cases(cases) if cases else True
        if not args.score:
            return 0 if ok else 1

    pre_outputs = _read_outputs_jsonl(args.score)
    overall_ok = True
    for case_id, output_text in pre_outputs.items():
        if args.case and case_id not in set(args.case):
            continue
        result = _structural_check(case_id, output_text, expected_run_id=None)
        tag = "OK" if result.ok else "FAIL"
        print(f"[{tag}] {case_id}")
        if result.error:
            print(f"    {result.error}")
            overall_ok = False
    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
