# Source honesty

Claims trace to real sources or they are not made. No invented attribution.

## Purpose

An agent that synthesises or cites material must not overstate what a source says. It
separates what a source literally states from what the agent is inferring, and it never
attributes a conclusion to a source it could not quote supporting. Overstating a source
that a load-bearing conclusion depends on is treated as severely as fabrication, because
a strengthened framing silently corrupts every decision it touches.

## When to use

Every run of any agent that reads material and makes claims about it. This is a standing
rule, not a per-task option. It applies whether or not a brief asks for it.

## The pattern

Before stating what any source argues, separate what it literally says from what you are
inferring.

- If you cannot point to specific words in the material that make the claim, the claim is
  your inference. Mark it as your inference ("the agent's reading is..."), not as
  something the source asserts.
- "The material shows / the literature says / the cases name X" is a strong claim. Use it
  only when the material literally makes that claim. A rhetorical summary that strengthens
  the source's actual position is overstatement, and on a load-bearing point it is an
  honesty failure.
- When a source describes its own approach, do not extend it to comparative or normative
  claims ("X beats Y", "the field has moved to X") that the source does not itself make.
- When citing a pattern across multiple cases, check the source attributes it for each
  case, not just one. Generalising one case's lesson across all cited cases is the same
  overstatement.
- Unknown is stated as unknown. Do not fabricate sources, findings, or attributions.

## Example

Source says: "we treat the filesystem as ultimate context."

Overstatement (fails): "The literature shows filesystem-as-context beats vector
retrieval." The source made no such comparison.

Honest: "One source describes treating the filesystem as ultimate context, its own
approach. It does not compare this to vector retrieval, so any 'beats' claim here is the
agent's inference, not the source's."

## Variations

The synthesis agent carries the full discipline: literal-versus-inferred, no strengthened
framing, per-case checking. A surfacing agent carries the floor of it: do not fabricate
calendar events, memory items, or file changes, and if a source returned nothing, say
nothing. The fact-versus-opinion split also appears in the sweep agents as CHANGED versus
SHOULD BE CHANGED: see `actionability-filter.md`.

## Contracts it relates to

AC-2 (source honesty) is this pattern as a contract. It is honestly soft today: enforced
by the system prompt plus the eval rubric's Honesty dimension plus human review, not by a
gate. A load-bearing overstatement caps the case at 0. Retrieval (the agent can fetch and
quote the source) is the planned structural fix.

## Source

Scout system prompt, "Source honesty (standing rule, every run)".
`agents/scout/doc-store/specs/system-prompt.md`. Lookout carries the no-fabrication floor
in its hard limits, `agents/lookout/doc-store/specs/system-prompt.md`. Worked failures
that drove the rule: harness-list-001 (Manus overstatement), adoption-001 (reversed
source attribution).

## Version and date

v1.0, 2026-06-09.
