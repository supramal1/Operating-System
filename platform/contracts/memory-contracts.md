# Memory Contracts (MC-1 .. MC-6)

**Status:** DRAFT — awaiting Mal's approval at Checkpoint 2 (revised prompt 2, 2026-06-03).
**Scope:** Cornerstone memory layer (Zep-backed). Facts only — notes covered by C01 R2 (separate).
**Adoption:** This file is canonical for the memory layer once approved. Existing `03-contracts/{01,02,06,12,14}*.md` rules covered here are superseded for the memory layer; rules NOT covered remain in those files. See Reconciliation section.

---

## Governing principle

A memory write is a durable claim about the state of the world that future agents will use to make decisions. Wrong, stale, or unauthorised memory contaminates every downstream output. The contracts below exist to make that failure mode hard to reach, not merely visible.

---

## MC-1 — Write-Gating

**Rule.** Memory writes (`POST /memory/fact`, `POST /memory/note`, `add_fact`, `add_note`) are permitted only for principals whose role is `HOD`. Reads (`/context`, `/recall`, `/search`, `list_facts`) are open to any authenticated principal whose namespace grants cover the requested scope.

**Why.** A single misauthored fact in canonical memory poisons every later retrieval. Writes must funnel through a small, accountable set of actors. Reads are safe to broaden because they're observe-only and gated by namespace grants.

**Enforcement.** HARD.

**Mechanism.** Role check at the API edge in `api/auth.py` resolution, applied at every write route in `api/routes/memory.py`. Role is seeded from config (single HOD = `malik.roberts@gmail.com` for now). Non-HOD writes return `403 Forbidden` with `error_code: MC1_WRITE_GATE_DENIED`.

**Evidence.** Audit log entry per attempted write with `{principal, role, action, decision, contract: "MC-1"}`. Acceptance test: a principal with role `staff` calling `POST /memory/fact` receives 403; the same call from an HOD succeeds.

---

## MC-2 — Agent Writes (Propose-Then-Approve)

**Rule.** No principal whose `authority` is `agent` may write directly to memory. Agent-originated content enters memory only via a `proposed` write from an HOD, who must explicitly approve the promotion to `current`. For the initial build (slice-1): no agent writes at all. The propose-then-approve workflow ships in slice-2.

**Why.** Agent reasoning is not a fact (C01 R3). Without an explicit human checkpoint, hallucinated or fabricated content silently becomes canonical. The promotion step forces a moment of human accountability.

**Enforcement.** HARD initially via outright denial of `authority=agent` writes; HARD on the promotion workflow once it exists.

**Mechanism.** Schema validation (MC-3) rejects writes where `authority == "agent"` and source is not a `promotion` record bearing an HOD approval signature. Until the promotion workflow exists, `authority=agent` is rejected unconditionally.

**Evidence.** Audit log shows zero accepted writes with `authority=agent` during slice-1. Acceptance test: any direct write attempt with `authority=agent` returns 403 with `error_code: MC2_AGENT_WRITE_DENIED`.

---

## MC-3 — Schema Validation

**Rule.** A memory write is rejected unless the payload validates against `co-platform/platform/schema/fact-schema.json`. The envelope MUST include: `type`, `authority`, `author`, `client` (string or null), `topic`, `source`, `created`. The cornerstone domain fields `key` and `value` are also required. (Status and supersession are derived from Zep's native temporal model per MC-5 — they are NOT envelope fields.)

**Why.** Without a schema gate, the envelope drifts. Drifted envelopes break retrieval, audit, and every downstream contract that depends on a stable field set. Validating at the gate is the cheapest place to catch it.

**Enforcement.** HARD.

**Mechanism.** JSON Schema validation at request-handler entry in `api/routes/memory.py` before any backend call. Rejected writes return `422 Unprocessable Entity` with per-field error detail and `error_code: MC3_SCHEMA_INVALID`. Schema file is loaded once at process start.

**Evidence.** Rejection includes field path, expected type/enum, actual value. Audit log entry records the rejection with the offending field. Acceptance tests: writes missing `topic` → 422; writes with `type=unknown_value` → 422; valid writes → 202 (Zep async).

---

## MC-4 — Fact Quality (One Topic Per Fact)

**Rule.** Every fact carries exactly one topic. Before writing a new fact, the system MUST look up existing `current` facts on the same `(client, topic)` pair. If one exists, the writer must explicitly choose: (a) supersede (which triggers MC-5), or (b) flag a genuinely-different fact that happens to share a topic. The system MUST NOT silently produce two `current` facts on the same topic.

**Why.** Composite facts ("the budget is X AND the deadline is Y") rot because they're updated piecewise and retrieval can't tell which half is stale. Two-current-facts-on-same-topic creates ambiguity at every retrieval. Both failure modes are the #1 quality problem in memory systems.

**Enforcement.** HARD on the "two-current-facts" check. SOFT on the composite detection (heuristic warning, not rejection — composite-detection is hard to get right without false positives).

**Mechanism.** Pre-write lookup by `(client, topic)` in `src/memory/facts.py` before calling `zep_client.add_fact_triple`. If a current fact exists and the writer hasn't passed `supersede=True` or `force_new=True`, return `409 Conflict` with `error_code: MC4_TOPIC_CONFLICT` and the existing fact's ID. Composite heuristic (multiple sentences, multiple dates, conjunction-and-numbers pattern) emits a warning log but does not block.

**Evidence.** Audit log: every write records pre-write duplicate-check result. Acceptance tests: writing topic X twice without `supersede` → second call returns 409; writing with `supersede=True` triggers MC-5 path.

---

## MC-5 — Supersession (Zep Native Temporal Model)

**Rule.** A "changed fact" is represented in Zep by deleting the old edge and writing a new edge with `valid_at = now`. Retrieval defaults to facts where Zep's `invalid_at` is null or in the future ("current"). The chain of supersession is **derived from `(client, topic)` plus temporal ordering on `created` / `valid_at`** — there is no literal `supersedes_uuid` pointer stored in the fact envelope.

**Why (and what changed from the original spec).** The original MC-5 wording assumed Zep supported explicit "mark this edge as superseded" updates with a `supersedes` pointer to the new edge. Smoke-tested on 2026-06-03 and confirmed: Zep has no edge-update endpoint, and `add_fact_triple` doesn't trigger Zep's auto-contradiction. The native model (delete + re-add with new `valid_at`) is what Zep is designed for; using it preserves the *behaviour* MC-5 cares about ("retrieval returns current, never stale") at the cost of an explicit UUID-pointer audit trail.

**Enforcement.** HARD on retrieval behaviour. The write path stops the current "delete and lose history" behaviour; instead, it deletes the previous edge ONLY when the writer has explicitly elected to supersede via MC-4's flag.

**Mechanism.**
- **Write (supersede path):** When `MC-4 supersede=True`, the write path:
  1. Looks up the current edge for `(client, topic)`.
  2. Deletes the current edge.
  3. Adds a new edge with `valid_at = now`, populated MC envelope.
  4. Records the chain in the audit log: `{action: "supersede", old_edge_uuid, new_edge_uuid_pending, client, topic, actor}`. (`new_edge_uuid_pending` because `add_fact_triple` is async — the UUID is resolved on next list/search.)
- **Read:** All read endpoints inject `search_filters.invalid_at = [[{">": now}, {"==": null}]]` (Zep's 2D AND/OR filter syntax) so superseded facts are excluded by default.
- **Audit trail:** The audit log IS the supersession chain. Any "what superseded what" lookup goes through audit, not through fact attributes.

**Evidence.** Audit log entries link old→new edge UUIDs. Acceptance tests:
- Write fact A on topic X → retrieve topic X returns A.
- Supersede A with B → retrieve topic X returns ONLY B (never A).
- Direct query of fact A's UUID still resolves (history preserved in audit log even if Zep edge is gone).

**Known constraint accepted.** Cornerstone's audit log is the only place the literal UUID chain is preserved. If the audit log is lost, the chain is unrecoverable from Zep alone. Mitigation: audit log is append-only (per C12 R3) and backed up.

---

## MC-6 — Cross-Client Isolation On Retrieval

**Rule.** Every memory retrieval MUST carry an explicit `client` scope (a single client identifier OR the explicit `agency-wide` scope). Zep search filters MUST refuse to return facts whose `client` field does not match. No retrieval may return facts from more than one client's scope in the same response without an explicit `multi_client=True` flag whose use is logged.

**Why.** This is the agency's #1 commercial and legal risk. The architecture is "single shared graph, client is a tag" (per Mal's project decision). That ONLY works if the tag-filter is unbypassable. A retrieval that silently returns Nike's budget to an Adidas project session is the failure mode that ends the agency contract.

**Enforcement.** HARD.

**Mechanism.**
- **At the API edge:** Every read route requires a `client_scope` parameter. Missing scope = 400.
- **At the Zep client:** `ZepClient.search()` and `list_edges()` are wrapped so that `search_filters` always includes a `property_filters` clause filtering edge attribute `mc_client == <requested_scope>` (or `IS NULL` for agency-wide). The unfiltered path is removed.
- **At the response layer:** A safety assertion verifies every returned edge's `mc_client` matches the requested scope; mismatches raise an error and are logged as `MC6_LEAK_DETECTED`.

**Evidence.** Per-request audit log entry: `{action: "retrieve", client_scope_requested, edges_returned: N, edges_mc_client_distinct: [...]}`. The distinct list must contain only the requested scope (or `null` for agency-wide). Acceptance tests:
- Read scoped to `nike_synthetic` never returns facts tagged `adidas_synthetic`.
- Read with no `client_scope` parameter returns 400.
- Read with `multi_client=True` succeeds AND logs the elevated scope.

**Inherits from.** C06 R2 (no cross-client memory search) and C14 R2 (cross-client promotion blocked by default). Promotion (C14 R1+R3) is OUT of scope here — it gets its own contract once the workflow exists.

---

## Reconciliation against 14 existing contracts

The new MC-1..MC-6 set covers the memory-specific rules from C01, C06, C12 (write portions), and parts of C14. Many other rules from the 14 contracts are NOT memory-specific and remain in their original files. The librarian-produced coverage matrix on 2026-06-03 surfaced the following:

### Fully absorbed by MC-1..MC-6
- C01 R1 (facts must be structured) → **MC-3**
- C01 acceptance tests (reject no-date, no-target, dedupe-supersede) → **MC-3 + MC-4 + MC-5**
- C06 R2 (no cross-client memory search) → **MC-6**
- C12 R2 (writes need source, author, target graph, date) → **MC-3** (envelope includes `author`, `source`, `client`, `created`)
- C14 R2 (cross-client promotion blocked) → **MC-6** (partial — applies to retrieval; promotion workflow itself out of scope)

### Partially covered — flagged for follow-up
- **C01 R3** (assistant analysis is not a fact): MC-2 covers "no agent writes" but the read-classifier ("did Malik accept this as durable?") is not built. **Recommendation:** keep C01 R3 as a soft contract in `03-contracts/`, revisit when promotion workflow lands.
- **C12 R1** (memory answers need provenance) — read-side provenance metadata. **Recommendation:** add as **MC-7** in a future revision. Out of scope for this build.
- **C12 R2** lists `contract_id` as a required write field. **Not present in MC-3 envelope.** Decision: drop `contract_id` for now (MC-3 itself IS the contract being enforced; `contract_id` is implicit). Re-add if the 14-contract enforcement-map needs explicit linkage.

### Not memory-specific — remain in original locations
- C03, C04, C05, C07, C08, C09, C10, C11, C13 — none belong in `memory-contracts.md`. They cover gateway/auth, execution boundaries, approvals, evals, measurement, incidents, vendor, identity, output publication. They stay as standalone contracts in `03-contracts/`.

### Strongest candidates for future MC-7+ (in priority order)
1. **Read-side provenance** (C12 R1) — every retrieval response includes graph_id, edge_id, retrieval_method, missing-evidence caveat.
2. **Graph routing / Memory Directory consult** (C02 R1-R3) — ask-before-read on ambiguity; Memory Directory registry as canonical routing table.
3. **Promotion workflow** (C14 R1, R3) — explicit promotion records with provenance link to source.

### Open questions for Mal
1. **`source` field in MC-3 envelope** — kept. Confirm OK.
2. **`contract_id` field** — dropped from envelope. Confirm OK.
3. **MC-6 scope** — currently retrieval-only. Should it also include the write-side equivalent (a write tagged `client=X` from a principal whose grants don't include `X` is rejected)? **Recommendation: yes**, but pin it before implementing.
4. **`client` field for agency-wide facts** — currently `null` for agency-wide. Alternative: explicit string `"agency"`. **Recommendation:** explicit `"agency"` (safer; null-vs-missing ambiguity is a footgun).

---

## Build sequence (drives the implementation)

1. **Schema** — `fact-schema.json` is the source of truth for the envelope. Build that first.
2. **Envelope** — add the fields to `FactWriteRequest` (`api/models.py`) and `fact_to_zep_triple` (`src/backends/zep_mapper.py`). 9 attrs total fits the 10-cap.
3. **Stop the delete-on-overwrite** — change `src/memory/facts.py:499-506` to require `supersede=True` flag. Without it, MC-4 conflict.
4. **Read-side filter** — add the `invalid_at`/`client` filter to every read path.
5. **Write-gate** — role check at `api/routes/memory.py`.
6. **Audit log entries** — supersession chain + retrieval scope log.
7. **Evals** — five mechanical checks (see eval set spec).

---

## Versioning

This document is versioned with the cornerstone repo. Changes require a new revision number at the top and an audit log entry. Old versions remain in git history.

**Revision:** 0.2 (2026-06-03)
**Authors:** Mal Roberts (HOD), Claude (drafting assistant)
**Approver:** Mal Roberts (2026-06-03)

---

## Slice status (2026-06-03)

| Contract | Slice-1 status | Slice-2 plan |
|---|---|---|
| MC-1 Write-gate | ✅ Enforced via HOD email allowlist + role check. Single HOD = `malik.roberts@gmail.com`. | Multi-HOD; per-client HOD designation when client team memory lands. |
| MC-2 Agent writes | ✅ Propose-then-approve workflow live (2026-06-03). `authority=agent` writes land as `mc_status='proposed'`; HOD promotes to `current` via `mc_promote_fact()` or `POST /memory/mc-fact/promote/{id}`. Proposed rows are excluded from default retrieval. | Multi-step proposal review (multiple reviewers, comment thread) — not built. |
| MC-3 Schema validation | ✅ Enforced at `mc_add_fact()` entry and at the Supabase CHECK constraints. | No change planned. |
| MC-4 Fact quality | ✅ Hard via Supabase unique partial index on `(mc_client, mc_topic) WHERE mc_status='current'`. | Add composite-detection classifier (currently soft/warn-only). |
| MC-5 Supersession | ✅ Via Supabase `mc_status` + `mc_superseded_at` + `mc_superseded_by` FK. Audit log records chain. | No change planned; Option A is the design. |
| MC-6 Cross-client isolation | ✅ Enforced at `mc_list_facts()` with WHERE clause + post-query leak assertion. HTTP route `/memory/mc-facts` requires `client_scope` param. | Write-side scope check (writer's grant must include the `mc_client` they're writing to). Currently relies on MC-1 single-HOD model. |

**Slice-2 backlog (deferred from this version):**
- MC-6 write-side scope check (reject `mc_client=X` writes when writer's grants don't include X)
- MC-4 composite-detection classifier (hard-enforce one-topic-per-fact)
- Read-side provenance metadata (candidate MC-7 per Reconciliation section)
- Multi-reviewer proposal flow (current MC-2 is single-HOD approval)

---

**Revision:** 0.2 (2026-06-03)
**Authors:** Mal Roberts (HOD), Claude (drafting assistant)
**Approver:** Mal Roberts (2026-06-03)
