# C07 Eval And Release Contract

## Purpose

Define what quality evidence is required before changes go live.

## Rules

### Rule 1: Critical Eval Failures Block Release

Enforcement: hard-enforced

Mechanism: release gate checks golden eval results.

Evidence: eval run id, failing cases, release decision.

### Rule 2: Eval Categories Track Cost Of Being Wrong

Enforcement: soft/model-honoured until weighting is encoded.

Mechanism: eval schema and scoring config.

Evidence: category coverage report.

### Rule 3: Defects Become Eval Cases

Enforcement: hard-enforced at PR review.

Mechanism: every production defect and every graded human-judge disagreement is captured as a frozen eval case (a replay fixture plus a failing assertion) in the same PR that fixes it. The case becomes part of the regression suite Rule 1 gates on. For a silently-failing class (a false green or dropped signal), the assertion must prove the failing input can no longer produce a clean result.

Evidence: the fixture file, the asserting test, and the fix commit share a PR.

(Ratified from `PROPOSED-C07-AMENDMENT-DEFECT-TO-EVAL.md`, co-eval-harness.)

### Pass Bar

A release is blocked when any critical case fails its rubric pass predicate, OR when the non-critical pass rate falls below the suite threshold, OR when any case regresses from pass to fail versus the last released agent version. Per-case predicates, dimension floors, the suite threshold, and the critical-case set are declared in each agent's rubric and release_policy and are version-controlled. Thresholds bind only for agents whose judge is calibrated; uncalibrated agents run the gate in report-only mode.

Per-agent instance (Lookout, 2026-06-10): per-case pass = mean(dimensions) >= 2.5 AND every dimension >= its floor (Restraint 2, all others 1) AND no dimension is 0; MC-6 caps Relevance at 0. Critical cases (any failure is an automatic block): `lookout-rel-04` (MC-6 client isolation), `lookout-rel-07` (AC-2 source honesty). Suite threshold: non-critical pass rate >= 0.85, zero pass-to-fail regressions. Declared in `cases/lookout/rubric.json` release_policy (co-eval-harness).

## Open Questions (RESOLVED 2026-06-10)

Marked resolved, not deleted, so the supersession stays visible.

- ~~First pass/fail threshold.~~ RESOLVED: the Pass Bar above. Per-case predicate (mean >= 2.5, dimension floors, no 0), critical-case hard block, suite pass rate >= 0.85, no pass-to-fail regression, declared per agent in rubric.release_policy.
- ~~Which cases are critical blockers.~~ RESOLVED: a case is critical if failing it corrupts memory (the MC-6 class) or destroys user trust in a way a later fix does not repair. Marked `is_critical` per agent, each naming the contract it protects. Defect-derived cases (Rule 3) default to `is_critical = false` unless they protect a contract rule. Lookout starts with `lookout-rel-04` (MC-6) and `lookout-rel-07` (AC-2).
- ~~Who signs off eval updates?~~ RESOLVED: the AI Ops owner. Eval-set changes (adding or editing golden cases, changing thresholds, flipping `is_critical`) require AC-1 human approval recorded against the approving principal; no agent self-approves (AC-4). The release decision is recorded with the deciding principal and the gate verdict it was based on.

## Ratification

Ratified 2026-06-10 by **Malik James-Williams, Head of AI Ops**.

Adopts `PROPOSED-C07-AMENDMENT.md` and its companion `PROPOSED-C07-AMENDMENT-DEFECT-TO-EVAL.md` (co-eval-harness), generalising Lookout's hand-authored pass bar to a contract-level template.

Preconditions met before ratification:

- **Judge calibration (A3):** Lookout's judge passed the pre-registered bar. Evidence: co-eval-harness `33afa37`, `docs/a3-calibration-bar.md`.
- **RLS hardening pass:** cornerstone-runtime `49c3ae7` (tier 1) and `e282ac5` (tier 2).

Enforcement is enabled for Lookout via `cases/lookout/rubric.json` release_policy (`gate_mode=enforced`, `ratified=true`). Thresholds are defaults chosen before calibration data; revisit after the first 30 days of real runs (`release_policy.revisit_after_days = 30`).
