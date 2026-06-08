# C12 Provenance And Audit Contract

> **SUPERSEDED 2026-06-08.** This contract's memory-layer write/provenance rules are superseded by the MC pack at `platform/contracts/memory-contracts.md` (MC-1 write-gating + MC-3 schema validation, Rev 0.2, approved 2026-06-03). Kept as history; do not enforce these rules. See `SUPERSEDED.md` for the supersession index.

## Purpose

Define what the system must prove about answers, memory writes, tool calls, approvals, releases, and refusals.

## Scope

- memory answers
- generated outputs
- memory writes
- graph routing
- tool calls
- approval holds
- release gates
- incidents
- failed refusals

## Draft Rules

### Rule 1: Memory Answers Need Provenance

Rule: Any answer based on memory must record the graph id, source type, source id when available, retrieval method, and missing-evidence caveats.

Enforcement: hard-enforced in harness response metadata; soft/model-honoured in final wording until UI support exists

Mechanism: provenance middleware and audit event schema.

Evidence: audit event includes graph id, edge id or episode id when available, and retrieval query.

### Rule 2: Writes Need Source And Contract Id

Rule: Every durable memory write must include source, author, target graph, contract id, and date.

Enforcement: hard-enforced

Mechanism: schema rejection at write time.

Evidence: rejected writes show missing fields; accepted writes return graph id and source reference.

### Rule 3: Audit Events Are Append-Only

Rule: Audit events must be append-only. Corrections are new events, not silent edits.

Enforcement: hard-enforced when audit store exists; soft/model-honoured before then

Mechanism: append-only log sink.

Evidence: correction event links back to the original event id.

## Open Questions

- Which audit store is canonical during local development?
- Which source ids are mandatory: graph id, edge id, episode id, file path, or tool call id?
- What audit data can be shown to non-admin users?

## Acceptance Tests

- Reject memory write without source.
- Reject memory write without contract id.
- Log graph routing decision with selected graph and reason.
- Log an approval hold and final approval or rejection.
