# Actionability filter

A finding is only an issue if it carries a specific proposed action. Otherwise it is
context.

## Purpose

A sweep or monitoring agent generates observations. Most observations are not issues.
This filter is the line between the two: an observation is surfaced as an issue only when
a specific action remains to be taken on it. If no action remains, it is context,
reported as such or dropped, never escalated into the issues list. The filter stops a
monitoring agent from drowning a real signal in a list of things that are technically
true but require nothing.

## When to use

Any agent that sweeps a system and reports findings (build health, cost, IAM drift,
infrastructure state). Apply it as the last pass before anything reaches an issues list
or an alert.

## The pattern

For every candidate finding, ask: is there a specific action that still needs taking?

- If yes, surface it as an issue, carrying the proposed action alongside the observation.
- If no action remains, it is not a finding. A failed build followed by a passing build
  is not an issue: nothing remains to do.
- Keep factual change separate from opinion. "Changed since the last sweep" is factual and
  surfaces as a warning to confirm intent. "Should be changed" is the agent's opinion and
  surfaces as context (info), not as an issue, unless it carries a named, evidence-backed
  action. "This binding looks broad" is not sufficient grounds for a proposed action.
- Run the filter twice where there is fan-in: once inside each specialist that produces
  findings, and once in the orchestrator that consolidates them, so nothing actionless
  survives consolidation.

## Example

Cost observation: spend on a service rose for one day after a backfill, then returned to
baseline.

Without the filter: surfaced as a cost anomaly. Noise. Nothing to do.

With the filter: no sustained change and no action remains, so it is not a finding. A
sustained week-over-week rise, carrying "investigate service X's growth" as the proposed
first step, is a finding.

## Variations

The unit of "action" shifts by domain: a proposed first investigation step for cost,
"review this diff and confirm intent" for an IAM change, a named alternative principal for
an IAM binding that should narrow. What is fixed: no proposed action means no issue, and
the factual-versus-opinion split is preserved end to end.

## Contracts it relates to

Closest kin is AC-2 (source honesty): the CHANGED-versus-SHOULD-BE-CHANGED split is the
same discipline as literal-versus-inferred, keeping fact apart from the agent's opinion.
It is also a restraint pattern in the Scout and Lookout sense, do not invent issues to
fill the page. Inside the sweep itself it runs as a hard filter, not a soft one.

## Source

The DevOps sweep specialists, proven in the agentic DevOps team personal-GCP pilot
("actionability test as a hard filter", refinement 3). The agent wording lives in the
sweep repo `supramal1/devOpsAgents` and the build note `agentic-devops-team-personal-pilot`;
this entry summarises the pattern rather than duplicating those specs.

## Version and date

v1.0, 2026-06-09.
