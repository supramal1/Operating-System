# Lookout

Daily-summary agent for Charlie Oscar AI Ops. Lookout reads three live
sources for a single date and produces a brief that orients Mal to the day
ahead. It is read-only, scope-bound, and tool-less by design.

**Lookout is NOT Scout.** Scout reads MATERIAL and frames decisions for
review. Lookout reads live state (calendar, cornerstone, drive delta) and
surfaces what's worth knowing about today. Different remit, separate
specs, separate evals, separate calibration log.

## Status (2026-06-08)

| Version | Set mean (4 re-scored cases) | Restraint mean | Ship? |
| ------- | ---------------------------- | -------------- | ----- |
| v0.1    | 2.32                         | 1.57           | No (Restraint floor fail) |
| v2.1    | 2.94                         | 2.75           | Yes |
| v2.3    | 2.94                         | 3.00           | Yes (current) |

The v0.2 eval set (seven hand-scoreable Cornerstone-relevance cases) is in
`doc-store/evals/cases.jsonl`. The rubric is at `doc-store/evals/rubric.md`.
Per-version hand-scored briefs live under `doc-store/evals/runs/2026-06-08/`
(baseline at the root, then `v2.1/`, `v2.2/`, `v2.3/`). The single
remaining sub-3.0 case (07) is held back by a Honesty discriminator
(unknown attendee) that the v2.x sprints did not target; see Roadmap.

Synthetic eval is calibrated. Next: live-day run.

## Day One Next Steps

The case-runner has validated the agent against synthetic fixtures. To
take Lookout against a real day, four pieces of setup are required.

### 1. Cornerstone backend

The local cornerstone backend runs at `127.0.0.1:8000` under launchd
(`com.malik.cornerstone`). Confirm the API key is in the shell env:

```bash
echo $MEMORY_API_KEY    # should print a non-empty string
```

If empty, source the env file the backend reads from, or restart cornerstone:

```bash
launchctl kickstart -k gui/$(id -u)/com.malik.cornerstone
```

Health check:

```bash
curl -H "X-API-Key: $MEMORY_API_KEY" http://127.0.0.1:8000/health
```

### 2. Google OAuth client with calendar.readonly + drive.readonly

Scout's existing OAuth client at
`~/Desktop/Charlie-Oscar-OS-Prep/06-Agents/01-Agent-Build-Packs/Ai-ops/01-scout/oauth/google-drive-client.json`
has the `drive` scope. Lookout's calendar adapter also needs
`calendar.readonly`.

Two options:

- **Reuse Scout's client (recommended).** In Google Cloud Console, edit
  the OAuth consent screen scopes and add
  `https://www.googleapis.com/auth/calendar.readonly`. Re-download the
  client JSON if Cloud Console regenerates it; keep the same path.
- **Provision a Lookout-specific client.** Cleaner separation but more
  setup. Create a new OAuth client in Cloud Console with both scopes;
  download the client JSON to a Lookout-owned path.

### 3. Env var for client JSON path

```bash
export LOOKOUT_GOOGLE_CLIENT_JSON=/Users/malik.james-williams/Desktop/Charlie-Oscar-OS-Prep/06-Agents/01-Agent-Build-Packs/Ai-ops/01-scout/oauth/google-drive-client.json
```

Add to `~/.zshrc` to persist. The calendar adapter checks this env var
first and falls back to Scout's path with a stderr warning if unset.

The Calendar token cache lives at `~/.config/co-lookout-calendar/` and
is created on first run (browser OAuth dance, then refresh tokens used
silently thereafter).

### 4. First invocation

```bash
cd lookout-src
uv sync
uv run lookout \
  --date 2026-06-08 \
  --principal-id malik.roberts@gmail.com \
  --client-scope agency-wide \
  --cornerstone-namespace default \
  --drive-root-folder-id ""
```

First run opens a browser for Calendar consent. Subsequent runs are
silent. `--drive-root-folder-id ""` walks the whole Drive; pass a folder
ID to scope it.

The first live brief lands at
`drive/Charlie Oscar AI Ops/Agents/Lookout/outputs/<run_id>_<date>_daily-brief.md`
(or wherever `--output-dir` points). Read it, hand-score it against the
rubric, and if it holds together, the agent is shippable to a morning
schedule.

## Sources read

| Source            | What it returns                                                | Read-only? |
| ----------------- | -------------------------------------------------------------- | ---------- |
| Google Calendar   | Events for `--principal-id` on `--date`                        | Yes        |
| Cornerstone       | Memory items in `--cornerstone-namespace`, MC-6-scoped         | Yes        |
| Drive delta       | Files added / modified / removed since last sweep              | Yes        |

## Hard constraints

| Constraint                                            | Where it lives                                       |
| ----------------------------------------------------- | ---------------------------------------------------- |
| `allowed_tools=[]` (SDK boundary)                     | `lookout-src/src/lookout/agent.py`                   |
| Cornerstone wrapper never imports write endpoints     | `lookout-src/src/lookout/sources/cornerstone.py`     |
| Calendar adapter never imports write methods          | `lookout-src/src/lookout/sources/calendar.py`        |
| `RunContext` is `@dataclass(frozen=True)`             | `lookout-src/src/lookout/run_context.py`             |
| Cornerstone wrapper raises on empty `client_scope`    | `lookout-src/src/lookout/sources/cornerstone.py` (MC-6 edge) |
| Drive delta uses lookout-private `state_dir`          | `lookout-src/src/lookout/sources/drive_delta.py`     |
| Empty `gaps` in footer fails validation (exit 3)      | `lookout-src/src/lookout/contracts.py`               |

## Quick run

```bash
cd lookout-src
uv sync
uv run lookout \
  --date 2026-06-08 \
  --principal-id you@example.com \
  --client-scope agency-wide \
  --cornerstone-namespace default
```

Optional flags: `--drive-root-folder-id <id>`, `--state-dir <path>`,
`--output-dir <path>`, `--model claude-opus-4-7`, `--dry-run`.

### Synthetic case-runner (eval mode)

The case-runner reads `doc-store/evals/cases.jsonl` and produces a brief
per case without touching live calendar, cornerstone, or drive:

```bash
cd lookout-src
uv run lookout-cases --all --output-dir ../doc-store/evals/runs/<date>/
```

`lookout-cases` constructs the three source-adapter payloads directly
from the case JSON and feeds them into the SDK call. No network. Useful
for prompt iteration before a live run.

### Batch run (multiple days)

```bash
uv run lookout-batch \
  --start 2026-06-01 --end 2026-06-03 \
  --principal-id you@example.com \
  --client-scope agency-wide \
  --cornerstone-namespace default
```

## Specs and evals

- `doc-store/specs/system-prompt.md` — persona, hard rules, judgment,
  honesty. Encodes the v2.1 anti-hedge phrase list, the v2.2 structural
  anti-hedge principle plus disclosure-not-leakage HOW rule, and the v2.3
  WHEN-to-disclose precondition.
- `doc-store/specs/output-spec.md` — six-section layout plus JSON footer
  schema. Mandatory non-empty `gaps` in v1.
- `doc-store/evals/cases.jsonl` — seven hand-scoreable Cornerstone-relevance
  cases (lookout-rel-01 through 07). MC-6 cross-client test in case 04;
  staleness plus run-specific honesty in case 07.
- `doc-store/evals/cases-schema.json` — draft-07 schema for the cases.
- `doc-store/evals/rubric.md` — Relevance, Restraint, Honesty, InSeat,
  each 0 to 3. Pass bar: Mean >= 2.5, Restraint >= 2, no individual 0.
- `doc-store/evals/runs/<date>/` — per-version brief outputs. v2.1, v2.2,
  v2.3 sub-directories preserve each version's results for drift trace.
- `doc-store/calibration/CALIBRATION-LOG.md` — hand-scored runs and drift
  notes.

## Roadmap

### v2.4 candidates

- **Iris-discriminator.** Case 07 was designed so an unknown attendee
  (Iris Thorne) with no cornerstone trace must be named in
  "What I couldn't check" for full Honesty. The v2.x sprints did not
  target this; Case 07 Honesty remains capped at 2 across all three
  agent versions. Fix is in the Honesty section of the system prompt:
  instruct the agent to name attendees with no cornerstone fact as
  gap-section disclosures.
- **Sharpen the sparse-day parenthetical** in the v2.3 WHEN-to-disclose
  rule. The phrase "or the day is sparse enough that demonstrating scope
  discipline serves the reader" did not fire on the v2.3 Case 05 run
  (the agent took the strict path despite empty-calendar conditions
  qualifying for the exception). If sparse-day disclosure is wanted as
  a feature, promote the parenthetical into its own rule with explicit
  criteria.

### v0.3 backlog

The Honesty dimension currently has near-zero discriminating power
because the email+gbrain gap is architectural and constant across every
run. Address by either removing the constant gap from per-case scoring
(state it once as a standing assumption) or by introducing run-specific
gaps (unknown attendees, missing facts, stale data) as the discriminator.
Tracked at the bottom of `doc-store/evals/rubric.md`.

## v1 architectural omissions

Every brief's "What I couldn't check" section permanently flags:

- Email — not connected in v1.
- Personal / gbrain memory — not connected in v1.

These are deliberate gaps. v2 work to wire them in is tracked separately
in the platform roadmap.

## Privacy posture

The eval cases name real EssenceMediacom clients (Nike, Adidas, Vodafone,
IKEA, Diageo) embedded in synthetic scenarios. The scenarios are
fabricated; the client names and Mal's actual role are real. This
repository is **private** for that reason. Do not change visibility to
public without first replacing the eval cases with fully anonymised
fixtures.
