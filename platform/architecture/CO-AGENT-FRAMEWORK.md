# How Charlie Oscar builds an agent

The repeatable process for hiring an AI agent onto a team. This is the sequence we ran to
build Scout, written so any team can run it again for any agent. Follow it in order; each
step produces an artifact the next step needs.

Read the principles first. They are not optional context, they are what stops this process
producing a confident, well-formatted, untrustworthy agent.

---

## The principles (read once, never skip)

1. **You own the standard. The agent executes against it.** Writing what "good" looks like
   (the job spec, the rubric, the goldens, the decisions) is yours. The agent digests,
   drafts, proposes, runs. The test for any task: does it DEFINE the standard or EXECUTE
   against it? Defining stays with a human. Executing can be delegated.

2. **A contract is enforcement, not a document.** A rule the agent reads and tries to honour
   is goodwill, and goodwill fails exactly when the agent is wrong or pushed. A real
   contract is a gate that refuses the action. Where you can't enforce a rule in code, label
   it "soft / model-honoured" so you know it's a hope, not a guarantee.

3. **The gate opens by earned trust, never by convenience.** Start fully gated: review every
   output. Loosen per task-type only after the agent has proven itself on real runs. Central,
   high-stakes, irreversible decisions stay gated permanently. "It's been fine so far" and
   "it'd be faster" are not reasons to open the gate; eval evidence is.

4. **Score judgment, not capability.** Dock the agent for failures within its control. Do
   NOT dock it for things it was never built to do (a v1 with no retrieval can't cite pages)
   — those are backlog items, not deductions. Exception: if it PRETENDS to a capability it
   lacks (a false citation, claimed context it can't know), that's a judgment failure and
   deducts hard. Being honest about a limit never deducts.

5. **Build narrow scope on a full-shape skeleton.** v1 does one small thing with a hard gate
   and no side effects, so the blast zone is tiny while you learn to trust it. But build the
   architecture (dial-able gate, structured handoff) so opening it up later is turning dials,
   not rebuilding.

6. **Keep a human on the loop, especially on the evals.** The eval layer is where human
   spot-checking is non-negotiable, because it's the layer that checks everything else.
   Never automate your own oversight of the thing that does your oversight.

---

## The process (in order)

### Step 1 — Write the job spec
Define the role before building anything. Derive it from a real human job (for the AI Ops
team, from the Head of AI Ops spec). Split the responsibilities by verb: authority verbs
(own, decide, formalise) stay with the human; support verbs (digest, draft, propose, run)
become the agent's remit. The job spec states: role summary, remit (broad, bounded),
granted scope (narrow, starts at one task), accountabilities, boundaries (the hard lines),
reporting/handoff, and the promotion path (how granted scope widens, on evidence).
> Artifact: job-spec.md. Owned by you. This is the agent's contract.

### Step 2 — Write the system prompt
How the agent is instructed, derived from the job spec. Carries the role, the
frame-don't-recommend discipline (or whatever the agent's equivalent discipline is), the
team's working values, the tone, and the hard limits. The system prompt is how you instruct;
the job spec is what you hold it to. They are different documents on purpose.
> Artifact: system-prompt.md.

### Step 3 — Write the output spec
The contract for what the agent produces. Decide the format for the READER, not for
completeness — lead with the answer, put detail below, hide machine-readable data out of the
reading path. Make the structure checkable (so a validator can enforce it).
> Artifact: output-spec.md. Some of this becomes hard-enforced structure.

### Step 4 — Write the contracts and decide enforcement
The input contract (what you hand it), the run contract (the gate behaviour). For each rule,
decide and label: hard-enforced (a gate in code refuses violations) or soft (model-honoured,
measured by evals). The gate is a hard stop — nothing the agent produces counts until a
human reviews it. No auto-proceed, no default-yes.
> Artifact: input-and-run-contract.md, plus the enforcement labels.

### Step 5 — Build it (narrow, transparent, instrumented)
Build v1 to the spec, no more. Minimal tools (ideally none with side effects for the first
agent). Instrument every run with traces (the trace tool is your review surface — treat
clean traces as a primary deliverable, not an add-on). Hard-enforce what the contracts say
to. When the build reports back, get an honest hard-vs-soft enforcement list.
> Artifact: the running agent + traces.

### Step 6 — Write the eval cases and the rubric
The cases come from whoever is the agent's real CUSTOMER (for an agent that serves you, you
write them; for an agent that does client work, harvest from the people who do that work).
A case is a task + a known-good standard + failure modes. Organise by the JUDGMENT the task
tests, not by output format. The rubric scores the qualities that matter, with cap
conditions (the binary, unforgivable failures) and graded dimensions (the spectrum
qualities). Build cases that HUNT for the agent's likely weak spots, not just easy passes.
> Artifacts: cases (schema'd), rubric. Both owned by you.

### Step 7 — Run it on real tasks
Hand it real work, one or a few at a time. Not a closed loop — you run, you read. For the
first agent, run a tidy task and a messy one: tidy proves it can format, messy proves it can
find signal in noise (the harder, realer test).
> Artifact: real outputs + traces.

### Step 8 — Hand-score, cold
You score each output against the rubric, before looking at any machine score. Score
judgment-only (principle 4). Watch for confirmation bias after a run of good scores — score
the restraint cases (where the right answer is "nothing here") hardest, because an eager
agent will manufacture insight.
> Artifact: hand-scores. These are the ground truth.

### Step 9 — Find the failure and encode it
The point of scoring is to find the failure mode. When you find one (Scout overstated a
load-bearing source), turn it into a RULE in the rubric (load-bearing overstatement caps at
0) and a worked example. The failure becomes a permanent part of the standard, so the agent
— and every future agent — is held to it.
> Artifact: updated rubric with the encoded lesson.

### Step 10 — Calibrate the judge
Once you have ~4-5 hand-scored cases across distinct failure modes, point the LLM judge at
them. Target 75-90% agreement with your scores. Below that, the rubric is fuzzy or the judge
is wrong — read the disagreements, they're the signal. The judge produces DRAFT scores you
review until it clears the bar. Never let it silently tune itself to agree.
> Artifact: a calibrated judge (or a known gap to fix).

### Step 11 — Open the gate, by earned trust
Only now, and only per task-type, loosen review on the things the agent has proven. Record
each loosening as a deliberate change to granted scope. Central decisions stay gated. This
is the dial from principle 3, turned for the first time.
> Artifact: updated job spec (widened granted scope).

### Then: repeat for the next agent
The next agent reuses this whole process. Change the job spec, the output spec, and the eval
cases; the skeleton (build → trace → gate → hand-score → encode → calibrate) is identical.
Scout proved the template; agent two tests whether it's reusable.

---

## What this looked like for Scout (the worked example)

- Job spec derived from the Head of AI Ops spec; Scout got the support verbs, Mal kept the
  authority verbs.
- Built v1 on the Claude Agent SDK, traced to Langfuse, no side-effect tools, hard stop after
  output. Hard-enforced: no tools, four-part structure, JSON footer, no recommendation on
  central decisions.
- Eval cases written by Mal (Scout's customer is Mal). Rubric with cap conditions + graded
  dimensions.
- Ran on a real messy task (the harness list). Hand-scored 0/15 — capped, because Scout
  overstated a load-bearing source (Manus). That failure was encoded as a rule.
- Ran three more (vendor, sequencing, thin-signal) built to bait known failures. All passed,
  including the restraint test. Four hand-scored cases now anchor the judge calibration.
- Found a contract bug along the way (the validator rejected a correct zero-decision brief) —
  caught only because a human was on the loop.

---

## Rolling it out across teams (decide before you ship this)

This framework is only real if the discipline travels with the templates. The risk: a team
takes the templates and drops the hard parts (the eval calibration, the cold hand-scoring,
the gate), because those are the tedious steps and the templates work without them — until
they don't. Decide whether this is GUIDANCE (here's how to do it well) or a STANDARD (this is
how agents get built at CO, and skipping the eval/gate steps isn't optional). The content is
the same; the rollout and the enforcement differ. That's a leadership call, not a template
choice.
