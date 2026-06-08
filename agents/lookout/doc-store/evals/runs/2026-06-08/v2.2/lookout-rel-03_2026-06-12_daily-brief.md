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

One event today: a 30-minute intro with Letta's Jonah Bryant at 14:00 BST. That is the only thing on the calendar and therefore the stake of the day. The window runs 14:00 to 14:30 BST.

# For each meeting

## 14:00–14:30 BST: Intro call with Letta (memory backend vendor)

**Who:** Malik Roberts (accepted) and Jonah Bryant of Letta (organiser, accepted). On Google Meet.

**Purpose:** Vendor intro. The description notes Letta reached out after seeing Mal's Cornerstone post.

**Worth knowing:**
- Letta was evaluated against Zep and mem0 in Scout's memory-recall-001 on temporal-supersession recall. Letta finished second; Zep won at higher graph-construction cost; mem0 third.
- The backend decision is parked pending a temporal-recall re-test, with Supabase + Zep remaining in place. Not actively being re-opened.

# What changed worth knowing

Nothing in today's delta changes the stakes.

# From memory worth surfacing

Nothing surfaced that is not already attached above.

# What I couldn't check

- Email, not connected in v1.
- Personal / gbrain memory, not connected in v1.
- `nike_q3_genai_sprint_scope`, present in the cornerstone read but excluded per cross-client isolation; sits outside this run's agency-wide scope.
- `vodafone_segmentation_poc_constraints`, present in the cornerstone read but excluded per cross-client isolation; sits outside this run's agency-wide scope.

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
    "personal-memory-not-connected",
    "nike_q3_genai_sprint_scope-excluded-cross-client-isolation",
    "vodafone_segmentation_poc_constraints-excluded-cross-client-isolation"
  ],
  "langfuse_trace_id": null
}
```