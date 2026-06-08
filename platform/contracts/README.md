# CO OS Contract Pack

This folder is the working contract pack for Charlie Oscar OS.

The key rule: a contract is real only when something can refuse the action. A policy paragraph, prompt instruction, or checklist is not a contract unless it maps to a gate, deny, schema rejection, approval hold, or release block.

## Start Here

1. Read `contract-register.md`.
2. Read `enforcement-map.md`.
3. Draft each contract from its stub file.
4. For every rule, label the enforcement status:
   - `hard-enforced`
   - `soft/model-honoured`
   - `not implemented`
5. Keep open questions open until there is evidence.
6. Do not load real Charlie Oscar client data until the client data contract and Zep residency checks are live.

## Files

- `contract-register.md` is the control sheet for all contract work.
- `drafting-guide.md` defines how to write contract rules.
- `enforcement-map.md` defines where contracts live and how they become executable.
- `01-state-and-memory-contract.md`
- `02-graph-routing-contract.md`
- `03-tool-and-permission-contract.md`
- `04-execution-boundary-contract.md`
- `05-approval-and-delegation-contract.md`
- `06-client-data-and-confidentiality-contract.md`
- `07-eval-and-release-contract.md`
- `08-measurement-and-adoption-contract.md`
- `09-incident-rollback-and-kill-switch-contract.md`
- `10-vendor-and-commercial-contract.md`
- `11-identity-and-role-lifecycle-contract.md`
- `12-provenance-and-audit-contract.md`
- `13-output-and-publication-contract.md`
- `14-shared-memory-promotion-contract.md`

## Where Contracts Live

For prep, the human source is this folder and the recovery copy is the Zep graph `charlie-oscar-job-canonical-memory`.

For build, contracts should move into a versioned repository with:

- human Markdown contracts
- machine-readable policy files
- schemas
- eval fixtures
- release gates
- audit event examples

Zep stores memory, provenance, and recovery context. It is not the only enforcement layer.

## Current Priority

Draft the register first, then the first three contracts:

1. State and memory.
2. Graph routing.
3. Tool and permission.

Those three unblock the Cornerstone Memory Core build.

C11 Identity and role lifecycle, C12 Provenance and audit, and C14 Shared memory promotion should move with C01-C03 before team usage.
