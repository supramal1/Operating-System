# Operating-System

Canonical home of Charlie Oscar's CO OS governing documents.

This repository is the single source of truth for the rules, schemas, architecture, and agent specifications that govern how the CO platform behaves. Drive is a backup / reference mirror only; if the repo and Drive ever disagree, the repo wins.

## Layout

```
platform/
  contracts/        agent + memory contracts, the C-pack (live + superseded markers),
                    register, drafting guide, README, SUPERSEDED index
  schema/           fact schema (validated at MC-3 write-time gate)
  architecture/     CO-AGENT-FRAMEWORK (how CO builds an agent), gateway auth model,
                    enforcement map (text + SVG)
agents/
  scout/            Scout runtime spec, doc-store, MCP wrapper, source
  lookout/          Lookout runtime spec, doc-store, source, README, CHANGELOG
```

## Read first

- `platform/contracts/README.md` — operating rule for contracts: a contract is real only when something can refuse the action.
- `platform/contracts/agent-contracts.md` — AC-1..AC-5, the rules every agent honours.
- `platform/contracts/memory-contracts.md` — MC-1..MC-6, the rules for the Cornerstone memory layer.
- `platform/contracts/SUPERSEDED.md` — which of the older C-pack rules have been replaced by the MC pack and where the replacements live.
- `platform/architecture/CO-AGENT-FRAMEWORK.md` — how CO builds an agent, end to end.

## Status

This is the post-2026-06-08 layout. The older Drive copies of these documents are being marked as backup / reference only in a follow-up sweep. Any Drive file still claiming canonical authority is stale and should be ignored in favour of what is here.

Owner: Mal. Repo identity: supramal1.
