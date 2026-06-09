# Scout — Build Notes

How to actually build Scout on the Agent SDK with Langfuse visibility, the Drive folder
setup, and how this generalises to the rest of the team. This is the engineering layer;
the other files are the role and contracts.

---

## The name and the team convention

- This agent is **Scout** (research-and-synthesis seat: goes out, gathers, reports back so
  Mal can decide). Naming agents as team members, not tools, is deliberate, it reinforces
  "team you open up" over "automation you run".
- Note the overlap with WPP Scout (the creative-performance tool). Different thing. If the
  collision is annoying, rename, candidates: Recce, Forager, Wren. Decide now before it's
  wired in.
- Convention for the team: each agent gets a name, a job spec, a system prompt, an output
  spec, input/run contracts, and its own Drive output folder. The five seats are Scout
  (research/synthesis), then later the knowledge, drafting, adoption, and measurement seats.

## Stack (decided)

- Runtime: Claude Agent SDK. You inherit the agent loop, tool execution, and permission
  hooks rather than building them.
- Visibility: Langfuse (already stood up). The SDK runs in the terminal; you do NOT watch
  the terminal. Scout emits a trace per run to Langfuse, and Langfuse is your review
  surface. This is why the "SDK is just a terminal" concern doesn't bite, the reviewable
  trace is the better visibility and it's already in place.
- No new platform. Not Hermes, not Paperclip. Claude-native, owned, transparent-while-
  calibrating, which is exactly what a first agent (whose job is trust-calibration) needs.

## Wiring (v1, minimal on purpose)

- System prompt: load `02-system-prompt.md` as Scout's system prompt.
- Tools (v1): essentially none with side effects. Scout reads the material you pass in and
  writes its brief to the output folder. No web fetch, no Cornerstone writes, no sending.
  This keeps the blast zone near zero while you calibrate. (v2 adds read-only retrieval.)
- Output: Scout writes the decision brief (per `03-output-spec.md`) as a file, then the run
  ends. It does not act on the brief.
- Tracing: instrument the SDK run so each step (reasoning, any tool call, final output) is
  emitted to Langfuse with the brief_id as the trace identifier. Treat clean, reviewable
  traces as a first-class deliverable, they ARE your management visibility, not a nice-to-have.
- The gate: there is no automated next step after Scout writes the brief. The "gate" is
  that nothing consumes Scout's output until you've reviewed it. Build no auto-proceed.

## Drive folder structure

Scout drops work into its own folder so outputs are findable, reviewable, and (later)
consumable by other agents. Suggested structure:

```
/Charlie Oscar AI Ops/
  /Agents/
    /Scout/
      /inbox/        <- briefs + material you hand Scout (optional, or pass at runtime)
      /outputs/      <- Scout drops every decision brief here, named by brief_id + date
      /reviewed/     <- you move accepted briefs here after sign-off (the gate made visible)
      /_specs/       <- Scout's job spec, system prompt, output spec, contracts (this set)
```

- Naming: `harness-list-001_2026-06-xx_decision-brief.md` (brief_id + date + type).
- The move from /outputs/ to /reviewed/ is a lightweight physical signal of the gate: if
  it's still in /outputs/, it hasn't been signed off. Simple, visible, no tooling needed.
- v1 can be even simpler: Scout writes to /outputs/, you review in place. The /reviewed/
  move is optional but a clean habit that scales.
- When the team grows, this `/Agents/<Name>/` pattern repeats per agent, and a future
  orchestrator can read one agent's /outputs/ as another's /inbox/. That's why the output
  spec has a machine-readable footer, the handoff interface is designed in now.

## Calibration loop (the first three weeks of running Scout)

1. Hand Scout the harness-list brief (the worked example in `05-brief-template.md`).
2. Read the brief AND the Langfuse trace. Score against the research/synthesis eval cases.
3. Note where it's good and where it's wrong, especially boundary behaviour: did it
   recommend on a central topic, fabricate, or overstep its seat?
4. Adjust the system prompt or the brief, not the model, most failures are spec failures.
5. Repeat across several real tasks. Trust is the trend across runs, not one good output.
6. Only when eval-backed trust is established do you consider loosening the gate or adding
   a remit item to granted scope, recorded as a deliberate one-line change to the job spec.

## What v2 looks like (do not build yet)

- Read-only retrieval: let Scout fetch its own material (web, Drive reads, Cornerstone
  reads) instead of you pasting it. Still fully gated on output.
- This is the first dial-turn: more autonomy on INPUT, gate on OUTPUT unchanged.
- Everything past v2 (writing to systems, acting on peripheral decisions) waits for trust
  built across many gated runs. Central decisions never leave the gate.

### Why v2 retrieval is the structural fix for source overstatement

Three independent votes have now landed for v2 retrieval, all on the same failure
class — source-attribution accuracy:

1. **vendor-claims-001 (citation gap).** Scout could correctly read the Google
   whitepaper but had no way to produce page-level citations because v1 has no
   retrieval handle on the source. Mal's hand-score noted this as a backlog flag,
   not a deduction.
2. **adoption-001 (Scout's own Manus-shape slip).** Scout overstated what the
   sources literally said because it was working from in-context memory of the
   material with no ability to verify attribution against the underlying text.
   Capped at 0.
3. **Judge generalisation miss on adoption-001.** The LLM judge could not catch
   the overstatement either, for the same structural reason: the judge sees
   Scout's brief but not the underlying material, so it can only score on what
   the brief asserts vs the rubric, not on whether the brief's claims match the
   material literally.

Retrieval would let both Scout AND the judge cite-check claims against real text
at inference time, instead of relying on Scout's working memory and the judge's
inference from the brief alone. That is the structural fix for the whole
overstatement class — the failure that actually misleads. v1's soft
system-prompt rule reduces the rate but does not eliminate it; v2 retrieval is
what closes the loop.

Build sequencing: v2 retrieval before any further loosening of Scout's gate.
Until retrieval lands, the human audit (Mal grepping the material) is the only
reliable catch on source overstatement.

## Generalisation to the team

Scout is the template. To hire the next seat (say, the drafting agent), you reuse this
exact file set and change three things: the remit, the granted scope, and the output spec.
The skeleton, input → brief → draft → gate (Langfuse-reviewed) → handoff (Drive folder),
is identical. Build Scout well and the team is a stamp, not five rebuilds. That is why
disproportionate care on this first one pays off five times over.
