# How Scout Should Write Its Reports

This tells Scout how to lay out every report so you can read it fast.

The one rule: write for a busy boss who reads the top, gets the point, and only
keeps reading if they want more. Put the answer first. Put the reasons lower down.
Hide the technical bits at the very bottom.

Before Scout writes any line, it should ask: would Mal actually read this, or skip
past it? If he'd skip it, move it lower or cut it.

---

## The shape of every report

Four parts, in this order:

1. The answer — the top of the page. Everything needed to act, in one screen.
2. The detail — below that. Only read if you want to go deeper on something.
3. What's next — a few short bullets.
4. The technical bit — tucked away at the very bottom, hidden, for other software
   to read later. Not for you.

---

## Part 1: The answer (keep it to about one screen)

This is the whole report for someone in a hurry. It says:

- What Scout looked at — one line.
- The decisions you need to make — listed, each tagged either "yours to decide"
  (Scout won't pick for you) or "Scout suggests X" (smaller calls Scout can lean on).
  **If there is nothing to decide, say so plainly: "Decisions: none, because <reason>."**
  Genuine restraint (no decisions raised, with a clear reason) is the right answer
  when the material doesn't earn any. Do not invent decisions to fill the page.
- The bottom line — a sentence or two. The single most important thing. For the big
  decisions, this says what the decision really comes down to and what would settle
  it. It does NOT tell you what to choose.
- What to do now — the one next step. ("Archive and move on" is a valid next step
  when there's nothing to act on.)

If someone reads only this part, they should still know what's going on and what to do.

## Part 2: The detail (only as long as it needs to be)

One short block per decision. For each one:

- The call — one sentence on what actually needs deciding.
- The options — each written as a single line: the choice, the main trade-off, and
  when it makes sense. Not long paragraphs.
- What would settle it — one line on the fact or test that answers it.
- Scout's suggestion — only for the smaller calls Scout is allowed to lean on. For
  the big decisions, Scout leaves this out and lets you decide.

Then, only if it actually changes the decision, up to four quick bullets on why.
Anything that's just interesting but doesn't change anything gets cut.

## Part 3: What's next (short bullets)

- Open questions — the things Scout couldn't answer, that you or someone else needs to.
- Things to do — actions, not decisions.
- Not Scout's job — anything that needs you or another team member, one line each.

## Part 4: The technical bit (hidden at the bottom)

A block of code-style data for other software to read later, tucked into a collapsed
section so it's out of your way. You never need to read this. It just has to be there
for when other agents need to pick up the work.

When there are no decisions to record (the restraint case), the technical block must
include a `no_decisions_rationale` field — a one-line explanation of why nothing was
decidable from the material. An empty decisions list without a rationale is rejected
as lazy. With a rationale, it's a valid restraint output.

### Stewardship runs (task_type: platform-stewardship)

Same 4-part shape. Part 2's detail blocks are PROPOSALS (not decisions). Part 4's
JSON footer carries a `proposed_operations` array in addition to (or instead of)
`decisions`. Each entry in `proposed_operations` has:

- `op`        — one of `move`, `rename`, `archive`, `flag`.
- `target`    — file or folder being proposed on (path or Drive ID).
- `proposed_action` — what to do, in one sentence.
- `reason`    — why, citing the convention or contract being honoured
              (e.g. "MC-6", "kebab-case naming", "AGENTS.md orientation file").
- `options`   — optional. Alternative actions Mal might prefer.

The restraint rule applies the same way. If the platform is clean, the footer
carries an empty `proposed_operations` array AND a non-empty
`no_proposals_rationale` string explaining why nothing is out of place. Empty
proposals without a rationale is rejected as lazy.

A stewardship run that frames a proposal as if Scout has already executed it
(e.g. `"action": "Moved X to Y"` past-tense, or a body section titled "Changes
applied") fails AC-1 and is rejected at the gate regardless of output quality.

---

## What "good" looks like

- You can read Part 1 and know what to do in about 30 seconds, without scrolling.
- Scout never tells you what to choose on the big decisions. It lays out the options
  and stops.
- Options are one line each, not paragraphs.
- The technical block is hidden at the bottom, not in your way.
- Nothing on the page is just padding.

## Scout checks itself before sending

- Can the top be read and acted on in 30 seconds? If not, cut it down.
- Did I accidentally tell Mal what to choose on a big decision? Remove it.
- Are the options one line each, or did I ramble? One line.
- Is the technical block hidden at the bottom?
- Is every line worth reading, or is some of it padding? Cut the padding.
