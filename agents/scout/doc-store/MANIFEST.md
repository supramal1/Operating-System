# Scout Doc Store

Canonical home for what Scout's runtime reads + the calibration log it informs. Scout's path constants now point here.

## Status: PHASE 1 COMPLETE (2026-06-02)

The 6 files Scout's runtime + eval tooling actually loads have been moved out of `…/01-scout/` into this doc-store. Scout's code constants point at the new locations. All 17 unit tests pass; `scout --help` loads; `scout-eval --validate` validates 3 cases from the new path.

## What moved (Phase 1, done)

| Source (in `…/01-scout/`) | Destination | Read by |
|---|---|---|
| `02-system-prompt.md` | `specs/system-prompt.md` | `src/scout/agent.py` (`load_system_prompt`) |
| `03-output-spec.md` | `specs/output-spec.md` | `src/scout/agent.py` (`load_output_spec`) |
| `07-scout_cases_schema.json` | `evals/cases-schema.json` | `src/scout/evals.py` (`DEFAULT_SCHEMA`) |
| `08-scout_cases.jsonl` | `evals/cases.jsonl` | `src/scout/evals.py`, `batch.py`, `judge_compare.py` |
| `09-scout_rubric.md` | `evals/rubric.md` | `src/scout/evals.py`, `batch.py`, `judge_compare.py` |
| `hand-scores/CALIBRATION-LOG.md` | `calibration/CALIBRATION-LOG.md` | (history, not code) |

## Code changes (Phase 1, done)

A `DOC_STORE` constant was introduced in three modules and the path constants now derive from it:

```python
DOC_STORE = (
    Path.home()
    / "Desktop" / "Charlie-Oscar-OS-Prep" / "co-platform"
    / "agents" / "scout" / "doc-store"
)
```

| File | Lines changed | Change |
|---|---|---|
| `src/scout/run.py` | 37–41 | `DEFAULT_SPECS_DIR` now points at `…/doc-store/specs/` |
| `src/scout/agent.py` | 176 | reads `system-prompt.md` (was `02-system-prompt.md`) |
| `src/scout/agent.py` | 183 | reads `output-spec.md` (was `03-output-spec.md`) |
| `src/scout/evals.py` | 42–50 | added `DOC_STORE`; cases/schema/rubric/specs-dir all derive from it |
| `src/scout/batch.py` | 62–71 | added `DOC_STORE`; specs/cases/rubric derive from it (drive + goldens stay on `HERE`) |
| `src/scout/judge_compare.py` | 34–41 | added `DOC_STORE`; cases/rubric derive from it (inbox + outputs stay on `HERE`) |
| `src/scout/run.py` | 66 | help text updated (`system-prompt.md`/`output-spec.md`) |

Smoke tests: `uv run scout --help` ✓ · `uv run scout-eval --validate` → "Validated 3 cases. OK." ✓ · `uv run pytest tests/` → 17/17 passed in 0.02s ✓

## What did NOT move (Phase 2, deferred)

These files stay in `…/01-scout/` because they are human documentation or operational write-targets, not "what Scout loads":

| Staying in `…/01-scout/` | Why |
|---|---|
| `01-job-spec.md`, `04-input-and-run-contract.md`, `05-brief-template.md`, `06-build-notes.md`, `10-job-spec.md` (duplicate of 01), `11-inbox-job-spec-briefs.md` | Human-readable docs about Scout; no code path reads them |
| `goldens/*` (golden outputs, `CALIBRATION_REPORT.md`, `registry.jsonl`, `README.md`) | Operational artifacts; `batch.py` writes drafts to `goldens/drafts/` — moving would tangle write paths |
| `hand-scores/{everything except CALIBRATION-LOG.md}` | Operational artifacts: judge inputs/results, holdout fixtures, source audits |
| `tests/`, `src/`, `pyproject.toml`, `uv.lock`, `.venv/`, `.env`, `README.md` | Scout's code + project files; doc-store is for docs, not code |

Phase 2 (if ever desired): move the 6 human-readable docs into `specs/` as reference material. No code change required. Not load-bearing for slice 1.

## Git state in `…/01-scout/`

After the move, `git status` in Scout's repo shows 6 deleted files (the moved ones). The user will need to stage + commit those deletions in `01-scout/` to record the move. Not auto-committed by this session.

## What this dir IS

- The single versioned home for what Scout's runtime reads + the calibration log
- The destination Scout's path constants now point at
- Git-trackable under `co-platform/`

## What this dir is NOT

- A copy. Files were moved, not duplicated. No drift risk.
- A change to Scout's agent behaviour. Only path constants + filename references changed. Same prompt content → same brief.
- A home for `goldens/` / `hand-scores/` operational write-targets. Those stay with Scout's code.
