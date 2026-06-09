# Scout calibration briefs — derived from Mal's Head of AI Ops job spec

Six briefs, mapped to the five responsibility areas. Each is a real decision you'll hit.
Some need you to attach real material (flagged MATERIAL: YOU PROVIDE); others run on
public sources. Run them, hand-score against the rubric, build the golden set.

================================================================
BRIEF 1 — Operating model (responsibility: evolve and scale the AI-enabled operating model)
================================================================
BRIEF_ID:        opmodel-001
THE QUESTION:    What are the realistic shapes an agency AI operating model can take, and
                 which decisions about ours do I need to make first?
MATERIAL:        Public: 2-3 write-ups of agency/consultancy AI operating models, plus the
                 CO OS cheat sheet (attach it). YOU PROVIDE the cheat sheet.
FEEDS DECISIONS: How CO OS is structured; build sequence; what "AI-first operating model"
                 concretely means for a 40-person agency.
CONSTRAINTS:     Solo operator initially; CEO-backed; intelligence + automation streams;
                 must show value on the four 90-day metrics.
KNOWN CENTRAL:   The operating-model shape is central. Frame, do not recommend.
GOOD LOOKS LIKE: Cuts to the few real structural choices, frames each with options and
                 what would settle it, flags what's already decided in the cheat sheet vs
                 still open.
SCOPE EDGES:     Not designing CO OS. Framing the structural decisions about it.

================================================================
BRIEF 2 — LLM governance (responsibility: own and mature the enterprise LLM setup)
================================================================
BRIEF_ID:        llm-gov-001
THE QUESTION:    What does good governance and usage-standard practice look like for an
                 enterprise LLM setup at a small agency, and what do I need to decide?
MATERIAL:        Public: enterprise LLM governance / acceptable-use frameworks. Optionally
                 YOU PROVIDE current CO LLM usage if you have it post-start.
FEEDS DECISIONS: Configuration, usage standards, governance model for CO's LLM tooling.
CONSTRAINTS:     Claude Team today (Enterprise an open question); multi-client agency so
                 client-data handling matters; 40 staff with varying AI literacy.
KNOWN CENTRAL:   The governance model is central. Frame, do not recommend.
GOOD LOOKS LIKE: Separates the genuinely-must-decide from the standard-practice-just-adopt;
                 flags where multi-client confidentiality changes the picture.
SCOPE EDGES:     Not writing the policy. Framing the governance decisions.

================================================================
BRIEF 3 — Knowledge architecture (responsibility: formalise how knowledge is stored/accessed)
================================================================
BRIEF_ID:        knowledge-001
THE QUESTION:    What are the viable patterns for how an agency stores and retrieves its
                 decisions, documents, and knowledge, and which fits CO?
MATERIAL:        Public: knowledge-management / org-memory patterns. YOU PROVIDE a short
                 note on CO's current state (where docs and decisions live today) once known.
FEEDS DECISIONS: How Cornerstone and the wider knowledge layer are structured; what becomes
                 durable org memory vs stays in tools.
CONSTRAINTS:     Cornerstone exists as the memory layer; multi-client; solo operator;
                 must be usable by non-technical staff.
KNOWN CENTRAL:   The knowledge architecture is central. Frame, do not recommend.
GOOD LOOKS LIKE: Frames the store/access decisions, flags the build-vs-adopt line, surfaces
                 what only works if staff actually use it (adoption dependency).
SCOPE EDGES:     Not building the knowledge layer. Framing how it should work.

================================================================
BRIEF 4 — Behaviour change (responsibility: drive consistent behaviour change across teams)
================================================================
BRIEF_ID:        adoption-001
THE QUESTION:    What does effective AI-tool adoption and behaviour change look like in a
                 small professional-services firm, and what's my first-90-days play?
MATERIAL:        Public: change-management / tool-adoption case studies, ideally
                 professional-services or agency context.
FEEDS DECISIONS: The adoption strategy that drives the 50%-weekly-usage metric; how to
                 handle the bad-first-impression risk; champions vs mandates.
CONSTRAINTS:     40 staff; adoption is one of the four metrics; CO culture is fast-moving
                 ("make it happen", "progress beats perfection"); trust is fragile early.
KNOWN CENTRAL:   The adoption strategy is central. Frame, do not recommend.
GOOD LOOKS LIKE: Surfaces the non-obvious adoption risks (especially the one bad output
                 killing a user), frames the strategic choices, ties to the usage metric.
SCOPE EDGES:     Not writing the rollout plan. Framing the adoption decisions.

================================================================
BRIEF 5 — Agent strategy (responsibility: define, deploy, improve AI agents)
================================================================
BRIEF_ID:        agent-strategy-001
THE QUESTION:    Given Scout is built, what's the right sequence and shape for the rest of
                 the agent team, and what decides which agent comes next?
MATERIAL:        The agent-team framework and Scout build pack (attach them). YOU PROVIDE.
FEEDS DECISIONS: Which agent seat to build second; what gates promotion from one to the next;
                 how much to standardise the template.
CONSTRAINTS:     Solo operator; Scout is the proven template; each agent's evals come from
                 its real customer; trust-calibration gates expansion.
KNOWN CENTRAL:   The team sequence is central. Frame, do not recommend.
GOOD LOOKS LIKE: Frames the next-agent decision against real criteria (dependency, risk,
                 who the customer is), not just "what would be useful".
SCOPE EDGES:     Not deciding the next agent. Framing the decision.

================================================================
BRIEF 6 — A deliberately messy one (calibration: tests Scout on low-signal material)
================================================================
BRIEF_ID:        messy-001
THE QUESTION:    Is there anything in this batch of mixed material that actually changes how
                 I should think about [topic you pick], or is it mostly noise?
MATERIAL:        YOU PROVIDE: deliberately pick a messy, mixed-quality batch (a few blog
                 posts, a vendor page, a thread) on a topic you care about. The point is to
                 see whether Scout can say "mostly noise, here's the one real thing" rather
                 than manufacturing insight to seem useful.
FEEDS DECISIONS: Whatever the topic feeds; the real test is Scout's restraint.
CONSTRAINTS:     As relevant to the topic.
KNOWN CENTRAL:   Depends on topic.
GOOD LOOKS LIKE: Scout is willing to say "little of value here" if that's true. Does NOT
                 inflate thin material into false insight. Honesty under low signal.
SCOPE EDGES:     As relevant.
