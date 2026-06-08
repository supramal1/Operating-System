# Superseded contracts

This file records which of the original C01..C14 governance pack have been retired in favour of the MC-1..MC-6 memory contracts pack at `platform/contracts/memory-contracts.md` (Rev 0.2, approved by Mal 2026-06-03).

The superseded files remain on disk as history. They are NOT to be enforced. New work consults the MC pack; the live C-contracts (C02, C03, C04, C05, C07-C13) still apply for cross-cutting governance the MC pack does not cover.

Decision date: 2026-06-08.

## What was superseded

| File | Old scope | Replaced by |
|---|---|---|
| `01-state-and-memory-contract.md` (C01) | Fact schema and shape, notes, temporal validity, source provenance, private vs team memory boundaries (memory-layer half) | MC-3 (schema validation), MC-4 (one topic per fact), MC-5 (supersession), MC-6 (cross-client isolation) |
| `06-client-data-and-confidentiality-contract.md` (C06) | Cross-client memory search prohibition, data-classification gate on writes | MC-6 (cross-client isolation on retrieval), MC-1 (write-gating) |
| `12-provenance-and-audit-contract.md` (C12) | Memory writes carry source + contract_id; write-time audit append-only | MC-1 (audit log entry per attempted write), MC-3 (schema-validated envelope) |
| `14-shared-memory-promotion-contract.md` (C14) | Private-to-shared promotion requires intent; cross-client promotion blocked; promoted memory keeps provenance | MC-2 (propose-then-approve), MC-6 (cross-client isolation) |

## What stayed live (the rest of the C-pack)

C02 graph routing, C03 tool & permission, C04 execution boundary, C05 approval & delegation, C07 eval & release, C08 measurement & adoption, C09 incident & rollback, C10 vendor & commercial, C11 identity & role lifecycle, C13 output & publication. None of these are memory-layer; the MC pack does not replace them.

## Why mark, not delete

Silent disappearance is how systems lose track of what happened. Renaming or deleting these files would erase the supersession event. Marking them in-place keeps the history visible: anyone opening one of these files sees the banner and is pointed at the MC pack; the index here records the substitution as a decision rather than a janitorial act.

## Drive note

The same supersession applies to any Drive copy of these files. As part of the Step 3 Drive backup, the older Drive copies of `memory-contracts.md` that still carry "MC-1 — HODs write, everyone reads" wording will be renamed to `memory-contracts.SUPERSEDED-2026-06-03.md` so the divergence is visible in Drive too. Both stale Drive copies (the Google Doc and the markdown export) get the same treatment, not just one.
