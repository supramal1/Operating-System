# CO OS Contract Enforcement Map

Status date: 2026-05-29

## Purpose

This file answers two questions:

1. Where do the contracts live?
2. How are they enforced?

The short answer: contracts start as human-readable Markdown in this starter pack, but they only become real when translated into policy files, schemas, runtime gates, eval gates, and audit evidence.

## Contract Locations

### Phase 0 Prep

Human source:

`/Users/malik.james-williams/Desktop/Charlie-Oscar-OS-Prep/03-contracts`

Memory checkpoint:

`charlie-oscar-job-canonical-memory`

Use this phase to draft the register, rules, acceptance tests, and open questions. Do not treat the Markdown as enforcement.

### Build Phase

Move the contracts into the owned codebase as a versioned contract pack.

Recommended layout:

```text
contracts/
  README.md
  register.md
  human/
    01-state-and-memory.md
    02-graph-routing.md
    ...
  policy/
    memory-write-policy.json
    graph-routing-policy.json
    tool-permissions.json
    output-publication-policy.json
  schemas/
    memory-fact.schema.json
    audit-event.schema.json
    memory-directory.schema.json
  evals/
    contract-cases.jsonl
    release-gates.json
  examples/
    audit-events/
    approval-records/
    refusal-records/
```

### Runtime Phase

Runtime systems should read the machine-readable contract files, not scrape policy from prose.

The human contracts explain intent. The policy, schemas, gates, and tests enforce behavior.

## Enforcement Layers

### Gateway Deny

Blocks disallowed tool calls, graph reads, graph writes, external sends, spend, and cross-client movement before they happen.

Primary contracts: C03, C05, C06, C09, C11, C13, C14.

### Harness Gate

Controls agent behavior before and after model calls: graph routing, memory writes, source checks, output status, approval state, and fallback behavior.

Primary contracts: C01, C02, C04, C05, C12, C13, C14.

### Schema Rejection

Rejects malformed facts, memory writes, audit events, policy files, and Memory Directory entries.

Primary contracts: C01, C02, C07, C12.

### Approval Hold

Stops actions until a human approves them.

Primary contracts: C05, C06, C10, C13, C14.

### Release Block

Prevents deployment or rollout when evals, smoke tests, contract tests, or critical scenarios fail.

Primary contracts: C07, C08, C09, C12.

### Audit Alert

Does not always block the action, but records and escalates missing provenance, unusual access, failed refusals, or policy drift.

Primary contracts: C08, C09, C12.

### Human Process

Used where automation cannot be trusted yet: vendor terms, commercial commitments, legal review, client data approval, and policy exceptions.

Primary contracts: C06, C10, C11, C13.

## Contract Enforcement Matrix

| Contract | Where It Lives In Build | Primary Enforcement | Evidence |
|---|---|---|---|
| C01 State and memory | memory schemas, write policy, Zep adapter | schema rejection, harness gate | accepted/rejected write logs, graph id, edge id, episode id |
| C02 Graph routing | Memory Directory, route policy, route tests | gateway deny, harness gate | selected graph, allowed graph list, route reason |
| C03 Tool and permission | tool permission matrix, gateway config | gateway deny | denied tool-call log, role/tool matrix |
| C04 Execution boundary | workflow classifier, runbook, harness config | harness gate | workflow route decision, rejected misuse |
| C05 Approval and delegation | approval policy, approval queue | approval hold | approval record, approver, timestamp, action summary |
| C06 Client data and confidentiality | data handling policy, graph isolation policy | gateway deny, approval hold | client graph id, redaction proof, blocked cross-client search |
| C07 Eval and release | release gates, eval cases, CI checks | release block | eval run id, pass/fail report, regression diff |
| C08 Measurement and adoption | reporting contract, baseline schema | audit alert, reporting review | weekly usage and value report |
| C09 Incident, rollback, and kill switch | kill-switch config, incident runbook | gateway deny, release block | incident id, disabled tool/graph, recovery log |
| C10 Vendor and commercial | decision register, evidence links | human process, approval hold | terms evidence, decision note, open-decision status |
| C11 Identity and role lifecycle | role matrix, identity claims, deprovision policy | gateway deny, human process | access-change log, deprovision smoke, admin action log |
| C12 Provenance and audit | audit schema, log sink, provenance middleware | schema rejection, audit alert | audit event id, source references, contract id |
| C13 Output and publication | output status policy, send gate, review rules | approval hold, gateway deny | draft/review/published state, approval record, claim evidence |
| C14 Shared memory promotion | promotion workflow, source/target graph policy | approval hold, harness gate | promotion record, source graph, target graph, redaction proof |

## Practical Answer

Put the contracts in three places:

1. `03-contracts/` now, as the human working pack.
2. A versioned `contracts/` folder in the owned codebase once building starts.
3. Zep as memory and provenance so future agents can recover the decisions.

Enforce them in four places first:

1. The gateway blocks disallowed tools, graph access, sends, and high-risk actions.
2. The harness controls graph routing, memory writes, source requirements, and output state.
3. Schemas reject invalid memory, audit, and directory records.
4. Evals and release gates block unsafe changes from going live.

Do not enforce contracts only through prompts, Notion pages, or Zep memory. Those are support surfaces, not control surfaces.
