@~/.claude/engineer/references/response-language-directive.md

<purpose>
Check project progress, summarize recent work and what's ahead, then intelligently route to the next action — either executing an existing plan or creating the next one. Provides situational awareness before continuing work.
</purpose>

<required_reading>
Read all files referenced by the invoking prompt's execution_context before starting.
</required_reading>

<process>

<step name="init_context">
**Load progress context (paths only):**

```bash
IFS= read -rd '' ENGINEER_ARGS <<'ENGINEER_ARGS_END' || true
$ARGUMENTS
ENGINEER_ARGS_END
ENGINEER_ARGS=${ENGINEER_ARGS%$'\n'}
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
FORENSIC_PARAM=""; if [[ "$ENGINEER_ARGS" =~ (^|[[:space:]])--forensic([[:space:]]|$) ]]; then FORENSIC_PARAM="--forensic"; fi
INIT=$(engineer_run query init.progress  $FORENSIC_PARAM)
```

Extract from init JSON: `project_exists`, `roadmap_exists`, `state_exists`, `requirements_exists`, `planning_exists`, `milestones_exists`, `init_incomplete`, `phases`, `current_phase`, `next_phase`, `milestone_version`, `completed_count`, `phase_count`, `paused_at`, `state_path`, `roadmap_path`, `project_path`, `config_path`.

```bash
DISCUSS_MODE=$(engineer_run query config-get workflow.discuss_mode --raw 2>/dev/null || echo "discuss")
```

**If `init_incomplete` is true (interrupted bootstrap):**

`.planning/` exists but the core initialization artifacts are missing (one or more of `REQUIREMENTS.md`, `ROADMAP.md`, `STATE.md` were never created — a bootstrap that stopped partway, e.g. after PROJECT.md). This is NOT a new project, NOT a missing STATE.md, and NOT a between-milestones state — do not fall through to any of those routes. Route to initialization recovery:

```
---

## ⚠ Initialization Incomplete

A partial `.planning/` was found: project initialization started but stopped before creating all core artifacts (missing: REQUIREMENTS.md, ROADMAP.md, STATE.md — whichever `requirements_exists` / `roadmap_exists` / `state_exists` report as false).

`/clear` then:

`/new-project` — resumes initialization from the first missing artifact; existing PROJECT.md (and any already-created artifacts) are kept, not regenerated.

---
```

Exit. (The payload's `init_incomplete` is computed with the between-milestones archive case excluded — `MILESTONES.md` present means missing ROADMAP/REQUIREMENTS is archival, and that state still routes to Route F below.)

If `init_incomplete` is false and `planning_exists` is false and `project_exists` is false (no `.planning/` directory at all):

```
No planning structure found.

Run /new-project to start a new project.
```

Exit.

If missing STATE.md: suggest `/new-project`.

**If ROADMAP.md missing but PROJECT.md exists (and `init_incomplete` is false):**

This means a milestone was completed and archived. Go to **Route F** (between milestones).

If missing both ROADMAP.md and PROJECT.md: suggest `/new-project`.
</step>

<step name="load">
**Use structured extraction from `engineer_run query`:**

Instead of reading full files, use targeted tools to get only the data needed for the report:
- `ROADMAP=$(engineer_run query roadmap.analyze)`
- `STATE=$(engineer_run query state-snapshot)`

This minimizes orchestrator context usage.
</step>

<step name="analyze_roadmap">
**Get comprehensive roadmap analysis (replaces manual parsing):**

```bash
ROADMAP=$(engineer_run query roadmap.analyze)
```

This returns structured JSON with:
- All phases with disk status (complete/partial/planned/empty/no_directory)
- Goal and dependencies per phase
- Plan and summary counts per phase
- Aggregated stats: total plans, summaries, progress percent
- Current and next phase identification

Use this instead of manually reading/parsing ROADMAP.md.
</step>

<step name="recent">
**Gather recent work context:**

- Find the 2-3 most recent SUMMARY.md files
- Use `summary-extract` for efficient parsing:
  ```bash
  engineer_run query summary-extract <path> --fields one_liner
  ```
- This shows "what we've been working on"
  </step>

<step name="position">
**Parse current position from init context and roadmap analysis:**

- Use `current_phase` and `next_phase` from `$ROADMAP`
- Note `paused_at` if work was paused (from `$STATE`)
- Count pending todos: use `init todos` or `list-todos`
- Check for active debug sessions: `(ls .planning/debug/*.md 2>/dev/null || true) | grep -v '/knowledge-base\.md$' | wc -l`
  </step>

<step name="report">
> ⚠️ Context authority: PROJECT.md, STATE.md, and ROADMAP.md are the authoritative sources
> for project name, milestone, current phase, and next-step routing. CLAUDE.md ## Project
> blocks are a secondary config aid that may be significantly stale — do NOT use the
> CLAUDE.md project description as a source for any progress report field.

**Generate progress bar from `engineer_run query progress` / `progress.json`, then present rich status report:**

```bash
# Get formatted progress bar
PROGRESS_BAR=$(engineer_run query progress.bar --raw)
```

Present:

````
# [Project Name]

**Progress:** {PROGRESS_BAR}
**Profile:** [quality/balanced/budget/inherit]
**Discuss mode:** {DISCUSS_MODE}

## Recent Work
- [Phase X, Plan Y]: [what was accomplished - 1 line from summary-extract]
- [Phase X, Plan Z]: [what was accomplished - 1 line from summary-extract]

## Current Position
Phase [N] of [total]: [phase-name]
Plan [M] of [phase-total]: [status]
CONTEXT: [✓ if has_context | - if not]

## Key Decisions Made
- [extract from $STATE.decisions[]]
- [e.g. jq -r '.decisions[].decision' from state-snapshot]

## Blockers/Concerns
- [extract from $STATE.blockers[]]
- [e.g. jq -r '.blockers[].text' from state-snapshot]

## Pending Todos
- [count] pending — /capture --list to review



## Active Debug Sessions
- [count] active — /debug to continue
(Only show this section if count > 0)

## What's Next
[Next phase/plan objective from roadmap analyze]
````

</step>


<step name="route">
**Determine next action based on verified counts.**

**Step 0: Resume-incomplete-phase invariant (Route 0)**

Before any current-phase-scoped counting, scan ALL phases for incomplete execution. This catches the case where STATE.md's `current_phase` was advanced past the phase that actually has unfinished work (common after a mid-execution session death from hang, token exhaustion, or API disruption). Without this guard, the current-phase-scoped count in Step 1 would inspect the wrong phase and the routing would skip the unfinished work.

**Skip if `--no-resume` or `--force` is present in `$ARGUMENTS`.**

Scan all phases via the `$ROADMAP` JSON already loaded in `analyze_roadmap`. For each phase entry, compare `plans` length to `summaries` length using the same plans-without-summaries predicate as `determine_next_action` Route 4 (`plans.length > summaries.length`). Stop at the first (lowest-numbered) phase where the predicate is true. Record its phase number as `INCOMPLETE_PHASE`.

If `$ROADMAP` is empty or the query failed, surface a warning rather than silently proceeding:

```bash
INCOMPLETE_PHASE=""
if [ -z "$ROADMAP" ]; then
  echo "⚠ WARNING: resume-incomplete-phase scan could not run (\$ROADMAP is empty)." >&2
  echo "  The incomplete-phase invariant  could not be verified." >&2
  echo "  Review project state carefully before continuing." >&2
else
  for PHASE_NUM in $(echo "$ROADMAP" | jq -r '.phases[] | (.number // .phase_number)'); do
    PHASE_DATA=$(echo "$ROADMAP" | jq --arg n "$PHASE_NUM" '.phases[] | select((.number // .phase_number) == ($n | tonumber))')
    # $PHASE_DATA is a `.phases[]` entry from `roadmap.analyze`, which
    # emits `plan_count`/`summary_count` SCALARS (src/roadmap.cts) — it has
    # never emitted `.plans`/`.summaries` ARRAYS. Reading those absent keys
    # (even with a `// []` fallback) always produced 0, permanently disabling
    # this resume-incomplete-phase check. Read the scalars the producer
    # actually emits.
    PLAN_COUNT=$(echo "$PHASE_DATA" | jq '.plan_count // 0')
    SUMMARY_COUNT=$(echo "$PHASE_DATA" | jq '.summary_count // 0')
    if [ "${PLAN_COUNT:-0}" -gt "${SUMMARY_COUNT:-0}" ]; then
      INCOMPLETE_PHASE="$PHASE_NUM"
      break
    fi
  done
fi
```

**If `INCOMPLETE_PHASE` is non-empty:** emit a one-line resume notice in the routing output and route to `/execute-phase ${INCOMPLETE_PHASE}` instead of running Step 1's current-phase routing. The progress report (already displayed by the `report` step above) gives the user full project status before this routing decision is shown.

```
---

## ▶ Next Up — Resuming incomplete Phase ${INCOMPLETE_PHASE}

`/clear` then:

`/execute-phase ${INCOMPLETE_PHASE} `

(plans without summaries detected; use --no-resume to skip this check and route by current_phase instead; --force to skip all gates)

---
```

Then exit the route step. Do NOT run Steps 1 through Routes A-F.

**If `INCOMPLETE_PHASE` is empty:** continue to Step 1.

**Step 1: Count plans, summaries, and issues in current phase**

Get plan/summary counts for the current phase from the single owner (LIVE
counts, i.e. `status: superseded` plans excluded, matching "outstanding work"):

```bash
PHASE_COUNTS=$(engineer_run query find-phase "${CURRENT_PHASE}")
X=$(echo "$PHASE_COUNTS" | jq -r '.plan_count // 0')
Y=$(echo "$PHASE_COUNTS" | jq -r '.summary_count // 0')
(ls -1 .planning/phases/[current-phase-dir]/*-UAT.md 2>/dev/null || true) | wc -l
```

State: "This phase has {X} plans, {Y} summaries."

**Step 1.5: Check for unaddressed UAT gaps**

Check for UAT.md files with status "diagnosed" (has gaps needing fixes).

```bash
# Check for diagnosed UAT with gaps or partial (incomplete) testing
grep -l "status: diagnosed\|status: partial" .planning/phases/[current-phase-dir]/*-UAT.md 2>/dev/null || true
```

Track:
- `uat_with_gaps`: UAT.md files with status "diagnosed" (gaps need fixing)
- `uat_partial`: UAT.md files with status "partial" (incomplete testing)

**Step 1.6: Cross-phase health check**

Scan ALL phases for outstanding verification debt using the CLI. Milestone scoping note: the audit milestone-filters the ACTIVE phase tree (`getMilestonePhaseFilter`), and deliberately adds ARCHIVED milestone trees unfiltered — each archived result carries an `archived_milestone` stamp. `summary.total_items` spans BOTH populations, so never read it as current-milestone debt.

```bash
DEBT=$(engineer_run query audit-uat --raw 2>/dev/null)
# A cross-population audit is exactly the payload that can exceed the CLI's
# below silently reads 0.
```

Segment the debt by population before counting:

```bash
CURRENT_DEBT=$(printf '%s' "$DEBT" | jq '[.results[] | select(has("archived_milestone") | not)] | map(.items | length) | add // 0' 2>/dev/null || echo 0)
ARCHIVED_DEBT=$(printf '%s' "$DEBT" | jq '[.results[] | select(has("archived_milestone"))] | map(.items | length) | add // 0' 2>/dev/null || echo 0)
```

Track: `outstanding_debt` — `CURRENT_DEBT`, the non-archived (current-milestone) count. Track `archived_debt` — `ARCHIVED_DEBT`, the still-open items in already-archived milestones. Track `parse_gap_files` — `summary.parse_gap_files` from the audit.

Archived debt stays VISIBLE — an item archived still-open is still open (the archived set can include an unrun security-boundary test). Render it as its own labeled line; never fold it into the current-milestone total and never filter it away.

`summary.parse_gap_files` counts EVERY file with `parse_gap: true`, archived or not — deliberately cross-population, unlike `outstanding_debt` (which scopes to non-archived results). An outstanding item does not stop mattering because its phase belongs to an already-archived milestone: a deferred human-UAT scenario or a `skipped` live-stack test is exactly what gets archived still-open, so an archived parse gap is exactly as much unread outstanding work as an archived `result: pending` row — it surfaces through `parse_gap_files` and the unparsed row below, keeping the whole cross-population picture visible.

**If outstanding_debt > 0 OR archived_debt > 0 OR parse_gap_files > 0:** Add a warning section to the progress report output (in the `report` step), placed between "## What's Next" and the route suggestion:

```markdown
## Verification Debt ({N} items across current-milestone phases; {M} items still open in archived milestones)

| Phase | File | Issue |
|-------|------|-------|
| {phase} | {filename} | {pending_count} pending, {skipped_count} skipped, {blocked_count} blocked |
| {phase} | {filename} | human_needed — {count} items |
| {phase} | {filename} | {unresolved_count} deferred items |
| {phase} | {filename} | unparsed — test blocks with no readable `result:` line |

Review: `/audit-uat ` — full cross-phase audit
Resume testing: `/verify-work {phase} ` — retest specific phase
```

The unparsed row comes from `results` entries with `parse_gap: true` (`summary.parse_gap_files` counts exactly those, archived or not). This is a WARNING, not a blocker — routing proceeds normally. The debt is visible so the user can make an informed choice.

**Step 1.7: Check verification status for the current phase**

A phase whose verification is anything but `passed` is NOT complete, even when every PLAN.md has a matching SUMMARY.md. The count-based status (`roadmap.analyze`) only sees plans/summaries, so without this check such a phase is reported complete and routing skips straight to the next phase. When the phase appears count-complete (`summaries = plans AND plans > 0`), consult the verification report (the same `verification.status` gate `ship` and `execute-phase` use, from ), on the phase directory the locator resolved:

```bash
PHASE_DIR=$(engineer_run query find-phase "${CURRENT_PHASE}" --pick directory)
VERIFICATION=$(engineer_run query verification.status "${PHASE_DIR}") || { echo "verification.status refused phase ${CURRENT_PHASE}'s report — see the error above." >&2; exit 1; }
VERIFICATION_STATUS=$(printf '%s' "$VERIFICATION" | jq -r '.status')
VERIFICATION_NEXT_ACTION=$(printf '%s' "$VERIFICATION" | jq -r '.next_action')
VERIFICATION_NEXT_COMMAND=$(printf '%s' "$VERIFICATION" | jq -r '.next_command')
```

Track: `verification_status` — the `.status` field of the closed set ; the query projects stale verification (`stale`, covered source changed after the verifier ran) and a missing report (`missing`) itself. A non-zero exit is a hard error (a report `status` outside `passed | gaps_found | human_needed`): surface it, never read it as "no status". Only `passed` routes as phase complete (Step 3); every other status routes back to close verification debt (Step 2) with the owner's `next_action` / `next_command`.

**Step 2: Route based on counts**

| Condition | Meaning | Action |
|-----------|---------|--------|
| uat_partial > 0 | UAT testing incomplete | Go to **Route E.2** |
| uat_with_gaps > 0 | UAT gaps need fix plans | Go to **Route E** |
| summaries < plans | Unexecuted plans exist | Go to **Route A** |
| summaries = plans AND plans > 0 AND verification_status = gaps_found | Phase executed; verification found gaps | Go to **Route V.gaps** |
| summaries = plans AND plans > 0 AND verification_status = human_needed | Phase executed; awaiting human verification | Go to **Route V.human** |
| summaries = plans AND plans > 0 AND verification_status ≠ passed | Phase executed; verification not passed | Go to **Route V** |
| summaries = plans AND plans > 0 AND verification_status = passed | Phase complete (verification passed) | Go to Step 3 |
| plans = 0 | Phase not yet planned | Go to **Route B** |

Rows are evaluated top to bottom; the first matching row wins. The `verification_status` rows must precede the passed row so non-`passed` verification is not reported as complete.

---

**Route A: Unexecuted plan exists**

Find the first PLAN.md without matching SUMMARY.md.
Read its `<objective>` section.

```
---

## ▶ Next Up — [${PROJECT_CODE}] ${PROJECT_TITLE}

**{phase}-{plan}: [Plan Name]** — [objective summary from PLAN.md]

`/clear` then:

`/execute-phase {phase} `

---
```

---

**Route B: Phase needs planning**

Check if `{phase_num}-CONTEXT.md` exists in phase directory.

Check if current phase has UI indicators:

```bash
PHASE_SECTION=$(engineer_run query roadmap.get-phase "${CURRENT_PHASE}" 2>/dev/null)
PHASE_HAS_UI=$(echo "$PHASE_SECTION" | grep -qi "UI hint.*yes" && echo "true" || echo "false")
```

**If CONTEXT.md exists:**

```
---

## ▶ Next Up — [${PROJECT_CODE}] ${PROJECT_TITLE}

**Phase {N}: {Name}** — {Goal from ROADMAP.md}
<sub>✓ Context gathered, ready to plan</sub>

`/clear` then:

`/plan-phase {phase-number} `

---
```

**If CONTEXT.md does NOT exist AND phase has UI (`PHASE_HAS_UI` is `true`):**

```
---

## ▶ Next Up — [${PROJECT_CODE}] ${PROJECT_TITLE}

**Phase {N}: {Name}** — {Goal from ROADMAP.md}

`/clear` then:

`/discuss-phase {phase}` — gather context and clarify approach

---

**Also available:**
- `/ui-phase {phase}` — generate UI design contract (recommended for frontend phases)
- `/plan-phase {phase}` — skip discussion, plan directly
- `/discuss-phase {phase}` — include assumptions check before planning

---
```

**If CONTEXT.md does NOT exist AND phase has no UI:**

```
---

## ▶ Next Up — [${PROJECT_CODE}] ${PROJECT_TITLE}

**Phase {N}: {Name}** — {Goal from ROADMAP.md}

`/clear` then:

`/discuss-phase {phase} ` — gather context and clarify approach

---

**Also available:**
- `/plan-phase {phase} ` — skip discussion, plan directly
- `/discuss-phase {phase} ` — include assumptions check before planning

---
```

---

**Route E: UAT gaps need fix plans**

UAT.md exists with gaps (diagnosed issues). User needs to plan fixes.

```
---

## ⚠ UAT Gaps Found

**{phase_num}-UAT.md** has {N} gaps requiring fixes.

`/clear` then:

`/plan-phase {phase} --gaps `

---

**Also available:**
- `/execute-phase {phase} ` — execute phase plans
- `/verify-work {phase} ` — run more UAT testing

---
```

---

**Route E.2: UAT testing incomplete (partial)**

UAT.md exists with `status: partial` — testing session ended before all items resolved.

```
---

## Incomplete UAT Testing

**{phase_num}-UAT.md** has {N} unresolved tests (pending, blocked, or skipped).

`/clear` then:

`/verify-work {phase} ` — resume testing from where you left off

---

**Also available:**
- `/audit-uat ` — full cross-phase UAT audit
- `/execute-phase {phase} ` — execute phase plans

---
```

---

**Route V: verification not passed**

All plans have summaries, but canonical verification has not passed (`missing`, `stale`, `unparseable`, `phase_dir_not_found` — the owner's closed set). The phase is implementation-complete, not phase-complete. Present the owner's answer; never name a command of your own for these statuses:

```
---

## Verification Not Passed

**Phase {phase}** has all plans summarized, but verification reads `${VERIFICATION_STATUS}`. ${VERIFICATION_NEXT_ACTION}

`/clear` then:

`${VERIFICATION_NEXT_COMMAND}` (omit this line when it is empty)

---
```

---

**Route V.gaps: verification found gaps (gaps_found)**

VERIFICATION.md exists with `status: gaps_found` — verification identified gaps that need fix plans. The phase is NOT complete.

```
---

## ⚠ Verification Gaps Found

**{phase_num}-VERIFICATION.md** reports `gaps_found`. ${VERIFICATION_NEXT_ACTION}

`/clear` then:

`${VERIFICATION_NEXT_COMMAND} ` — plan the gap fixes (the owner's route: plan-phase --gaps)

---
```

---

**Route V.human: human verification required (human_needed)**

VERIFICATION.md exists with `status: human_needed` — automated checks passed but manual verification items remain. The phase is NOT complete until they are resolved.

```
---

## Human Verification Required

**{phase_num}-VERIFICATION.md** reports `human_needed`. ${VERIFICATION_NEXT_ACTION}

`/clear` then:

`${VERIFICATION_NEXT_COMMAND} ` — resume human verification (the owner's route: verify-work)

---
```

---

**Step 3: Check milestone status (only when phase complete)**

Read ROADMAP.md and identify:
1. Current phase number
2. All phase numbers in the current milestone section

Count total phases and identify the highest phase number.

State: "Current phase is {X}. Milestone has {N} phases (highest: {Y})."

**Route based on milestone status:**

| Condition | Meaning | Action |
|-----------|---------|--------|
| current phase < highest phase | More phases remain | Go to **Route C** |
| current phase = highest phase | All phases complete | Go to **Route D** |

---

**Route C: Phase complete, more phases remain**

Read ROADMAP.md to get the next phase's name and goal.

Check if next phase has UI indicators:

```bash
NEXT_PHASE_SECTION=$(engineer_run query roadmap.get-phase "$((Z+1))" 2>/dev/null)
NEXT_HAS_UI=$(echo "$NEXT_PHASE_SECTION" | grep -qi "UI hint.*yes" && echo "true" || echo "false")
```

**If next phase has UI (`NEXT_HAS_UI` is `true`):**

```
---

## ✓ Phase {Z} Complete

## ▶ Next Up — [${PROJECT_CODE}] ${PROJECT_TITLE}

**Phase {Z+1}: {Name}** — {Goal from ROADMAP.md}

`/clear` then:

`/discuss-phase {Z+1}` — gather context and clarify approach

---

**Also available:**
- `/ui-phase {Z+1}` — generate UI design contract (recommended for frontend phases)
- `/plan-phase {Z+1}` — skip discussion, plan directly
- `/verify-work {Z}` — user acceptance test before continuing

---
```

**If next phase has no UI:**

```
---

## ✓ Phase {Z} Complete

## ▶ Next Up — [${PROJECT_CODE}] ${PROJECT_TITLE}

**Phase {Z+1}: {Name}** — {Goal from ROADMAP.md}

`/clear` then:

`/discuss-phase {Z+1} ` — gather context and clarify approach

---

**Also available:**
- `/plan-phase {Z+1} ` — skip discussion, plan directly
- `/verify-work {Z} ` — user acceptance test before continuing

---
```

---

**Route D: All phases complete (milestone ready to close)**

```
---

## 🎉 Milestone Complete

All {N} phases finished!

## ▶ Next Up — [${PROJECT_CODE}] ${PROJECT_TITLE}

**Complete Milestone** — archive and prepare for next

`/clear` then:

`/complete-milestone `

---

**Also available:**
- `/verify-work ` — user acceptance test before completing milestone

---
```

---

**Route F: Between milestones (ROADMAP.md missing, PROJECT.md exists)**

A milestone was completed and archived. Ready to start the next milestone cycle.

Read MILESTONES.md to find the last completed milestone version.

```
---

## ✓ Milestone v{X.Y} Complete

Ready to plan the next milestone.

## ▶ Next Up — [${PROJECT_CODE}] ${PROJECT_TITLE}

**Start Next Milestone** — questioning → research → requirements → roadmap

`/clear` then:

`/new-milestone `

---
```

</step>

<step name="edge_cases">
**Handle edge cases:**

- Phase complete but next phase not planned → offer `/plan-phase [next] `
- All work complete → offer milestone completion
- Blockers present → highlight before offering to continue
- Handoff file exists → mention it, offer `/resume-work `
</step>

<!-- engineer:section id="forensic-audit" when="flag:--forensic" -->
If `section_manifest` is `null` or `"forensic-audit"` is in its `included` list: read and execute `engineer/workflows/progress/steps/forensic-audit.md`. Otherwise skip — do not read the file.
<!-- /section -->

</process>

<success_criteria>

- [ ] Rich context provided (recent work, decisions, issues)
- [ ] Current position clear with visual progress
- [ ] What's next clearly explained
- [ ] Smart routing: /execute-phase if plans exist, /plan-phase if not
- [ ] User confirms before any action
- [ ] Seamless handoff to appropriate engineer command
      </success_criteria>
