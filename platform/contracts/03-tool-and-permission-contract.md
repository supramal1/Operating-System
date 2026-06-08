# C03 Tool And Permission Contract

## Purpose

Define which tools, data, and memory graphs each role or agent can access.

## Scope

- MCP gateway
- role-to-tool mapping
- graph permissions
- secret handling
- tool audit

## Draft Rules

### Rule 1: Tools Are Denied By Default

Rule: A user or agent can only call tools explicitly granted to their role.

Enforcement: hard-enforced

Mechanism: gateway deny.

Evidence: denied calls produce audit events with role, tool, and reason.

### Rule 2: Secrets Are References, Not Payload

Rule: Secrets must not be embedded in prompts, memory, fixtures, or contract documents.

Enforcement: hard-enforced where gateway supports secret references; soft/model-honoured in local drafts.

Mechanism: gateway secret reference and secret scanner.

Evidence: no secret values in logs or memory writes.

### Rule 3: Graph Access Follows Role

Rule: Tool access and graph access must be checked together.

Enforcement: hard-enforced

Mechanism: route planner refuses graph search when role is not allowed.

Evidence: route traces show role, graph allowlist, and denied candidates.

## Open Questions

- What roles exist in month one?
- Does Claude Team provide enough central provisioning for this contract?
- Does the gateway support all needed audit fields?

## Acceptance Tests

- Champion user cannot access private Malik graph.
- Paid media user cannot access another client's graph.
- AI Ops admin can inspect route traces.
- Tool call with embedded secret is rejected or redacted.
