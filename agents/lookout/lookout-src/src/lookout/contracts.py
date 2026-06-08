"""Lookout contracts: output structural validation + required-gaps gate.

This module enforces the *structure* of Lookout's output. It does not judge
quality — evals and Mal's review handle that.

Aligned to output-spec.md (six sections):
    1. # The day at a glance
    2. # For each meeting
    3. # What changed worth knowing
    4. # From memory worth surfacing
    5. # What I couldn't check
    6. # The technical bit

Hard-enforced here:
- Output must contain all six section headings in spec order.
- Output must contain a fenced ```json ... ``` block (the "technical bit").
- That JSON must parse, be an object, and carry every required footer key.
- `run_id` in the footer must match the run_id passed in (round-trip check).
- `gaps` MUST be a non-empty array of strings. Empty gaps = honesty failure
  in v1 (email and personal memory are NEVER connected). Exit code 3.

If any check fails, the run aborts BEFORE the file is written.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any


# Substring matched (the spec headings allow trailing parenthetical context).
REQUIRED_HEADING_PREFIXES = (
    "# The day at a glance",
    "# For each meeting",
    "# What changed worth knowing",
    "# From memory worth surfacing",
    "# What I couldn't check",
    "# The technical bit",
)

# Find every fenced ```json``` block. The LAST one is the footer.
_FENCED_JSON_RE = re.compile(r"```json\s*(?P<body>\{.*?\})\s*```", re.DOTALL)

# Footer must carry these top-level keys.
_FOOTER_REQUIRED_KEYS = {
    "run_id",
    "date",
    "scope",
    "source_counts",
    "gaps",
    "langfuse_trace_id",
}

_SCOPE_REQUIRED_KEYS = {"principal_id", "client_scope", "cornerstone_namespace"}
_SOURCE_COUNTS_REQUIRED_KEYS = {
    "calendar_events",
    "cornerstone_items",
    "drive_added",
    "drive_modified",
}


class OutputContractError(ValueError):
    """Raised when Lookout's output fails structural validation."""


@dataclass(frozen=True)
class ValidatedOutput:
    text: str
    footer: dict[str, Any]


def validate_output(text: str, *, expected_run_id: str) -> ValidatedOutput:
    """Structurally validate Lookout's daily brief.

    Checks (any failure raises OutputContractError):
    - All six section-heading prefixes appear, in order.
    - A fenced ```json ... ``` block is present and parses as a JSON object.
    - Footer carries every required top-level key.
    - Footer `run_id` matches the run id passed in.
    - `gaps` is a non-empty list of non-empty strings (the honesty gate).
    """
    _check_headings_in_order(text)
    footer = _extract_footer(text)
    _check_footer_schema(footer)

    if footer["run_id"] != expected_run_id:
        raise OutputContractError(
            f"Footer run_id {footer['run_id']!r} does not match "
            f"expected {expected_run_id!r}."
        )

    return ValidatedOutput(text=text, footer=footer)


def _check_headings_in_order(text: str) -> None:
    indices: list[int] = []
    for prefix in REQUIRED_HEADING_PREFIXES:
        idx = text.find(prefix)
        if idx == -1:
            raise OutputContractError(
                f"Output is missing required heading prefix {prefix!r}. "
                f"See output-spec.md."
            )
        indices.append(idx)
    if indices != sorted(indices):
        raise OutputContractError(
            "Required headings are present but not in the spec order "
            "(glance -> meetings -> changes -> memory -> gaps -> technical)."
        )


def _extract_footer(text: str) -> dict[str, Any]:
    matches = list(_FENCED_JSON_RE.finditer(text))
    if not matches:
        raise OutputContractError(
            "Output must contain a fenced ```json ... ``` block "
            "(the 'technical bit' at the end)."
        )
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

    if not isinstance(footer["run_id"], str) or not footer["run_id"]:
        raise OutputContractError("Footer run_id must be a non-empty string.")

    if not isinstance(footer["date"], str) or not footer["date"]:
        raise OutputContractError("Footer date must be a non-empty ISO string.")

    scope = footer["scope"]
    if not isinstance(scope, dict):
        raise OutputContractError("Footer scope must be an object.")
    miss = _SCOPE_REQUIRED_KEYS - scope.keys()
    if miss:
        raise OutputContractError(f"Footer scope missing keys: {sorted(miss)}.")

    counts = footer["source_counts"]
    if not isinstance(counts, dict):
        raise OutputContractError("Footer source_counts must be an object.")
    miss = _SOURCE_COUNTS_REQUIRED_KEYS - counts.keys()
    if miss:
        raise OutputContractError(
            f"Footer source_counts missing keys: {sorted(miss)}."
        )

    # Honesty gate: gaps MUST be non-empty.
    gaps = footer["gaps"]
    if not isinstance(gaps, list):
        raise OutputContractError("Footer gaps must be an array of strings.")
    if not gaps:
        raise OutputContractError(
            "Footer gaps is empty. v1 Lookout has no email or personal-memory "
            "source, so gaps can never be empty. At minimum it must list "
            "'email-not-connected' and 'personal-memory-not-connected'."
        )
    for i, g in enumerate(gaps):
        if not isinstance(g, str) or not g.strip():
            raise OutputContractError(
                f"Footer gaps[{i}] must be a non-empty string."
            )

    trace_id = footer["langfuse_trace_id"]
    if trace_id is not None and not isinstance(trace_id, str):
        raise OutputContractError(
            "Footer langfuse_trace_id must be a string or null."
        )
