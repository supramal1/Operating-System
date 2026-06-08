# C09 Incident, Rollback, And Kill Switch Contract

## Purpose

Define how CO OS stops, degrades, recovers, and explains failures.

## Draft Rules

### Rule 1: Every Agentic Surface Needs A Stop Mechanism

Enforcement: hard-enforced before rollout.

Mechanism: disable tool, disable graph, disable agent, or revoke credential.

Evidence: kill-switch drill result.

### Rule 2: Degraded Mode Must Be Explicit

Enforcement: hard-enforced

Mechanism: if Zep, gateway, evals, or tool APIs are unavailable, the agent must state what is unavailable and avoid presenting fallback as canonical.

Evidence: failure scenario tests.

## Open Questions

- Who can trigger the kill switch?
- Where is the incident log stored?
- What is the staff fallback on a bad day?
