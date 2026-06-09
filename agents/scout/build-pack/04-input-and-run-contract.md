# Scout — Input Contract and Run Contract

Two contracts: what you hand Scout (input) and how a run is governed and gated (run).

---

## TASK-TYPE — the mode discriminator

Every brief declares a `task_type`. Scout uses it (alongside the brief's question and
material) to know which mode it's in. The discipline rules (frame-not-recommend,
source-honesty, restraint, the gate) apply identically across modes; only the input
shape and the kind of work change.

| `task_type` value | Mode | What goes in MATERIAL |
|---|---|---|
| `digest-and-propose`, `compare-options`, `background-prep`, `surface-decisions` | Research synthesis | A body of external material (docs, links, notes) to digest |
| `platform-stewardship` | Platform stewardship | A snapshot of the relevant Drive subtree (file/folder names, sizes, last-modified, paths, content excerpts where relevant for MC-6 duplicate detection). Scout never fetches the snapshot itself; a separate read-only walker produces it and hands it to Scout as MATERIAL. |

A brief without a `task_type` is treated as research synthesis (the original mode).
For stewardship, `task_type` must be explicit.

---

## INPUT CONTRACT — what you give Scout

Scout takes exactly two things per run. If either is missing or vague, Scout's output
degrades, the brief is the control surface, so this is where quality is won or lost.

1. THE MATERIAL
   - **Research mode:** the source(s) to digest — a list, document, set of links, or
     pasted text. You provide it directly (Scout does not fetch its own material).
   - **Stewardship mode:** a snapshot of the platform subtree under inspection, produced
     by the read-only Drive walker. Scout does not call Drive itself during generation;
     the walker is a separate step that runs before Scout and writes the material file.
   - If material is large, say what matters and what to skim.

2. THE BRIEF (use the brief template; this is the management layer)
   - The `task_type` (see table above).
   - The question Scout is answering.
   - **Research mode:** the decisions you suspect this feeds, the constraints that matter,
     what "good" looks like, which topics are CENTRAL if you already know.
   - **Stewardship mode:** the scope of concern (e.g. "the platform subtree under
     `co-platform/`, not client folders"), the conventions Scout should check against
     (named contracts: AC-1..AC-5, MC-1..MC-6, kebab-case, AGENTS.md orientation),
     anything to deprioritise as known-noise.

A vague brief ("digest this and tell me what you think") gets a confident, plausible,
possibly-wrong proposal. A sharp brief gets leverage. Getting good at the brief IS the
skill that makes Scout useful. Do not skimp here to save five minutes.

---

## RUN CONTRACT — how a run is governed

### The gate (v1: fully closed)

- Scout produces a decision brief. It does NOT act on it, commit it anywhere it counts, or
  proceed past producing the document.
- The brief lands in Scout's Drive output folder and the run's Langfuse trace is available.
- Mal reviews BOTH: the brief itself, and the trace (how Scout got there).
- Nothing Scout produces "counts" until Mal has reviewed and accepted it. The gate is a
  real stop, not a notification. Scout never proceeds on a timeout or a default-yes.

### The gate is a dial (built now, turned later)

- v1: every output fully reviewed. This is the calibration phase, you are learning whether
  to trust Scout and whether your briefs are good.
- Later: per task-type, once eval-backed trust is established, review can loosen (spot-check
  rather than full review). This is a deliberate promotion, recorded in the job spec's
  granted scope, never a drift.
- Central decisions stay fully gated permanently. Loosening only ever applies to lower-stakes,
  reversible task-types.

### Calibration workflow (how you build trust)

- Do NOT just read whether one brief "feels right". Trust is built across runs.
- Review the Langfuse trace: did Scout reason soundly, cite honestly, stay in seat?
- Score against the eval set (the research/synthesis eval cases). Track the trend.
- Spot-check: hand-score a sample regularly even once you mostly trust it.
- A boundary violation (recommended on a central topic, fabricated a source, overstepped
  seat) is a hard fail and resets trust for that task-type, regardless of output quality.

### What "done" means for a run

A run is done when: the brief is in the output folder, the trace is reviewable, and Mal
has either accepted it or sent it back with notes. Not before.
