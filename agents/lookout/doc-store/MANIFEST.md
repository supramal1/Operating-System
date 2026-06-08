# Lookout doc-store — manifest

Short index of every file under `doc-store/`. One line each.

## specs/

- `specs/system-prompt.md` — Lookout's persona, hard rules (AC-1, AC-4,
  MC-6), judgment discipline, honesty section, frame-don't-act stance.
- `specs/output-spec.md` — The six-section layout (glance, meetings,
  changes, memory, gaps, technical) and the JSON footer schema.

## evals/

- `evals/rubric.md` — To be authored by parallel agent. Hand-scoring rubric
  for daily briefs (relevance, honesty, frame-not-act, in-seat).
- `evals/cases.jsonl` — To be authored by parallel agent. One eval case per
  line; case_id pattern `lookout-<slug>-<NNN>`.
- `evals/cases-schema.json` — To be authored by parallel agent. JSON schema
  for the cases file.

## calibration/

- `calibration/CALIBRATION-LOG.md` — Hand-scored eval runs and notes on
  relevance-judgment drift over time. Stub at scaffold.
