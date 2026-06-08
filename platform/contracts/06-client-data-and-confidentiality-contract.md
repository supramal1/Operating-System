# C06 Client Data And Confidentiality Contract

> **SUPERSEDED 2026-06-08.** This contract's memory-layer rules are superseded by the MC pack at `platform/contracts/memory-contracts.md` (MC-6 cross-client isolation, Rev 0.2, approved 2026-06-03). Kept as history; do not enforce these rules. See `SUPERSEDED.md` for the supersession index.

## Purpose

Prevent client data leakage, residency breaches, and unsafe memory writes.

## Draft Rules

### Rule 1: No Real Client Data Before Residency Evidence

Enforcement: hard-enforced for prep pack; hard-enforced in production once gateway and memory policy exist.

Mechanism: ingestion gate and data-classification check.

Evidence: blocked ingestion log and vendor evidence link.

### Rule 2: No Cross-Client Memory Search

Enforcement: hard-enforced

Mechanism: graph routing deny across client graphs.

Evidence: route trace shows only the allowed client graph.

## Open Questions

- Zep Cloud data residency and processing terms.
- Retention policy for client memory.
- PII handling standard and deletion process.
