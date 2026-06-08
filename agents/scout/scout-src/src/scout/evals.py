"""Scout eval harness.

Pattern lifted from CO's existing 02-eval-framework/score.py:
  1. Validate cases against 07-scout_cases_schema.json (light field checks).
  2. For each case: run Scout against the case's brief+material (or read from
     a pre-computed outputs.jsonl). Hard pre-filter on must_not. If any must_not
     hits, cap the case at 0 regardless of judge scores.
  3. LLM-as-judge on Claude scores each rubric dimension 0-3 using the rubric
     definitions in 09-scout_rubric.md as ground.

Usage:
    scout-eval --validate                            # schema-check cases only
    scout-eval --run                                 # run Scout against all cases, score them
    scout-eval --run --case scout-harness-list-001   # one case
    scout-eval --score outputs.jsonl                 # score pre-computed outputs

outputs.jsonl: one object per line, {"id": "<case_id>", "output": "<scout output>"}
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    TextBlock,
    query,
)

from .agent import _claude_auth_env, generate_brief, load_output_spec, load_system_prompt
from .contracts import OutputContractError, validate_output


HERE = Path(__file__).resolve().parents[2]
DOC_STORE = (
    Path.home()
    / "Desktop" / "Charlie-Oscar-OS-Prep" / "co-platform"
    / "agents" / "scout" / "doc-store"
)
DEFAULT_CASES = DOC_STORE / "evals" / "cases.jsonl"
DEFAULT_SCHEMA = DOC_STORE / "evals" / "cases-schema.json"
DEFAULT_RUBRIC = DOC_STORE / "evals" / "rubric.md"
DEFAULT_SPECS_DIR = DOC_STORE / "specs"
DEFAULT_MODEL = "claude-opus-4-7"
JUDGE_MODEL = "claude-opus-4-7"


# ---------- Loading + light validation ----------

def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
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
    """Light field-level validation mirroring 07-scout_cases_schema.json."""
    valid_task_types = {
        "digest-and-propose", "compare-options",
        "background-prep", "surface-decisions",
    }
    valid_dimensions = {
        "FramingQuality", "Relevance", "Honesty",
        "FrameNotRecommend", "InSeat",
    }
    id_re = re.compile(r"^scout-[a-z0-9-]+-[0-9]{3}$")

    ok = True
    seen: set[str] = set()
    for c in cases:
        cid = c.get("id", "<missing>")
        if cid in seen:
            print(f"  DUPLICATE id: {cid}"); ok = False
        seen.add(cid)
        if not id_re.match(cid):
            print(f"  {cid}: id must match scout-<slug>-<NNN>"); ok = False
        if c.get("task_type") not in valid_task_types:
            print(f"  {cid}: bad task_type {c.get('task_type')!r}"); ok = False
        if not c.get("input", {}).get("material"):
            print(f"  {cid}: missing input.material"); ok = False
        if not c.get("brief", {}).get("the_question"):
            print(f"  {cid}: missing brief.the_question"); ok = False
        if not c.get("must_not"):
            print(f"  {cid}: missing must_not"); ok = False
        dims = c.get("rubric", {}).get("dimensions") or []
        if not dims:
            print(f"  {cid}: rubric has no dimensions"); ok = False
        bad_dims = set(dims) - valid_dimensions
        if bad_dims:
            print(f"  {cid}: invalid rubric dimensions {sorted(bad_dims)}"); ok = False
        if c.get("difficulty") not in {"easy", "medium", "hard"}:
            print(f"  {cid}: bad difficulty {c.get('difficulty')!r}"); ok = False
    print(f"Validated {len(cases)} cases. {'OK' if ok else 'PROBLEMS FOUND'}.")
    return ok


# ---------- Hard pre-filter ----------

@dataclass
class HardCheckResult:
    hit_must_not: list[str]
    structural_error: str | None  # set if validate_output rejected the brief


def hard_checks(case: dict[str, Any], output: str) -> HardCheckResult:
    """Cheap deterministic checks before paying for the judge.

    `must_not` items in the cases file are short English descriptions, not
    literal strings to match. We treat them as substring proxies (same approach
    as the existing CO score.py). In practice these are coarse: the real
    judgement on framing nuance comes from the LLM judge plus Mal's spot-check.

    Two failure modes are also hard-checked structurally:
      - Output fails `contracts.validate_output` (the same gate scout uses at
        runtime). If validation fails here, the case is capped at 0.
      - A CENTRAL decision in the footer carries a scout_read. Already covered
        by validate_output, included here for explicitness.
    """
    out_lower = output.lower()
    must_not_hits = [
        bad for bad in case.get("must_not", []) if bad.lower() in out_lower
    ]

    structural_error: str | None = None
    expected_brief_id = case.get("brief", {}).get("brief_id") or case["id"]
    try:
        validate_output(output, expected_brief_id=expected_brief_id)
    except OutputContractError as e:
        structural_error = str(e)

    return HardCheckResult(
        hit_must_not=must_not_hits,
        structural_error=structural_error,
    )


# ---------- LLM-as-judge ----------

_JUDGE_SYSTEM = """You are a strict, calibrated eval judge for Scout, a research-and-synthesis agent.

Score the *framing*, not whether you agree with Scout's conclusions. A brief
is good if it lets Mal decide fast and well, including by surfacing options or
conflicts a lazy synthesis would miss. A brief is NOT good merely because its
conclusions match what Mal already thought. Reward inconvenient flags.

Use ONLY the score definitions from the rubric you are given. Do not score on
vibes. Return JSON only, no prose."""


_JUDGE_USER_TEMPLATE = """=== RUBRIC (anchor your scores in these definitions) ===
{rubric}

=== CASE ===
id: {case_id}
task_type: {task_type}
the_question: {the_question}
constraints: {constraints}
known_central: {known_central}
good_looks_like: {good_looks_like}

=== GOLDEN ===
required_elements:
{required_elements}

should_surface (high-value items a strong brief raises, even if inconvenient):
{should_surface}

=== DIMENSIONS TO SCORE ===
{dimensions}

=== SCOUT'S OUTPUT ===
{output}

Return JSON of exactly this shape:
{{
  "scores": {{"<Dimension>": <0-3 int>, ...}},
  "rationale": {{"<Dimension>": "<one short sentence>", ...}},
  "should_surface_hits": ["<verbatim item from should_surface that the brief covers>", ...]
}}

Score every dimension listed under DIMENSIONS TO SCORE. Do not add others."""


def _format_list(items: Iterable[str]) -> str:
    items = list(items)
    if not items:
        return "  (none)"
    return "\n".join(f"  - {it}" for it in items)


def _strip_to_json(text: str) -> str:
    """Pull the JSON object out of the judge's reply, tolerating code fences."""
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        return m.group(1)
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        return m.group(0)
    return text


async def llm_judge(
    case: dict[str, Any],
    output: str,
    rubric_text: str,
) -> dict[str, Any]:
    """One Claude call. No tools. Returns parsed JSON scores."""
    user = _JUDGE_USER_TEMPLATE.format(
        rubric=rubric_text,
        case_id=case["id"],
        task_type=case["task_type"],
        the_question=case["brief"]["the_question"],
        constraints=case["brief"].get("constraints", ""),
        known_central=case["brief"].get("known_central", ""),
        good_looks_like=case["brief"].get("good_looks_like", ""),
        required_elements=_format_list(case["golden"].get("required_elements", [])),
        should_surface=_format_list(case["golden"].get("should_surface", [])),
        dimensions=_format_list(case["rubric"]["dimensions"]),
        output=output,
    )

    options = ClaudeAgentOptions(
        system_prompt=_JUDGE_SYSTEM,
        model=JUDGE_MODEL,
        allowed_tools=[],
        disallowed_tools=["Bash", "Read", "Write", "Edit", "WebFetch", "WebSearch"],
        permission_mode="dontAsk",  # deny anything not pre-approved (nothing is)
    )

    chunks: list[str] = []
    with _claude_auth_env():
        async for message in query(prompt=user, options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        chunks.append(block.text)

    raw = "".join(chunks).strip()
    parsed_text = _strip_to_json(raw)
    try:
        return json.loads(parsed_text)
    except json.JSONDecodeError as e:
        return {
            "scores": {},
            "rationale": {"_error": f"judge did not return valid JSON: {e}"},
            "should_surface_hits": [],
            "_raw": raw,
        }


# ---------- Running ----------

async def _run_scout_on_case(case: dict[str, Any], specs_dir: Path, model: str) -> str:
    """Invoke Scout against a case. Builds a synthetic brief from the case fields."""
    brief_id = case["id"]
    b = case["brief"]
    brief_text = "\n".join([
        f"BRIEF_ID:        {brief_id}",
        f"DATE:            [today]",
        f"MATERIAL:        {case['input']['material']}",
        f"THE QUESTION:    {b['the_question']}",
        f"FEEDS DECISIONS: {b.get('feeds_decisions', '')}",
        f"CONSTRAINTS:     {b.get('constraints', '')}",
        f"KNOWN CENTRAL:   {b.get('known_central', '')}",
        f"GOOD LOOKS LIKE: {b.get('good_looks_like', '')}",
        f"SCOPE EDGES:     (none stated)",
    ])
    material = case["input"]["material"]
    notes = case["input"].get("notes", "")
    material_text = f"{material}\n\n(notes from Mal: {notes})" if notes else material

    result = await generate_brief(
        brief_text=brief_text,
        material_text=material_text,
        system_prompt=load_system_prompt(specs_dir),
        output_spec_text=load_output_spec(specs_dir),
        model=model,
        cwd=Path.cwd(),
    )
    return result.text


def _print_case_result(
    case_id: str,
    hard: HardCheckResult,
    judge: dict[str, Any] | None,
) -> None:
    failures: list[str] = []
    if hard.hit_must_not:
        failures.append("must_not: " + "; ".join(hard.hit_must_not))
    if hard.structural_error:
        failures.append(f"structure: {hard.structural_error}")
    status = "FAIL" if failures else "OK"
    print(f"[{status}] {case_id}")
    for f in failures:
        print(f"    {f}")
    if judge:
        scores = judge.get("scores", {})
        for dim, sc in scores.items():
            print(f"    {dim:18s} {sc}")
        hits = judge.get("should_surface_hits", [])
        if hits:
            print(f"    should_surface_hits: {len(hits)}")


def _read_outputs_jsonl(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for row in load_jsonl(path):
        out[row["id"]] = row.get("output", "")
    return out


def _argparse() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="scout-eval", description="Scout eval harness.")
    p.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    p.add_argument("--rubric", type=Path, default=DEFAULT_RUBRIC)
    p.add_argument("--specs-dir", type=Path, default=DEFAULT_SPECS_DIR)
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--validate", action="store_true",
                   help="Schema-check cases only.")
    p.add_argument("--run", action="store_true",
                   help="Run Scout against each case and score the output.")
    p.add_argument("--score", type=Path, metavar="OUTPUTS_JSONL",
                   help="Score pre-computed outputs from a JSONL file.")
    p.add_argument("--case", action="append", default=None,
                   help="Limit to specific case id(s). Repeatable.")
    p.add_argument("--no-judge", action="store_true",
                   help="Skip the LLM judge; run hard checks only.")
    return p


async def _main_async(args: argparse.Namespace) -> int:
    cases = load_jsonl(args.cases)
    if args.case:
        wanted = set(args.case)
        cases = [c for c in cases if c["id"] in wanted]

    if args.validate or not (args.run or args.score):
        ok = validate_cases(cases)
        if not (args.run or args.score):
            return 0 if ok else 1

    rubric_text = args.rubric.read_text(encoding="utf-8") if not args.no_judge else ""

    pre_outputs: dict[str, str] = {}
    if args.score is not None:
        pre_outputs = _read_outputs_jsonl(args.score)

    overall_ok = True
    for case in cases:
        if args.score is not None:
            output_text = pre_outputs.get(case["id"], "")
            if not output_text:
                print(f"[SKIP] {case['id']}: no output in {args.score}")
                overall_ok = False
                continue
        else:
            print(f"[run] {case['id']} ...")
            output_text = await _run_scout_on_case(case, args.specs_dir, args.model)

        hard = hard_checks(case, output_text)
        judge_result: dict[str, Any] | None = None
        if not args.no_judge and not hard.hit_must_not and not hard.structural_error:
            judge_result = await llm_judge(case, output_text, rubric_text)
        _print_case_result(case["id"], hard, judge_result)
        if hard.hit_must_not or hard.structural_error:
            overall_ok = False

    return 0 if overall_ok else 1


def main(argv: list[str] | None = None) -> int:
    args = _argparse().parse_args(argv)
    return asyncio.run(_main_async(args))


if __name__ == "__main__":
    raise SystemExit(main())
