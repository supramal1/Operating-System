# CO OS Cookbook

The cookbook is the reuse layer of CO OS. It holds the cross-agent prompt patterns
and the staff-facing Claude Desktop skills that are worth keeping in one canonical
place rather than re-deriving each time an agent is built. The repo is the only home
for this material. Drive never holds a copy of cookbook content.

## The one rule

An entry earns a place here only if it is reused across more than one agent, or it is
a genuine reusable pattern in its own right. That is the whole admission test.

Agent-specific system prompts do not belong here. They live with their agent under
`agents/<name>/`, where the commit history is the audit record for that agent. A
discipline that is true for exactly one agent and will never be reused is that agent's
own prompt, not a cookbook entry. Before adding anything, ask whether a second agent
would adopt it, or whether it states a pattern that outlives any single agent. If
neither is true, it stays with its agent.

## Layout

```
cookbook/
  COOKBOOK.md     this file
  TEMPLATE.md     the per-entry format every entry follows
  prompts/        agent-facing prompt patterns
  skills/         staff-facing Claude Desktop SKILL.md capability files
```

- **`prompts/`** holds agent-facing prompt patterns: disciplines and instruction blocks
  proven inside a real agent or eval that other agents can adopt. Each entry follows
  `TEMPLATE.md` and cites the agent or eval it was proven in.
- **`skills/`** holds staff-facing Claude Desktop `SKILL.md` capability files. These are
  for CO staff to use, not for agents to read. None exist yet; see `skills/README.md`.

## Serving is deliberately undecided

How skills get distributed to staff is an open decision, not an oversight. The two
candidates are Claude Team central provisioning and a dedicated MCP server. Which one
wins is deferred until after start, pending a check on what Claude Team central
provisioning actually offers. This scaffold builds the reuse layer only. It stands up
no serving mechanism, and nothing here should assume one exists.

## Provenance

Every entry carries its Source (the agent or eval it was proven in), the contracts it
relates to, and a version and date. A pattern is proven first and promoted here second,
never invented here. When an entry is superseded, mark it, do not delete it, the same
standing rule the contracts pack follows.
