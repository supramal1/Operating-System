# C01 State And Memory Contract

> **SUPERSEDED 2026-06-08.** This contract's memory-layer rules are superseded by the MC pack at `platform/contracts/memory-contracts.md` (MC-1..MC-6, Rev 0.2, approved 2026-06-03). Kept as history; do not enforce these rules. See `SUPERSEDED.md` for the supersession index.

## Purpose

Define how CO OS stores, reads, updates, and proves memory.

## Scope

- Cornerstone Memory Core
- Zep graphs
- facts
- notes
- temporal validity
- source provenance
- private vs team memory boundaries

## Draft Rules

### Rule 1: Facts Must Be Structured

Rule: Every durable fact must have one topic, a stable key, a factual value, a date or temporal anchor, a source, and a target graph.

Enforcement: hard-enforced

Mechanism: schema rejection at write time

Evidence: rejected writes show field-level errors; accepted writes return graph id and edge id.

### Rule 2: Notes May Be Eventual

Rule: Freeform notes may be written immediately but must not be treated as searchable until Zep processing exposes them to graph retrieval.

Enforcement: hard-enforced for write acknowledgement; soft/model-honoured for user expectation until UI status exists

Mechanism: note writes return `zep_episode_uuid`; retrieval status is checked separately.

Evidence: direct episode fetch confirms landing; later search/list confirms retrieval.

### Rule 3: Assistant Analysis Is Not A Fact By Default

Rule: Assistant-generated analysis cannot be saved as fact unless Malik accepts it as a decision or durable operating rule.

Enforcement: soft/model-honoured initially

Mechanism: write policy and review prompt; later add write classifier.

Evidence: write logs show accepted source and author.

## Open Questions

- What fact keys are reserved for system state?
- Should temporal supersession delete old facts or set `invalid_at` only?
- Should all facts require an explicit contract id?

## Acceptance Tests

- Reject fact with no date.
- Reject fact with no graph target.
- Update existing fact without duplicating active truth.
- Write note and verify by episode UUID before graph retrieval.
