# C05 Approval And Delegation Contract

## Purpose

Define what must stop for human approval before an agent acts.

## Draft Rules

### Rule 1: External Sends Require Approval

Enforcement: hard-enforced

Mechanism: approval hold before email, client message, or external publication.

Evidence: approval record with approver, timestamp, content hash, and action id.

### Rule 2: Irreversible Or High-Cost Actions Require Approval

Enforcement: hard-enforced

Mechanism: gateway hold for spend, deletion, production changes, and cross-client actions.

Evidence: blocked action appears in audit log.

## Open Questions

- What spend threshold applies in month one?
- Who can approve client-facing output?
- Where should approvals live before a bespoke app exists?
