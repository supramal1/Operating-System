# CO OS Contract Register

Status date: 2026-05-29

Purpose: control the contract work before building or wiring more systems. This register decides what must exist, what each contract protects, what can be enforced now, and what evidence is required before moving from prep to live Charlie Oscar usage.

## Register

| ID | Contract | Purpose | Primary Owner | Hard-Enforced Targets | Soft Or Not Implemented Areas | Evidence Required | Build Implication | Status |
|---|---|---|---|---|---|---|---|---|
| C01 | State and memory | Define how state, facts, notes, temporal truth, and memory writes work. | AI Ops | Fact schema, date requirement, one-topic facts, write target selection, temporal supersession. | Freeform note retrieval is eventual in Zep; some write-quality checks may start as model-honoured. | Fact write/list/recall smoke; note episode UUID verification; temporal recall test. | Build Cornerstone Memory Core fact/note API and Zep adapter. | Draft stub created |
| C02 | Graph routing | Define how an AI chooses which Zep graph to read or write. | AI Ops | Memory Directory lookup, graph allowlist, role-scoped graph access, provenance on answers. | Ambiguous graph selection may require ask-before-read until classifier is proven. | Routing scenarios for private, team, client, and ambiguous queries. | Build Memory Directory, route endpoint, and graph selection tests. | Draft stub created |
| C03 | Tool and permission | Define who and what can call which tools. | AI Ops plus Ops owner | Gateway deny for disallowed tools, role-based access, secrets by reference. | Some desktop-local tools may initially rely on human discipline. | Gateway sandbox results; per-role tool matrix. | Gateway integration and permission map. | Draft stub created |
| C04 | Execution boundary | Separate owned harness work from Dify, Claude Desktop, and managed agents. | AI Ops | Harness owns open-ended tool loops; Dify limited to deterministic staff-authored flows. | Claude Managed Agents boundary remains phase-3 and vendor-dependent. | Examples showing where each workflow belongs. | Prevent duplicate portal or launcher work. | Draft stub created |
| C05 | Approval and delegation | Define actions that must stop for approval. | AI Ops plus business owner | External sends, spend, irreversible actions, cross-client movement, client-facing outputs. | Approval UI may start as manual or Claude-mediated. | Approval scenario tests and audit log sample. | Build approval hold contract before broad rollout. | Draft stub created |
| C06 | Client data and confidentiality | Prevent leakage, mishandling, and residency breaches. | AI Ops plus leadership/legal owner | No real client data until residency terms checked; no cross-client memory search; PII handling. | Vendor terms and retention details are open. | Zep terms review; client isolation test; red-team leakage cases. | Blocks real client-data ingestion. | Draft stub created |
| C07 | Eval and release | Define what blocks changes from going live. | AI Ops | Golden eval set as release gate; failed critical scenarios block release. | Some quality metrics may remain measured but not blocking at first. | Eval run results, regression threshold, release report. | Build release gate around eval harness. | Draft stub created |
| C08 | Measurement and adoption | Tie system work to the four 90-day metrics. | Malik plus James cadence | Usage proof, quality proof, effort/margin baselines, pilot proof. | Margin and effort baselines need real CO data. | Baseline control sheet and weekly reporting format. | Build reporting only after source metrics are known. | Draft stub created |
| C09 | Incident, rollback, and kill switch | Define stop, degrade, recover, and explain behavior. | AI Ops plus operations owner | Kill switch, disable tool/graph, safe degradation, incident log. | Automated rollback may come later. | Failure drills for gateway down, Zep down, bad memory, bad tool call. | Build operational controls before broad staff rollout. | Draft stub created |
| C10 | Vendor and commercial | Track external dependencies, terms, and unresolved commercial gates. | Malik plus leadership | Do not treat vendor capability or terms as settled without evidence. | Obot vs MCPX, Claude Team vs Enterprise, Zep residency, monthly run-rate, Dan IP/commercial terms. | Vendor decision notes and evidence links. | Blocks production architecture decisions that depend on vendor guarantees. | Draft stub created |
| C11 | Identity and role lifecycle | Define users, roles, teams, joiners, movers, leavers, and temporary access. | AI Ops plus operations owner | Role claims, graph scope, tool scope, deprovisioning, admin actions. | Desktop-local usage may start with manual role discipline. | Role matrix, access-change log, deprovisioning smoke. | Build identity claims and role map before team rollout. | Draft stub created |
| C12 | Provenance and audit | Define what every answer, memory write, tool call, approval, and release must prove. | AI Ops | Audit event schema, source references, graph ids, actor ids, contract ids. | Full immutable log store may come after local smoke. | Audit event samples, missing-provenance refusal tests. | Build audit event schema and provenance middleware. | Draft stub created |
| C13 | Output and publication | Define draft, review, approval, and external publication rules. | AI Ops plus business owner | External sends, client-facing outputs, unsupported claims, performance claims. | Some review flows may start as manual holds. | Output status tests, approval evidence, bad-claim rejection. | Build publication gate for emails, briefs, decks, and recommendations. | Draft stub created |
| C14 | Shared memory promotion | Define how private findings become team, client, or canonical CO OS memory. | AI Ops | Promotion approval, source/target graph proof, client isolation, redaction. | Generalised learnings may need human review at first. | Private-to-team, team-to-client, and cross-client rejection tests. | Build promotion workflow before broad team memory usage. | Draft stub created |

## Contract Dependencies

Cornerstone Memory Core depends on:

- C01 State and memory
- C02 Graph routing
- C03 Tool and permission
- C06 Client data and confidentiality
- C09 Incident, rollback, and kill switch
- C11 Identity and role lifecycle
- C12 Provenance and audit
- C14 Shared memory promotion

Gateway sandbox depends on:

- C03 Tool and permission
- C05 Approval and delegation
- C06 Client data and confidentiality
- C09 Incident, rollback, and kill switch
- C11 Identity and role lifecycle
- C12 Provenance and audit

Phase 1 real-data ingestion depends on:

- C01 State and memory
- C02 Graph routing
- C06 Client data and confidentiality
- C11 Identity and role lifecycle
- C12 Provenance and audit
- C14 Shared memory promotion
- Zep residency and processing terms evidence

Release governance depends on:

- C07 Eval and release
- C08 Measurement and adoption
- C09 Incident, rollback, and kill switch
- C12 Provenance and audit

Client-facing output depends on:

- C05 Approval and delegation
- C06 Client data and confidentiality
- C07 Eval and release
- C12 Provenance and audit
- C13 Output and publication

Team rollout depends on:

- C08 Measurement and adoption
- C11 Identity and role lifecycle
- C12 Provenance and audit
- C14 Shared memory promotion

## Open Questions

1. Which graph registry store is canonical: a dedicated Zep graph, a local config file, or both?
2. Which roles exist at launch: Malik/private, AI Ops, champion user, leadership, client-team user, admin?
3. Which graph reads are allowed by default and which require explicit approval?
4. What must be logged for every memory answer: graph id, episode id, edge id, namespace, score, or source file?
5. What is the first release gate threshold for the golden eval set?
6. What is the manual fallback when Zep, gateway, or Claude is down?
7. Which identity provider or role source should be authoritative at launch?
8. Which outputs count as client-facing before they leave Charlie Oscar systems?
9. Who can promote a memory from private to team or client graph?
10. Which audit store is canonical before a full observability stack exists?

## Next Actions

1. Read `enforcement-map.md` before drafting implementation work.
2. Fill C01-C03 in detail before building Cornerstone Memory Core.
3. Fill C11-C12 alongside C02-C03 before team access.
4. Fill C13 before any client-facing output workflow.
5. Convert the register and enforcement map into acceptance tests.
6. Add a Memory Directory schema to C02.
7. Keep C06 blocked until Zep residency and processing terms are verified.
