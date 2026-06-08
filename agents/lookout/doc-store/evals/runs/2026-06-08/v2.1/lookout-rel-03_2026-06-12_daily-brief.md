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

One event on the calendar, a 30-minute vendor intro with Letta at 14:00 BST. Earliest start 14:00, latest end 14:30. The stake is the Letta call itself: they reached out off the back of Mal's Cornerstone post, and memory recall already has prior work on Letta vs Zep that bears on how the conversation lands.

# For each meeting

**14:00–14:30 BST — Intro call, Letta team (memory backend vendor)**

- **Who:** Jonah Bryant (j.bryant@letta.com, organiser) and Mal. Google Meet.
- **Purpose:** Vendor intro, 30 minutes. Description says Letta reached out after seeing Mal's Cornerstone post.
- **Worth knowing:**
  - Cornerstone backend decision is parked, not actively re-opening. Current stack is Supabase plus Zep on graph `charlie-oscar-job-canonical-memory`. Letta and mem0 were considered as alternatives.
  - Scout's memory-recall-001 result: Zep won on temporal-supersession recall at higher graph-construction cost, Letta came second, mem0 third. The stated position is stay on Zep for now, re-test in Q4.

# What changed worth knowing

Nothing in today's delta changes the stakes. Drive sweep returned no added, modified, or removed files.

# From memory worth surfacing

Nothing surfaced that is not already attached above.

# What I couldn't check

- Email, not connected in v1.
- Personal / gbrain memory, not connected in v1.
- No source errors reported by calendar, cornerstone, or drive delta on this run.

# The technical bit

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