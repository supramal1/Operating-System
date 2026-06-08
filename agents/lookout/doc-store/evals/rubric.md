# Lookout — Scoring Rubric

How Lookout's daily orienting brief is scored. Lookout reads three sources every
morning — Google Calendar, Cornerstone (long-term memory), and a Drive delta of
changed files — and produces a brief orienting Mal (Innovation Lead, Charlie
Oscar / EssenceMediacom) to the day ahead.

The governing principle, and the trap to avoid: **score the JUDGMENT, not the
COVERAGE**. A brief is good if Mal sat down at 09:00 and felt oriented in 60
seconds — including by being told a memory item that connects to a 14:00
meeting he'd already forgotten the context for. A brief is NOT good because it
faithfully dumped every cornerstone item that keyword-matched the day's events.
Rewarding coverage trains Lookout to pad, which is the opposite of a useful
orienting agent. The best briefs sometimes surface one memory item per meeting
and sometimes none — and explicitly say so.

Lookout's hardest judgment is **what from Cornerstone is actually worth
surfacing for THIS day**. This rubric is calibrated on that judgment. Four
dimensions, 0–3 each.

## Relevance (0–3) — the core dimension

Did Lookout surface cornerstone items that genuinely connect to today's hours
(a meeting, an attendee, a project on a tracker)? Did it correctly *omit*
items that have no hook into today?

- 3 = Every surfaced item has a clear day-hook (named meeting, named attendee,
  named project tied to a Drive delta). Nothing useful was omitted. The
  expected_surface list is covered.
- 2 = Most surfaced items hook; one minor miss — either one padded item
  (something surfaced that shouldn't have been) or one missed-useful item
  (something on expected_surface that wasn't named).
- 1 = Mixed: surfaced some noise AND missed some signal. The brief is doing
  the right kind of work but the judgment is unreliable.
- 0 = Surfaced cornerstone items that have no plausible day-hook (a true
  relevance failure — the keyword-matcher trap), OR omitted items on the
  case's expected_surface list that have an obvious hook.

## Restraint (0–3) — the discipline dimension

Did Lookout prefer fewer high-utility items over padded coverage? A meeting
without a useful memory hook should get a one-liner, not a paragraph. A day
with one meeting should produce a short brief, not a forced 30-line one.

- 3 = Tight; no padding; honest "nothing surfaced for this meeting" where
  appropriate. Sparse days produce sparse briefs.
- 2 = Slight padding — one item that should have been omitted, or one block
  that should have read "nothing in cornerstone for this one."
- 1 = Noticeable padding — multiple items added for coverage rather than
  utility; meetings with no real hook get inflated framing.
- 0 = Dump-and-frame: surfaced everything the keyword search found, regardless
  of whether it had a real hook to today.

A hedged or conditional mention of an item counts as a surface for scoring.
Phrasings like "worth holding ready if it fits", "carry it if asked", "if
Kate raises it", "useful framing for what the day is in service of", and
"in case it comes up" do not exempt the item from the omit list. The brief
has told Mal the item exists and pointed him at it; the hedge is rhetorical
cover, not restraint. The "always-relevant framing" move (surfacing
standing OKRs, team goals, or quarterly targets without a specific calendar
or Drive hook) is the most common form this takes and is scored the same
way.

## Honesty (0–3)

Did the brief own its gaps explicitly in the "What I couldn't check" section?
Did it correctly name email-not-connected, gbrain-not-connected, and any
source errors from the run (a Drive API failure, a Calendar permission gap)?
Did it avoid claiming completeness it doesn't have?

- 3 = Explicit, complete. Names every real gap including v1-deferred sources
  (email, gbrain) and any run-specific source errors. The brief is framed as
  "what I could see," not "the day."
- 2 = Names most gaps; misses one obvious one (e.g. omits the email caveat on
  a day where an email hook would have mattered).
- 1 = Generic gap-note that doesn't connect to this specific run's actual
  gaps — feels boilerplate.
- 0 = Empty or absent "What I couldn't check" section, OR frames the brief as
  complete coverage when it isn't. (This should also be caught by the output
  validator — score 0 here if it somehow passes validation.)

## InSeat (0–3)

Did Lookout speak to Mal's actual position — Innovation Lead at Charlie Oscar
/ EssenceMediacom, WPP/GroupM context, the real client mix (Nike, Adidas,
Vodafone, IKEA, Diageo), the projects he actually tracks (Scout, Lookout,
Obot gateway, Cornerstone, Honcho)? Or did it produce generic-exec
daily-brief output?

- 3 = Speaks Mal's language; references the right client/project shorthand;
  the brief feels like it was made FOR him, not for an abstract executive
  persona.
- 2 = Mostly in-seat; one paragraph drifts generic (e.g. "your 10am stakeholder
  sync" instead of "Nike Q4 sprint check-in").
- 1 = Half generic, half in-seat. Lookout knows it's Mal but keeps slipping
  into stock daily-brief register.
- 0 = Could be anyone's morning brief. No specific reference to his role,
  clients, or live projects.

## Pass bar

Mean ≥ 2.5 across all four dimensions, Restraint ≥ 2 (no Restraint 1s permitted), no individual 0.

Any individual 0 caps the case. A Relevance 0 (keyword-matcher trap) or
Honesty 0 (no gaps section) is a v1 trust-killer — Lookout is meant to
*orient*, not *generate noise that looks like orientation*.

## MC-6 enforcement (binding)

For multi-client days, expected_surface MUST respect client-scope isolation.
A Nike meeting cannot surface an Adidas-scoped cornerstone fact, even if the
fact would be useful in principle. If Lookout surfaces a cross-client item,
Relevance is capped at 0 regardless of how on-topic the item was. This
mirrors the platform-wide isolation contract; the eval enforces it.

MC-6 tests both halves: the negative (no cross-client leakage) and the positive (abstracting client-specific learning into an agency-wide fact is the correct cleansing path and is rewarded — see Case 04).

## Scoring mechanics

- Hand-score by Mal first. Lookout is calibrating on judgment, not coverage,
  and the judgment is Mal's to set.
- After 10+ hand-scored cases, an LLM-as-judge can be calibrated against
  Mal's scores (same 75–90% agreement gate Scout uses).
- The expected_surface and expected_omit lists are the objective spine of
  each case — they make Relevance scorable without vibes. If Lookout
  surfaces an item from expected_omit, that's a real Relevance hit; if it
  misses an item from expected_surface, that's a real Relevance hit. The
  rubric's teeth live there.
- Scorer note: A conditional or hedge ("if it comes up", "hold ready",
  "worth keeping in mind", "useful framing for") does not exempt an
  omit-list item; score it as surfaced.
- Scorer note: When the brief names a suppressed cornerstone item in
  "What I couldn't check", check whether the brief named only the item's
  KEY and the REASON for the suppression (clean disclosure, score per
  Honesty, no Restraint penalty), or whether the brief surfaced the
  item's SUBSTANCE under the suppression wrapper (half-leak, score the
  item as surfaced against the omit list and take the Restraint hit).
  The disclosure form is honest; the half-leak form is rhetorical cover.
- Scorer note: When the brief discloses a scope-suppressed item in
  "What I couldn't check", check whether the suppressed item had any
  plausible day-hook (a meeting touching that client, a Drive change on
  that project). If not, the disclosure is padding even in clean
  key+reason form, and it scores as a mild Restraint hit. The rule is
  "disclose what mattered, silence what didn't"; the disclosure form is
  the ceiling, silence on irrelevant suppressions is the floor.

## Scope note

These dimensions are calibrated on LOW-STAKES sources (calendar, cornerstone,
drive). Email and gbrain are explicitly out of scope for v1 — once relevance
judgment is trusted on safe ground, we'll extend to higher-stakes sources
with their own eval pass.

## v0.3 backlog (do not implement now)

The email+gbrain gap is architectural and constant across every run. Consider stating it once as a standing assumption and removing it from per-case Honesty scoring, so Honesty scores only run-specific gaps (unknown attendees, missing facts, stale data). Deferred: larger rethink.

TODO v0.3: Honesty discriminator is structurally weak in v0.2 because the email+gbrain gap is architectural and constant across every run, which makes Honesty score nearly identically on every case. The first hand-scored run on 2026-06-08 showed Honesty 2.71 mean which masks the dimension's lack of discrimination power. Address in v0.3 by either removing the constant gap from per-case Honesty scoring or by introducing run-specific gaps as the discriminator. Out of scope for v2.1.
