# Skills

This folder holds staff-facing Claude Desktop `SKILL.md` capability files for CO staff.
These are skills for people to use, not agent-facing prompt patterns. Agent-facing
patterns live in `../prompts/`.

## Status

None exist yet. No skills have been authored.

The first skills get written once the serving mechanism is decided. How skills reach
staff is an open decision: Claude Team central provisioning versus a dedicated MCP server,
deferred until after start (see `../COOKBOOK.md`). There is no point authoring skills
before we know how they are distributed, so this folder is a deliberate placeholder.

## Format

When skills are authored, each follows Anthropic's `SKILL.md` conventions: a folder per
skill containing a `SKILL.md` with YAML frontmatter (name, description, and the other
supported fields) and the capability instructions in the body. Reference the current
Anthropic Claude Desktop skill documentation at authoring time rather than copying a
format snapshot here.
