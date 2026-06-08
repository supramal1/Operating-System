# C13 Output And Publication Contract

## Purpose

Define when work is a draft, when it is ready for review, and when it can be sent or used externally.

## Scope

- emails
- briefs
- presentations
- research summaries
- recommendations
- client-facing performance claims
- external sends
- publication approvals

## Draft Rules

### Rule 1: Outputs Must Have A Status

Rule: Every generated output must be labelled as draft, review, approved, published, or blocked.

Enforcement: hard-enforced in output workflow; soft/model-honoured for ad hoc desktop use

Mechanism: output status field and publication gate.

Evidence: output record shows status, owner, timestamp, and approval state.

### Rule 2: Client-Facing Output Needs Approval

Rule: Client-facing emails, briefs, decks, and recommendations must not be sent externally without approval.

Enforcement: hard-enforced for managed send tools; human process for manual copy/paste

Mechanism: approval hold and send gate.

Evidence: approval record links to output id, approver, and final content hash or version id.

### Rule 3: Unsupported Claims Must Be Blocked Or Labelled

Rule: Performance claims, legal claims, commercial claims, and client-data claims must either cite evidence or be blocked from publication.

Enforcement: hard-enforced for managed publication; soft/model-honoured in draft prose

Mechanism: claim classifier, source check, and approval hold.

Evidence: output shows claim evidence, missing-evidence label, or block reason.

## Open Questions

- Which outputs count as client-facing before they leave Charlie Oscar systems?
- Who can approve publication for each output type?
- Which claims require evidence before review rather than before send?

## Acceptance Tests

- Block external send for draft output.
- Hold client-facing deck for approval.
- Reject unsupported performance claim in approved output.
- Allow internal draft with clear missing-evidence label.
