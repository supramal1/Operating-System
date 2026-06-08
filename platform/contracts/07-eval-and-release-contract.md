# C07 Eval And Release Contract

## Purpose

Define what quality evidence is required before changes go live.

## Draft Rules

### Rule 1: Critical Eval Failures Block Release

Enforcement: hard-enforced

Mechanism: release gate checks golden eval results.

Evidence: eval run id, failing cases, release decision.

### Rule 2: Eval Categories Track Cost Of Being Wrong

Enforcement: soft/model-honoured until weighting is encoded.

Mechanism: eval schema and scoring config.

Evidence: category coverage report.

## Open Questions

- First pass/fail threshold.
- Which cases are critical blockers.
- Who signs off eval updates?
