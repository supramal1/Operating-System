---
run_id: lookout-rel-03
date: 2026-06-12
agent: Lookout
agent_version: 0.1.0
model: claude-opus-4-7
langfuse_trace_id: synthetic-no-trace
principal_id: malik.roberts@essencemediacom.com
client_scope: agency-wide
---

# The day at a glance

One meeting on the calendar: a 30-minute vendor intro with Letta at 14:00–14:30 BST on Google Meet. That is the only stake of the day. Letta reached out off the back of Mal's Cornerstone post, and Scout has prior evaluation data on Letta from memory-recall-001 that ties directly to the conversation.

# For each meeting

## 14:00–14:30 BST — Intro call, Letta team (memory backend vendor)

**Who:** Jonah Bryant (Letta, organiser, j.bryant@letta.com) and Mal. Google Meet. Both accepted.

**Purpose:** 30-minute vendor intro. Per the invite, Letta reached out after seeing Mal's Cornerstone post.

**Worth knowing:**
- Cornerstone currently runs on Supabase plus Zep (graph charlie-oscar-job-canonical-memory). The backend decision is parked pending a temporal-recall re-test and is not actively being reopened.
- Scout's memory-recall-001 case compared Zep, Letta, and mem0 on temporal-supersession recall. Zep won the temporal case but at higher graph-construction cost. Letta came second. Decision was to stay on Zep for now and re-test in Q4.

# What changed worth knowing

Nothing in today's delta changes the stakes. Drive returned no added, modified, or removed files in scope.

# From memory worth surfacing

Nothing in memory ties to today's stakes that is not already attached above.

# What I couldn't check

- Email — not connected in v1.
- Personal / gbrain memory — not connected in v1.
- No source errors from this run; calendar, cornerstone, and Drive delta all returned cleanly.

# The technical bit

<details><summary>Technical data</summary>

```json
{
  "run_id": "lookout-rel-03",
  "date": "2026-06-12",
  "scope": {
    "principal_id": "malik.roberts@essencemediacom.com",
    "client_scope": "agency-wide",
    "cornerstone_namespace": "default"
  },
  "source_counts": {
    "calendar_events": 1,
    "cornerstone_items": 5,
    "drive_added": 0,
    "drive_modified": 0
  },
  "gaps": [
    "email-not-connected",
    "personal-memory-not-connected"
  ],
  "langfuse_trace_id": null
}
```

</details>