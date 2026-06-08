# C02 Graph Routing Contract

## Purpose

Define how an AI chooses which memory graph to read from or write to.

## Scope

- Memory Directory
- graph selection
- namespace filtering
- permissions
- provenance
- ambiguous queries

## Draft Rules

### Rule 1: Select Graphs Before Searching

Rule: The system must consult the Memory Directory before searching Zep.

Enforcement: hard-enforced

Mechanism: route endpoint refuses graph search without a selected graph set.

Evidence: trace includes directory candidates, selected graphs, and rejected graphs.

### Rule 2: Graphs Are Hard Boundaries

Rule: Graphs are the primary isolation boundary; namespaces are secondary filters inside a graph.

Enforcement: hard-enforced

Mechanism: route plan contains graph ids and allowed scopes before search calls are made.

Evidence: no search call is made against a graph outside the user's allowed graph list.

### Rule 3: Ambiguity Must Not Silently Broaden Access

Rule: If a query could belong to private memory and team memory, or multiple client graphs, the system must ask or return a staged route plan instead of searching everything.

Enforcement: hard-enforced

Mechanism: ambiguity threshold in router; ask-before-read response.

Evidence: ambiguous scenario tests show no unauthorized graph calls.

## Memory Directory Minimum Schema

```json
{
  "graph_id": "co_ai_ops_memory",
  "label": "CO AI Ops Memory",
  "owner": "AI Ops",
  "purpose": "AI Ops delivery, evals, contracts, CO OS build context",
  "sensitivity": "internal",
  "allowed_roles": ["ai_ops", "leadership"],
  "default_namespaces": ["contracts", "evals", "cornerstone"],
  "read_allowed": true,
  "write_allowed": true,
  "when_to_call": ["CO OS build", "evals", "contracts", "agent workflows"],
  "example_queries": ["What is the eval release gate?", "Which contracts block Memory Core?"]
}
```

## Starter Graphs

- `malik_charlie_oscar_private`
- `co_company_memory`
- `co_ai_ops_memory`
- `co_team_paid_media_memory`
- `co_client_<name>_memory`
- `co_memory_directory`

## Open Questions

- Should `co_memory_directory` be stored in Zep, local config, or both?
- What happens when the directory itself is unavailable?
- Which graph owns general company glossary terms?

## Acceptance Tests

- Private prep query routes only to private graph.
- AI Ops eval query routes to AI Ops graph.
- Client query with no cleared client graph asks before searching.
- Ambiguous query does not fan out to all graphs.
