@~/.claude/engineer/references/run-resolver.md

<!-- engineer:loop-host
step: plan
points: plan:pre, plan:post
agent-roles: researcher, planner, checker
produces: PLAN.md
consumes: CONTEXT.md
-->
<purpose>
Create executable phase prompts (PLAN.md files) for a roadmap phase with integrated research and verification. Default flow: Research (if needed) -> Plan -> Verify -> Done. Orchestrates phase-researcher, planner, and plan-checker agents with a revision loop (max 3 iterations).
</purpose>

<required_reading>
Read all files referenced by the invoking prompt's execution_context before starting.

@~/.claude/engineer/references/ui-brand.md
@~/.claude/engineer/references/revision-loop.md
@~/.claude/engineer/references/gate-prompts.md
@~/.claude/engineer/references/agent-contracts.md
@~/.claude/engineer/references/gates.md
</required_reading>

<available_agent_types>
Valid Engineer subagent types (use exact names — do not fall back to 'general-purpose'):
- phase-researcher — Researches technical approaches for a phase
- pattern-mapper — Analyzes codebase for existing patterns, produces PATTERNS.md
- planner — Creates detailed plans from phase scope
- plan-checker — Reviews plan quality before execution
</available_agent_types>

<runtime_compatibility>
**Subagent spawning — top-level Claude Code:**
The Agent tool IS available in a top-level Claude Code session. Always spawn
phase-researcher, planner, and plan-checker as separate Agent() calls.
Never absorb these roles inline. Role separation is required regardless of `--chain`
or `--auto` — those options suppress interactive prompts only; they NEVER authorize
collapsing plan roles into the orchestrator context.

**Backgrounded Claude Code (via manager/autonomous):**
The calling workflow (manager.md / autonomous.md) already runs plan-phase inline via
Skill() on Claude Code so that the plan-checker subagent can still spawn. plan-phase
itself does not need to detect this case.

** caveat (discuss-phase early-exit):**
The "display the command and exit" instruction near `## 4` applies only to the
discuss-phase early-exit path. It does NOT authorize inline role performance for any
plan-phase agents.

**Other runtimes:**
Do not pre-judge Agent availability by introspection. Always attempt the actual
Agent() call for phase-researcher, planner, and plan-checker. Only
a real tool-unavailable error returned by Agent() is a reliable absence signal —
never stop based on a self-assessed "I think Agent is unavailable." If the call
fails with a tool-unavailable error, log the gap and stop — do NOT collapse
researcher/planner/checker roles inline. Independent agent contexts are required
for the plan-checker gate to be meaningful.
</runtime_compatibility>

<process>

## 0. Git Branch Invariant

**Do not create, rename, or switch git branches during plan-phase.** Branch identity is established at discuss-phase and is owned by the user's git workflow. A phase rename in ROADMAP.md is a plan-level change only — it does not mutate git branch names. If `phase_slug` in the init JSON differs from the current branch name, that is expected and correct; leave the branch unchanged.


## 1. Initialize

Load all context in one call (paths only to minimize orchestrator context):

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
GRAN_PARAM=""; if [[ "$ENGINEER_ARGS" =~ (^|[[:space:]])--granularity[[:space:]]+([^[:space:]-][^[:space:]]*) ]]; then GRAN_PARAM="--granularity ${BASH_REMATCH[2]}"; fi
PRD_PARAM=""; if [[ "$ENGINEER_ARGS" =~ (^|[[:space:]])--prd[[:space:]]+([^[:space:]-][^[:space:]]*) ]]; then PRD_PARAM="--prd ${BASH_REMATCH[2]}"; fi
INGEST_PARAM=""; if [[ "$ENGINEER_ARGS" =~ (^|[[:space:]])--ingest[[:space:]]+([^[:space:]-][^[:space:]]*) ]]; then INGEST_PARAM="--ingest ${BASH_REMATCH[2]}"; fi
RESEARCH_PHASE_PARAM=""; if [[ "$ENGINEER_ARGS" =~ (^|[[:space:]])--research-phase[[:space:]]+([^[:space:]-][^[:space:]]*) ]]; then RESEARCH_PHASE_PARAM="--research-phase ${BASH_REMATCH[2]}"; fi
REVIEWS_PARAM=""; if [[ "$ENGINEER_ARGS" =~ (^|[[:space:]])--reviews([[:space:]]|$) ]]; then REVIEWS_PARAM="--reviews"; fi
# Project the just-completed planning mode onto the execute-phase follow-up:
# a --gaps run creates gap_closure plans, so the Next Up handoff must point at
# execute-phase's matching --gaps-only scope rather than the whole-phase run.
# Standard and --reviews runs leave GAPS_EXEC_FLAG empty → their Next Up is unchanged.
GAPS_MODE=false
if [[ "$ENGINEER_ARGS" =~ (^|[[:space:]])--gaps([[:space:]]|$) ]]; then GAPS_MODE=true; fi
GAPS_EXEC_FLAG=""
if [ "$GAPS_MODE" = "true" ]; then GAPS_EXEC_FLAG="--gaps-only"; fi
ENGINEER_WS=$(echo " $ENGINEER_ARGS" | sed -nE 's/.* --ws +([A-Za-z0-9][A-Za-z0-9._-]*).*/--ws \1/p' | head -n 1)
INIT=$(engineer_run query init.plan-phase ${ENGINEER_WS:+--ws=${ENGINEER_WS##* }} "$PHASE" $GRAN_PARAM $PRD_PARAM $INGEST_PARAM $RESEARCH_PHASE_PARAM $REVIEWS_PARAM)
if [[ "$INIT" == @file:* ]]; then INIT=$(cat "${INIT#@file:}"); fi
AGENT_SKILLS_RESEARCHER=$(engineer_run query agent-skills phase-researcher ${ENGINEER_WS:+--ws=${ENGINEER_WS##* }})
AGENT_SKILLS_PLANNER=$(engineer_run query agent-skills planner ${ENGINEER_WS:+--ws=${ENGINEER_WS##* }})
AGENT_SKILLS_CHECKER=$(engineer_run query agent-skills plan-checker ${ENGINEER_WS:+--ws=${ENGINEER_WS##* }})
CONTEXT_WINDOW=$(engineer_run query config-get context_window --raw 2>/dev/null || echo "200000")
```

When the tdd capability's `workflow.tdd_mode` is active (resolved via the plan:pre render-hooks), the planner agent is instructed to apply `type: tdd` to eligible tasks using heuristics from `engineer/references/tdd.md`. The TDD guidance is injected via the tdd capability's contribution hook at §5.6; no inline config-get is needed.

When `CONTEXT_WINDOW >= 500000`, the planner prompt includes the 3 most recent prior-phase CONTEXT.md/SUMMARY.md files plus any phases in the current phase's `Depends on:` field (explicit deps load regardless of recency).

** — `prior_verify_commands` is NOT part of that enrichment and is never gated on `CONTEXT_WINDOW`.** It is a handful of one-line `<automated>` commands harvested from the nearest prior phase that had any; the payload is tiny and its absence at 200k is exactly what made the planner re-invent a verify command and author an unrunnable path. Surface it at every context window.

Parse JSON for: `researcher_model`, `planner_model`, `checker_model`, `research_enabled`, `plan_checker_enabled`, `nyquist_validation_enabled`, `commit_docs`, `text_mode`, `phase_found`, `phase_dir`, `phase_number`, `phase_name`, `phase_slug`, `padded_phase`, `has_research`, `has_context`, `has_reviews`, `has_plans`, `plan_count`, `phase_status`, `planning_exists`, `roadmap_exists`, `phase_req_ids`, `response_language`, `granularity`, `prior_verify_commands` (array of `{phase, plan, task, command}`, possibly empty; emitted at every context window), `threat_id_duplicates` + `threat_id_duplicate_count` (cross-plan threat-ID collisions; consumed at step 5.55).

Omit the `model=` param from an `Agent()` call when its `researcher`/`planner`/`checker`_model is `"inherit"` or empty — passing `model=""` 404s on non-Claude runtimes; omitting inherits the orchestrator model (mirrors execute-phase).

**If `response_language` is set:** All user-facing orchestrator output — narration between tool calls, status updates, progress notes, findings, questions, prompts, and explanations — MUST be in `{response_language}`; technical terms, code, paths, and subagent prompts stay in English. Pass `response_language: {value}` into every spawned subagent prompt.

**File paths (for <required_reading> blocks):** `state_path`, `roadmap_path`, `requirements_path`, `context_path`, `research_path`, `verification_path`, `uat_path`, `reviews_path`. These are null if files don't exist.

**If `planning_exists` is false:** Error — run `/new-project` first.

## 1.5. Closed-Phase Gate 

Read and execute `engineer/workflows/plan-phase/steps/closed-phase-gate.md` — it parses `phase_status` from the init JSON, sets `FORCE_REPLAN` from `$ARGUMENTS`, and hard-stops replanning a `Complete` phase: `--reviews` on a closed phase is never overridable (exit 1), and replanning otherwise requires `--force` (else exit 1, pointing at `${verification_path}`); under `--force` it continues but emits a WARNING banner. Only `Complete` is gated — `Executed` / `Needs Review` are legitimate replans.

## 2. Parse and Normalize Arguments

Extract from $ARGUMENTS: phase number (integer or decimal like `2.1`), flags (`--research`, `--skip-research`, `--research-phase <N>`, `--gaps`, `--skip-verify`, `--skip-ui`, `--prd <filepath>`, `--ingest <path-or-glob>`, `--ingest-format <auto|nygard|madr|narrative>`, `--reviews`, `--text`, `--bounce`, `--skip-bounce`, `--no-reversibility-gates`, `--tdd`, `--granularity <coarse|standard|fine>`, `--force` (override closed-phase gate, see §1.5)).

**`--research-phase <N>` — research-only mode.** When this flag is present, parse `<N>` as the phase number (overrides any positional phase argument), set `RESEARCH_ONLY=true`, and treat the rest of this workflow as a research-dispatch only — the planner spawn (step 8), plan-checker, verification, gaps, bounce, and post-planning-gaps blocks all skip on `RESEARCH_ONLY`. Use this for cross-phase research, doc review before committing to a planning approach, and correction-without-replanning loops. Replaces the deleted `/research-phase` command.

In research-only mode, two modifiers control behavior when `RESEARCH.md` already exists:

- **`--research`** — force-refresh re-research without prompting. Re-spawns the researcher unconditionally and overwrites the existing RESEARCH.md. (This is the existing `--research` flag's standard "force re-research" semantics, reused here.)
- **`--view`** — view-only: print existing `RESEARCH.md` to stdout, do **not** spawn the researcher. Sets `VIEW_ONLY=true`. Cheapest mode for the correction-without-replanning loop. If `RESEARCH.md` does not exist, error with a hint to drop `--view`.

```bash
IFS= read -rd '' ENGINEER_ARGS <<'ENGINEER_ARGS_END' || true
$ARGUMENTS
ENGINEER_ARGS_END
ENGINEER_ARGS=${ENGINEER_ARGS%$'\n'}
RESEARCH_ONLY=false
VIEW_ONLY=false
if [[ "$ENGINEER_ARGS" =~ --research-phase[[:space:]]+([0-9]+[A-Z]?(\.[0-9]+)*) ]]; then
  RESEARCH_ONLY=true
  PHASE="${BASH_REMATCH[1]}"
fi
if $RESEARCH_ONLY && [[ "$ENGINEER_ARGS" =~ (^|[[:space:]])--view([[:space:]]|$) ]]; then
  VIEW_ONLY=true
fi
```

**`--granularity <coarse|standard|fine>` — CLI override.** When present, this value is the resolved granularity passed to the planner — it wins over any per-phase `granularities.<type>` config, top-level `granularity` config, or project defaults. The init JSON always includes a `granularity` field reflecting the resolved value; read it from there. Invalid values (anything other than `coarse`, `standard`, `fine`) cause an error at the CLI boundary.

Set `TEXT_MODE=true` if `--text` is present in $ARGUMENTS OR `text_mode` from init JSON is `true`. When `TEXT_MODE` is active, replace every `AskUserQuestion` call with a plain-text numbered list and ask the user to type their choice number. This is required for Claude Code remote sessions (`/rc` mode) where TUI menus don't work through the Claude App.

```bash
IFS= read -rd '' ENGINEER_ARGS <<'ENGINEER_ARGS_END' || true
$ARGUMENTS
ENGINEER_ARGS_END
ENGINEER_ARGS=${ENGINEER_ARGS%$'\n'}
if [[ "$ENGINEER_ARGS" =~ (^|[[:space:]])--tdd([[:space:]]|$) ]]; then
  engineer_run query config-set workflow.tdd_mode true 2>/dev/null || true
fi
REVERSIBILITY_GATES=true
if [[ "$ENGINEER_ARGS" =~ (^|[[:space:]])--no-reversibility-gates([[:space:]]|$) ]]; then REVERSIBILITY_GATES=false; fi
```

**Baseline-discipline flags.** `REVERSIBILITY_GATES` defaults to `true`; it is not persisted per-phase or read from config.

Extract express-path args from $ARGUMENTS: `PRD_FILE` (`--prd <filepath>`), `INGEST_PATH` (`--ingest <path-or-glob>`), and optional `INGEST_FORMAT` (`--ingest-format <auto|nygard|madr|narrative>`, default `auto`).

`--prd` and `--ingest` are mutually exclusive. If both are present, error and exit:
`Invalid arguments: cannot combine \`--prd\` with \`--ingest\`.`

**If no phase number:** Auto-detect it — `query init.plan-phase` and `query roadmap.get-phase` require an explicit number, so this is an orchestrator step. Run `engineer_run query roadmap.analyze` and read `next_phase` (first phase with `disk_status` of `no_directory`, `empty`, `discussed`, or `researched`). If `next_phase` is `null`, read ROADMAP.md's `### Phase N:` headers and ask the user which phase to plan. Set `PHASE` to the result before step 1's `query init.plan-phase "$PHASE"` call.

**If `phase_found` is false:** Validate phase exists in ROADMAP.md. If valid, create the directory using `expected_phase_dir` from init (includes `project_code` prefix when set):
```bash
mkdir -p "${expected_phase_dir}"
```

Set `phase_dir="${expected_phase_dir}"` after creation.

**Existing artifacts from init:** `has_research`, `has_plans`, `plan_count`.

<!-- engineer:section id="reviews-prerequisite" when="flag:--reviews" -->
If `section_manifest` is `null` or `"reviews-prerequisite"` is in its `included` list: read and execute `engineer/workflows/plan-phase/steps/reviews-prerequisite.md`. Otherwise skip — do not read the file.
<!-- /section -->

## 3. Validate Phase

```bash
PHASE_INFO=$(engineer_run query roadmap.get-phase "${PHASE}")
```

**If `found` is false:** Error with available phases. **If `found` is true:** Extract `phase_number`, `phase_name`, `goal` from JSON.

<!-- engineer:section id="prd-express-gate" when="flag:--prd" -->
If `section_manifest` is `null` or `"prd-express-gate"` is in its `included` list: read and execute `engineer/workflows/plan-phase/steps/prd-express-gate.md`. Otherwise skip — do not read the file.
<!-- /section -->

<!-- engineer:section id="adr-ingest-express-path" when="flag:--ingest" -->
If `section_manifest` is `null` or `"adr-ingest-express-path"` is in its `included` list: read and execute `engineer/workflows/plan-phase/steps/adr-ingest-express-path.md`. Otherwise skip — do not read the file.
<!-- /section -->

## 4. Load CONTEXT.md

**Skip if:** PRD express path or ADR ingest express path was used (CONTEXT.md already created in step 3.5/3.6).

Check `context_path` from init JSON.

If `context_path` is not null, display: `Using phase context from: ${context_path}`

**If `context_path` is null (no CONTEXT.md exists):**

Read discuss mode for context gate label:
```bash
DISCUSS_MODE=$(engineer_run query config-get workflow.discuss_mode --raw 2>/dev/null || echo "discuss")
```

If `TEXT_MODE` is true, present as a plain-text numbered list:
```
No CONTEXT.md found for Phase {X}. Plans will use research and requirements only — your design preferences won't be included.

1. Continue without context — Plan using research + requirements only
[If DISCUSS_MODE is "assumptions":]
2. Gather context (assumptions mode) — Analyze codebase and surface assumptions before planning
[If DISCUSS_MODE is "discuss" or unset:]
2. Run discuss-phase first — Capture design decisions before planning

Enter number:
```

Otherwise use AskUserQuestion:
- header: "No context"
- question: "No CONTEXT.md found for Phase {X}. Plans will use research and requirements only — your design preferences won't be included. Continue or capture context first?"
- options:
  - "Continue without context" — Plan using research + requirements only
  If `DISCUSS_MODE` is `"assumptions"`:
  - "Gather context (assumptions mode)" — Analyze codebase and surface assumptions before planning
  If `DISCUSS_MODE` is `"discuss"` (or unset):
  - "Run discuss-phase first" — Capture design decisions before planning

If "Continue without context": Proceed to step 5.
If "Run discuss-phase first":
  **IMPORTANT:** Do NOT invoke discuss-phase as a nested Skill/Task call — AskUserQuestion
  does not work correctly in nested subcontexts. Instead, display the command
  and exit so the user runs it as a top-level command:
  ```
  Run this command first, then re-run /plan-phase {X} ${ENGINEER_WS}:

  /discuss-phase {X} ${ENGINEER_WS}
  ```
  **Exit the plan-phase workflow. Do not continue.**

## 4.6. Context Drift Pre-Check (drift plan:pre gate)

Capability-driven dispatch, same lazy-init pattern already used elsewhere in this file for
`PLAN_PRE_HOOKS_JSON`:

```bash
if [ -z "${PLAN_PRE_HOOKS_JSON:-}" ]; then
  PLAN_PRE_HOOKS_JSON=$(engineer_run loop render-hooks plan:pre --raw)
fi
```

If `activeHooks` (from `PLAN_PRE_HOOKS_JSON`) has a `kind == "gate"`, `capId == "drift"`,
`check.query == "verify.context-drift"` entry (`workflow.context_drift_precheck` on), run the
check before either the research-reuse decision (§5.1) or the pattern-mapper reuse decision
(§7.8) can fire — both would otherwise silently reuse a stale artifact with zero signal.
Otherwise skip to §5.

```bash
DRIFT=$(engineer_run verify context-drift "${PHASE}" 2>/dev/null) || { echo "Warning: context-drift check could not look (exit $?)" >&2; DRIFT='{"skipped":true}'; }
```

If `skipped` is true, continue silently to §5 — nothing to compare (no CONTEXT.md yet, no
upstream artifacts yet). A non-zero exit (`69` `UNAVAILABLE`,: the phase directory did not
resolve or an artifact could not be read) is a check that could not look, not "nothing to compare":
the warning above is its signal, and planning continues (the check is advisory).

If `stale_artifacts` is a non-empty array, print `message` verbatim (it names each stale
artifact and the command to regenerate it). Then:

- If `DRIFT.block` is `false` (the default, `workflow.context_drift_action: warn`): continue to
  §5 — this is advisory only, exactly like the codebase-drift pre-check at §5.65.
- If `DRIFT.block` is `true` (opt-in `workflow.context_drift_action: block`): **exit the
  plan-phase workflow** rather than continuing. Do not spawn the researcher, the planner, or the
  pattern mapper against a premise the user has not yet reconciled. Point the user at re-running
  `/plan-phase {X}` once the named artifacts are regenerated, or at disabling the check with
  `engineer_run query config-set workflow.context_drift_action warn` if the flag was a false positive.

If `stale_artifacts` is empty, continue silently to §5 — nothing to report.

## 5. Handle Research

**Skip if:** `--gaps` flag or `--skip-research` flag or `--reviews` flag.

<!-- engineer:section id="research-only-modifiers" when="flag:--research-phase" -->
If `section_manifest` is `null` or `"research-only-modifiers"` is in its `included` list: read and execute `engineer/workflows/plan-phase/steps/research-only-modifiers.md`. Otherwise skip — do not read the file.
<!-- /section -->

### 5.1. Standard Research Decision

**Skip if** `RESEARCH_ONLY=true` (the research-only mode in 5.0 already determined the path: spawn or exit). Without this guard, an LLM following the workflow could fall through into "use existing, skip to step 6" → planner spawn, violating the research-only contract. **CR finding: this gate makes the early-exit unreachable from any non-research-only branch.**

**If `has_research` is true (from init) AND no `--research` flag:** Use existing, skip to step 6.

**If RESEARCH.md missing OR `--research` flag:**

**If no explicit flag (`--research` or `--skip-research`) and not `--auto`:**
Ask the user whether to research, with a contextual recommendation based on the phase:

If `TEXT_MODE` is true, present as a plain-text numbered list:
```
Research before planning Phase {X}: {phase_name}?

1. Research first (Recommended) — Investigate domain, patterns, and dependencies before planning. Best for new features, unfamiliar integrations, or architectural changes.
2. Skip research — Plan directly from context and requirements. Best for bug fixes, simple refactors, or well-understood tasks.

Enter number:
```

Otherwise use AskUserQuestion:
```
AskUserQuestion([
  {
    question: "Research before planning Phase {X}: {phase_name}?",
    header: "Research",
    multiSelect: false,
    options: [
      { label: "Research first (Recommended)", description: "Investigate domain, patterns, and dependencies before planning. Best for new features, unfamiliar integrations, or architectural changes." },
      { label: "Skip research", description: "Plan directly from context and requirements. Best for bug fixes, simple refactors, or well-understood tasks." }
    ]
  }
])
```

If user selects "Skip research": skip to step 6.

**If `--auto` and `research_enabled` is false:** Skip research silently (preserves automated behavior).

Display banner:
```
### Engineer ► RESEARCHING PHASE {X}

◆ Spawning researcher... (runs in a subagent — no output until it returns, ~1–5 min; expected, not a freeze)
```

### Spawn phase-researcher

```bash
if engineer_run query teams-status --active >/dev/null 2>&1; then
  echo "⚠️  CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS detected. Engineer's multi-agent orchestration is not validated under claude-code agent-teams and may stall (a subagent's completion can fail to route to the orchestrator). Recommend disabling agent-teams for Engineer workflows." >&2
fi
```

```bash
PHASE_DESC=$(engineer_run query roadmap.get-phase "${PHASE}" --pick section)
if [ -z "${PLAN_PRE_HOOKS_JSON:-}" ]; then
  PLAN_PRE_HOOKS_JSON=$(engineer_run loop render-hooks plan:pre --raw)
fi
```

Find the active `research` step hook in `PLAN_PRE_HOOKS_JSON`. Use the hook's `fragment.inline` as the prompt template and substitute the phase fields below before spawning its declared `ref.agent`.

```markdown
{research_hook.fragment.inline}
```

```
Agent(
  prompt=filled_research_hook_fragment,
  subagent_type=research_hook.ref.agent,
  model="{researcher_model}",
  description="Research Phase {phase}"
)
```

<!-- engineer:protected -->
> **ORCHESTRATOR RULE — ALL RUNTIMES**: After calling Agent() above, stop working on this task immediately. Do not read more files, edit code, or run tests related to this task while the subagent is active. Wait for the subagent to return its result. This prevents duplicate work, conflicting edits, and wasted context. Only resume when the subagent result is available. Never call `ScheduleWakeup` or any host wake/sleep-scheduling tool to literalize this wait — the Agent() call returns on its own; a partial-args wake call surfaces a red validation error.

### Handle Researcher Return

- **`## RESEARCH COMPLETE`:** Display confirmation, continue to step 6
- **`## RESEARCH BLOCKED`:** Display blocker, offer: 1) Provide context, 2) Skip research, 3) Abort

<!-- engineer:section id="research-only-early-exit" when="flag:--research-phase" -->
If `section_manifest` is `null` or `"research-only-early-exit"` is in its `included` list: read and execute `engineer/workflows/plan-phase/steps/research-only-early-exit.md`. Otherwise skip — do not read the file.
<!-- /section -->

## 5.5. Create Validation Strategy

Skip if `nyquist_validation_enabled` is false OR `research_enabled` is false.

If `research_enabled` is false and `nyquist_validation_enabled` is true: warn "Nyquist validation enabled but research disabled — VALIDATION.md cannot be created without RESEARCH.md. Plans will lack validation requirements (Dimension 8)." Continue to step 6.

**But Nyquist is not applicable for this run** when all of the following are true:
- `research_enabled` is false
- `has_research` is false
- no `--research` flag was provided

In that case: **skip validation-strategy creation entirely**. Do **not** expect `RESEARCH.md` or `VALIDATION.md` for this run, and continue to Step 6.

```bash
grep -l "## Validation Architecture" "${PHASE_DIR}"/*-RESEARCH.md 2>/dev/null || true
```

**If found:**
1. Read template: `engineer/templates/VALIDATION.md`
2. Write to `${PHASE_DIR}/${PADDED_PHASE}-VALIDATION.md` (use Write tool)
3. Fill frontmatter: `{N}` → phase number, `{phase-slug}` → slug, `{date}` → current date
4. Verify:
```bash
test -f "${PHASE_DIR}/${PADDED_PHASE}-VALIDATION.md" && echo "VALIDATION_CREATED=true" || echo "VALIDATION_CREATED=false"
```
5. If `VALIDATION_CREATED=false`: STOP — do not proceed to Step 6
6. If `commit_docs`: `commit "docs(phase-${PHASE}): add validation strategy"`

**If not found:** Warn and continue — plans may fail Dimension 8.

## 5.55. Security Threat Model Gate

> Capability-driven dispatch. Resolves active `plan:pre` hooks via the capability registry; the security hook's `when` condition is evaluated by the registry.

```bash
PLAN_PRE_HOOKS_JSON=$(engineer_run loop render-hooks plan:pre --raw)
```

**Contribution dispatch:** inject every `kind == "contribution"` fragment from `PLAN_PRE_HOOKS_JSON` per @~/.claude/engineer/references/loop-hook-dispatch.md, in array order, into the role each entry's `into` names — planner-targeted ones land in the prompt block below, orchestrator-targeted ones in your working context. The security specialization below is one such contribution, not a replacement for the generic dispatch.

Resolve active contribution hooks from `PLAN_PRE_HOOKS_JSON` where `kind == "contribution"` and `capId == "security"`.

**Threat-ID uniqueness (applies whether or not the security hook is active):** if the init payload's `threat_id_duplicate_count` is non-zero, init reports `threat_id_duplicates` — each `T-{phase}-NN` ID claimed by more than one live PLAN file in this phase. Surface the list to the planner spawn prompt in step 8 — "these threat IDs are already claimed by earlier plans in this phase: {list}; number new registers continuing after the phase's highest in-use `T-{phase}-NN`". Regardless of the count, include the numbering rule in the planner spawn prompt whenever this phase already has PLAN files: threat IDs are unique within a phase, and new registers continue after the highest in-use `T-{phase}-NN` — the count only reports an EXISTING collision, it cannot prevent the first one. The reserved `T-{phase}-SC` row is never listed. execute-phase hard-stops on a non-empty list regardless of what happened here.

**If no active security contribution hook exists:** Skip to step 5.6.

If an active security contribution hook exists, read `SECURITY_ASVS` from the hook's `configValues.security_asvs_level` (default: `1`) and `SECURITY_BLOCK` from `configValues.security_block_on` (default: `"high"`). These values are resolved by the capability registry from user config using the same four-level precedence as hook activation — no inline `config-get` is needed.

Display banner:

```
### Engineer ► SECURITY THREAT MODEL REQUIRED (ASVS L{SECURITY_ASVS})

Each PLAN.md must include a <threat_model> block.
Block on: {SECURITY_BLOCK} severity threats.
Opt out: set security_enforcement: false in .planning/config.json
```

Continue to step 5.6. Security config is passed to the planner in step 8.

## 5.6. Plan:Pre Capability Dispatch and UI Design Contract Gate

> Capability-driven dispatch. Resolves active `plan:pre` hooks via the capability registry; each hook's `when` condition is evaluated by the registry — no inline config-get needed. This section handles skill-based planning preflights such as `ai-integration`, agent-backed hooks through `ref.agent`, and the UI gate whose deterministic check comes from `check.query`.
>
> **Config semantics (cutover fix):** `workflow.ui_phase` gates UI-SPEC *generation* (step); `workflow.ui_safety_gate` gates the *planning block* (gate). Both-on = identical to OLD §5.6. Intended change: `{ui_phase:true, ui_safety_gate:false}` now auto-generates in pipelines but does NOT block manual planning (each key controls exactly what its description says).

```bash
PLAN_PRE_HOOKS_JSON=${PLAN_PRE_HOOKS_JSON:-$(engineer_run loop render-hooks plan:pre --raw)}
HOOKS_JSON="$PLAN_PRE_HOOKS_JSON"
```

Read the `activeHooks` array directly from `PLAN_PRE_HOOKS_JSON` / `HOOKS_JSON` (in-context — do NOT invoke a shell pipeline).

**Branch 1 — all plan:pre hooks inactive (`activeHooks` is empty or absent):** Skip to step 6.

**Generic step hook dispatch contract:** For each active entry where `kind == "step"`:
- If `ref.skill` is set, dispatch with `Skill(skill="${ref.skill}", args="${PHASE} --auto ${ENGINEER_WS}")` when pipeline mode allows auto-chaining. Use `ref.skill` directly — `ui-phase` → `ui-phase`.
- If `ref.agent` is set, dispatch with `Agent(prompt=filled_hook_fragment, subagent_type=ref.agent, model="{researcher_model}")`. Use the hook's `fragment.inline` as the prompt body and fill phase fields before spawning.
- The `research` hook is handled by §5.1's research decision. The `pattern-mapper` hook is handled by §7.8 after `RESEARCH_PATH` is known. Future plan:pre agent hooks use the same `ref.agent` fragment contract.

Run the UI deterministic gate whenever **any** `plan:pre` UI hook is active — including the step-only case (`workflow.ui_safety_gate` off). (`check.query` = `"ui.plan-gate"`, dot-normalized to `ui-plan-gate` per `loop-hook-dispatch.md` § `gate`.)

```bash
GATE=$(engineer_run check ui-plan-gate "${PHASE}" --raw) && GATE_EXIT=0 || GATE_EXIT=$?
```

A non-zero `GATE_EXIT` is a command failure, including `69` (`UNAVAILABLE`: the gate could not read its evidence, so its `frontend: false` is not an answer): surface it and stop; never fall through to Branch 2. Otherwise read `frontend`, `hasUiSpec`, and `block` from `GATE`.

**Branch 2 — no frontend indicators (`frontend` is `false`):** Skip silently to step 6.

**Branch 3 — UI-SPEC already exists (`hasUiSpec` is `true`):**

```bash
UI_SPEC_FILE=$(ls "${PHASE_DIR}"/*-UI-SPEC.md 2>/dev/null | head -1)
UI_SPEC_PATH="${UI_SPEC_FILE}"
```

Display: `Using UI design contract: ${UI_SPEC_PATH}`. Continue to step 6.

**Branch 4 — `--skip-ui` in `$ARGUMENTS`:** Skip silently to step 6.

**Branches 5 & 6 — frontend detected, UI-SPEC missing, no `--skip-ui`.**

Read the ephemeral auto-chain flag:

```bash
AUTO_CHAIN=$(engineer_run query check auto-mode --pick auto_chain_active 2>/dev/null)
AUTO_CHAIN="${AUTO_CHAIN:-false}"
```

**Branch 5 — `AUTO_CHAIN` is `true` (pipeline / `--auto`):** Fire each active UI **step** hook — runs independently of whether a gate is active (covers `{ui_phase:true,ui_safety_gate:false}`). For each entry in `activeHooks` (in array order) where `kind == "step"` and `ref.skill` is set:

```
Skill(skill="${ref.skill}", args="${PHASE} --auto ${ENGINEER_WS}")
```

After all UI step hooks return, re-read:

```bash
UI_SPEC_FILE=$(ls "${PHASE_DIR}"/*-UI-SPEC.md 2>/dev/null | head -1)
UI_SPEC_PATH="${UI_SPEC_FILE}"
```

Continue to step 6.

**Branch 6 — `AUTO_CHAIN` is `false` (manual): generic gate handling.** For each entry in `activeHooks` where `kind == "gate"` and `blocking` is `true`: if `block:true` (from `GATE`), output the block below and **EXIT the plan-phase workflow**. If no active blocking gate (e.g. `workflow.ui_safety_gate` is off), continue to step 6 — no block.

Output this markdown directly (not as a code block):

```
## ⚠ UI-SPEC.md missing for Phase {N}
▶ Recommended next step:
`/ui-phase {N} ${ENGINEER_WS}` — generate UI design contract before planning

---
Also available:
- `/plan-phase {N} --skip-ui ${ENGINEER_WS}` — plan without UI-SPEC (not recommended for frontend phases)
```

**Exit the plan-phase workflow. Do not continue.**

## 5.65. Codebase Map Freshness Pre-Check (drift plan:pre gate)

If `activeHooks` (from `PLAN_PRE_HOOKS_JSON`, §5.6) has a `kind == "gate"`, `capId == "drift"`,
`check.query == "verify.codebase-drift"` entry (`workflow.plan_drift_precheck` on), run the same check the
execute gate uses; otherwise skip to step 6:

```bash
DRIFT=$(engineer_run verify codebase-drift 2>/dev/null) || { echo "Warning: codebase-drift check could not look (exit $?)" >&2; DRIFT='{"skipped":true}'; }
```

This gate is **non-blocking** and **never blocks, never spawns** the mapper at plan time. If `skipped` or
`action_required` is false, continue silently to step 6. If `action_required` is true, print `message`
verbatim (it ends with a `/map-codebase` pointer) and continue — planning proceeds whether or not the
map is refreshed first. (`drift_action: auto-remap` stays at `execute:wave:post`.)

## 6. Check Existing Plans

```bash
ls "${PHASE_DIR}"/*-PLAN.md 2>/dev/null || true
```

**If exists AND no `--reviews` flag:** Offer: 1) Add more plans, 2) View existing, 3) Replan from scratch.

## 7. Use Context Paths from INIT

Extract from INIT JSON:

```bash
_engineer_field() { engineer_run query json.get --payload "$1" --field "$2" --raw; }
STATE_PATH=$(_engineer_field "$INIT" state_path)
ROADMAP_PATH=$(_engineer_field "$INIT" roadmap_path)
REQUIREMENTS_PATH=$(_engineer_field "$INIT" requirements_path)
RESEARCH_PATH=$(_engineer_field "$INIT" research_path)
VERIFICATION_PATH=$(_engineer_field "$INIT" verification_path)
UAT_PATH=$(_engineer_field "$INIT" uat_path)
CONTEXT_PATH=$(_engineer_field "$INIT" context_path)
REVIEWS_PATH=$(_engineer_field "$INIT" reviews_path)
PATTERNS_PATH=$(_engineer_field "$INIT" patterns_path)

# Resolve the phase SPEC (carries the ## Edge Coverage section the planner lifts resolved
# edges from). UNCONDITIONAL — must NOT live in §4.5 Check AI-SPEC, which is skipped
# on non-AI phases; gating it there silently starves the planner of the SPEC ( review).
# init resolves the plain phase SPEC (never the -UI-SPEC.md variants) through the one shared predicate.
PHASE_DIR_FOR_SPEC=$(_engineer_field "$INIT" phase_dir)
SPEC_PATH=$(_engineer_field "$INIT" spec_path)
SPEC_FILE="${SPEC_PATH}"
# Resolve the phase UI-SPEC separately (the glob above excludes -UI-SPEC.md); it carries the
# ## UI Considerations section the planner lifts by the same rule as ## Edge Coverage.
UI_SPEC_FILE=$(ls "${PHASE_DIR_FOR_SPEC}"/*-UI-SPEC.md 2>/dev/null | head -1)
UI_SPEC_PATH="${UI_SPEC_FILE}"
```

**If plans exist AND the `--reviews` flag is set:** Before replanning from `--reviews`, scan
`REVIEWS_PATH` for open plan-revision conflicts inside the writer-owned delimiter pair. Go
straight to replanning with those records included, and flip the matching line to `- [x]` once
the chosen resolution is applied, using the SAME close gate as step 12 below.

## 7.5. Verify Nyquist Artifacts

Skip if `nyquist_validation_enabled` is false OR `research_enabled` is false.

Also skip if all of the following are true:
- `research_enabled` is false
- `has_research` is false
- no `--research` flag was provided

In that no-research path, Nyquist artifacts are **not required** for this run.

```bash
VALIDATION_EXISTS=$(ls "${PHASE_DIR}"/*-VALIDATION.md 2>/dev/null | head -1)
```

If missing and Nyquist is still enabled/applicable — ask user:
1. Re-run: `/plan-phase {PHASE} --research ${ENGINEER_WS}`
2. Disable Nyquist with the exact command:
   `engineer_run query config-set workflow.nyquist_validation false`
3. Continue anyway (plans fail Dimension 8)

Proceed to Step 7.8 (or Step 8 if pattern mapper is disabled) only if user selects 2 or 3.

## 7.8. Spawn pattern-mapper Agent (Optional)

Pattern mapper activation is owned by the `pattern-mapper` capability's `plan:pre` step hook. Read `PLAN_PRE_HOOKS_JSON` and skip if no active step hook has `capId == "pattern-mapper"` and `ref.agent == "pattern-mapper"`. Also skip if no CONTEXT.md and no RESEARCH.md exist for this phase (nothing to extract file lists from).

**If PATTERNS.md already exists** (`PATTERNS_PATH` is non-empty from step 7): Skip to step 8 (use existing).

Display banner:
```
### Engineer ► PATTERN MAPPING PHASE {X}

◆ Spawning pattern mapper... (runs in a subagent — no output until it returns, ~1–5 min; expected, not a freeze)
```

Use the active `pattern-mapper` hook's `fragment.inline` as the prompt template and substitute the phase fields below before spawning its declared `ref.agent`.

```markdown
{pattern_mapper_hook.fragment.inline}
```

Spawn with:
```
Agent(
  prompt=filled_pattern_mapper_hook_fragment,
  subagent_type=pattern_mapper_hook.ref.agent,
  model="{researcher_model}",
)
```

<!-- engineer:protected -->
> **ORCHESTRATOR RULE — ALL RUNTIMES**: After calling Agent() above, stop working on this task immediately. Do not read more files, edit code, or run tests related to this task while the subagent is active. Wait for the subagent to return its result. This prevents duplicate work, conflicting edits, and wasted context. Only resume when the subagent result is available. Never call `ScheduleWakeup` or any host wake/sleep-scheduling tool to literalize this wait — the Agent() call returns on its own; a partial-args wake call surfaces a red validation error.

**Handle return:**
- **`## PATTERN MAPPING COMPLETE`:** Update `PATTERNS_PATH` to the created file path, continue to step 8.
- **Any error or empty return:** Log warning, continue to step 8 without patterns (non-blocking).

After pattern mapper completes, update the path variable:
```bash
PATTERNS_PATH="${PHASE_DIR}/${PADDED_PHASE}-PATTERNS.md"
```

## 7.9. Regenerate API-SURFACE.md (intel gate)

> Capability-driven dispatch. Resolves active `plan:pre` step hooks via the capability registry; the intel hook's `when: intel.enabled` condition is evaluated by the registry — no inline config-get needed.

Read the active intel step hook from `PLAN_PRE_HOOKS_JSON` where `kind == "step"` and `capId == "intel"`.

**If no active intel step hook exists:** `API_SURFACE_PATH` stays empty; skip to step 8. The step-8 planner entry for API Surface is omitted when `API_SURFACE_PATH` is empty.

**If an active intel step hook exists:**
```bash
engineer_run intel api-surface
API_SURFACE_PATH="$(dirname "$STATE_PATH")/intel/API-SURFACE.md"
echo "✓ API surface regenerated: ${API_SURFACE_PATH}"  # injected into step 8 as HINT
```

Continue to step 8.

## 7.95. Spec-less Probe Fallback (gate)

When the SPEC did not supply `## Edge Coverage` / `## Prohibitions`, plan-phase runs the probe protocol
and authors the predicates into PLAN.md `must_haves` (the *else branch* of the
`<downstream_consumer>` lift below). Core workflow-body substrate, not a capability rail. Runs
after `$SPEC_FILE` (Step 7), before the planner spawn (Step 8).

**Read and run** the gate + edge probe in `engineer/references/specless-probe-fallback.md`
(§0 default-ON toggle + per-section absence via the `spec-section` helper, visibly skipping when
disabled or no requirement IDs; §A deterministic edge probe → `$COVERAGE` when `EDGE_ABSENT`; §B
prohibition recall in the planner). Pass `$COVERAGE` and `$SPECLESS_FALLBACK_DISABLED` into Step 8.

## 7.99. Bounded Stall-Detection Helpers 

Read+execute `engineer/workflows/plan-phase/steps/stall-detection-helpers.md` (defines
`engineer_stall_should_recover`/`engineer_stall_watch`, and how `{outputFile}` below is bound;
independent of the teams-status guard above, AC2).

## 8. Spawn planner Agent

Display banner:
```
### Engineer ► PLANNING PHASE {X}

◆ Spawning planner... (runs in a subagent — no output until it returns, ~1–5 min; expected, not a freeze)
```

Planner prompt:

```markdown
<planning_context>
**Phase:** {phase_number}
**Mode:** {standard | gap_closure | reviews}

<required_reading>
- {state_path} (Project State)
- {roadmap_path} (Roadmap)
- {requirements_path} (Requirements)
- {context_path} (USER DECISIONS from /discuss-phase)
- {research_path} (Technical Research)
- {PATTERNS_PATH} (Pattern Map — analog files and code excerpts, if exists)
- {verification_path} (Verification Gaps - if --gaps)
- {uat_path} (UAT Gaps - if --gaps)
- {reviews_path} (Cross-AI Review Feedback - if --reviews; actionable findings must be incorporated or explicitly deferred/rejected in PLAN.md)
- {UI_SPEC_PATH} (UI Design Contract — visual/interaction specs, if exists)
- {SPEC_PATH} (Phase SPEC — carries the ## Edge Coverage section to lift resolved edges from, if exists)
- {API_SURFACE_PATH} (API Surface — HINT ONLY, when intel capability is active; see <intel_surface_hint> below)
${CONTEXT_WINDOW >= 500000 ? `
**Cross-phase context (1M model enrichment):**
- CONTEXT.md files from the 3 most recent completed phases (locked decisions — maintain consistency)
- SUMMARY.md files from the 3 most recent completed phases (what was built — reuse patterns, avoid duplication)
- LEARNINGS.md files from the 3 most recent completed phases (structured decisions, patterns, lessons, surprises — skip silently if a phase has no LEARNINGS.md; prefix each block with \`[from Phase N LEARNINGS]\` for source attribution; if total size exceeds 15% of context budget, drop oldest first)
- CONTEXT.md, SUMMARY.md, and LEARNINGS.md from any phases listed in the current phase's "Depends on:" field in ROADMAP.md (regardless of recency — explicit dependencies always load, deduplicated against the 3 most recent)
- Skip all other prior phases to stay within context budget
` : ''}
</required_reading>
${prior_verify_commands.length > 0 ? `
<proven_verify_commands>
**Verify commands the previous phase actually ran  — reuse before re-deriving.** These
are the `<automated>` commands from the nearest prior phase that had any. They resolved from
the executor's cwd in a real run, so a path here is grounded evidence, not a guess. When this
phase's build/test story is the same, **copy the command verbatim**; do not re-derive a
directory. Surfaced at every context window — not part of the 1M enrichment above.

{For each entry in \`prior_verify_commands\`: \`- Phase {phase} · {task}: \\\`{command}\\\`\`}
</proven_verify_commands>
` : ''}
${API_SURFACE_PATH ? `
<intel_surface_hint>
**API Surface (HINT — may be incomplete):** When \`intel.enabled\` is true, \`${API_SURFACE_PATH}\` lists symbols extracted from the codebase by regex/JS analysis. Prefer symbols listed there when referencing existing code. This surface is regex/JS-derived and MAY BE INCOMPLETE — a symbol's absence means *unknown*, not *nonexistent*. Never treat the surface as exhaustive. If you reference a symbol that is not in the surface and this phase creates it, list it under "Artifacts this phase produces".
</intel_surface_hint>
` : ''}
${AGENT_SKILLS_PLANNER}

<review_incorporation_contract>
**If Mode is reviews:** REVIEWS.md is feedback input, not a hidden execution contract. /execute-phase primarily consumes PLAN.md plus the normal phase context, so every current actionable review finding must become visible in the relevant PLAN.md before planning can pass.

For each current actionable finding in REVIEWS.md, the planner MUST either:
- incorporate it into a PLAN.md task, `<action>`, `<acceptance_criteria>`, `<verify>`, `must_haves`, threat model, or artifact list; or
- explicitly document a deferral/rejection rationale in the relevant PLAN.md, using the Review Dispositions Ledger in `engineer/references/planner-reviews.md`.

Historical findings already incorporated, explicitly deferred/rejected in PLAN.md, or marked fully resolved do not require new plan changes.
</review_incorporation_contract>

**Phase requirement IDs (every ID MUST appear in a plan's `requirements` field):** {phase_req_ids}

<tracked_source_paths>
**Tracked-source paths :** Every path you write into PLAN.md —
`files_modified`, `must_haves.artifacts`, action paths, and paths inherited
from `{PATTERNS_PATH}` or prior-phase plans — must name git-tracked source,
never a gitignored build or install output (e.g. `dist/<module>.js`,
`build/generated/...`, `.venv/lib/python3.*/site-packages/<pkg>/...`; executor
edits to an output die on the next build or install). Verify existing-file
paths with `git ls-files -- <path>` (non-empty = tracked); resolve a gitignored
hit to the tracked source it is built or installed from (`src/<module>.ts`, the
generator's `.proto`/schema file, `src/<pkg>/...`). A not-yet-existing path is
a new file — keep the intended path. Re-verify inherited paths: fix an output
path, never inherit. Submodule files: check
from within the submodule.
</tracked_source_paths>

<!-- engineer:protected:start -->
<failing_direction_contract>
**Stated failing direction :** Every runnable `<automated>` verify command
you write MUST be followed by a `<fails_when>` sibling naming what output
constitutes failure — an exit code, a string in the output, a missing line. A
command with no expressible failure mode is not an acceptance test.

```xml
<verify>
  <automated>npm --prefix apps/api test -- auth.spec.ts</automated>
  <fails_when>non-zero exit, or "0 passed" in the summary line</fails_when>
</verify>
```

One statement per runnable command, placed immediately after it: within a task
each `<fails_when>` binds to the nearest preceding `<automated>`, and the first
statement after a command is the binding one. Name an OBSERVABLE signal, never
the word "failure" — `non-zero exit` is complete, `the command fails` is a
restatement. `TBD`/`TODO`/`N/A`/`none`/`unknown`/`?`/`-` are rejected outright as
whole values. The `MISSING — Wave 0 …` sentinel is exempt: it is not runnable, so
it has no failure mode to state. Ask yourself: if this command were silently
doing nothing, what in its output would tell me? If you cannot answer, fix the
command — do not invent a statement for it.
Rules + worked examples: @~/.claude/engineer/references/planner-failing-direction.md
</failing_direction_contract>
<!-- engineer:protected:end -->

**Project instructions:** Read ./CLAUDE.md or ./.claude/CLAUDE.md if either exists — follow project-specific guidelines
**Project skills:** Check .claude/skills/ or .agents/skills/ directory (if either exists) — read SKILL.md files, plans should account for project skill rules

{For each active entry in `PLAN_PRE_HOOKS_JSON` where `kind == "contribution"` and `into == "planner"` (in array order): inject the entry's `fragment.inline` verbatim here. This delivers all planner-targeted contributions — including tdd's `<tdd_mode_active>` block (type:tdd heuristics), schema-gate's schema-push detection guidance (if active at plan:pre), and security's threat-model guidance. For the security contribution, also surface the resolved `configValues`: `security_asvs_level` (ASVS enforcement level) and `security_block_on` (severity threshold) so the planner uses the configured values when generating `<threat_model>` blocks. If no active planner contributions exist, omit this block entirely.}

**REVERSIBILITY_GATES:** ${REVERSIBILITY_GATES} (false = rate but do not gate; see `planner-reversibility.md`.)
**Granularity:** {granularity}

<specless_probe_fallback>
**Spec-less probe fallback** (only when step 7.95 set `EDGE_ABSENT` and/or `PROHIB_ABSENT`). The SPEC
omitted that section — author its predicates into `must_haves` via the `<downstream_consumer>`
else-branch below, per §A/§B/§C of `engineer/references/specless-probe-fallback.md`
(descriptor-less prohibitions, never auto-dismiss, no silent drops).

Edge coverage report (`$COVERAGE`, present when `EDGE_ABSENT`):

```json
{COVERAGE}
```
${SPECLESS_FALLBACK_DISABLED ? `
**⚠ ${SPECLESS_FALLBACK_DISABLED}** — record this in the plan (a visible, recorded choice); do not generate probe predicates this run.
` : ''}

</planning_context>

<!-- engineer:protected:start -->
<downstream_consumer>
Output consumed by /execute-phase. Plans need:
- Frontmatter (wave, depends_on, files_modified, autonomous)
- Tasks in XML format with read_first and acceptance_criteria fields (MANDATORY on every task)
- Verification criteria
- must_haves for goal-backward verification
- If the SPEC has an `## Edge Coverage` section, lift every resolved (verification: explicit) edge's acceptance criterion into `must_haves.truths` as a plain string, and every resolved (verification: backstop) edge **as a structured flat-scalar marker** — an object item `{ statement: <the check>, verification: backstop }`, NOT a prose note (the verifier branches deterministically on the `verification: backstop` field; a parenthetical is unparseable — the  fragility). Use a flat scalar `verification:` continuation key, never a nested object. At verify time a `backstop` truth the verifier cannot confirm with explicit evidence abstains → `human_needed` (reason `insufficient_spec`), never a silent pass (see `engineer/references/honest-verifier.md`). `unresolved` edges are explicit assumptions — surface them in the plan, do not silently drop them. **Otherwise** (`EDGE_ABSENT`): apply the SAME lift to the fallback report `{COVERAGE}` (per §C of `engineer/references/specless-probe-fallback.md`); a SPEC-supplied section is never re-run.
- If the SPEC has a `## Prohibitions` section, lift every resolved prohibition into the `must_haves.prohibitions:` sibling block (NOT `truths`) with `statement`+`status`+`verification`, via the single `projectProhibitions` serializer (Hyrum — no second serializer); unresolved -> flagged assumptions, don't drop; never put a must-NOT under `truths`. **Otherwise** (`PROHIB_ABSENT`), author the recalled prohibitions into the SAME block via the SAME `projectProhibitions` contract but **descriptor-less** (no `check_*`) so each disposes flagged-unverified; never auto-dismiss. Section-level precedence + no-silent-drop equality apply (§C).
- If a `-UI-SPEC.md` exists (resolved above as `UI_SPEC_PATH`) with a `## UI Considerations` section, lift it by the **identical rule** as `## Edge Coverage` above — resolved (explicit) → `must_haves.truths` string, resolved (backstop) → flat scalar `{ statement, verification: backstop }`, `unresolved` → explicit planner assumption (no new verb). Read it from `UI_SPEC_PATH` (the SPEC glob excludes `-UI-SPEC.md`).
- **"Artifacts this phase produces" section (MANDATORY)** — list every symbol this phase creates: decorators, classes, functions, CLI flags, struct/dataclass fields, new file paths. The plan-review-convergence source-grounding pass reads this section to exclude newly-created symbols from drift verification; omitting it causes new symbols to be flagged for acknowledgement.
</downstream_consumer>
<!-- engineer:protected:end -->

<deep_work_rules>
## Anti-Shallow Execution Rules (MANDATORY)

Every task MUST include these fields — they are NOT optional:

1. **`<read_first>`** — Files the executor MUST read before touching anything. Always include:
   - The file being modified (so executor sees current state, not assumptions)
   - Any "source of truth" file referenced in CONTEXT.md (reference implementations, existing patterns, config files, schemas)
   - Any file whose patterns, signatures, types, or conventions must be replicated or respected

2. **`<acceptance_criteria>`** — Verifiable conditions that prove the task was done correctly. Rules:
   - Every criterion must be checkable as a source assertion, behavior assertion, test command, or CLI output
   - NEVER use subjective language ("looks correct", "properly configured", "consistent with")
   - Include exact strings, patterns, values, command outputs, or observable behavior where that is the right proof
   - Examples:
     - Code: `auth.py contains def verify_token(` / `test_auth.py exits 0`
     - Behavior: `POST /api/auth/login returns 200 + httpOnly JWT cookie for valid credentials`
     - Config: `.env.example contains DATABASE_URL=` / `Dockerfile contains HEALTHCHECK`
     - Docs: `README.md contains '## Installation'` / `API.md lists all endpoints`
     - Infra: `deploy.yml has rollback step` / `docker-compose.yml has healthcheck for db`

3. **`<action>`** — Must include CONCRETE values, not references. Rules:
   - NEVER say "align X with Y", "match X to Y", "update to be consistent" without specifying the exact target state
   - Include concrete identifiers and reference values: config keys, function signatures, SQL table names, class names, import paths, env vars, endpoint paths, etc.
   - If CONTEXT.md has a comparison table or expected values, copy only the target identifiers/values needed to remove ambiguity
   - Do not include full file contents, fenced code blocks, or complete implementations in `<action>`
   - The executor should understand the intended target state from `<action>` and use `<read_first>` files for current implementation details, patterns, and source-of-truth context

**Why this matters:** Executor agents work from the plan text. Vague instructions like "update the config to match production" produce shallow one-line changes. Concrete instructions like "add DATABASE_URL, set POOL_SIZE=20, add REDIS_URL, and read config/runtime.ts before editing" produce complete work without turning the planner into the executor.
</deep_work_rules>

<!-- engineer:protected:start -->
<quality_gate>
- [ ] PLAN.md files created in phase directory
- [ ] Each plan has valid frontmatter
- [ ] Tasks are specific and actionable
- [ ] Every task has `<read_first>` with at least the file being modified
- [ ] Every task has `<acceptance_criteria>` with behavior, test-command, CLI, or source assertions
- [ ] Every `<action>` contains concrete identifiers without fenced code blocks or full implementations
- [ ] Dependencies correctly identified
- [ ] Waves assigned for parallel execution
- [ ] must_haves derived from phase goal
- [ ] Every PLAN.md includes an "Artifacts this phase produces" section listing symbols created by this phase (decorators, classes, functions, CLI flags, struct/dataclass fields, new file paths)
- [ ] Every SPEC ## Edge Coverage resolved edge is represented in a plan's must_haves (no silent drops)
- [ ] Every UI-SPEC ## UI Considerations resolved consideration is represented in a plan's must_haves (no silent drops)
- [ ] Every SPEC ## Prohibitions resolved item is represented in a plan's must_haves.prohibitions (no silent drops)
</quality_gate>
<!-- engineer:protected:end -->
```

Spawn the planner as a single long-lived Agent:

**Dispatch/wait gate — `PLANNER_STALL_DETECTION_ENABLED` (config key `planner.stall_detection_enabled`, resolved in `plan-phase/steps/stall-detection-helpers.md`):**
- **`true` (default):** use `run_in_background=true` in the Agent() call shown below, then use `engineer_stall_watch` as specified after it.

```text
Agent(
  prompt=filled_prompt,
  subagent_type="planner",
  model="{planner_model}",
  description="Plan Phase {phase}",
  run_in_background=true
)
```

**ORCHESTRATOR RULE — ALL RUNTIMES (when `PLANNER_STALL_DETECTION_ENABLED` is `true`):** `TS=$(date +%s)`; repeat `PLANNER_STALL_RESULT=$(engineer_stall_watch "$TS" "{outputFile}" "${PHASE_DIR}"'/*-PLAN.md' "## PLANNING COMPLETE" "## PHASE SPLIT RECOMMENDED" "## ⚠ Source Audit" "## CHECKPOINT REACHED" "## PLANNING INCONCLUSIVE")` while waiting/active — `marker_received` -> step 9; `stalled` -> 9a.

- **`false`:** issue the same Agent() call but omit `run_in_background`; await its ordinary runtime-native completion and pass the real returned result to step 9. Skip `engineer_stall_watch` entirely. This is not fire-and-forget; empty, truncated, or unrecognized returns still use step 9a.

## 9. Handle Planner Return

- **`## PLANNING COMPLETE`:** Display plan count. If `--skip-verify` or `plan_checker_enabled` is false (from init): skip to step 13. Otherwise: step 10.
- **`## PHASE SPLIT RECOMMENDED`:** The planner determined the phase exceeds the context budget for full-fidelity implementation of all source items. Handle in step 9b.
- **`## ⚠ Source Audit: Unplanned Items Found`:** The planner's multi-source coverage audit found items from REQUIREMENTS.md, RESEARCH.md, ROADMAP goal, or CONTEXT.md decisions that are not covered by any plan. Handle in step 9c.
- **`## CHECKPOINT REACHED`:** Present to user, get response, spawn continuation (step 12)
- **`## PLANNING INCONCLUSIVE`:** Show attempts, offer: Add context / Retry / Manual
- **Empty / truncated / no recognized marker:** → Filesystem fallback (step 9a).

## 9a. Filesystem Fallback (Planner)

**Triggered when:** Agent() returns but the return contains no recognized marker (`## PLANNING COMPLETE`, `## PHASE SPLIT RECOMMENDED`, `## ⚠ Source Audit`, `## CHECKPOINT REACHED`, `## PLANNING INCONCLUSIVE`).

```bash
DISK_PLANS=$(engineer_run query find-phase "${PHASE_NUMBER}" | jq -r '.plan_count_all // 0')
```

If `DISK_PLANS` is greater than 0 (a known Windows stdio hang pattern — the planner wrote plans to disk but the return never arrived), offer: 1) Accept plans (treat as `## PLANNING COMPLETE`), 2) Retry planner (return to step 8), 3) Stop. If it is 0 and no marker, treat as `## PLANNING INCONCLUSIVE`. Full banner text: `engineer/workflows/plan-phase/detail/elaboration.md` § 9a.

## 9b. Handle Phase Split Recommendation

When the planner returns `## PHASE SPLIT RECOMMENDED`, the phase's source items exceed the context budget for full-fidelity implementation. Extract the planner's proposed sub-phase groupings and present the user three options via AskUserQuestion: Split into sub-phases (use `/phase --insert`, then replan each), Proceed anyway (return to planner accepting degraded quality), or Prioritize (AskUserQuestion multiSelect to choose now vs. later, create CONTEXT.md per sub-phase). Full banner text: `engineer/workflows/plan-phase/detail/elaboration.md` § 9b.

## 9c. Handle Source Audit Gaps

When the planner returns `## ⚠ Source Audit: Unplanned Items Found`, items from REQUIREMENTS.md, RESEARCH.md, ROADMAP goal, or CONTEXT.md decisions have no corresponding plan. Present each gap to the user with three options: Add a plan (return to planner, step 8), Split phase (`/phase --insert`, then replan), or Defer (record in CONTEXT.md `## Deferred Ideas` with developer confirmation, proceed to step 10). Full banner text: `engineer/workflows/plan-phase/detail/elaboration.md` § 9c.

## 10. Spawn plan-checker Agent

Display banner:
```
### Engineer ► VERIFYING PLANS

◆ Spawning plan checker... (runs in a subagent — no output until it returns, ~1–5 min; expected, not a freeze)
```

**Verify-command probes.** Before spawning, run both deterministic probes and
hand their JSON to the checker. The first resolves each `<automated>` command's target; the
second reports which runnable commands carry a `<fails_when>` statement naming their failure
signal. Neither executes command text, and neither prescribes a replacement — the first reports
which `<automated>` targets resolve, which do not, and which it refused to guess at; the second
reports which commands state a failure signal and never authors one. Handing both over is what
stops the checker hand-reasoning the filesystem or the plans.

```bash
VERIFY_PATHS=$(engineer_run check verify-command-paths "${PHASE}" --raw) && VERIFY_PATHS_EXIT=0 || VERIFY_PATHS_EXIT=$?
FAILING_DIRECTIONS=$(engineer_run check verify-failure-directions "${PHASE}" --raw) && FAILING_DIRECTIONS_EXIT=0 || FAILING_DIRECTIONS_EXIT=$?
```

Branch on each `*_EXIT`: `0` — the probe looked; use the JSON. `69` (`UNAVAILABLE`) — the
probe **could not look**: the JSON is still printed and carries `status: 'unresolvable'`, so hand it
to the checker unchanged, and never read it as "every path resolved". Any other non-zero is a command
failure: stop and surface it, and do not hand the checker an empty value.

Checker prompt:

```markdown
<verification_context>
**Phase:** {phase_number}
**Phase Goal:** {goal from ROADMAP}
**Mode:** {standard | gap_closure | reviews}

<required_reading>
- {PHASE_DIR}/*-PLAN.md (Plans to verify)
- {roadmap_path} (Roadmap)
- {requirements_path} (Requirements)
- {context_path} (USER DECISIONS from /discuss-phase)
- {research_path} (Technical Research — includes Validation Architecture)
- {reviews_path} (Cross-AI Review Feedback - if --reviews; verify actionable findings are represented in PLAN.md)
</required_reading>

${AGENT_SKILLS_CHECKER}

<verify_command_path_probe>
**Deterministic verify-command path probe ** — already run; do NOT re-derive these
verdicts by reading the filesystem yourself. Act on `severity` per the "Verify Command Path
Resolvability" dimension: `blocker` → BLOCKER, `warning` → WARNING, `none` → silent.
`status: pending_creation` is not a finding. A non-empty `readError` means the probe could not
look — a WARNING, not a pass. Report the failing target verbatim; never prescribe a
replacement path.

```json
{VERIFY_PATHS}
```
</verify_command_path_probe>

<failing_direction_probe>
**Deterministic failing-direction probe ** — already run; do NOT re-derive these verdicts
by re-reading the plans yourself. Act on `severity` per check 8f: `blocker` → BLOCKER,
`warning` → WARNING, `none` → silent. `status: sentinel` is a Wave-0 `MISSING` placeholder and is
not a finding. A non-empty `readError` means the probe could not look — a WARNING, not a pass.
Quote the command that has no stated failure mode; never author the statement for the planner.

```json
{FAILING_DIRECTIONS}
```
</failing_direction_probe>

<review_incorporation_verification>
**If Mode is reviews:** Read REVIEWS.md and verify each current actionable review finding is visible in executable PLAN.md content or explicitly deferred/rejected in the relevant PLAN.md. A finding remains actionable if it requires a concrete plan task, `<action>`, `<acceptance_criteria>`, `<verify>`, `must_haves`, threat-model item, stale-path correction, or execution contract change before /execute-phase runs.

If an actionable finding remains only in REVIEWS.md and would be invisible to /execute-phase, return `## ISSUES FOUND`. Use WARNING by default; use BLOCKER when the missing incorporation can prevent the phase goal, create unsafe execution, or invalidate verification.
</review_incorporation_verification>

**Phase requirement IDs (MUST ALL be covered):** {phase_req_ids}

**Project instructions:** Read ./CLAUDE.md or ./.claude/CLAUDE.md if either exists — verify plans honor project guidelines
**Project skills:** Check .claude/skills/ or .agents/skills/ directory (if either exists) — verify plans account for project skill rules
</verification_context>

<expected_output>
- ## VERIFICATION PASSED — all checks pass
- ## ISSUES FOUND — structured issue list
</expected_output>
```

```
Agent(
  prompt=checker_prompt,
  subagent_type="plan-checker",
  model="{checker_model}",
  description="Verify Phase {phase} plans",
  run_in_background=true
)
```

**Dispatch/wait gate — `PLANNER_STALL_DETECTION_ENABLED` (config key `planner.stall_detection_enabled`, resolved in `plan-phase/steps/stall-detection-helpers.md`):**
- **`true` (default):** use `run_in_background=true` in the Agent() call above, then use `engineer_stall_watch` below.

**ORCHESTRATOR RULE — ALL RUNTIMES (when `PLANNER_STALL_DETECTION_ENABLED` is `true`):** `TS=$(date +%s)`; repeat `CHECKER_STALL_RESULT=$(engineer_stall_watch "$TS" "{outputFile}" "${PHASE_DIR}"'/*-PLAN.md' "## VERIFICATION PASSED" "## ISSUES FOUND")` while waiting/active.

- **`false`:** issue the same Agent() call but omit `run_in_background`; await its ordinary runtime-native completion and pass the real returned result to step 11. Skip `engineer_stall_watch` entirely. Treat a recognized returned marker exactly like `marker_received`; empty, truncated, or unrecognized returns still use step 11a.

## 11. Handle Checker Return

- **`marker_received` + `## VERIFICATION PASSED`:** If the return lists an entry whose severity is BLOCKER or WARNING, in the YAML issues block or listed in prose (a mention such as "no warnings" or a zero count is not an entry), treat it as `## ISSUES FOUND` instead: display issues, check iteration count, proceed to step 12, which counts those prose entries as BLOCKER/WARNING entries (the no-YAML-block shortcut there does not apply). The sentinel never decides alone, and an entry with a missing or unrecognized severity counts as a BLOCKER. Otherwise display confirmation, proceed to step 13.
- **`marker_received` + `## ISSUES FOUND`:** Display issues, check iteration count, proceed to step 12.
- **`stalled`:** Automatically surface 11a's recovery choice (Accept verification / Retry checker / Stop) — no manual interrupt needed.
- **Empty / truncated / no recognized marker:** → Filesystem fallback (step 11a).

**Thinking partner for architectural tradeoffs (conditional):** If `features.thinking_partner` is enabled and the checker's issues contain architectural tradeoff keywords ("architecture", "approach", "strategy", "pattern", "vs", "alternative"), present a brief Option A/B analysis with a recommendation and ask "Apply this to the revision? [Yes] / [No, I'll decide]". If disabled, skip. Full prompt template: `engineer/workflows/plan-phase/detail/elaboration.md` § 11 thinking-partner.

## 11a. Filesystem Fallback (Checker)

**Triggered when:** Checker Agent() returns but the return contains neither `## VERIFICATION PASSED` nor `## ISSUES FOUND`.

```bash
DISK_PLANS=$(engineer_run query find-phase "${PHASE_NUMBER}" | jq -r '.plan_count_all // 0')
```

If `DISK_PLANS` is greater than 0 (plans exist on disk; a known Windows stdio hang pattern), offer: 1) Accept verification (treat as `## VERIFICATION PASSED`, continue to step 13), 2) Retry checker (return to step 10), 3) Stop. If it is 0, something is seriously wrong — display error and stop. Full banner text: `engineer/workflows/plan-phase/detail/elaboration.md` § 11a.

## 12. Revision Loop (Max 3 Iterations)

Track `iteration_count` (starts at 1 after initial plan + check).
Track `prev_issue_count` (initialized to `Infinity` before the loop begins).
Track `stall_reentry_count` (starts at 0; incremented each time "Adjust approach" re-enters step 8).

**If iteration_count < 3:**

Parse issue count from checker return: count BLOCKER + WARNING entries in the YAML issues block (structured output from plan-checker); an entry whose severity is missing or unrecognized counts as a BLOCKER (fail closed). Entries a `## VERIFICATION PASSED` return lists in prose count the same way. If the checker's return contains no YAML issues block and lists no BLOCKER or WARNING entry in prose (i.e., the plan was approved with no issues), treat `issue_count` as 0 and skip the stall check — the plan passed. Proceed to step 13 — likewise when every entry in the block is explicitly INFO (display them as advisories). Advisory format: `ℹ advisory — {dimension}: {description}` per INFO entry, listed once before the step-13 output.

Display (only when entering the revision loop — skip if the paragraph above already proceeded to step 13): `Revision iteration {N}/3 -- {blocker_count} blockers, {warning_count} warnings`

**Stall detection:** If `issue_count >= prev_issue_count`:
  Display: `Revision loop stalled — issue count not decreasing ({issue_count} issues remain after {N} iterations)`

  **If `stall_reentry_count < 2`:**
    Ask user:
      Question: "Issues remain after {N} revision attempts with no progress. Proceed with current output?"
      Options: "Proceed anyway" | "Adjust approach"
    If "Proceed anyway": accept current plans and continue to step 13.
    If "Adjust approach": increment `stall_reentry_count`, open freeform discussion, then re-enter step 8 (full replanning). Note: re-entry resets `iteration_count` and `prev_issue_count` but `stall_reentry_count` persists across re-entries and is capped at 2.

  **If `stall_reentry_count >= 2`:**
    Display: `Stall persists after 2 re-planning attempts. The following issues could not be resolved automatically:`
    List the remaining issues from the checker.
    Suggest: "Consider resolving these issues manually or running `/debug` to investigate root causes."
    Options: "Proceed anyway" | "Abandon"
    If "Proceed anyway": accept current plans and continue to step 13.
    If "Abandon": stop workflow.

Set `prev_issue_count = issue_count`.

Revision prompt:

```markdown
<revision_context>
**Phase:** {phase_number}
**Mode:** revision

<required_reading>
- {PHASE_DIR}/*-PLAN.md (Existing plans)
- {context_path} (USER DECISIONS from /discuss-phase)
</required_reading>

${AGENT_SKILLS_PLANNER}

**Checker issues:** {structured_issues_from_checker}
</revision_context>

<instructions>
`required_property` + evidence + severity BIND. `fix_hint` is ONE non-binding example route: a
smaller or different mechanism reaching the same property resolves it — say which. Re-check CONTEXT.md's locked decisions, capability guidance, and existing plan constraints
BEFORE editing; if a hint would contradict one, or the
property is unreachable without breaking one, return `## REVISION_CONFLICT` with the conflict and
the alternatives rather than applying or working around it. Full contract:
`engineer/references/planner-revision.md`.

Do NOT replan from scratch unless fundamental. Return what changed.
</instructions>
```

```
Agent(
  prompt=revision_prompt,
  subagent_type="planner",
  model="{planner_model}",
  description="Revise Phase {phase} plans",
  run_in_background=true
)
```

**Dispatch/wait gate — `PLANNER_STALL_DETECTION_ENABLED` (config key `planner.stall_detection_enabled`, resolved in `plan-phase/steps/stall-detection-helpers.md`):**
- **`true` (default):** use `run_in_background=true` in the Agent() call above, then use `engineer_stall_watch` below.

**ORCHESTRATOR RULE — ALL RUNTIMES (when `PLANNER_STALL_DETECTION_ENABLED` is `true`):** (7.99; no marker, mtimes only) `TS=$(date +%s)`; repeat `PLANNER_STALL_RESULT=$(engineer_stall_watch "$TS" "{outputFile}" "${PHASE_DIR}"'/*-PLAN.md')` while waiting/active — `stalled` -> 1) Accept as revised, to step 13, 2) Retry, 3) Stop.

- **`false`:** issue the same Agent() call but omit `run_in_background`; await its ordinary runtime-native completion and pass the real returned result into the existing revision-return handling. Skip `engineer_stall_watch` entirely; an empty, truncated, or unrecognized result keeps the existing filesystem fallback.

**If the planner returns `## REVISION_CONFLICT`:** follow the shared Conflict Return protocol in
`engineer/references/revision-loop.md`, with this workflow's bindings:

```bash
if ! CONVERGENCE_ENABLED=$(engineer_run query config-get workflow.plan_review_convergence --raw 2>/dev/null); then
  echo "BLOCKED: cannot read workflow.plan_review_convergence." >&2
  exit 1
fi
REVIEWS_FILE="${REVIEWS_PATH}"
if [ "${CONVERGENCE_ENABLED}" = "true" ] && [ -n "${REVIEWS_FILE}" ] && [ ! -f "${REVIEWS_FILE}" ]; then
  echo "BLOCKED: cannot persist plan-revision conflict -- REVIEWS_PATH not a regular file: ${REVIEWS_FILE}" >&2
  exit 1
fi
```

- Counter not spent: `iteration_count`.
- Record channel: `$REVIEWS_FILE`'s `## Plan-Revision Conflicts` section. plan-phase wrote the
  line, so plan-phase closes it.
- After re-spawning, return to this step, not the checker.
- Escalates via the iteration cap on repeated `required_property`, and on the THIRD conflict
  return of this loop whatever property it names.
- Sanitize-then-insert is real shell; fields reach `awk` via `ENVIRON`, never `-v` (decodes
  literal `\n` as a real newline). Export the row's
  `CONFLICT_DIMENSION/_PLAN/_PROPERTY/_CONSTRAINT/_ALTERNATIVES`, then run:

```bash
if [ "${CONVERGENCE_ENABLED}" = "true" ] && [ -n "${REVIEWS_FILE}" ]; then
  san() { printf '%s' "$1" | tr '\r\n\t' '   ' | sed -E 's/^[[:space:]]*[#|`-]+[[:space:]]*//'; }
  LINE="- [ ] REVISION_CONFLICT $(san "${CONFLICT_DIMENSION}")/$(san "${CONFLICT_PLAN}") — required_property: $(san "${CONFLICT_PROPERTY}") | conflicts with: $(san "${CONFLICT_CONSTRAINT}") | alternatives: $(san "${CONFLICT_ALTERNATIVES}")"
  END='<!-- engineer:plan-revision-conflicts:end -->'
  TMP=$(mktemp "${REVIEWS_FILE}.XXXXXX")
  if ! LINE="$LINE" END="$END" awk '
    { cur = $0; sub(/\r$/, "", cur) }
    cur == ENVIRON["LINE"] { seen = 1 }
    cur == ENVIRON["END"] && !ins { if (!seen) print ENVIRON["LINE"]; ins = 1 }
    { print }
    END { if (!ins) exit 2 }
  ' "${REVIEWS_FILE}" > "${TMP}"; then
    rm -f "${TMP}"
    echo "BLOCKED: no end delimiter in '${REVIEWS_FILE}'." >&2
    exit 1
  fi
  mv "${TMP}" "${REVIEWS_FILE}"
fi
```

**Otherwise (revised plans, not `## REVISION_CONFLICT`):** if this re-spawn followed a
resolved conflict, close its record — nothing persists across fences, so export `REVIEWS_FILE`,
the same `CONFLICT_DIMENSION`/`CONFLICT_PLAN` used to open it, and `CONFLICT_RESOLUTION` (a
one-line summary). Then run:

```bash
if [ "${CONVERGENCE_ENABLED}" = "true" ] && [ -n "${REVIEWS_FILE}" ]; then
  san() { printf '%s' "$1" | tr '\r\n\t' '   ' | sed -E 's/^[[:space:]]*[#|`-]+[[:space:]]*//'; }
  PREFIX="- [ ] REVISION_CONFLICT $(san "${CONFLICT_DIMENSION}")/$(san "${CONFLICT_PLAN}") — "
  RES=$(printf '%s' "${CONFLICT_RESOLUTION}" | tr '\r\n\t' '   ')
  TMP=$(mktemp "${REVIEWS_FILE}.XXXXXX")
  if ! PREFIX="$PREFIX" RES="$RES" awk '
    { cur = $0; sub(/\r$/, "", cur) }
    !d && index(cur, ENVIRON["PREFIX"]) == 1 { print "- [x]" substr(cur, 6) " | resolved: " ENVIRON["RES"]; d = 1; next }
    { print }
    END { if (!d) exit 2 }
  ' "${REVIEWS_FILE}" > "${TMP}"; then
    rm -f "${TMP}"
    echo "BLOCKED: no open conflict '${CONFLICT_DIMENSION}/${CONFLICT_PLAN}' in '${REVIEWS_FILE}'." >&2
    exit 1
  fi
  mv "${TMP}" "${REVIEWS_FILE}"
fi
```

Spawn checker again (step 10), then increment `iteration_count`.

**If iteration_count >= 3:**

Recount BLOCKER + WARNING by the same rule — an entry whose severity is missing or unrecognized counts as a BLOCKER (fail closed). If `issue_count` is 0 — PASSED with no BLOCKER/WARNING entry in the YAML block or in prose, or every entry in the block is explicitly INFO — display any advisories and proceed to step 13; the gate below fires on everything else.

Display: `Max iterations reached. {N} issues remain:` + issue list

Offer: 1) Force proceed, 2) Provide guidance and retry, 3) Abandon

## 12.5. Plan Bounce (Optional External Refinement)

**Skip if:** `--skip-bounce`, `--gaps`, or bounce not activated (`--bounce` flag or `workflow.plan_bounce` config; `--skip-bounce` always wins). Requires `workflow.plan_bounce_script` set to a valid script path — warn and skip if bounce is activated with no script configured.

For each `*-PLAN.md`: back it up to `*-PLAN.pre-bounce.md`, invoke `${BOUNCE_SCRIPT}` with the plan file and `workflow.plan_bounce_passes` (default 2), validate the result's YAML frontmatter integrity, and restore from backup on either broken frontmatter or a non-zero script exit. After all plans are bounced, re-run the plan checker (step 10) on the modified plans, restoring any that fail. Commit surviving bounced plans if at least one survived (`refactor(${padded_phase}): bounce plans through external refinement`), display a `{survived}/{total}` summary, and remove all `*-PLAN.pre-bounce.md` backups. Exact banner text, messages, and commands: `engineer/workflows/plan-phase/detail/elaboration.md` § 12.5.

## 13. Requirements Coverage Gate

After plans pass the checker (or checker is skipped), verify that all phase requirements are covered by at least one plan.

**Skip if:** `phase_req_ids` is null or TBD (no requirements mapped to this phase).

**Step 1: Extract requirement IDs claimed by plans**
```bash
# Collect all requirement IDs from plan frontmatter
PLAN_REQS=$(grep -h "requirements_addressed\|requirements:" ${PHASE_DIR}/*-PLAN.md 2>/dev/null | tr -d '[]' | tr ',' '\n' | sed 's/^[[:space:]]*//' | sort -u)
```

**Step 2: Compare against phase requirements from ROADMAP**

For each REQ-ID in `phase_req_ids`:
- If REQ-ID appears in `PLAN_REQS` → covered ✓
- If REQ-ID does NOT appear in any plan → uncovered ✗

**Step 3: Check CONTEXT.md features against plan objectives**

Read CONTEXT.md `<decisions>` section. Extract feature/capability names. Check each against plan `<objective>` blocks. Features not mentioned in any plan objective → potentially dropped.

**Step 4: Report**

If all requirements covered and no dropped features:
```
✓ Requirements coverage: {N}/{N} REQ-IDs covered by plans
```
→ Proceed to step 14.

If gaps found:
```
## ⚠ Requirements Coverage Gap

{M} of {N} phase requirements are not assigned to any plan:

| REQ-ID | Description | Plans |
|--------|-------------|-------|
| {id} | {from REQUIREMENTS.md} | None |

{K} CONTEXT.md features not found in plan objectives:
- {feature_name} — described in CONTEXT.md but no plan covers it

Options:
1. Re-plan to include missing requirements (recommended)
2. Move uncovered requirements to next phase
3. Proceed anyway — accept coverage gaps
```

If `TEXT_MODE` is true, present as a plain-text numbered list (options already shown in the block above). Otherwise use AskUserQuestion to present the options.

## 13a. Decision Coverage Gate

Verify every trackable decision in CONTEXT.md `<decisions>` is referenced by at
least one plan. This **translation gate** refuses to mark a phase planned
when a discuss-phase decision silently dropped.

**Skip if** `workflow.context_coverage_gate` is `false` (absent = enabled), or
no CONTEXT.md exists for this phase, or its `<decisions>` block is empty.

```bash
GATE_CFG=$(engineer_run query config-get workflow.context_coverage_gate --raw 2>/dev/null || echo "true")
if [ "$GATE_CFG" != "false" ]; then
  # CONTEXT_PATH from step-1 init doesn't survive into this Bash block;
  # recompute it. Only run when a CONTEXT.md exists (handler fails closed on an
  # empty arg, so an unguarded empty glob would halt a context-less phase).
  CONTEXT_PATH=$(ls "${PHASE_DIR}"/*-CONTEXT.md 2>/dev/null | head -1)
  if [ -n "$CONTEXT_PATH" ]; then
    GATE_RESULT=$(engineer_run query check.decision-coverage-plan "${PHASE_DIR}" "${CONTEXT_PATH}") && GATE_EXIT=0 || GATE_EXIT=$?
    # 69 UNAVAILABLE = the gate could not look: surface it and stop.
    [ "$GATE_EXIT" -eq 0 ] || { echo "Decision coverage gate could not run (exit ${GATE_EXIT}): $GATE_RESULT"; exit 1; }
    # BLOCKING: refuse to mark phase planned when a trackable decision is uncovered.
    # `passed: true` covers both real-pass and skipped cases (gate disabled / no CONTEXT.md /
    # no trackable decisions). Verify-phase counterpart deliberately omits this exit-1 — that
    # gate is non-blocking by design (review finding F15).
    echo "$GATE_RESULT" | jq -e '(.passed // .data.passed) == true' >/dev/null || {
      echo "$GATE_RESULT" | jq -r '(.message // .data.message // "Decision coverage gate failed.")'
      exit 1
    }
  fi
fi
```

The handler returns JSON:
```json
{ "passed": true, "skipped": false, "total": 2, "covered": 2,
  "uncovered": [{ "id": "D-01", "text": "...", "category": "..." }], "message": "..." }
```

On a caller error (non-file context, `could-not-parse`, a bad phase dir or one with no plans)
`total` and `covered` are `null`, `uncovered` is omitted, `passed` stays
`false`. A missing context argument answers `total: 0`.

**If `passed` is true (or `skipped` is true):** Display
`✓ Decision coverage: {M}/{N} decisions covered` (or `(skipped)`) and proceed
to step 13b.

**If `passed` is false:** Display the handler's `message` block. It already
names each uncovered decision (`D-NN | category | text`) and tells the user
what to do — cite the id in a relevant plan's `must_haves` / `truths`, or
move the decision under `### Claude's Discretion` / tag it `[informational]`
if it should not be tracked. Then offer:

```text
Options:
1. Re-plan to cover missing decisions (recommended)
2. Edit CONTEXT.md to mark dropped decisions as [informational] / Discretion
3. Proceed anyway — accept the coverage gap
```

If `TEXT_MODE` is true, present as a plain-text numbered list. Otherwise use
AskUserQuestion. Selecting "Proceed anyway" continues to step 13b but
records the override in STATE.md so verify-phase can re-surface it.

**Why this gate blocks:** failing here is cheap. The plans are the contract
between discuss-phase and execute-phase; if a decision isn't visible in any
plan, no executor will implement it. Catching that now beats discovering it
after thousands of dollars of execution.

## 13b. Record Planning Completion in STATE.md

After plans pass all gates, record that planning is complete so STATE.md reflects the new phase status:

```bash
engineer_run query state.planned-phase --phase "${PHASE_NUMBER}" --name "${PHASE_NAME}" --plans "${PLAN_COUNT}"
```

This updates STATUS to "Ready to execute", sets the correct plan count, and timestamps Last Activity.

## 13c. Annotate ROADMAP with Wave Dependencies and Cross-cutting Constraints

After plans are finalized, annotate the ROADMAP.md plan list for this phase with:
- **Wave dependency notes** — a bold header before each wave group ("Wave 2 *(blocked on Wave 1 completion)*")
- **Cross-cutting constraints** — a "Cross-cutting constraints:" subsection listing `must_haves.truths` entries that appear in 2 or more plans

This step is derived entirely from existing PLAN frontmatter — no extra LLM pass is required.

```bash
engineer_run query roadmap.annotate-dependencies "${PHASE_NUMBER}"
```

This operation is idempotent: if wave headers or cross-cutting constraints already exist in the ROADMAP phase section, the command returns without modifying the file. Skip this step if `plan_count` is 0.

## 13d. Commit Plans if commit_docs is true

If `commit_docs` is true (from the init JSON parsed in step 1), commit the generated plan artifacts (including any ROADMAP.md annotations from step 13c):

```bash
engineer_run query commit "docs(${PADDED_PHASE}): create phase plan" --files "${PHASE_DIR}"/*-PLAN.md .planning/STATE.md .planning/ROADMAP.md
```

This commits all PLAN.md files for the phase plus the updated STATE.md and ROADMAP.md to version-control the planning artifacts. Skip this step if `commit_docs` is false.

## 13e. Post-Planning Gap Analysis (plan:post capability gate dispatch)

Proactive, non-blocking coverage report gated on `workflow.post_planning_gaps`
(default `true`). Dispatched via the `plan:post` capability gate owned by the
`gap-analysis` capability. Reads REQUIREMENTS.md and CONTEXT.md
`<decisions>` and cross-references each REQ-ID / D-ID against `${PHASE_DIR}/*-PLAN.md`.

```bash
IFS= read -rd '' ENGINEER_ARGS <<'ENGINEER_ARGS_END' || true
$ARGUMENTS
ENGINEER_ARGS_END
ENGINEER_ARGS=${ENGINEER_ARGS%$'\n'}
PLAN_POST_HOOKS_JSON=$(engineer_run loop render-hooks plan:post --raw)
ENGINEER_WS=$(echo " $ENGINEER_ARGS" | sed -nE 's/.* --ws +([A-Za-z0-9][A-Za-z0-9._-]*).*/--ws \1/p' | head -n 1)
PHASE_REQ_IDS=$(engineer_run query init.plan-phase ${ENGINEER_WS:+--ws=${ENGINEER_WS##* }} "$PHASE" --pick phase_req_ids 2>/dev/null)
PHASE_REQ_IDS="${PHASE_REQ_IDS:-TBD}"
```

Read the `activeHooks` array from `PLAN_POST_HOOKS_JSON` in-context. If
`activeHooks` is empty or absent, skip this step silently — do NOT key the skip
on any one capability's gate being absent.

**Step and contribution dispatch:** dispatch every `kind == "step"` hook and inject every `kind == "contribution"` fragment per @~/.claude/engineer/references/loop-hook-dispatch.md (skip each kind silently when none), before gate evaluation below.

⚠ **Validate `check` before shell use** (third-party manifest input; wherever `${hook.check.query}` appears, write the dot-normalized query, each `.` as `-`, and validate and pass that same value) — `loop-hook-dispatch.md` § `gate`.

**For each active entry where `kind == "gate"`** (process in array order). **Dispatch by check shape** (the registry validates exactly one of `query`/`predicate`/`agentVerdict`):

```bash
# named-query gate:
GATE_RESULT=$(engineer_run check ${hook.check.query} "${PHASE_DIR}" "${PHASE_REQ_IDS}" --raw) && CHECK_EXIT=0 || CHECK_EXIT=$?
```
OR, for a generic `predicate` gate, inline the predicate as compact JSON (note the `--phase-dir`/`--phase-number`/`--phase-req-ids` flags feed `${PHASE_DIR}`/`${PHASE_NUMBER}`/`${PHASE_REQ_IDS}` interpolation):
```bash
GATE_RESULT=$(engineer_run check predicate --predicate '<hook.check.predicate as JSON>' --phase-dir "${PHASE_DIR}" --phase-number "${PHASE_NUMBER}" --phase-req-ids "${PHASE_REQ_IDS}" --raw) && CHECK_EXIT=0 || CHECK_EXIT=$?
```
(Read the hook's `check` object in-context to pick the branch; a gate with neither is a malformed registry entry — skip with a warning.)

**Step 1 — did the CHECK COMMAND itself succeed?**
If the check command failed (non-zero `CHECK_EXIT`, empty output, or unparseable JSON):
- `onError == "halt"` → halt and surface command error.
- `onError == "skip"` → log a warning and continue to the next hook.

**Step 2 — read `GATE_RESULT.block` (boolean).** Only reached when command succeeded.

- If `hook.blocking == true` and `GATE_RESULT.block == true`: halt. (gap-analysis is always `blocking: false` so this branch is informational only.)
- If `hook.blocking == false` (advisory): if `GATE_RESULT.block == true` or non-empty `table`/`summary`, output the gap table and continue. Advisory gates never block phase completion.
- If `hook.blocking == true` and `GATE_RESULT.block == false`: continue silently.

## 14. Present Final Status

Route to `<offer_next>` OR `auto_advance` depending on flags/config.

## 15. Auto-Advance Check

Read and execute `engineer/workflows/plan-phase/steps/auto-advance-check.md`. It checks `--auto` / `--chain` and the ephemeral chain flag, then reads this phase's CONTEXT execution authorization before any execute-phase dispatch. Auto flags and persistent preferences never grant implementation permission. Without direct, phase-scoped user authorization, clear the ephemeral flag, report that planning is complete, and route to `<offer_next>`; otherwise follow the gate's authorized handoff procedure.

</process>

<offer_next>
Output this markdown directly (not as a code block):

`${GAPS_EXEC_FLAG}` projects the just-completed planning mode onto the follow-up execute command: it expands to `--gaps-only` for a `--gaps` planning run (so the handoff points at execute-phase's gap-closure scope — only the newly created `gap_closure: true` plans — not the whole phase) and to empty for a standard or `--reviews` run (whole-phase scope, unchanged). Substitute it verbatim; when empty, collapse the extra space.

### Engineer ► PHASE {X} PLANNED ✓

**Phase {X}: {Name}** — {N} plan(s) in {M} wave(s)

| Wave | Plans | What it builds |
|------|-------|----------------|
| 1    | 01, 02 | [objectives] |
| 2    | 03     | [objective]  |

Research: {Completed | Used existing | Skipped}
Verification: {Passed | Passed with override | Skipped}

---

## ▶ Next Up — [${PROJECT_CODE}] ${PROJECT_TITLE}

**Execute Phase {X}** — run all {N} plans

/clear then:

/execute-phase {X} ${GAPS_EXEC_FLAG} ${ENGINEER_WS}

---

**Also available:**
- cat .planning/phases/{phase-dir}/*-PLAN.md — review plans
- /plan-phase {X} --research — re-research first
- /review --phase {X} --all — peer review plans with external AIs
- /plan-phase {X} --reviews — replan incorporating review feedback

---
</offer_next>

<windows_troubleshooting>
Read `engineer/workflows/plan-phase/steps/windows-troubleshooting.md` if plan-phase freezes on Windows during agent spawning (stdio deadlocks with MCP servers) — it covers force-kill, orphaned-node cleanup, stale task-dir cleanup, reducing the MCP server count, and the `--skip-research` fallback.
</windows_troubleshooting>

<!-- engineer:protected:start -->
<success_criteria>
- [ ] .planning/ directory validated
- [ ] Phase validated against roadmap
- [ ] Phase directory created if needed
- [ ] CONTEXT.md loaded early (step 4) and passed to ALL agents
- [ ] Research completed (unless --skip-research or --gaps or exists)
- [ ] phase-researcher spawned with CONTEXT.md
- [ ] Existing plans checked
- [ ] planner spawned with CONTEXT.md + RESEARCH.md
- [ ] Plans created (PLANNING COMPLETE or CHECKPOINT handled)
- [ ] plan-checker spawned with CONTEXT.md
- [ ] Verification passed OR user override OR max iterations with user decision
- [ ] User sees status between agent spawns
- [ ] User knows next steps
</success_criteria>
<!-- engineer:protected:end -->
