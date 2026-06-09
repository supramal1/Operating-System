# Scout (v1)

Research-and-synthesis agent for Charlie Oscar AI Ops. Takes a filled-in brief and a
material file, produces a decision brief (Parts 1-4 + JSON footer per `03-output-spec.md`),
writes it to the outputs folder, stops.

Single source of truth: the spec files `01-job-spec.md` through `06-build-notes.md` in
this directory. Where this README and the spec disagree, the spec wins.

## What v1 is and is not

| Yes | No |
| --- | --- |
| Reads a brief + material from disk | Fetches its own material |
| Writes one markdown file to `outputs/` | Writes to any system of record |
| One Langfuse trace per `brief_id` | Sends, publishes, or notifies anything |
| Hard structural validation before writing | Auto-proceed past the gate |
| Hard-fails on a CENTRAL recommendation | Recommends on CENTRAL decisions |

## Setup

```sh
cd 01-scout
uv sync --extra dev
cp .env.example .env   # fill in Langfuse keys (and ANTHROPIC_API_KEY if needed)
```

## Run

```sh
uv run scout \
  --brief    drive/Charlie\ Oscar\ AI\ Ops/Agents/Scout/inbox/<your-brief>.md \
  --material drive/Charlie\ Oscar\ AI\ Ops/Agents/Scout/inbox/<your-material>.md
```

Optional flags:
- `--drive-root <path>` to point at a synced Drive folder
- `--specs-dir <path>` if you move the spec files
- `--model claude-opus-4-7` (default)

Scout exits with code 0 on success, 2 on a malformed brief, 3 if its own output fails
structural validation (no file written in either failure case).

## Evals

```sh
uv run scout-eval --validate                   # schema-check 08-scout_cases.jsonl
uv run scout-eval --run                        # run Scout against every case, score
uv run scout-eval --run --case scout-harness-list-001
uv run scout-eval --run --no-judge             # hard checks only
uv run scout-eval --score outputs.jsonl        # score pre-computed outputs
```

Scoring follows `09-scout_rubric.md`: a hard `must_not` + structural pre-filter, then
Claude as judge on the rubric dimensions, 0-3 each. The judge is calibrated to score
framing, not agreement.

## Layout

```
01-scout/
  01-..-06-..md            <- spec files (the contract; not edited by code)
  07-scout_cases_schema.json
  08-scout_cases.jsonl
  09-scout_rubric.md
  pyproject.toml
  src/scout/               <- the implementation
    agent.py               <- Claude Agent SDK call, no tools
    contracts.py           <- structural validators (input + output)
    render.py              <- file body + filename
    run.py                 <- CLI
    langfuse_trace.py      <- one trace per brief_id
    evals.py               <- hard pre-filter + LLM judge
  tests/                   <- contract + render tests
  drive/Charlie Oscar AI Ops/Agents/Scout/
    inbox/  outputs/  reviewed/  _specs/
```

## What is structurally enforced vs trusted to the model

**Hard (runtime, no escape):**
- No tools are available to the agent: `allowed_tools=[]`, built-ins disallowed by name,
  and a `can_use_tool` callback that denies anything else. v1 takes no side-effecting
  action because nothing it could call exists.
- The input brief must carry every required field with a non-empty value, and its
  `BRIEF_ID` must be filesystem-safe.
- The output must contain the four part headings in spec order.
- The output must end with a JSON footer that parses, contains the required keys, and
  has at least one decision with at least two options per decision.
- Every decision with `type == "CENTRAL"` must have `scout_read == null`. A CENTRAL
  recommendation rejects the run; no file is written.
- The footer's `brief_id` must match the brief Scout was run against.

**Soft (model-honoured, measured by evals + review):**
- Quality of synthesis and compression.
- Honesty of citations, conflicts shown, uncertainty marked.
- Correctness of CENTRAL vs PERIPHERAL labelling beyond the JSON-level check.
- Whether the framing actually surfaces inconvenient options Mal would have missed.
- Tone (direct, British spelling, no em dashes) per the system prompt.
