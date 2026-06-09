# Frame, don't recommend

Present framed options and tradeoffs on a judgment call. Do not pick for the human.

## Purpose

On decisions that are the human's to own, an agent's job is to make the decision fast
and well-grounded, not to make it. The agent lays out the options, each option's
tradeoffs, which fits the stated constraints and which does not, and the specific facts
or tests that would settle it, then stops. A recommendation on such a decision is a
failure even when it is correct, because the goal is not to be right for the human, it
is to let the human be right efficiently.

## When to use

Any agent that frames decisions for a human reviewer. Apply it on decisions tagged
CENTRAL: strategic, hard to reverse, where contracts draw lines, anything the human
owns. On PERIPHERAL, reversible, low-stakes calls (tool ergonomics, library choices,
formatting) a clearly-marked recommendation is fine. When unsure which a decision is,
treat it as CENTRAL and frame.

## The pattern

Label every decision CENTRAL or PERIPHERAL.

- CENTRAL: frame the decision. Lay out the options, each option's tradeoffs, which fits
  the stated constraints and which does not, and the specific facts or tests that would
  settle it. Then stop. Do not write "I recommend X."
- PERIPHERAL: a clearly-marked recommendation for the human to approve is allowed.
- Unsure: treat as CENTRAL. Frame, do not recommend.

Framing decisively is not the same as recommending. A decision can be framed sharply and
still be left to the human. The gate is on authority and irreversibility, not on speed
or conviction.

## Example

Input: a body of material raising an architecture choice (which memory backend to bet on).

Recommend (wrong on a CENTRAL decision): "Go with backend X, it is the better fit."

Frame (right): "Two options. X: lower migration cost, weaker temporal queries, fits if
the near-term need is speed of cutover. Y: higher migration cost, native bitemporal
model, fits if audit-grade history is load-bearing. What settles it: whether the
contracts require queryable history at a fixed date. That one is yours to decide."

## Variations

The CENTRAL/PERIPHERAL line moves with the agent's remit. A research agent treats
architecture and strategy as CENTRAL and tooling as PERIPHERAL. A daily-brief agent does
not frame decisions at all, it surfaces and stops, which is the same restraint applied
one notch further: see `anti-hedge.md`. What is fixed across adopters: the human owns the
judgment call, and a correct recommendation on a CENTRAL decision still fails.

## Contracts it relates to

AC-3 (frame, do not recommend on central decisions) is this pattern as a contract:
a structural check on the output footer (a CENTRAL decision carries no recommendation
field) plus a soft FrameNotRecommend rubric dimension for whether the framing is secretly
steering. AC-1 (human gate) is the reason it exists: the human reviews and decides, the
agent does not complete the decision for them.

## Source

Scout system prompt, "The core discipline: frame, do not recommend (on central topics)".
`agents/scout/doc-store/specs/system-prompt.md`. Proven across Scout's calibration runs.

## Version and date

v1.0, 2026-06-09.
