"""Scout contracts: input + output structural validation.

This module enforces the *structure* of Scout's inputs and outputs. It does not
judge quality - that is what the evals and Mal's review are for.

Aligned to the rewritten `03-output-spec.md` (plain-language, four parts):
  Part 1 — The answer
  Part 2 — The detail (decision blocks live here now)
  Part 3 — What's next
  Part 4 — The technical bit (a fenced JSON block, typically inside <details>)

Hard-enforced here:
- Required brief fields must be present and non-empty.
- Output must contain all four part headings in spec order.
- Output must contain a fenced ```json ... ``` block (the "technical bit").
- That JSON must parse, be an object, and carry `brief_id` matching the run.
- It must carry a `decisions` array. Each decision must have a `name`, a `tag`
  (string), and a `scout_suggestion` field (null or string).
- HARD DISCIPLINE GATE: if a decision's `tag` contains "yours to decide"
  (case-insensitive), `scout_suggestion` MUST be null. This is the new-spec
  equivalent of the old "no scout_read on CENTRAL decisions" gate.

If any of these fail, the run aborts BEFORE the file is written.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any


# ---------- Brief (input) ----------

REQUIRED_BRIEF_FIELDS = (
    "BRIEF_ID",
    "DATE",
    "MATERIAL",
    "THE QUESTION",
    "FEEDS DECISIONS",
    "CONSTRAINTS",
    "KNOWN CENTRAL",
    "GOOD LOOKS LIKE",
    "SCOPE EDGES",
)


@dataclass(frozen=True)
class Brief:
    brief_id: str
    raw: str
    fields: dict[str, str]


class BriefError(ValueError):
    """Raised when the input brief is malformed or missing required fields."""


_FIELD_LINE_RE = re.compile(
    r"^(?P<key>[A-Z][A-Z _]+):\s*(?P<value>.*)$"
)


def parse_brief(text: str) -> Brief:
    """Parse the filled-in brief template.

    The template uses `FIELD_NAME:` lines (see 05-brief-template.md). We tolerate
    extra prose and continuation lines, but every required field must appear with
    a non-empty value.
    """
    fields: dict[str, list[str]] = {}
    current_key: str | None = None

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        m = _FIELD_LINE_RE.match(line)
        if m and m.group("key").strip() in REQUIRED_BRIEF_FIELDS:
            current_key = m.group("key").strip()
            fields.setdefault(current_key, []).append(m.group("value").strip())
        elif current_key is not None and line.strip():
            # Continuation of the previous field's value.
            fields[current_key].append(line.strip())

    joined = {k: " ".join(v).strip() for k, v in fields.items()}

    missing = [f for f in REQUIRED_BRIEF_FIELDS if not joined.get(f)]
    if missing:
        raise BriefError(
            f"Brief is missing required fields: {', '.join(missing)}. "
            f"See 05-brief-template.md."
        )

    brief_id = joined["BRIEF_ID"]
    if not re.fullmatch(r"[a-zA-Z0-9._-]+", brief_id):
        raise BriefError(
            f"BRIEF_ID {brief_id!r} must be a filesystem-safe slug "
            f"(letters, digits, dot, underscore, dash only)."
        )

    return Brief(brief_id=brief_id, raw=text, fields=joined)


# ---------- Decision-brief output ----------

# Substring matched (the new spec's headings carry parentheticals like
# "(keep it to about one screen)", which we do not want to require verbatim).
REQUIRED_HEADING_PREFIXES = (
    "## Part 1: The answer",
    "## Part 2: The detail",
    "## Part 3: What's next",
    "## Part 4: The technical bit",
)

# Find every fenced ```json``` block. We take the LAST one as the technical
# footer, since the new spec wraps it inside a collapsed <details> section that
# may have trailing markup.
_FENCED_JSON_RE = re.compile(r"```json\s*(?P<body>\{.*?\})\s*```", re.DOTALL)

# Minimum keys the JSON footer must carry.
_FOOTER_REQUIRED_KEYS = {"brief_id", "decisions"}
_DECISION_REQUIRED_KEYS = {"name", "tag", "scout_suggestion"}

# Substring (case-insensitive) that marks a decision as "yours to decide" -
# i.e. a big decision Scout must NOT carry a suggestion on.
_YOURS_TO_DECIDE = "yours to decide"


class OutputContractError(ValueError):
    """Raised when Scout's output fails structural validation."""


@dataclass(frozen=True)
class ValidatedOutput:
    text: str
    footer: dict[str, Any]


def validate_output(text: str, expected_brief_id: str) -> ValidatedOutput:
    """Structurally validate Scout's decision brief.

    Checks (any failure raises OutputContractError):
    - All four part-heading prefixes appear, in order.
    - A fenced ```json ... ``` block is present and parses as a JSON object.
    - The footer carries `brief_id` (matching the run) and `decisions`.
    - Every decision has `name`, `tag`, `scout_suggestion`.
    - HARD DISCIPLINE GATE: any decision whose `tag` contains "yours to decide"
      (case-insensitive) must have `scout_suggestion == null`. This is the
      "frame, don't recommend on big decisions" gate.
    - RESTRAINT GATE: `decisions` may be empty ONLY IF the footer carries a
      non-empty `no_decisions_rationale` string explaining why nothing is
      decidable. Empty decisions without rationale is rejected (the "lazy
      Scout" case); empty decisions with rationale passes (the "honest
      restraint" case, e.g. thin-signal-001).
    """
    _check_headings_in_order(text)
    footer = _extract_footer(text)
    _check_footer_schema(footer)
    _check_frame_not_recommend(footer)

    if footer["brief_id"] != expected_brief_id:
        raise OutputContractError(
            f"Footer brief_id {footer['brief_id']!r} does not match "
            f"expected {expected_brief_id!r}."
        )

    return ValidatedOutput(text=text, footer=footer)


def _check_headings_in_order(text: str) -> None:
    indices: list[int] = []
    for prefix in REQUIRED_HEADING_PREFIXES:
        idx = text.find(prefix)
        if idx == -1:
            raise OutputContractError(
                f"Output is missing required heading prefix {prefix!r}. "
                f"See 03-output-spec.md."
            )
        indices.append(idx)
    if indices != sorted(indices):
        raise OutputContractError(
            "Required headings are present but not in the spec order "
            "(Part 1 -> 2 -> 3 -> 4)."
        )


def _extract_footer(text: str) -> dict[str, Any]:
    matches = list(_FENCED_JSON_RE.finditer(text))
    if not matches:
        raise OutputContractError(
            "Output must contain a fenced ```json ... ``` block "
            "(the 'technical bit' in Part 4)."
        )
    # The last fenced json is the footer (preceding ones, if any, are body).
    body = matches[-1].group("body")
    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        raise OutputContractError(f"Footer JSON does not parse: {e}") from e
    if not isinstance(data, dict):
        raise OutputContractError("Footer JSON must be an object, not an array.")
    return data


def _check_footer_schema(footer: dict[str, Any]) -> None:
    missing = _FOOTER_REQUIRED_KEYS - footer.keys()
    if missing:
        raise OutputContractError(
            f"Footer is missing required keys: {sorted(missing)}."
        )

    if not isinstance(footer["brief_id"], str) or not footer["brief_id"]:
        raise OutputContractError("Footer brief_id must be a non-empty string.")

    decisions = footer["decisions"]
    if not isinstance(decisions, list):
        raise OutputContractError("Footer decisions must be an array.")
    if not decisions:
        # Empty decisions array is allowed ONLY IF accompanied by a non-empty
        # no_decisions_rationale string. This distinguishes honest restraint
        # ("nothing to decide here, and here's why") from lazy output.
        rationale = footer.get("no_decisions_rationale")
        if not isinstance(rationale, str) or not rationale.strip():
            raise OutputContractError(
                "Empty decisions array requires a no_decisions_rationale "
                "field explaining why there is nothing to decide."
            )
        return  # restraint case; no per-decision checks to run

    for i, d in enumerate(decisions):
        if not isinstance(d, dict):
            raise OutputContractError(f"decisions[{i}] must be an object.")
        miss = _DECISION_REQUIRED_KEYS - d.keys()
        if miss:
            raise OutputContractError(
                f"decisions[{i}] missing keys: {sorted(miss)}."
            )
        if not isinstance(d["name"], str) or not d["name"]:
            raise OutputContractError(
                f"decisions[{i}].name must be a non-empty string."
            )
        if not isinstance(d["tag"], str) or not d["tag"]:
            raise OutputContractError(
                f"decisions[{i}].tag must be a non-empty string "
                f"(e.g. 'yours to decide' or 'Scout suggests <option>')."
            )
        sug = d["scout_suggestion"]
        if sug is not None and not isinstance(sug, str):
            raise OutputContractError(
                f"decisions[{i}].scout_suggestion must be null or a string."
            )


def _check_frame_not_recommend(footer: dict[str, Any]) -> None:
    """Hard discipline gate: no scout_suggestion on 'yours to decide' decisions."""
    violations: list[str] = []
    for i, d in enumerate(footer["decisions"]):
        tag_lower = d["tag"].lower()
        is_big = _YOURS_TO_DECIDE in tag_lower
        if is_big and d.get("scout_suggestion") not in (None, ""):
            violations.append(
                f"decisions[{i}] ({d.get('name', '?')!r}) is tagged "
                f"{d['tag']!r} but carries a scout_suggestion: "
                f"{d.get('scout_suggestion')!r}."
            )
    if violations:
        raise OutputContractError(
            "Frame-don't-recommend violation on 'yours to decide' "
            "decisions:\n  - " + "\n  - ".join(violations)
        )
