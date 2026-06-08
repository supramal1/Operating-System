# C14 Shared Memory Promotion Contract

> **SUPERSEDED 2026-06-08.** This contract's memory-layer rules are superseded by the MC pack at `platform/contracts/memory-contracts.md` (MC-2 propose-then-approve + MC-6 cross-client isolation, Rev 0.2, approved 2026-06-03). Kept as history; do not enforce these rules. See `SUPERSEDED.md` for the supersession index.

## Purpose

Define how a private memory, team learning, or client-specific fact becomes shared memory.

## Scope

- Malik private memory
- AI Ops team memory
- client team memory
- canonical CO OS memory
- redaction
- generalised learnings
- cross-client isolation

## Draft Rules

### Rule 1: Promotion Requires Intent

Rule: Memory cannot move from private to team, client, or canonical CO OS memory without an explicit promotion action.

Enforcement: hard-enforced

Mechanism: promotion workflow with source graph, target graph, reason, approver, and contract id.

Evidence: promotion record shows actor, source graph, target graph, reason, approval state, and timestamp.

### Rule 2: Cross-Client Promotion Is Blocked By Default

Rule: Client-specific memory must not be promoted into another client graph or shared cross-client space unless it is redacted and generalised.

Enforcement: hard-enforced

Mechanism: graph isolation policy and redaction check.

Evidence: blocked promotion log or approved generalised-learning record.

### Rule 3: Promoted Memory Keeps Provenance

Rule: Promoted memory must keep a link to its source and explain why it is safe to share.

Enforcement: hard-enforced

Mechanism: promotion schema and provenance middleware.

Evidence: promoted fact or note includes source graph, source id, target graph, author, and approval record.

## Open Questions

- Who can promote Malik/private memory into team memory?
- Which learnings are allowed to become canonical CO OS memory?
- Should promotion copy the original source or create a summarised derivative?

## Acceptance Tests

- Block private-to-team promotion without approval.
- Block client-to-client promotion.
- Allow redacted generalised learning with approval.
- Preserve source graph and source id on promoted memory.
