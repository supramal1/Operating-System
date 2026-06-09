# Anti-hedge

A hedge does not make an item safe to surface. Omitted means omitted.

## Purpose

When an agent surfaces material for a human, a conditional wrapper does not earn an item
its place. "Worth holding ready if it comes up", "carry it if asked", "in case it comes
up" and the rest of that family are not valid framings for surfacing something. A hedged
surface is still a surface: telling the human an item exists and pointing at it is a
surface regardless of the rhetorical cover. If you reach for a conditional to justify
including a fact, that is the signal to cut the fact, not to soften it.

## When to use

Any agent that surfaces items to a human under a relevance bar (a daily brief, a digest,
a shortlist). It is the restraint discipline applied to inclusion: the bar is "useful for
this, now", not "relevant in general".

## The pattern

- The hedge does not save the item. A conditional or hedge does not make an item safe to
  include. The phrase list is a sample of the shape, not the rule: new phrasings you have
  not seen verbatim fall under it the same way.
- The shape itself: conditional rationale attached to a concrete present-tense hook is
  still a residual hedge. A real hook earning its place does not license attaching an "in
  case", "should it come up", "if it turns out" rationale on top of it. Let the hook stand
  on its own concrete connection, or cut the surface entirely if the conditional was the
  only thing justifying it.
- The always-relevant trap. Standing OKRs, team goals, quarterly targets, mission
  statements and similar always-true facts are the items most likely to be padding. Do not
  surface them as "framing" or "context for what the day is in service of" unless they
  attach to a specific event whose own description asks for them.
- If nothing qualifies, say so. "Nothing surfaced" is honest and welcome. Inventing items
  to fill a heading is a failure.

## Example

A Drive change updates a design note today. That is a concrete hook for surfacing the
design constraint the note satisfies.

Hedged (fails): also surface "the deployment infrastructure for that note, in case it
needs to be verified against the deployed instance." The "in case" is conditional
rationale piled on top of the hook.

Clean: surface the constraint the note satisfies. Do not surface the adjacent
infrastructure on a conditional-verification rationale.

## Variations

This is `frame-dont-recommend.md` taken one notch further: a framing agent withholds the
recommendation, a surfacing agent withholds the item itself unless it has a present hook.
What is fixed across adopters: the conditional is never what makes a surface valid, and
the absence of a qualifying item is reported plainly, not papered over.

## Contracts it relates to

No hard contract gates this. It is measured by the eval rubric's Restraint dimension: a
hedged surface scores as a surface, and the pass bar requires Restraint at or above 2. In
spirit it sits next to AC-1: the brief presents and stops, and a hedged include is a soft
way of pushing an item the human did not need.

## Source

Lookout system prompt, "The hedge does not save the item" and "The always-relevant
framing trap". `agents/lookout/doc-store/specs/system-prompt.md`. The fix history is in
`agents/lookout/CHANGELOG.md`: v0.1 failed Restraint at 1.57 across the set on hedged
`expected_omit` items (repeat offender: the Q3 OKRs surfaced as hedged padding). The v2.1
sprint added the banned-phrase list, v2.2 generalised it from a phrase list to the
structural shape, v2.3 tightened the matching disclosure rule.

## Version and date

v1.0, 2026-06-09.
