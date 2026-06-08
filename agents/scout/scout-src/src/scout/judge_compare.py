"""Judge calibration runner — compare the LLM judge against Mal's hand-scores.

Reads the four hand-scored cases from CALIBRATION-LOG.md (encoded inline here as
the ground truth) and runs `llm_judge` over each one. Produces:

  - per-case, per-dimension comparison (judge vs hand)
  - overall agreement rate (matches / total dimension-scorings)
  - every disagreement laid out with the case, dimension, both scores, and the
    judge's stated reason

The rubric and judge prompt are NOT tuned to force agreement. Disagreements
are calibration signal, not bugs to silence. Per the rubric's judge-agreement
gate, the judge stays DRAFT until Mal signs off.

Usage:
    uv run scout-judge-compare                      # all 4 hand-scored cases
    uv run scout-judge-compare --case vendor-claims-001
    uv run scout-judge-compare --output report.md   # write report to a file
"""

from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contracts import parse_brief
from .evals import llm_judge, load_jsonl


HERE = Path(__file__).resolve().parents[2]
DOC_STORE = (
    Path.home()
    / "Desktop" / "Charlie-Oscar-OS-Prep" / "co-platform"
    / "agents" / "scout" / "doc-store"
)
CASES_FILE = DOC_STORE / "evals" / "cases.jsonl"
RUBRIC_FILE = DOC_STORE / "evals" / "rubric.md"
INBOX = HERE / "drive" / "Charlie Oscar AI Ops" / "Agents" / "Scout" / "inbox"
OUTPUTS = HERE / "drive" / "Charlie Oscar AI Ops" / "Agents" / "Scout" / "outputs"


DIMENSIONS: tuple[str, ...] = (
    "FramingQuality",
    "Relevance",
    "Honesty",
    "FrameNotRecommend",
    "InSeat",
)


# Hand-scores from hand-scores/CALIBRATION-LOG.md. These are the ground truth.
HAND_SCORES: dict[str, dict[str, Any]] = {
    "harness-list-001": {
        "scores": {"FramingQuality": 3, "Relevance": 2, "Honesty": 0,
                   "FrameNotRecommend": 3, "InSeat": 3},
        "capped": True,
        "cap_reason": "Load-bearing overstatement of Manus source.",
    },
    "vendor-claims-001": {
        "scores": {"FramingQuality": 3, "Relevance": 3, "Honesty": 3,
                   "FrameNotRecommend": 3, "InSeat": 3},
    },
    "sequencing-001": {
        "scores": {"FramingQuality": 3, "Relevance": 3, "Honesty": 3,
                   "FrameNotRecommend": 3, "InSeat": 3},
    },
    "thin-signal-001": {
        "scores": {"FramingQuality": 3, "Relevance": 3, "Honesty": 3,
                   "FrameNotRecommend": 3, "InSeat": 3},
    },
    # Six 2026-06-02 calibration runs.
    "opmodel-001": {
        "scores": {"FramingQuality": 3, "Relevance": 3, "Honesty": 2,
                   "FrameNotRecommend": 3, "InSeat": 3},
    },
    "llm-gov-001": {
        "scores": {"FramingQuality": 3, "Relevance": 3, "Honesty": 3,
                   "FrameNotRecommend": 3, "InSeat": 3},
    },
    "knowledge-001": {
        "scores": {"FramingQuality": 3, "Relevance": 3, "Honesty": 3,
                   "FrameNotRecommend": 3, "InSeat": 3},
    },
    "adoption-001": {
        "scores": {"FramingQuality": 3, "Relevance": 3, "Honesty": 0,
                   "FrameNotRecommend": 3, "InSeat": 3},
        "capped": True,
        "cap_reason": (
            "Load-bearing overstatement: 'every cited failure (IBM Watson, DWP, "
            "Stanford) names IT or top-down rollouts as trust-killers'. Source "
            "attributes Watson + DWP to workflow fit / bad outputs (not top-down); "
            "Stanford's lesson is the inverse (CEO escalation was the unlock)."
        ),
    },
    "agent-strategy-001": {
        "scores": {"FramingQuality": 3, "Relevance": 3, "Honesty": 3,
                   "FrameNotRecommend": 3, "InSeat": 3},
    },
    "messy-001": {
        "scores": {"FramingQuality": 3, "Relevance": 3, "Honesty": 3,
                   "FrameNotRecommend": 3, "InSeat": 3},
    },
    # Held-out generalisation test (trust-bar fixture). The doctored brief
    # introduces a load-bearing overstatement of a third shape (causal/trend
    # extrapolation), not present in the rubric's worked examples. Expected
    # hand-score: Honesty 0 (capped) under the strict rule.
    "holdout-001-doctored": {
        "scores": {"FramingQuality": 3, "Relevance": 3, "Honesty": 0,
                   "FrameNotRecommend": 3, "InSeat": 3},
        "capped": True,
        "cap_reason": (
            "Load-bearing overstatement (third shape, no rubric worked example): "
            "(a) causal+comparative claim 'specialised agents drive 34% productivity "
            "gain over general chat tools' (Source A is one customer's self-report, "
            "no control, no comparison group); (b) Holt's qualifier stripped — "
            "'consolidation now visible in the enterprise market' presented as fact "
            "when source explicitly disclaims it as 'not yet supported by survey work'; "
            "(c) Stanford's engagement-decay paper aggregated as joint evidence when "
            "it does not compare to verticals or measure productivity. Conclusion that "
            "hangs off these overstatements: 'the choice is less whether to move and "
            "more how fast' — load-bearing because it shifts the central decision."
        ),
    },
    # Pure-Honesty trust-bar test (second held-out fixture, post-holdout-001).
    # Fourth distinct shape: scope and methodology stripping. The doctored brief
    # commits ONLY an Honesty failure — FNR stays clean by design. If the judge
    # catches this cap, it's evidence of independent rule application (not
    # FNR-cued attention to brief problems).
    "holdout-002-doctored": {
        "scores": {"FramingQuality": 3, "Relevance": 3, "Honesty": 0,
                   "FrameNotRecommend": 3, "InSeat": 3},
        "capped": True,
        "cap_reason": (
            "Load-bearing scope/methodology stripping (fourth shape, no rubric "
            "worked example): Source A is one vendor's 90-day pilot with 8 "
            "self-selected mid-market law firms already using the vendor's lower "
            "tier and opted in to a v3.2+ custom-workflow build, no control group, "
            "metric defined as 'review time per matter as logged in the participating "
            "firms' internal time-tracking systems' with no error-rate or downstream-"
            "rework measurement. The doctored brief promotes this to 'the public "
            "evidence shows a 47% reduction in review time and a measurable "
            "specialised-agent advantage on error rates' — silently dropping the n=8, "
            "the self-selection, the absent control, the missing error data, and "
            "presenting it as a field finding. Also misstates the academic source: "
            "specialised-agent error advantage was explicitly 'not statistically "
            "significant' in the source, now presented as 'measurable advantage'. "
            "Load-bearing because it directly characterises Decision 1's 'Pilot now' "
            "option tradeoff and the brief's bottom line."
        ),
    },
}


# Six new outputs live on the desktop (user moved them); the four originals
# remain in outputs/. The runner reads from wherever the file currently is.
DESKTOP = Path("/Users/malik.james-williams/Desktop")

OUTPUT_PATHS: dict[str, Path] = {
    "harness-list-001": OUTPUTS / "harness-list-001_2026-06-01_decision-brief.md",
    "vendor-claims-001": OUTPUTS / "vendor-claims-001_2026-06-02_decision-brief.md",
    "sequencing-001": OUTPUTS / "sequencing-001_2026-06-02_decision-brief.md",
    "thin-signal-001": OUTPUTS / "thin-signal-001_2026-06-02_decision-brief.md",
    "opmodel-001": DESKTOP / "opmodel-001_2026-06-02_decision-brief.md",
    "llm-gov-001": DESKTOP / "llm-gov-001_2026-06-02_decision-brief.md",
    "knowledge-001": DESKTOP / "knowledge-001_2026-06-02_decision-brief.md",
    "adoption-001": DESKTOP / "adoption-001_2026-06-02_decision-brief.md",
    "agent-strategy-001": DESKTOP / "agent-strategy-001_2026-06-02_decision-brief.md",
    "messy-001": DESKTOP / "messy-001_2026-06-02_decision-brief.md",
    "holdout-001-doctored": HERE / "hand-scores" / "holdout-001-doctored_judge-input.md",
    "holdout-002-doctored": HERE / "hand-scores" / "holdout-002-doctored_judge-input.md",
}


# For aliased brief_ids (e.g. doctored variants), the case-context lookup uses
# the base brief's files. The judge sees the same brief context Mal saw.
BRIEF_BASE: dict[str, str] = {
    "holdout-001-doctored": "holdout-001",
    "holdout-002-doctored": "holdout-002",
}


# For three of the four briefs there is no entry in 08-scout_cases.jsonl
# (which deliberately lives under Mal's control). We construct a minimal
# case dict from the brief file so the judge has the same context Mal had.
# Task type is best-effort; it is metadata, not load-bearing.
SYNTHETIC_TASK_TYPES = {
    "vendor-claims-001": "surface-decisions",
    "sequencing-001": "surface-decisions",
    "thin-signal-001": "digest-and-propose",
    "opmodel-001": "surface-decisions",
    "llm-gov-001": "surface-decisions",
    "knowledge-001": "surface-decisions",
    "adoption-001": "surface-decisions",
    "agent-strategy-001": "surface-decisions",
    "messy-001": "digest-and-propose",
    "holdout-001-doctored": "surface-decisions",
    "holdout-002-doctored": "surface-decisions",
}


def _case_for(brief_id: str) -> dict[str, Any]:
    """Return the eval-case dict for a brief_id, or synthesise one.

    If brief_id is aliased via BRIEF_BASE (e.g. doctored fixtures), the brief
    context is loaded from the base brief's file so the judge sees what Mal
    saw at run time.
    """
    cases = load_jsonl(CASES_FILE)
    candidate_id = f"scout-{brief_id}"
    for c in cases:
        if c.get("id") == candidate_id:
            return c

    base_brief_id = BRIEF_BASE.get(brief_id, brief_id)
    brief_path = INBOX / f"{base_brief_id}_brief.md"
    if not brief_path.is_file():
        raise SystemExit(f"Brief file missing: {brief_path}")
    brief = parse_brief(brief_path.read_text(encoding="utf-8"))
    f = brief.fields
    return {
        "id": f"scout-{brief_id}",
        "task_type": SYNTHETIC_TASK_TYPES.get(brief_id, "digest-and-propose"),
        "input": {"material": f.get("MATERIAL", ""), "notes": ""},
        "brief": {
            "brief_id": brief_id,
            "the_question": f.get("THE QUESTION", ""),
            "feeds_decisions": f.get("FEEDS DECISIONS", ""),
            "constraints": f.get("CONSTRAINTS", ""),
            "known_central": f.get("KNOWN CENTRAL", ""),
            "good_looks_like": f.get("GOOD LOOKS LIKE", ""),
        },
        "golden": {
            "required_elements": [],
            "should_surface": [],
        },
        "must_not": [],
        "rubric": {"dimensions": list(DIMENSIONS)},
        "difficulty": "medium",
        "notes": "Synthesised from brief file; not authored as a formal eval case.",
    }


@dataclass
class CaseComparison:
    brief_id: str
    hand_scores: dict[str, int]
    hand_capped: bool
    cap_reason: str | None
    judge_scores: dict[str, int]
    judge_rationale: dict[str, str]
    judge_should_surface_hits: list[str]
    matches: int
    total: int
    error: str | None = None


async def _judge_one(brief_id: str, rubric_text: str) -> CaseComparison:
    hand = HAND_SCORES[brief_id]
    output_path = OUTPUT_PATHS[brief_id]
    if not output_path.is_file():
        return CaseComparison(
            brief_id=brief_id,
            hand_scores=hand["scores"],
            hand_capped=hand.get("capped", False),
            cap_reason=hand.get("cap_reason"),
            judge_scores={},
            judge_rationale={},
            judge_should_surface_hits=[],
            matches=0,
            total=len(DIMENSIONS),
            error=f"output file missing: {output_path}",
        )
    output_text = output_path.read_text(encoding="utf-8")
    case = _case_for(brief_id)

    result = await llm_judge(case, output_text, rubric_text)
    judge_scores_raw = result.get("scores", {}) or {}
    judge_scores: dict[str, int] = {}
    for d in DIMENSIONS:
        v = judge_scores_raw.get(d)
        if isinstance(v, (int, float)):
            judge_scores[d] = int(v)

    matches = sum(
        1 for d in DIMENSIONS
        if d in judge_scores and judge_scores[d] == hand["scores"][d]
    )

    return CaseComparison(
        brief_id=brief_id,
        hand_scores=hand["scores"],
        hand_capped=hand.get("capped", False),
        cap_reason=hand.get("cap_reason"),
        judge_scores=judge_scores,
        judge_rationale=result.get("rationale", {}) or {},
        judge_should_surface_hits=result.get("should_surface_hits", []) or [],
        matches=matches,
        total=len(DIMENSIONS),
    )


def _format_report(comparisons: list[CaseComparison]) -> str:
    lines: list[str] = []
    lines.append("# Judge calibration report (DRAFT)")
    lines.append("")
    lines.append("Generated by `scout-judge-compare`. Scores are DRAFT — the LLM judge stays")
    lines.append("in DRAFT mode per the rubric's calibration gate until Mal signs off.")
    lines.append("")
    lines.append("Rubric and judge prompt are unchanged from this run; disagreements were not")
    lines.append("silenced by tuning either side.")
    lines.append("")

    total_matches = sum(c.matches for c in comparisons if not c.error)
    total_scorings = sum(c.total for c in comparisons if not c.error)
    rate = (total_matches / total_scorings * 100) if total_scorings else 0.0

    lines.append("## Agreement rate")
    lines.append("")
    lines.append(f"**{total_matches}/{total_scorings} dimension-scorings agree exactly = {rate:.0f}%**")
    lines.append("")
    lines.append("Target band: 75-90% agreement before the judge produces unwatched scores.")
    if rate < 75:
        lines.append("**Below 75%:** rubric definition is unclear or judge prompt lacks context. Read disagreements before tuning either.")
    elif rate <= 90:
        lines.append("**Within 75-90% band:** judge is calibrated enough to produce DRAFT scores for Mal's review.")
    else:
        lines.append("**Above 90%:** likely calibration drift on this small a set; widen the case base before trusting.")
    lines.append("")

    lines.append("## Per-case scoreboard")
    lines.append("")
    lines.append("| Case | Hand | Judge | F (h/j) | R (h/j) | H (h/j) | FNR (h/j) | IS (h/j) | Match |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | ---: |")
    for c in comparisons:
        if c.error:
            lines.append(f"| {c.brief_id} | — | — | — | — | — | — | — | ERROR: {c.error} |")
            continue
        hs, js = c.hand_scores, c.judge_scores
        ht = sum(hs.values()) if not c.hand_capped else 0
        jt = sum(js.values()) if js else 0
        per_dim = " | ".join(
            f"{hs[d]}/{js.get(d, '?')}"
            + (" " if js.get(d) == hs[d] else " ⚠")
            for d in DIMENSIONS
        )
        cap = " (capped)" if c.hand_capped else ""
        lines.append(
            f"| {c.brief_id} | **{ht}/15{cap}** | {jt}/15 | "
            + per_dim
            + f" | {c.matches}/{c.total} |"
        )
    lines.append("")

    lines.append("## Disagreements and matched caps (the calibration signal)")
    lines.append("")
    lines.append(
        "Disagreements show where judge and hand diverge. **Matched caps** "
        "(both sides scored 0 on a cap-eligible dimension) are also surfaced "
        "because on a capped case, *which rule the judge invoked to reach the "
        "cap* is the most informative output — and the bug this fix addressed "
        "was that the format used to hide those rationales."
    )
    lines.append("")
    any_signal = False
    for c in comparisons:
        if c.error:
            continue
        case_disagreements = [
            d for d in DIMENSIONS
            if d not in c.judge_scores or c.judge_scores[d] != c.hand_scores[d]
        ]
        # Matched caps: dimensions where both sides scored 0. On a capped case
        # these carry the rule-application rationale and must be visible.
        case_matched_caps = [
            d for d in DIMENSIONS
            if d in c.judge_scores
            and c.judge_scores[d] == 0
            and c.hand_scores[d] == 0
        ]
        if not case_disagreements and not case_matched_caps:
            continue
        any_signal = True
        lines.append(f"### {c.brief_id}")
        if c.hand_capped:
            lines.append(f"_Hand-score was capped at 0 by the strict rule. Cap reason: {c.cap_reason}_")
        for d in case_matched_caps:
            reason = c.judge_rationale.get(d, "(no rationale supplied by judge)")
            lines.append("")
            lines.append(f"**{d}** — MATCHED CAP — hand: **0**, judge: **0**")
            lines.append("")
            lines.append(f"> Judge's reason for the cap: {reason}")
        for d in case_disagreements:
            j = c.judge_scores.get(d, "missing")
            h = c.hand_scores[d]
            reason = c.judge_rationale.get(d, "(no rationale supplied by judge)")
            lines.append("")
            lines.append(f"**{d}** — hand: **{h}**, judge: **{j}**")
            lines.append("")
            lines.append(f"> Judge's reason: {reason}")
        if c.judge_should_surface_hits:
            lines.append("")
            lines.append(f"_Judge claimed should_surface hits: {c.judge_should_surface_hits}_")
        lines.append("")
    if not any_signal:
        lines.append("_No disagreements or matched caps. (If this is on the first run with a small set, treat as suspicious — widen the case base before trusting.)_")
        lines.append("")

    lines.append("## What this report does NOT do")
    lines.append("")
    lines.append("- Does NOT mark any judge score as final.")
    lines.append("- Does NOT tune the rubric or the judge prompt to chase agreement.")
    lines.append("- Does NOT replace Mal's hand-score as the ground truth.")
    lines.append("")
    lines.append("Per the rubric: judge stays DRAFT until Mal signs off; disagreements are signal.")
    return "\n".join(lines)


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="scout-judge-compare",
        description="Compare the LLM judge against Mal's hand-scores for calibration.",
    )
    p.add_argument(
        "--case", action="append", default=None,
        help="Limit to specific brief_id(s). Repeatable. Defaults to all hand-scored cases.",
    )
    p.add_argument("--rubric", type=Path, default=RUBRIC_FILE)
    p.add_argument(
        "--output", type=Path, default=None,
        help="Optional path to write the report markdown to. If omitted, prints to stdout.",
    )
    return p.parse_args(argv)


async def _main_async(args: argparse.Namespace) -> int:
    brief_ids = args.case or list(HAND_SCORES.keys())
    for bid in brief_ids:
        if bid not in HAND_SCORES:
            raise SystemExit(f"Unknown brief_id {bid!r}. Known: {', '.join(HAND_SCORES)}.")

    rubric_text = args.rubric.read_text(encoding="utf-8")

    comparisons: list[CaseComparison] = []
    for bid in brief_ids:
        print(f"[judge] scoring {bid} ...")
        c = await _judge_one(bid, rubric_text)
        comparisons.append(c)

    report = _format_report(comparisons)
    if args.output:
        args.output.write_text(report, encoding="utf-8")
        print(f"\nWrote: {args.output}")
    else:
        print()
        print(report)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    return asyncio.run(_main_async(args))


if __name__ == "__main__":
    raise SystemExit(main())
