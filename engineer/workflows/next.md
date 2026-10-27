@~/.claude/engineer/references/response-language-directive.md

<purpose>
Detect current project state and automatically advance to the next logical Engineer workflow step.
Reads project state to determine: discuss → plan → execute → verify → complete progression.
</purpose>

<required_reading>
Read all files referenced by the invoking prompt's execution_context before starting.
</required_reading>

<process>

<step name="detect_state">
Read project state to determine current position:

```bash
_engineer_identity_ok() {
  [ -f "$1" ] || return 1
  [ "$(sh "$1" query runtime-identity --pick packageName --raw 2>/dev/null)" = "engineer-runtime" ]
}
_engineer_select() {
  for _engineer_candidate do
    if _engineer_identity_ok "$_engineer_candidate"; then
      ENGINEER_RUN="$_engineer_candidate"
      return 0
    fi
  done
  return 1
}
if [ -n "${ENGINEER_RUN:-}" ]; then
  _engineer_identity_ok "$ENGINEER_RUN" || {
    printf '%s\n' "ERROR: ENGINEER_RUN does not identify engineer-runtime: $ENGINEER_RUN" >&2
    exit 1
  }
else
  _engineer_root=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
  _engineer_runtime_root=${RUNTIME_DIR:-$_engineer_root}
  _engineer_path_candidate=$(command -v engineer_run 2>/dev/null || true)
  _engineer_select \
    "$_engineer_root/engineer/bin/engineer_run" \
    "$_engineer_runtime_root/engineer/bin/engineer_run" \
    "$_engineer_root/.claude/engineer/bin/engineer_run" \
    "$_engineer_root/.codex/engineer/bin/engineer_run" \
    "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/engineer/bin/engineer_run" \
    "${CODEX_HOME:-$HOME/.codex}/engineer/bin/engineer_run" \
    "$_engineer_path_candidate" || {
    printf '%s\n' 'ERROR: No engineer-runtime launcher was found. Install the Claude or Codex workflow runtime or set ENGINEER_RUN.' >&2
    exit 1
  }
fi
export ENGINEER_RUN
engineer_run() {
  sh "$ENGINEER_RUN" "$@"
}
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  _engineer_path_escaped=$(printf '%s' "${ENGINEER_RUN%/*}" | sed 's/[\\`"$]/\\&/g')
  printf 'export PATH="%s:$PATH"\n' "$_engineer_path_escaped" >> "$CLAUDE_ENV_FILE" 2>/dev/null || true
fi
# Get state snapshot
engineer_run query state.json 2>/dev/null || echo "{}"
```

Also read:
- `.planning/STATE.md` — current phase, progress, plan counts
- `.planning/ROADMAP.md` — milestone structure and phase list

Extract:
- `current_phase` — which phase is active
- `plan_of` / `plans_total` — plan execution progress
- `progress` — overall percentage
- `status` — active, paused, etc.

If no `.planning/` directory exists:
```
No Engineer project detected. Run `/new-project` to get started.
```
Exit.
</step>

<step name="safety_gates">
Run hard-stop checks before routing. Exit on first hit unless `--force` was passed.

If `--force` flag was passed, skip all gates, Route 0, and the prior-phase completeness prompt.
Print a one-line warning: `⚠ --force: skipping safety gates`
Then proceed directly to `determine_next_action`. (Route 0 and `prior_phase_completeness` are NOT reached under `--force`.)

**Gate 1: Unresolved checkpoint**
Check if `.planning/.continue-here.md` exists:
```bash
[ -f .planning/.continue-here.md ]
```
If found:
```
⛔ Hard stop: Unresolved checkpoint

`.planning/.continue-here.md` exists — a previous session left
unfinished work that needs manual review before advancing.

Read the file, resolve the issue, then delete it to continue.
Use `--force` to bypass this check.
```
Exit (do not route).

**Gate 2: Error state**
Check if STATE.md contains `status: error` or `status: failed`:
If found:
```
⛔ Hard stop: Project in error state

STATE.md shows status: {status}. Resolve the error before advancing.
Run `/health` to diagnose, or manually fix STATE.md.
Use `--force` to bypass this check.
```
Exit.

**Gate 3: Unchecked verification**
Check if the current phase has a VERIFICATION.md with any `FAIL` items that don't have overrides:
If found:
```
⛔ Hard stop: Unchecked verification failures

VERIFICATION.md for phase {N} has {count} unresolved FAIL items.
Address the failures or add overrides before advancing to the next phase.
Use `--force` to bypass this check.
```
Exit.

After all three hard-stop gates pass, continue to `resume_incomplete_phase`.
</step>

<step name="resume_incomplete_phase">
**Hard invariant: any phase with PLAN.md files lacking matching SUMMARY.md files must be completed before `/progress --next` routes to any forward action.**

This catches the common failure mode where a session died mid-execution (hang, token exhaustion, API connection drop) and STATE.md's `current_phase` got advanced past the phase that actually has unfinished work. Without this gate, `/progress --next` would route by `current_phase` and silently skip the partially-executed phase.

**Skip if `--no-resume` was passed** (fall through to `prior_phase_completeness`). (`--force` already bypassed all gates and Route 0 at `safety_gates` — it never reaches this step.)

**Why Route 0 runs here (after Gates 1-3, before the prior-phase defer prompt):** This step is a hard invariant independent of `current_phase`'s value — it must run before any routing rule that reads `current_phase`. Gates 1-3 are cheap repo/state validity checks that must always run — skipping them on the resume path would risk advancing into a broken-state project. The prior-phase completeness-scan DEFER PROMPT, however, must NOT run in the default (no-flag) case when Route 0 is about to resume the phase automatically: that would force a double-decision (prompt first, then resume anyway), overriding the user's choice. Route 0 placed here means: default = resume silently (no defer prompt); `--no-resume` = skip Route 0 and fall through to the prior-phase defer prompt in `prior_phase_completeness`; `--force` = jump straight to `determine_next_action` at `safety_gates` (never reaches Route 0 or `prior_phase_completeness` at all).

Scan ALL phases in ROADMAP order (lowest-numbered to highest) for incomplete-execution state. Use `engineer_run query roadmap.analyze` to get the phase list, then for each phase number `N` query `engineer_run query find-phase <N>` JSON and inspect its `plans` and `summaries` arrays. A phase is **incomplete-execution** when `plans.length > summaries.length` (at least one PLAN.md has no matching SUMMARY.md).

Stop at the first such phase. Record its phase number as `INCOMPLETE_PHASE`. This is the lowest-numbered phase that needs continued execution.

Illustrative bash:

```bash
INCOMPLETE_PHASE=""
ROADMAP_JSON=$(engineer_run query roadmap.analyze)
ROADMAP_SCOPE=$(echo "$ROADMAP_JSON" | jq -r '.scope // "complete"')
if [ $? -ne 0 ] || [ -z "$ROADMAP_JSON" ]; then
  echo "⚠ WARNING: resume-incomplete-phase scan could not run (roadmap.analyze failed)." >&2
  echo "  The incomplete-phase invariant (#160) could not be verified." >&2
  echo "  Proceeding to prior-phase completeness check — review project state carefully." >&2
  # Fall through to prior_phase_completeness rather than silently skipping
elif [ "$ROADMAP_SCOPE" != "complete" ]; then
  # #3184/#3165: roadmap.analyze succeeded and returned a well-formed document,
  # but its milestone window did not see all of its input, so `.phases[]` is a
  # NON-answer rather than a real empty. Looping it would run the invariant over
  # a phase list the scan could not populate and report "clean" — the silent
  # disarm #3165 reports. Treated as scan-failed, same as an outright failure.
  echo "⚠ WARNING: resume-incomplete-phase scan could not be scoped (roadmap.analyze scope: $ROADMAP_SCOPE)." >&2
  echo "  The milestone window did not cover the whole ROADMAP, so the phase list is incomplete." >&2
  echo "  The incomplete-phase invariant (#160) could not be verified — review project state carefully." >&2
  # Fall through to prior_phase_completeness rather than silently passing
else
  for PHASE_NUM in $(echo "$ROADMAP_JSON" | jq -r '.phases[] | (.number // .phase_number // empty)'); do
    PHASE_JSON=$(engineer_run query find-phase "$PHASE_NUM")
    if [ $? -ne 0 ] || [ -z "$PHASE_JSON" ]; then
      echo "⚠ WARNING: Could not query phase $PHASE_NUM — skipping in resume scan." >&2
      continue
    fi
    PLAN_COUNT=$(echo "$PHASE_JSON" | jq '(.plans // []) | length')
    SUMMARY_COUNT=$(echo "$PHASE_JSON" | jq '(.summaries // []) | length')
    if [ "${PLAN_COUNT:-0}" -gt "${SUMMARY_COUNT:-0}" ]; then
      INCOMPLETE_PHASE="$PHASE_NUM"
      break
    fi
  done
fi
```

**If `INCOMPLETE_PHASE` is non-empty:** route to `/execute-phase $INCOMPLETE_PHASE` and exit. Display a one-line notice before invoking:

```
▶ Resuming incomplete Phase ${INCOMPLETE_PHASE} (plans without summaries detected)
  /execute-phase ${INCOMPLETE_PHASE}
  (use --no-resume to skip this check and defer via the prior-phase prompt)
```

Then invoke via SlashCommand. Do not continue to subsequent steps.

**If `INCOMPLETE_PHASE` is empty:** continue to `prior_phase_completeness`.
</step>

<step name="prior_phase_completeness">
**Prior-phase completeness scan (runs when `--no-resume` was passed and Route 0 was skipped, or when Route 0 found no incomplete-execution phases in the default case). NOT reached under `--force` — that flag jumps directly to `determine_next_action` at `safety_gates`.**

**Prior-phase completeness scan:**
Scan all phases that precede the current phase in ROADMAP.md order for incomplete work. For each prior phase number `N`, use `engineer_run query find-phase <N>` JSON (plans, summaries, incomplete_plans, etc.) to inspect that phase.

Detect three categories of incomplete work:
1. **Plans without summaries** — a PLAN.md exists in a prior phase directory but no matching SUMMARY.md exists (execution started but not completed).
2. **Verification failures not overridden** — a prior phase has a VERIFICATION.md with `FAIL` items that have no override annotation.
3. **CONTEXT.md without plans** — a prior phase directory has a CONTEXT.md but no PLAN.md files (discussion happened, planning never ran).

If no incomplete prior work is found, continue to `determine_next_action` silently with no interruption.

If incomplete prior work is found, show a structured completeness report:
```
⚠ Prior phase has incomplete work

Phase {N} — "{name}" has unresolved items:
  • Plan {N}-{M} ({slug}): executed but no SUMMARY.md
  [... additional items ...]

Advancing before resolving these may cause:
  • Verification gaps — future phase verification won't have visibility into what prior phases shipped
  • Context loss — plans that ran without summaries leave no record for future agents

Options:
  [C] Continue and defer these items to backlog
  [S] Stop and resolve manually (recommended)
  [F] Force advance without recording deferral

Choice [S]:
```

**If the user chooses "Stop" (S or Enter/default):** Exit without routing.

**If the user chooses "Continue and defer" (C):**
1. For each incomplete item, create a backlog entry in `ROADMAP.md` under `## Backlog` using the existing `999.x` numbering scheme:
```markdown
### Phase 999.{N}: Follow-up — Phase {src} incomplete plans (BACKLOG)

**Goal:** Resolve plans that ran without producing summaries during Phase {src} execution
**Source phase:** {src}
**Deferred at:** {date} during /progress --next advancement to Phase {dest}
**Plans:**
- [ ] {N}-{M}: {slug} (ran, no SUMMARY.md)
```
2. Commit the deferral record:
```bash
engineer_run query commit "docs: defer incomplete Phase {src} items to backlog" \
  --files .planning/ROADMAP.md
```
3. Continue routing to `determine_next_action` immediately — no second prompt.

**If the user chooses "Force" (F):** Continue to `determine_next_action` without recording deferral.
</step>

<step name="spike_sketch_notice">
Check for pending spike/sketch work and surface a notice (does not change routing):

```bash
# Check for pending spikes (verdict: PENDING in any README)
PENDING_SPIKES=$(grep -rl 'verdict: PENDING' .planning/spikes/*/README.md 2>/dev/null | wc -l | tr -d ' ')

# Check for pending sketches (winner: null in any README)
PENDING_SKETCHES=$(grep -rl 'winner: null' .planning/sketches/*/README.md 2>/dev/null | wc -l | tr -d ' ')
```

If either count is > 0, display before routing:
```
⚠ Pending exploratory work:
  {PENDING_SPIKES} spike(s) with unresolved verdicts in .planning/spikes/
  {PENDING_SKETCHES} sketch(es) without a winning variant in .planning/sketches/

  Resume with `/spike` or `/sketch`, or continue with phase work below.
```

Only show lines for non-zero counts. If both are 0, skip this notice entirely.
</step>

<step name="determine_next_action">
Apply routing rules based on state:

**Route 1: No phases exist yet → discuss**
If ROADMAP has phases but no phase directories exist on disk:
→ Next action: `/discuss-phase <first-phase>`

**Route 2: Phase exists but has no CONTEXT.md or RESEARCH.md → discuss**
If the current phase directory exists but has neither CONTEXT.md nor RESEARCH.md:
→ Next action: `/discuss-phase <current-phase>`

**Route 3: Phase has context but no plans → plan**
If the current phase has CONTEXT.md (or RESEARCH.md) but no PLAN.md files:
→ Next action: `/plan-phase <current-phase>` (or `/plan-review-convergence <current-phase>` when `PLAN_STRATEGY=converge`)

**Route 4: Phase has plans but incomplete summaries → execute**
If plans exist but not all have matching summaries:
→ Next action: `/execute-phase <current-phase>`

**Route 5: All plans have summaries → verify and complete**
If all plans in the current phase have summaries:
→ Next action: `/verify-work`

**Route 6: Phase complete, next phase exists → advance**
If the current phase is complete and the next phase exists in ROADMAP:
→ Next action: `/discuss-phase <next-phase>`

**Route 7: All phases complete → complete milestone**
If all phases are complete:
→ Next action: `/complete-milestone`

**Route 8: Paused → resume**
If STATE.md shows paused_at:
→ Next action: `/resume-work`
</step>

<step name="show_and_execute">
Parse the arguments passed to this workflow to detect the plan strategy and build convergence pass-through args:

```bash
IFS= read -rd '' GSD_ARGS <<'GSD_ARGS_END' || true
$ARGUMENTS
GSD_ARGS_END
GSD_ARGS=${GSD_ARGS%$'\n'}
PLAN_STRATEGY="local"
if echo "$GSD_ARGS" | grep -qE '(^|[[:space:]])\-\-(converge|cross-ai)([[:space:]]|$)'; then
  PLAN_STRATEGY="converge"
fi

CONVERGENCE_ARGS=""
# Lane flags derived from the declared roster (#2800/#2272); --all and --text are convergence
# controls, not reviewer lanes, so they stay literal.
for REVIEW_FLAG in $(engineer_run review-lane flags) --all --text; do
  if echo "$GSD_ARGS" | grep -qE "(^|[[:space:]])${REVIEW_FLAG}([[:space:]]|$)"; then
    CONVERGENCE_ARGS="${CONVERGENCE_ARGS} ${REVIEW_FLAG}"
  fi
done

MAX_CYCLES_ARG=""
if echo "$GSD_ARGS" | grep -qE '\-\-max-cycles\s+[0-9]+'; then
  MAX_CYCLES_ARG=$(echo "$GSD_ARGS" | grep -oE '\-\-max-cycles\s+[0-9]+' | awk '{print $2}')
  CONVERGENCE_ARGS="${CONVERGENCE_ARGS} --max-cycles ${MAX_CYCLES_ARG}"
fi
```

If `PLAN_STRATEGY` is `converge`, fail fast unless the convergence feature gate is enabled:

```bash
if [ "$PLAN_STRATEGY" = "converge" ]; then
  CONVERGENCE_ENABLED=$(engineer_run query config-get workflow.plan_review_convergence --raw 2>/dev/null || echo "false")
  if [ "$CONVERGENCE_ENABLED" != "true" ]; then
    printf '%s\n' \
      '/progress --next --converge is disabled (workflow.plan_review_convergence=false).' \
      '' \
      'Enable plan convergence with:' \
      '' \
      '  gsd config-set workflow.plan_review_convergence true' \
      '' \
      'Then re-run with --converge.'
    exit 1
  fi
fi
```

Display the determination:

```
## Engineer Next

**Current:** Phase [N] — [name] | [progress]%
**Status:** [status description]

▶ **Next step:** `/[command] [args]`
  [One-line explanation of why this is the next step]
```

Then immediately invoke the determined command via SlashCommand.
Do not ask for confirmation — the whole point of `/progress --next` is zero-friction advancement.

**Route 3 convergence override:** When the routing decision is Route 3 (plan) and `PLAN_STRATEGY=converge`, invoke `/plan-review-convergence <current-phase> ${CONVERGENCE_ARGS}` instead of `/plan-phase <current-phase>`.

**If `--auto` was passed:** after the determined command completes, automatically re-invoke `/progress --next --auto` (forwarding `--converge`/`--cross-ai` and any reviewer flags if they were originally passed) to continue chaining to the next step. Repeat until one of:
- A milestone completes (`/complete-milestone` is reached)
- A blocking decision is required (safety gate triggers, prior-phase completeness prompt, user input needed)
- An error or paused state is detected

When stopping due to a blocker, display:
```
⛔ Auto-chain stopped: [reason — e.g. safety gate, blocking decision required]

Resume with: `/progress --next --auto` once resolved.
```
</step>

</process>

<success_criteria>
- [ ] Project state correctly detected
- [ ] Gates 1-3 (repo/state validity) run first — always, even on the resume path
- [ ] Route 0 (resume_incomplete_phase) runs AFTER Gates 1-3 and BEFORE the prior-phase defer prompt — no double-decision in the default (no-flag) case
- [ ] Default (no flag): Route 0 resumes incomplete phase silently, exits — user never sees the prior-phase defer prompt
- [ ] `--no-resume`: Route 0 skipped, prior_phase_completeness defer prompt runs as before
- [ ] `--force`: everything skipped (Gates, Route 0, prior_phase_completeness) → straight to `determine_next_action`
- [ ] Scan uses `engineer_run` (canonical resolver form); errors are surfaced rather than suppressed
- [ ] A `roadmap.analyze` result whose `scope` is not `complete` is treated as scan-failed (warn + fall through), never as a clean empty scan (#3184/#3165)
- [ ] Predicate is plans-without-summaries (`plans.length > summaries.length`) — consistent with `determine_next_action` Route 4
- [ ] Next action correctly determined from routing rules
- [ ] Command invoked immediately without user confirmation
- [ ] Clear status shown before invoking
- [ ] `--converge` routes Route 3 planning through `gsd-plan-review-convergence`
- [ ] `--cross-ai` is accepted as an alias for `--converge`
- [ ] `--converge` fails fast with enable instructions when `workflow.plan_review_convergence=false`
- [ ] `--converge` forwards reviewer selector flags and `--max-cycles N`
- [ ] Default planning remains `gsd-plan-phase` when convergence is not requested
</success_criteria>
