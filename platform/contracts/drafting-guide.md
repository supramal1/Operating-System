# Contract Drafting Guide

## Definition

A CO OS contract defines what a system is allowed to do, what it must refuse, what evidence it must produce, and what happens when the rule cannot be enforced yet.

A contract is not the same as:

- a policy paragraph
- a prompt instruction
- a best-practice note
- a dashboard metric
- an eval score

Those can support the contract, but the contract itself must point to enforcement.

## Rule Format

Write every rule in this shape:

```text
Rule:
The system must ...

Why:
The risk this controls is ...

Enforcement:
hard-enforced | soft/model-honoured | not implemented

Mechanism:
gateway deny | harness gate | approval hold | schema rejection | release block | audit alert | human process

Evidence:
What proves the rule fired or was checked.

Failure Mode:
What happens if the rule cannot be checked.
```

## Enforcement Labels

`hard-enforced` means the system refuses, blocks, holds, rejects, or prevents the action.

`soft/model-honoured` means the model is instructed to behave correctly, but the system does not yet prevent failure.

`not implemented` means the rule is desired but has no current mechanism.

## Drafting Standard

Each contract should include:

- purpose
- scope
- owners
- rules
- enforcement map
- evidence required
- open questions
- build implications
- acceptance tests

Keep examples synthetic unless explicitly cleared for real Charlie Oscar data.
