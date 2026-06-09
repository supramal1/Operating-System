# Scout — Brief Template

Fill this in for each task and hand it to Scout with the material. This is the management
layer: the quality of Scout's output is determined here. Keep a copy of each filled brief
alongside the output it produced, so you can see which briefs produced good work.

---

## TEMPLATE (copy this per task)

```
BRIEF_ID:        [short stable id, e.g. harness-list-001]
DATE:            [date]
MATERIAL:        [what you are handing Scout: link, doc, pasted text. Note what matters
                  and what to skim if large.]
THE QUESTION:    [the single question Scout is answering]
FEEDS DECISIONS: [the decisions you suspect this informs, so Scout frames toward them]
CONSTRAINTS:     [the real constraints Scout should test options against:
                  Claude-native stack, solo operator, three-week window, no real CO data
                  yet, etc.]
KNOWN CENTRAL:   [any topics you already know are CENTRAL = frame only, no recommendation]
GOOD LOOKS LIKE: [what a strong output for THIS task contains]
SCOPE EDGES:     [what is explicitly out of scope for this brief]
```

---

## WORKED EXAMPLE (the harness-engineering list task)

```
BRIEF_ID:        harness-list-001
DATE:            [today]
MATERIAL:        The awesome-harness-engineering GitHub list (paste URL or contents).
                 Focus on: agent loop, permissions, memory, human-in-the-loop, evals.
                 Skim: the provider-specific and coding-agent-only entries.
THE QUESTION:    What in this list is decision-relevant to building the Charlie Oscar AI
                 Ops agent team and harness, and what decisions does it raise for me?
FEEDS DECISIONS: Harness build choices; the memory-backend question (Zep vs alternatives);
                 the approval/permission design; the eval approach.
CONSTRAINTS:     Claude-native (Agent SDK + Langfuse, already chosen); solo operator, no
                 team yet; three-week pre-start window; calibrating trust on first agent;
                 contracts must be enforced not goodwill.
KNOWN CENTRAL:   Harness architecture; memory-backend bet; contract/permission lines.
                 (Frame these, do not recommend.)
GOOD LOOKS LIKE: A tight brief that cuts the 60+ entries down to what matters for my
                 build, frames the 3–4 real decisions with options/tradeoffs/settling-facts,
                 flags where the list challenges decisions I've already made (e.g. memory
                 alternatives to Zep), and tells me what to actually read myself versus
                 what Scout has digested for me.
SCOPE EDGES:     Not asking Scout to design the harness or pick the memory backend. Asking
                 it to frame those decisions. Implementation and final choices are mine.
```

---

## Brief-writing notes (the skill)

- The more specific FEEDS DECISIONS and CONSTRAINTS are, the sharper the framing you get
  back. "Fits if" framing is only possible if Scout knows your real constraints.
- Mark KNOWN CENTRAL generously. When in doubt, mark it central, so Scout frames rather
  than recommends. You can always ask for a recommendation on a peripheral thing later.
- GOOD LOOKS LIKE is where you smuggle in your taste. Be concrete. "Cut to what matters
  and flag where it challenges my prior decisions" produces better work than "be thorough".
- A brief you can reuse with small edits across similar tasks is a sign the role is well
  defined. Keep good briefs as patterns.
