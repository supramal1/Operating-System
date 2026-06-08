# Lookout Changelog

Hand-scored eval runs and the prompt deltas that produced them. See
`doc-store/evals/rubric.md` for the scoring rubric and
`doc-store/calibration/CALIBRATION-LOG.md` for free-form calibration notes.

## v2.3 (2026-06-08)

**Prompt delta**: WHEN-to-disclose precondition added to the
`Disclosure, not leakage` sub-section of the Honesty section. Disclosure
of a scope-suppressed cornerstone item in "What I couldn't check" is
reserved for suppressions that are decision-shaping for today. Items
with no plausible day-hook (no client meeting, no Drive change on the
project, no live stake) get silence, not disclosure.

**Rubric delta**: sibling scorer note in Scoring mechanics: "When the
brief discloses a scope-suppressed item in 'What I couldn't check',
check whether the suppressed item had any plausible day-hook. If not,
the disclosure is padding even in clean key+reason form, and it scores
as a mild Restraint hit."

**Hand-scored result (4 re-scored cases)**:

| Case | Relevance | Restraint | Honesty | InSeat | Mean | Δ vs v2.1 |
| ---- | --------- | --------- | ------- | ------ | ---- | --------- |
| 02   | 3         | 3         | 3       | 3      | 3.0  | 0         |
| 03   | 3         | 3         | 3       | 3      | 3.0  | 0         |
| 05   | 3         | 3         | 3       | 3      | 3.0  | +0.25     |
| 07   | 3         | 3         | 2       | 3      | 2.75 | +0.50     |
| Set  | 3.0       | 3.0       | 2.75    | 3.0    | 2.94 | 0         |

**Verdict**: SHIP. Case 05 cleared on a real improvement (slice-2
isolation surface relocated inline with its Drive-change hook, cleaner
signal-to-noise). Case 07 improved on Relevance and Restraint but
Honesty stayed at 2 because Iris Thorne, the unknown attendee the case
was designed to discriminate on, is still not named in gaps. Set mean
unchanged from v2.1. Diminishing returns are real; two prompt sprints
moved the set mean by 0. Iris-discriminator is the only synthetic-eval
issue still worth fixing on judgement grounds and is the natural v2.4
candidate. The v0.3 Honesty rebuild (email+gbrain constant-gap) is the
bigger systemic issue but is deferred.

## v2.2 (2026-06-08)

**Prompt delta** (two additions):

1. Structural anti-hedge principle in the `The hedge does not save the item`
   sub-section: conditional rationale attached to a concrete present-tense
   hook is still a residual hedge. The phrase list (from v2.1) is a sample
   of the shape, not the rule. New phrasings the agent has not seen
   verbatim fall under the same rule. Includes a worked example using the
   v2.1 Case 05 Obot VPS conditional-verification failure.
2. `Disclosure, not leakage` sub-section in the Honesty section: when
   excluding an item from the brief, name it in "What I couldn't check"
   only by KEY and REASON, never SUBSTANCE.

**Rubric delta**: sibling scorer note in Scoring mechanics covering the
disclosure form distinction (key + reason = honest disclosure; substance
under suppression wrapper = half-leak, score as surfaced).

**Hand-scored result**: not scored in isolation. v2.2 was a milestone on
the way to v2.3; the over-disclosure failure mode the WHEN-precondition
later fixed was introduced by Fix 2 here and caught at the v2.3 layout
review.

## v2.1 (2026-06-08)

**Prompt delta** (two additions to the Judgment section):

1. `The hedge does not save the item` sub-section. Verbatim list of
   banned hedge phrases ("hold ready", "if it fits", "carry it if asked",
   "if Kate raises it", "useful framing for", "in case it comes up",
   "worth keeping in mind", "if it turns out"). A hedged surface is still
   a surface; the brief telling Mal an item exists and pointing him at
   it is a surface regardless of the rhetorical cover.
2. `The always-relevant framing trap` sub-section. Standing OKRs, team
   goals, quarterly targets, and similar always-true facts are not to be
   surfaced as "framing" or "context for what the day is in service of"
   unless they attach to a specific calendar event whose description
   asks for them.

**Rubric delta**: explicit hedged-counts-as-surface paragraph in the
Restraint section, plus a one-line scorer note in Scoring mechanics.
Pass bar tightened to add "Restraint >= 2 (no Restraint 1s permitted)".

**Hand-scored result (4 cases that failed at v0.1)**:

| Case | Relevance | Restraint | Honesty | InSeat | Mean | Δ vs v0.1 |
| ---- | --------- | --------- | ------- | ------ | ---- | --------- |
| 02   | 3         | 3         | 3       | 3      | 3.0  | +0.5      |
| 03   | 3         | 3         | 3       | 3      | 3.0  | +0.75     |
| 05   | 3         | 2         | 3       | 3      | 2.75 | +0.5      |
| 06   | 3         | 3         | 3       | 3      | 3.0  | +1.0      |
| Set  | 3.0       | 2.75      | 3.0     | 3.0    | 2.94 | +0.69     |

**Verdict**: SHIP. Restraint floor of 2 cleared on every case; Case 06
moved from 2.0 to 3.0; Case 04 (MC-6) held at 3.0/3.0/3.0/3.0. Case 05
residual conditional ("in case the update needs to be verified") slipped
through the v2.1 phrase list and became the v2.2 sprint target.

## v0.1 (2026-06-03 scaffold, 2026-06-08 hand-scored baseline)

**Initial scaffold**. Agent skeleton ported from Scout (tool-less SDK
call, Langfuse tracing pattern, two-pass validator, YAML front-matter
renderer). Source adapters built from scratch: Calendar (Google
installed-app OAuth, `calendar.readonly` scope), Cornerstone (thin
`httpx` wrapper around `127.0.0.1:8000/context`), Drive delta (wraps
`library.scripts.drive_sweep.sweep` with Lookout-private state dir).
RunContext as `@dataclass(frozen=True)` AC-4 boundary. Six-section output
spec with mandatory non-empty `gaps`.

**Eval set**: seven hand-scoreable Cornerstone-relevance cases authored
to stress specific judgement dimensions (clean win, noise-resistance,
sparse-day restraint, MC-6 cross-client, drive-only signal, adversarial
keyword overlap, staleness plus run-specific honesty).

**Hand-scored baseline**:

| Case | Relevance | Restraint | Honesty | InSeat | Mean |
| ---- | --------- | --------- | ------- | ------ | ---- |
| 01   | 1         | 2         | 2       | 3      | 2.0  |
| 02   | 3         | 1         | 3       | 3      | 2.5  |
| 03   | 2         | 1         | 3       | 3      | 2.25 |
| 04   | 3         | 3         | 3       | 3      | 3.0  |
| 05   | 2         | 1         | 3       | 3      | 2.25 |
| 06   | 1         | 1         | 3       | 3      | 2.0  |
| 07   | 2         | 2         | 2       | 3      | 2.25 |
| Set  | 2.0       | 1.57      | 2.71    | 3.0    | 2.32 |

**Verdict**: FAIL. Restraint pinned at 1.57 across the set (floor of
2.0 fails on four of seven cases). Single named failure mechanism: the
hedge. Agent surfaces `expected_omit` items wrapped in conditional
language. Repeat offender: `innovation_team_q3_okrs` fires as hedged
padding in cases 03, 05, and 06. Only Case 04 (MC-6 canonical 3) passed
outright. Diagnosis drove the v2.1 anti-hedge sprint.
