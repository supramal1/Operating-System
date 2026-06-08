# MC Contracts — Checkpoint 2 Final Report (GREEN)

**Date:** 2026-06-03
**Author:** Claude (under Mal's direction)
**Verdict:** ✅ **CLEARED.** 21/21 evals pass. Safe to proceed to Prompt 1 (seeding) when ready.

---

## Headline

```
21 passed, 0 failed in 24.56s
```

| Required eval | Status |
|---|---|
| 1. Retrieval correctness | ✅ PASS |
| 2. Temporal supersession (MC-5) | ✅ PASS |
| 3. Authority/type filtering | ✅ PASS |
| 4. Schema rejection (MC-3) | ✅ PASS (8 malformed payloads, all rejected) |
| 5. Write-gate (MC-1) | ✅ PASS |

Plus bonus coverage on MC-2 (agent writes denied), MC-4 (dup-topic logic), MC-5 (audit log chain), and MC-6 (scope validation + cross-client isolation).

---

## Architecture as built

```
Caller
  │
  ▼
mc_add_fact(envelope)
  │
  ├─ MC-1 (mc_contracts.check_mc1_write_gate)        # HOD-only writes
  ├─ MC-2 (mc_contracts.check_mc2_agent_write)        # no agent authority
  ├─ MC-3 (mc_contracts.check_mc3_schema)             # validate against fact-schema.json
  ├─ MC-4 (mc_contracts.check_mc4_topic_dup)          # synchronous Supabase read
  │
  ├──→ Supabase mc_facts (CANONICAL, synchronous)
  │      • UNIQUE INDEX on (mc_client, mc_topic) WHERE mc_status='current'
  │      • MC-5 supersession: old row gets mc_status='superseded', mc_superseded_by=new_id
  │
  └──→ Zep graph.add(type='json')  [async, best-effort, for semantic search]
         • zep_episode_uuid backfilled onto the Supabase row when mirror succeeds

mc_list_facts(client_scope)
  │
  ├─ MC-6 (mc_contracts.check_mc6_scope_required)     # scope mandatory + slug format
  │
  └──→ Supabase mc_facts WHERE mc_client = scope AND mc_status = 'current'
         • leak assertion: every returned row's mc_client must match scope
```

## What changed since the initial Checkpoint 2

| Component | Status |
|---|---|
| `co-platform/platform/contracts/memory-contracts.md` | ✅ Unchanged — spec was correct |
| `co-platform/platform/schema/fact-schema.json` | ✅ Unchanged — envelope was correct |
| `src/memory/mc_contracts.py` | ✅ Unchanged — gates always worked |
| `src/memory/mc_audit.py` | ✅ Unchanged |
| **`src/memory/mc_write.py`** | 🔁 **Rewritten** — Supabase canonical, Zep async mirror |
| `src/backends/zep.py` | 📦 Still has the `graph_id` bug for direct fact-triple writes; **not relevant to MC contracts anymore** (we don't go through it for facts) |
| `api/models.py` | ✅ Unchanged — MC envelope on FactWriteRequest |
| `src/backends/zep_mapper.py` | ✅ Unchanged — used by legacy add_fact, not MC path |
| **`schema/migrations/051_mc_facts.sql`** | 🆕 **New** — applied to Supabase project `bksxovxcbescoytwmghq` |
| **`tests/mc_evals/`** | ✅ All 7 files updated; conftest bypasses parent's Supabase stub |
| `pyproject.toml` | + `zep-cloud==3.22.0` (used by mc_write for the async mirror) |

## Why this works where Zep alone didn't

| MC requirement | Zep alone | Supabase canonical + Zep mirror |
|---|---|---|
| Read-after-write within ms | ❌ Async, 30s–minutes | ✅ Synchronous |
| "At most one current per (client, topic)" enforced | ❌ No constraint primitives | ✅ UNIQUE partial index |
| Explicit `supersedes` pointer | ❌ Lost when edge deleted | ✅ `mc_superseded_by` FK column |
| Audit chain reconstruction | Requires audit log | Same — audit log still records, but FK in Supabase is the primary chain |
| Semantic search across facts | ✅ (Zep's strength) | ✅ Still available via Zep mirror, async |
| Cross-client filter at retrieval | Partial (Zep filters unreliable) | ✅ WHERE clause + leak assertion |

## The mc_facts table

```sql
mc_facts (
    id UUID PK,
    mc_type TEXT CHECK ∈ (decision, fact, preference, playbook, draft),
    mc_authority TEXT CHECK ∈ (HOD, staff, agent),
    mc_author TEXT,
    mc_client TEXT CHECK ~ '^[a-z][a-z0-9-]*$',
    mc_topic TEXT CHECK ~ '^[a-z][a-z0-9-]*$',
    mc_source TEXT,
    mc_created TIMESTAMPTZ,
    mc_status TEXT CHECK ∈ (current, superseded),
    mc_superseded_at TIMESTAMPTZ,
    mc_superseded_by UUID FK → mc_facts(id),
    key TEXT, value TEXT, category TEXT, namespace TEXT,
    zep_episode_uuid UUID,
    created_at, updated_at,
    CONSTRAINT supersession_consistency CHECK (
        (status='current' AND superseded_at IS NULL AND superseded_by IS NULL)
        OR
        (status='superseded' AND superseded_at IS NOT NULL)
    )
)

UNIQUE INDEX mc_facts_unique_current_topic (mc_client, mc_topic) WHERE mc_status='current';
INDEX mc_facts_client_status_idx (mc_client, mc_status);
INDEX mc_facts_topic_idx (mc_topic);
INDEX mc_facts_supersedes_idx (mc_superseded_by) WHERE mc_superseded_by IS NOT NULL;
INDEX mc_facts_authority_type_idx (mc_authority, mc_type) WHERE mc_status='current';
```

## What was NOT done (per stop-on-fail discipline)

- ❌ No real client data loaded — synthetic only throughout
- ❌ No agent has write access (MC-2 fully enforced)
- ❌ Did not seed any production data (Prompt 1) — that gate is now unlocked but awaits your signal
- ❌ Did not modify legacy `src/memory/facts.py:add_fact()` — it still works as today
- ❌ Did not change cornerstone behaviour for notes, sessions, conversations, documents

## What you'd see immediately if you used this

A new public surface that wraps the `mc_add_fact()` / `mc_list_facts()` Python API into a route (`POST /memory/mc-fact`, `GET /memory/mc-facts?client_scope=X`). That route layer is the next step beyond Prompt 1.

For now, the MC contracts are accessible from Python code, MCP tools, or any other consumer that imports `src.memory.mc_write`.

## Path forward (your decision)

1. **Proceed to Prompt 1 (seeding)** — load real CO facts into `mc_facts` via `mc_add_fact()`. Evals stay green for regression coverage.
2. **Add the HTTP route layer** — expose MC writes/reads at the API edge before seeding, so external clients (MCP, future agents) can use them.
3. **Drive sync** — upload all four canonical docs (`memory-contracts.md`, `fact-schema.json`, `mc-evals-checkpoint-2-report.md`, `mc-checkpoint-2-option-a-findings.md`, this file) to `co-platform/platform/` per the canonical-storage rule.

I'd do #3 first (it's housekeeping), then your call on #1 vs #2.

## Cleanup notes

- Audit log path during evals is session-scoped via `tmp_path_factory.mktemp` → no pollution of any real audit log
- Test client slugs are `mc-test-<8 hex>` prefix; `mc_delete_test_facts` refuses to delete any slug without that prefix → no risk of deleting real data
- The 1,236 existing Zep edges in `charlie-oscar-job-canonical-memory` are untouched — they're for notes/episodes, not MC facts

---

## In one line

The MC contracts spec is correct, the gate code is correct, the storage is now backed by Supabase with Zep as the async semantic index — and the eval suite is now the safety net that catches any regression.
