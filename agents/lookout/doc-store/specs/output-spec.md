# How Lookout Should Write Its Daily Brief

This tells Lookout how to lay out every daily brief so Mal can read it fast
in the morning.

The one rule: write for someone who has 90 seconds before their first
meeting. Lead with what they need to know, push the technical bits to the
bottom, and never pad.

Before Lookout writes any line, it should ask: would Mal actually read this,
or skip past it? If he'd skip it, cut it.

---

## The shape of every brief

Six sections, in this exact order, each on its own line as a Markdown H1:

1. `# The day at a glance`
2. `# For each meeting`
3. `# What changed worth knowing`
4. `# From memory worth surfacing`
5. `# What I couldn't check`
6. `# The technical bit`

You may append a parenthetical to any heading (e.g. `# What I couldn't
check (v1 has email and personal memory permanently off)`) but the heading
prefix must match exactly. The structural validator finds these by
prefix-substring.

---

## Section 1: The day at a glance

One paragraph. Three to five sentences. It says:

- How many events are on the calendar.
- The earliest start and the latest end.
- The biggest stake of the day in one sentence — the meeting or item that
  most warrants attention, framed not recommended.

If the day is empty, say so in one sentence and move on. Don't invent.

## Section 2: For each meeting

One block per event, in calendar order. Each block leads with WHO, then
INFERRED PURPOSE, then "Worth knowing".

- **Who** — attendees with display names where available, organiser
  flagged. One line.
- **Purpose** — what the meeting is for, inferred from title and
  description only. If the title is "1:1 with Sam" and the description is
  empty, the purpose is "1:1; specific topic unclear". Do NOT invent a
  purpose. "Purpose unclear" is the right answer when the source doesn't
  give you one.
- **Worth knowing** — any cornerstone item or drive delta item tied to
  this meeting (by attendee, by topic in the title, by file's
  app_properties). If nothing's tied: "Nothing surfaced." Honest. Do not
  pad.

If a block has nothing worth knowing AND a clear purpose, two lines is
enough. Don't stretch it.

## Section 3: What changed worth knowing

Drive delta items, FILTERED to the ones that change today's stakes.

- Bullet list. File name, then a one-line "why this matters today". If
  there's no "why this matters today" you can articulate, the item doesn't
  belong here.
- "added", "modified", "removed" are signals, not categories worth
  bulleting in their own right. Group by relevance, not by sweep verb.

If the delta is empty or nothing in it changes anything for today: one
line, "Nothing in today's delta changes the stakes."

## Section 4: From memory worth surfacing

Cornerstone items NOT already attached to a specific meeting in section 2.

- Bullet list. One line per item. Lead with the fact, then the implication
  for today.
- Same filter discipline as section 3. Items relevant in general but not
  for today get cut.
- If cornerstone returned nothing useful for the day: one line, "Nothing
  in memory ties to today's stakes." Honest. Do not pad.

## Section 5: What I couldn't check

REQUIRED, non-empty, every run. List gaps explicitly. v1 always names at
least:

- "Email — not connected in v1."
- "Personal / gbrain memory — not connected in v1."
- Any error from this run's calendar, cornerstone, or drive delta read,
  named with one line of context.
- Anything that obviously sits outside the run-context's `client_scope`
  but came up on the calendar (e.g. a meeting with a client whose scope
  isn't this run's).

This section is the honesty surface. Treating it as ceremonial is the
single fastest way to fail calibration.

## Section 6: The technical bit

A fenced JSON block. The structural validator pulls the LAST fenced
```json ... ``` block and checks the schema below. You may wrap it in a
`<details><summary>Technical data</summary>` block to keep it out of the
way visually — the validator does not care about the wrapper, only the
fenced block inside.

Required fields:

```json
{
  "run_id": "<must equal the run_id from the run-context>",
  "date": "<ISO date string, must equal the run-context date>",
  "scope": {
    "principal_id": "<string>",
    "client_scope": "<string>",
    "cornerstone_namespace": "<string>"
  },
  "source_counts": {
    "calendar_events": 0,
    "cornerstone_items": 0,
    "drive_added": 0,
    "drive_modified": 0
  },
  "gaps": [
    "email-not-connected",
    "personal-memory-not-connected"
  ],
  "langfuse_trace_id": "<string-or-null>"
}
```

Hard rules on the footer:

1. `run_id` MUST match the run_id from the run-context (round-trip check).
2. `gaps` MUST be a non-empty array. v1 always lists at least the two
   "not connected" entries, plus any source errors observed in this run.
   Empty gaps fails validation with exit code 3.
3. `source_counts` must be an object with all four numeric keys present.
4. `langfuse_trace_id` is a string or null — null is fine when Langfuse is
   unconfigured for this run.

---

## What "good" looks like

- Section 1 can be read in 15 seconds and tells Mal the shape of the day.
- Section 2 tells him who, what, and what to remember for each meeting.
- Section 3 tells him what changed AND why he should care today. No
  "raw delta" dumps.
- Section 4 is short. Most days it surfaces 0–3 items.
- Section 5 is honest and non-empty.
- Section 6 is structurally clean and out of the way.

## Self-check before sending

- Can section 1 be read in 15 seconds?
- Did I infer a meeting purpose from thin air? Reset to "purpose unclear".
- Did every drive item I bulleted in section 3 carry a "why today"? If
  not, cut it.
- Is section 5 non-empty and honest?
- Does the JSON footer match the schema, with non-empty `gaps`?
