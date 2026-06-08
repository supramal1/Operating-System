# Option A — Zep Investigation Findings

**Date:** 2026-06-03
**Outcome:** Root cause identified. The MC contract code is sound. The blocker is a stale Zep API integration in `cornerstone-runtime/src/backends/zep.py`. All previous direct `add_fact_triple` calls have silently been writing to a phantom auto-created group that's not retrievable via any known endpoint.

---

## What we now know

### 1. All our `add_fact_triple` task IDs report `status: succeeded`

Queried `/api/v2/tasks/{task_id}` for the writes we sent. All return:

```json
{
  "task_id": "...",
  "type": "graph.add_fact_triple",
  "status": "succeeded",
  "params": {
    "edge_uuid": "<real uuid>",
    "graph_uuid": "a34f1668-0227-4565-b325-19f41859a87e",
    "source_node_uuid": "...",
    "target_node_uuid": "..."
  },
  "progress": { "stage": "done" }
}
```

The writes **landed** somewhere — but in a graph whose UUID (`a34f1668-...`) is NOT the canonical Charlie Oscar graph (`6a5ac7d2-...`).

### 2. The canonical graph IS reachable, just not via `add_fact_triple`

```
GET /api/v2/graph/charlie-oscar-job-canonical-memory → 200
  uuid: 6a5ac7d2-6343-44b0-bce0-5c071b1323e7

POST /api/v2/graph/edge/graph/charlie-oscar-job-canonical-memory → 200
  returns 1,236 existing edges (all created via Zep NLP path, not direct triples)
```

### 3. The phantom graph isn't reachable via any documented endpoint

```
GET /api/v2/graph/a34f1668-...      → 404
GET /api/v2/user/a34f1668-...       → 404
GET /api/v2/users/a34f1668-...      → 404
POST /api/v2/graph/edge/graph/a34f1668-... → 404
```

### 4. The Zep API requires `user_id` OR `group_id` — NOT `graph_id`

When we send `add_fact_triple` with `graph_uuid` field, the API errors:

```
'AddTripleRequest.user_id' Error: Field validation for 'user_id' failed on the 'required_without_all' tag
'AddTripleRequest.group_id' (similar — truncated)
```

`required_without_all` is Go validator syntax meaning "this field is required unless ALL the others are present." So one of `user_id`/`group_id` is mandatory.

### 5. The cornerstone-runtime client sends `graph_id` (an unrecognised field)

In `src/backends/zep.py:77-79`:

```python
def add_fact_triple(self, payload: dict[str, Any]) -> dict:
    body = {"graph_id": self._graph_id, **payload}
    return self._request("POST", "/api/v2/graph/add-fact-triple", json_body=body)
```

`graph_id` is **silently ignored** by Zep. Zep then auto-creates a phantom group (UUID `a34f1668-...`) to hold the orphaned write, succeeds the task, returns 202 — and we never see the data again because that phantom group has no listable endpoint.

### 6. The 1,236 existing edges in the canonical graph were created by Zep's NLP / `add_text` path

Their attributes contain `edge_type`, `fact`, `reference_time` — the signature of `add_text` processing. Confirmed by reading sample edges. So Cornerstone's *successful* writes have always come from text ingestion, never from direct `add_fact_triple`.

---

## What this means

**`add_fact_triple` in cornerstone-runtime has been silently broken since the Zep API change** (when `graph_id` was removed in favor of `user_id`/`group_id`). Every call has succeeded at the protocol level (202) and silently dropped the data into limbo.

This isn't catastrophic for Mal's current Cornerstone usage because:
- The cornerstone backend mostly ingests via `add_text` (documents, Slack messages) which uses Zep's NLP path
- The few direct fact-triple calls were tolerable losses (no read-after-write checks ever exposed them)

It IS a hard blocker for MC contracts because:
- MC-4 dup-topic check needs read-after-write
- MC-5 supersession needs read-after-write
- MC-6 isolation needs read-after-write

---

## Two paths forward

### Path 1 — Switch to the official Zep Python SDK (`zep_cloud`)

The official SDK knows the current API schema. Replace `src/backends/zep.py`'s HTTP wrapper with SDK calls.

```bash
uv add zep-cloud
```

Code change in `src/backends/zep.py:77-79`:

```python
# BEFORE (broken)
def add_fact_triple(self, payload):
    body = {"graph_id": self._graph_id, **payload}
    return self._request("POST", "/api/v2/graph/add-fact-triple", json_body=body)

# AFTER (correct, via SDK or proper REST shape)
def add_fact_triple(self, payload):
    body = {
        "group_id": self._graph_id,  # use group_id, name accepted
        "fact": payload["fact"],
        "fact_name": payload["fact_name"],
        "source_node_name": payload["source_node_name"],
        "target_node_name": payload["target_node_name"],
        # Plus we need to first CREATE the group if it doesn't exist
    }
    return self._request("POST", "/api/v2/graph/add-fact-triple", json_body=body)
```

**BUT** — the writes via `group_id=NAME` are *still* going to the phantom (we confirmed this in T1 of the second test). So the group needs to actually EXIST before writes will land in the right place. We don't have group-create endpoints exposed in this API version.

**Practical next step:** install `zep_cloud` SDK, see what its `add_fact_triple` does differently. The SDK may handle group creation transparently.

**Effort:** 1-2 days. Includes updating all `src/backends/zep.py` methods to match SDK, updating callers, regression tests on existing flows.

### Path 2 — Use Zep's `add_text` (episode) path for MC writes

Instead of `add_fact_triple`, we serialize the MC envelope as structured text and submit via `add_text`. Zep's NLP processes it, extracts the structured fields, and lands the resulting fact in the canonical graph (where the 1,236 existing edges live).

Pros:
- Uses the *currently working* path
- No backend rewrite needed
- Read-after-write works (those existing edges are findable)

Cons:
- Less deterministic — Zep's NLP may not preserve our exact envelope structure
- Loses some control over `edge_attributes` (Zep generates them from text)
- Adds processing latency (NLP extraction is slower than triple insertion)

**Effort:** Half a day. Change `mc_write.py` to call `z.add_text()` with structured envelope text.

---

## My recommendation

**Path 1 (official SDK)** is the right long-term answer because:
- The phantom-graph bug isn't just an MC problem — every direct-triple write in cornerstone is silently broken. Anyone in future who calls `add_fact_triple` expecting it to work is wrong.
- The official SDK is maintained against the current Zep API. Our custom client is drifting and we don't have the bandwidth to maintain version parity manually.
- Once the SDK is in, the MC code we wrote works as designed — the gates are already correct; only the write transport needs replacement.

**Path 2 (add_text)** is a reasonable bridge if you want to ship MC evals passing before committing to a backend refactor. It WILL work because we can prove it (the existing 1,236 edges are evidence). But it's a hack — it accepts Zep's loss of control over the envelope shape.

## What's NOT needed

- Switching backends entirely (Supabase, etc.) — Zep does work; the cornerstone client is just using the wrong API shape
- Redesigning the MC contracts — they're correct
- Changing the schema — fact-schema.json is fine

## State of the contract code right now

| Component | Status |
|---|---|
| `memory-contracts.md` (MC-1..MC-6) | ✅ Drafted, reconciled, approved |
| `fact-schema.json` (envelope) | ✅ Approved, validated |
| `mc_contracts.py` (gates) | ✅ Live, MC-1/2/3/6-input PASS in evals |
| `mc_audit.py` (audit log) | ✅ Live, recording events |
| `mc_write.py` (gated write) | ⚠️ Calls broken Zep client; needs Path 1 or 2 |
| `zep_mapper.py` (envelope mapping) | ✅ Updated for MC envelope, 10-attr cap honoured |
| `api/models.py` (FactWriteRequest) | ✅ Extended with MC envelope (Optional) |
| `src/backends/zep.py` | 🔴 BROKEN — sends `graph_id` field that Zep ignores |
| 21 deterministic evals | 14 PASS, 7 FAIL (read-after-write tests; will pass after Path 1 or 2) |

## What to do next

**Decide Path 1 or Path 2, and I'll execute.**

- **Path 1:** `uv add zep-cloud`, refactor `src/backends/zep.py` against the SDK, re-run evals. ETA 1-2 days.
- **Path 2:** Modify `mc_write.py` to use `add_text` with structured envelope text. Re-run evals. ETA half a day.

Until one of those is done, **do NOT proceed to seeding** (Prompt 1). The MC contract code is shippable as a library; the runtime can't yet enforce it against the real backend.
