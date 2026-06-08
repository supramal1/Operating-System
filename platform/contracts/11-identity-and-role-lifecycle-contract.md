# C11 Identity And Role Lifecycle Contract

## Purpose

Define who can use CO OS, what roles mean, how access changes, and how access ends.

## Scope

- users
- roles
- teams
- administrators
- temporary access
- joiners, movers, and leavers
- graph scopes
- tool scopes

## Draft Rules

### Rule 1: Every Action Has An Actor

Rule: Every memory read, memory write, tool call, approval, and publication action must have an actor id, role, and permitted scope.

Enforcement: hard-enforced for gateway and harness actions

Mechanism: gateway claims check and audit event schema.

Evidence: audit event includes actor id, role, graph scope, tool scope, and contract id.

### Rule 2: Role Changes Must Recalculate Access

Rule: When a user changes role, their graph access, tool access, approval rights, and publication rights must be recalculated.

Enforcement: hard-enforced when identity integration exists; human process before then

Mechanism: role matrix and access-change workflow.

Evidence: access-change log shows old role, new role, changed scopes, approver, and timestamp.

### Rule 3: Leavers Must Lose Access

Rule: Leavers, expired contractors, and revoked users must lose access to CO OS memory, tools, and approval rights.

Enforcement: hard-enforced when identity integration exists; human process before then

Mechanism: deprovisioning checklist, gateway deny, and access smoke.

Evidence: deprovisioning smoke confirms the user cannot read graphs or call tools.

## Open Questions

- Which identity provider is authoritative at launch?
- Which launch roles are real: Malik/private, AI Ops, champion user, leadership, client-team user, admin?
- Who can grant temporary access?
- How long can temporary access last?

## Acceptance Tests

- Block graph read when actor has no graph scope.
- Block tool call when actor has no tool scope.
- Recalculate access after role change.
- Confirm leaver cannot read memory or call tools.
