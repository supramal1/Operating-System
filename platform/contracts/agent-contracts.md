# Agent contracts

Enforceable rules that govern how agents behave. Each states: what it binds, the rule, how it is enforced (HARD = gated in code, refuses on violation; SOFT = model-honoured, measured by evals), and the consequence on violation. Read top to bottom, this is the honest map of which agent rules are actually enforced versus held by goodwill-plus-evals.

Owner: Mal. Canonical location: co-platform/platform/contracts/. Referenced, not copied.

## AC-1 — Human gate (no autonomous completion)

  - **Binds:** all agents.
  - **Rule:** An agent produces output for review and stops. Nothing it produces counts as done, and no downstream action is taken, until a human has reviewed and accepted it.
  - **Enforcement:** HARD. The run ends after output is written. No auto-proceed, no timeout-advance, no default-yes. There is no code path from agent output to a side-effect without human action.
  - **On violation:** treated as a platform defect, not an agent fault, fix the path that allowed auto-proceed. Build must restore the hard stop before the agent runs again.
  - **Owner:** Mal. Status: active.

## AC-2 — Source honesty

  - **Binds:** all agents that synthesise or cite source material (currently Scout).
  - **Rule:** An agent must not overstate what a source says. It must distinguish what a source literally states from what the agent infers, and must not attribute a conclusion to a source it cannot quote supporting.
  - **Severity:** overstating a source on which a load-bearing conclusion depends is treated as severely as fabrication. Trivial paraphrase imprecision is a minor fault.
  - **Enforcement:** SOFT (model-honoured), measured by the eval rubric's Honesty dimension. A load-bearing overstatement caps Honesty and the whole case at 0. Hard enforcement is not currently possible; v2 retrieval (agent can fetch and quote the source) is the structural fix. Until then this rule is held by the system prompt plus evals plus human review, NOT by a gate.
  - **On violation:** case capped at 0; agent not promoted on that task-type; logged to the calibration record as a worked example.
  - **Worked examples:** harness-list-001 (Manus overstatement), adoption-001 (reversed source attribution).
  - **Owner:** Mal. Status: active. Known-soft, retrieval is the fix.

## AC-3 — Frame, do not recommend (on central decisions)

  - **Binds:** agents that frame decisions for a human (currently Scout).
  - **Rule:** On decisions tagged CENTRAL (strategic, hard to reverse, the human's to own), the agent frames options and tradeoffs and stops. It does not recommend. On PERIPHERAL, reversible decisions it may recommend, clearly marked.
  - **Enforcement:** PARTIAL. Hard on the structural check (a CENTRAL decision in the output footer must carry no recommendation field, validator refuses otherwise). Soft on the judgment of whether framing is secretly steering, measured by the rubric's FrameNotRecommend dimension.
  - **On violation:** structural, run rejected before output is accepted. Judgment, scored down or capped on FrameNotRecommend.
  - **Owner:** Mal. Status: active.

## AC-4 — Agent never sets its own scope

  - **Binds:** all agents.
  - **Rule:** An agent does not choose what it can access, which memory graph it reads, what client it acts for, or what its own permissions are. Scope is set by the authenticated context the run executes under, before the agent acts. The agent receives a scoped handle; it cannot widen it.
  - **Enforcement:** HARD (must be). Scope is fixed at the boundary (gateway / run context), not inside the agent. An agent cannot query across the boundary it was given. This is the rule that prevents cross-client reach; it cannot be soft.
  - **On violation:** treated as a critical platform defect. The agent run is halted and the scoping boundary fixed before any further runs. Not an acceptable soft failure.
  - **Owner:** Mal. Status: active. Load-bearing for confidentiality.

## AC-5 — Agents propose, they do not author the standard

  - **Binds:** all agents.
  - **Rule:** An agent may draft, digest, synthesise, and propose. It may not author or silently change the governing standard, its own rubric, contracts, goldens, or the decisions a human owns. Where an agent drafts a change to a standard, a human signs off before it takes effect.
  - **Enforcement:** SOFT to HARD depending on artifact. Hard where the standard is in a store the agent can't write to without human approval; soft where it relies on the agent's discipline. Default: agents do not have write access to the contracts, rubrics, or schema; only humans (HODs) do.
  - **On violation:** any agent-authored change to a standard is void until human-reviewed; the write path that allowed it is closed.
  - **Owner:** Mal. Status: active.

## How to read this set

Count the HARDs and SOFTs. AC-1 and AC-4 are hard, those are the rules that protect against the worst outcomes (uncontrolled action, cross-client leakage) and they must never be soft. AC-2 is honestly soft and that is your known exposure, retrieval closes it. AC-3 and AC-5 are partial. The soft rules are where human review is doing the enforcing, so they are the rules you cannot stop watching until they are made hard.
