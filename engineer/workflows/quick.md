<purpose>
Execute small, ad-hoc tasks with Engineer guarantees (atomic commits, STATE.md tracking). Quick mode spawns planner (quick mode) + executor(s), tracks tasks in `.planning/quick/`, and records completion through the runtime.

With `--full` flag: enables the complete quality pipeline — discussion + research + plan-checking + verification. One flag for everything.

With `--validate` flag: enables plan-checking (max 2 iterations) and post-execution verification only. Discussion remains the default and research runs as needed.

With `--discuss` flag: lightweight discussion phase before planning. Surfaces assumptions, clarifies gray areas, captures decisions in CONTEXT.md so the planner treats them as locked.

With `--research` flag: spawns a focused research agent before planning. Investigates implementation approaches, library options, and pitfalls. Use when you're unsure how to approach a task.

Granular flags are composable: `--discuss --research --validate` gives the same result as `--full`.
</purpose>

<required_reading>
Read all files referenced by the invoking prompt's execution_context before starting.
</required_reading>

<available_agent_types>
Valid Engineer subagent types (use exact names — do not fall back to 'general-purpose'):
- phase-researcher — Researches technical approaches for a phase
- planner — Creates detailed plans from phase scope
- plan-checker — Reviews plan quality before execution
- executor — Executes plan tasks, commits, creates SUMMARY.md
- verifier — Verifies phase completion, checks quality gates
- code-reviewer — Reviews source files for bugs, security issues, and code quality
</available_agent_types>

<default_preparation>
For a new or resumed implementation task, set DISCUSS_MODE=true by default. Ask the clarifying questions needed to establish scope before planning. Use the complete copied discussion-phase step; no --discuss flag is required. Reuse decisions already supplied by the user.
Set RESEARCH_MODE=true when the scoped task has unresolved technical questions that need research before the planner can build its plan. Use the complete copied research-phase step when needed; no --research flag is required. List and status requests remain read-only.
</default_preparation>
<process>
**Step 1: Parse arguments and get task description**

Parse `$ARGUMENTS` for:
- `--full` flag → store `$FULL_MODE=true`, `$DISCUSS_MODE=true`, `$RESEARCH_MODE=true`, `$VALIDATE_MODE=true`
- `--validate` flag → store `$VALIDATE_MODE=true`
- `--discuss` flag → store `$DISCUSS_MODE=true`
- `--research` flag → store `$RESEARCH_MODE=true`
- Remaining text → use as `$DESCRIPTION` if non-empty

After parsing, normalize: if `$DISCUSS_MODE` and `$RESEARCH_MODE` and `$VALIDATE_MODE` are all true, set `$FULL_MODE=true`. This ensures `--discuss --research --validate` is treated identically to `--full`.

Before creating a new quick record, run `quick-tasks-migrate` to import any legacy Quick Tasks table rows into canonical QUICK.md records. Migration is idempotent and preserves the source table. `quick.create`/`quick.update` remain authoritative for the active task; after completion, `quick-tasks-append` writes its history row through the schema-safe table helper.

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
RESPONSE_LANGUAGE=$(engineer_run query config-get response_language --raw --default "" 2>/dev/null || echo "")
```

**If `response_language` is set:** All user-facing output of this workflow — narration between tool calls, status updates, progress notes, findings, questions, prompts, and explanations — MUST be presented in `{response_language}`. Technical terms, code, file paths, and subagent prompts stay in English — only user-facing output is translated.

If `$DESCRIPTION` is empty after parsing, prompt user interactively:

**Text mode (`workflow.text_mode: true` in config or `--text` flag):** Set `TEXT_MODE=true` if `--text` is present in `$ARGUMENTS` OR `text_mode` from init JSON is `true`. When TEXT_MODE is active, replace every `AskUserQuestion` call with a plain-text numbered list and ask the user to type their choice number. This is required for non-Claude runtimes (OpenAI Codex) where `AskUserQuestion` is not available.

```
AskUserQuestion(
  header: "Quick Task",
  question: "What do you want to do?",
  followUp: null
)
```

Store response as `$DESCRIPTION`.

If still empty, re-prompt: "Please provide a task description."

Display banner based on active flags:

If `$FULL_MODE` (all phases enabled — `--full` or all granular flags):
```
### Engineer ► QUICK TASK (FULL)

◆ Discussion + research + plan checking + verification enabled
```

If `$DISCUSS_MODE` and `$VALIDATE_MODE` (no research):
```
### Engineer ► QUICK TASK (DISCUSS + VALIDATE)

◆ Discussion + plan checking + verification enabled
```

If `$DISCUSS_MODE` and `$RESEARCH_MODE` (no validate):
```
### Engineer ► QUICK TASK (DISCUSS + RESEARCH)

◆ Discussion + research enabled
```

If `$RESEARCH_MODE` and `$VALIDATE_MODE` (no discuss):
```
### Engineer ► QUICK TASK (RESEARCH + VALIDATE)

◆ Research + plan checking + verification enabled
```

If `$DISCUSS_MODE` only:
```
### Engineer ► QUICK TASK (DISCUSS)

◆ Discussion phase enabled — surfacing gray areas before planning
```

If `$RESEARCH_MODE` only:
```
### Engineer ► QUICK TASK (RESEARCH)

◆ Research phase enabled — investigating approaches before planning
```

If `$VALIDATE_MODE` only:
```
### Engineer ► QUICK TASK (VALIDATE)

◆ Plan checking + verification enabled
```

---

**Step 2: Initialize**

```bash
IFS= read -rd '' ENGINEER_ARGS <<'ENGINEER_ARGS_END' || true
$ARGUMENTS
ENGINEER_ARGS_END
ENGINEER_ARGS=${ENGINEER_ARGS%$'\n'}
DISCUSS_PARAM=""; if [[ "$ENGINEER_ARGS" =~ (^|[[:space:]])--discuss([[:space:]]|$) ]]; then DISCUSS_PARAM="--discuss"; fi
RESEARCH_PARAM=""; if [[ "$ENGINEER_ARGS" =~ (^|[[:space:]])--research([[:space:]]|$) ]]; then RESEARCH_PARAM="--research"; fi
VALIDATE_PARAM=""; if [[ "$ENGINEER_ARGS" =~ (^|[[:space:]])--validate([[:space:]]|$) ]]; then VALIDATE_PARAM="--validate"; fi
FULL_PARAM=""; if [[ "$ENGINEER_ARGS" =~ (^|[[:space:]])--full([[:space:]]|$) ]]; then FULL_PARAM="--full"; fi
engineer_run quick-tasks-migrate || exit $?
INIT=$(engineer_run query init.quick  "$DESCRIPTION" $DISCUSS_PARAM $RESEARCH_PARAM $VALIDATE_PARAM $FULL_PARAM)
AGENT_SKILLS_PLANNER=$(engineer_run query agent-skills planner )
AGENT_SKILLS_EXECUTOR=$(engineer_run query agent-skills executor )
AGENT_SKILLS_CHECKER=$(engineer_run query agent-skills plan-checker )
AGENT_SKILLS_VERIFIER=$(engineer_run query agent-skills verifier )
AGENT_SKILLS_RESEARCHER=$(engineer_run query agent-skills phase-researcher )
```

Parse JSON for: `planner_model`, `executor_model`, `checker_model`, `verifier_model`, `reviewer_model`, `researcher_model`, `commit_docs`, `branch_name`, `quick_id`, `slug`, `date`, `timestamp`, `quick_dir`, `task_dir`, `roadmap_exists`, `planning_exists`, `response_language`.

`init.quick` does not emit dedicated `state_path`/`project_path` fields, so derive them from the already-absolute `quick_dir` (files handed to a spawned subagent must resolve regardless of that subagent's own cwd):
```bash
STATE_PATH="$(dirname "${quick_dir}")/STATE.md"
PROJECT_PATH="$(dirname "${quick_dir}")/PROJECT.md"
```

```bash
RUNTIME=$(engineer_run query runtime-identity --pick host --raw 2>/dev/null || echo "claude")
```

**Resolve isolation now.** Read @~/.claude/engineer/references/dispatch-isolation-gate.md
and run its `Resolve ISOLATION`, `Single-agent dispatch sites`, and `Resolve the harness flag`
blocks in order; they set `ISOLATION`/`HARNESS_FLAG` via `query dispatch-isolation`.
`ISOLATION` — not `RUNTIME` — gates every worktree decision below. Substitute `{harnessFlag}`
in Step 6's `Agent()` with `$HARNESS_FLAG`+comma when `ISOLATION = "harness-worktree"`, else
empty. `{harnessFlag}`
is a template placeholder, not a shell variable.

Before isolated dispatch, run a startup orphan sweep before spawning any executors. This reaps locked worktrees whose lock-owner process is dead, whose branch is merged into the default branch, and whose lock file mtime is older than 5 minutes. Running it at startup prevents accumulation of orphaned worktrees from prior sessions that exited without cleanup.

```bash
if true; then
  engineer_run query worktree.reap-orphans 2>/dev/null || true
fi
```

If the project uses git submodules, worktree isolation is unsafe **only when the quick task touches a submodule path**. The previous behavior unconditionally disabled worktree isolation whenever `.gitmodules` existed, which penalised every quick task in a submodule project even when the task was nowhere near a submodule. Parse submodule paths from `.gitmodules` so the executor can act on actual submodule paths rather than the mere file's existence:

```bash
# Parse submodule paths from .gitmodules once (empty if no .gitmodules).
# SUBMODULE_PATHS is a newline-separated list of repo-relative paths used as
# a fail-loud commit-time guard inside the quick-task executor — if the
# executor stages any path that falls inside SUBMODULE_PATHS, it must abort
# the commit and surface the conflict rather than silently corrupting the
# submodule state.
if [ -f .gitmodules ]; then
  SUBMODULE_PATHS=$(git config --file .gitmodules --get-regexp '^submodule\..*\.path$' 2>/dev/null | awk '{print $2}')
else
  SUBMODULE_PATHS=""
fi
```

The quick planner declares the exact `files_modified` and `files_deleted` paths before dispatch. Block a declared submodule intersection and retain the fail-loud commit-time guard: if any staged path falls inside `SUBMODULE_PATHS`, abort and report the unsupported submodule scope. Resolve that scope before retrying in an isolated checkout. If `SUBMODULE_PATHS` is empty (no `.gitmodules` in the repo), worktree isolation proceeds normally.

**If `roadmap_exists` is false:** Error — Quick mode requires an active project with ROADMAP.md. Run `/new-project` first.

Quick tasks can run mid-phase - validation only checks ROADMAP.md exists, not phase status.

---

**Step 2.5: Handle quick-task branching**

**If `branch_name` is empty/null:** Skip and continue on the current branch.

**If `branch_name` is set:** Check out the quick-task branch before any planning commits.

The new branch must fork off the project's default branch (`origin/HEAD`), not
off whatever HEAD happens to be checked out — otherwise consecutive quick tasks
compound on top of each other and stay unpushed. If `$branch_name`
already exists locally, reuse it as-is so resumed work is not rebased.

```bash
DEFAULT_BRANCH=$(engineer_run query git.base-branch 2>/dev/null \
  || git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|^origin/||' \
  || echo main)

if git show-ref --verify --quiet "refs/heads/$branch_name"; then
  git switch "$branch_name" \
    || { echo "ERROR: Could not switch to existing quick-task branch '$branch_name'." >&2; exit 1; }
else
  # Fetch the default branch so origin/$DEFAULT_BRANCH is current. If the fetch
  # fails (offline, no remote, auth failure) AND we have no local copy of
  # origin/$DEFAULT_BRANCH to fall back on, abort.
  if ! git fetch --quiet origin "$DEFAULT_BRANCH"; then
    if ! git show-ref --verify --quiet "refs/remotes/origin/$DEFAULT_BRANCH"; then
      echo "ERROR: Could not fetch origin/$DEFAULT_BRANCH and no local copy exists. Refusing to create '$branch_name' off the current HEAD. Resolve the remote/network issue and retry." >&2
      exit 1
    fi
    echo "WARNING: git fetch origin $DEFAULT_BRANCH failed; using the local copy of origin/$DEFAULT_BRANCH as base." >&2
  fi

  if [ -n "$(git status --porcelain)" ]; then
    echo "WARNING: Uncommitted changes present. Carrying them onto the new quick-task branch — they will be branched off origin/$DEFAULT_BRANCH (not the previous-task HEAD)."
  else
    # Best-effort: fast-forward the local default branch so subsequent local
    # work sees the latest tip. Failure here is non-fatal because we always
    # create the new branch directly from origin/$DEFAULT_BRANCH below.
    git switch --quiet "$DEFAULT_BRANCH" 2>/dev/null \
      && git merge --ff-only --quiet "origin/$DEFAULT_BRANCH" 2>/dev/null \
      || true
  fi

  # Pin the new branch to origin/$DEFAULT_BRANCH so the start point is
  # deterministic regardless of which branch we are currently on.
  # On success HEAD is exactly at origin/$DEFAULT_BRANCH, so a post-creation
  # merge-base / "ahead-of" guard would be unreachable — the explicit base
  # argument here is the single source of correctness.
  # --no-track: with the default branch.autoSetupMerge=true, checkout -b from a
  # remote-tracking ref wires branch.<name>.merge to refs/heads/$DEFAULT_BRANCH
  # (origin/master), so a GUI sync pushes quick-task commits straight onto
  # origin/$DEFAULT_BRANCH, bypassing PR review.
  git checkout -b "$branch_name" "origin/$DEFAULT_BRANCH" --no-track \
    || { echo "ERROR: Could not create '$branch_name' from origin/$DEFAULT_BRANCH." >&2; exit 1; }
fi
```

All quick-task commits for this run stay on that branch. User handles merge/rebase afterward.

---

**Step 3: Create task directory**

```bash
mkdir -p "${task_dir}"
```

---

**Step 4: Create quick task directory**

Create the directory for this quick task:

```bash
QUICK_DIR="${task_dir}"
mkdir -p "$QUICK_DIR"
# Worktree-relative form for an isolated executor: the guard blocks absolute paths outside its worktree.
_QTOP=$(git rev-parse --show-toplevel 2>/dev/null)
_QTOP_DIR=$(git -C "$QUICK_DIR" rev-parse --show-toplevel 2>/dev/null)
QUICK_DIR_REL=$(git -C "$QUICK_DIR" rev-parse --show-prefix 2>/dev/null)
QUICK_DIR_REL="${QUICK_DIR_REL%/}"
if [ -z "$QUICK_DIR_REL" ] || [ "$_QTOP" != "$_QTOP_DIR" ]; then QUICK_DIR_REL="$QUICK_DIR"; fi
```

Report to user:
```
Creating quick task ${quick_id}: ${DESCRIPTION}
Directory: ${QUICK_DIR}
```

Store `$QUICK_DIR` for use in orchestration.

---

**Step 4 ordering:** Check whether `workflow.research_before_questions` is enabled in `.planning/config.yaml` (or the config from init context) — the same check `/discuss-phase` and `/new-project` already make. When **enabled**, execute the research-phase section BELOW BEFORE the discussion-phase section: a gray-area answer given without research is written to `<quick_id>-CONTEXT.md` as a locked decision downstream agents are told not to revisit, so the evidence must come first. When **false or unset**, keep the written order (discussion, then research) — behavior unchanged.

<!-- engineer:section id="discussion-phase" when="flag:--discuss" -->
Read and execute `engineer/workflows/quick/steps/discussion-phase.md`.
<!-- /section -->

---

<!-- engineer:section id="research-phase" when="flag:--research" -->
If RESEARCH_MODE is true, read and execute `engineer/workflows/quick/steps/research-phase.md`.
<!-- /section -->

---

**Step 5: Spawn planner (quick mode)**

Read `workflow.tdd_mode` directly; when enabled, pass the native TDD flag and `engineer/references/tdd.md` guidance to this planner and its revisions.

**If `$VALIDATE_MODE`:** Use `quick-full` mode with stricter constraints.

**If NOT `$VALIDATE_MODE`:** Use standard `quick` mode.

Display: `◆ Spawning planner... (runs in a subagent — no output until it returns, ~1–5 min; expected, not a freeze)`

```
Agent(
  prompt="
<planning_context>

**Mode:** ${VALIDATE_MODE ? 'quick-full' : 'quick'}
**Directory:** ${QUICK_DIR}
**Description:** ${DESCRIPTION}

<required_reading>
- ${STATE_PATH} (Project State)
- ./CLAUDE.md or ./.claude/CLAUDE.md (if exists — follow project-specific guidelines)
${DISCUSS_MODE ? '- ' + QUICK_DIR + '/' + quick_id + '-CONTEXT.md (User decisions — locked, do not revisit)' : ''}
${RESEARCH_MODE ? '- ' + QUICK_DIR + '/' + quick_id + '-RESEARCH.md (Research findings — use to inform implementation choices)' : ''}
</required_reading>

${AGENT_SKILLS_PLANNER}

**Project skills:** Check .claude/skills/ or .agents/skills/ directory (if either exists) — read SKILL.md files, plans should account for project skill rules


</planning_context>

<constraints>
- Create a SINGLE plan with 1-3 focused tasks
- Declare exact repo-relative `files_modified` and `files_deleted` arrays in frontmatter; no globs or implicit deletion authority. These arrays become mandatory worktree ownership inputs.
- Quick tasks should be atomic and self-contained
- PATH FORM : every path in the plan BODY — `files`, `verify`, `<automated>`, task actions — is repo-root-relative, and every `<automated>` command assumes cwd at the checkout root. Only the `<required_reading>` inputs above are absolute . An absolute path copied from this context into `<automated>` pins the command to THIS checkout; a worktree-isolated executor then runs it against the main tree and it passes on unchanged code.
- MUTABLE-SCOPE AUTHORITY : when concrete edit or verification scope depends on mutable external state (a merge index, PR/base diffs, the working tree), authorize scope ONLY from a live observation made at planning time — for conflict resolution that is the fresh merge index via `git diff --name-only --diff-filter=U` — or keep `files`/`verify` CONDITIONAL on that observation. Historical STATE.md entries, recovery notes, and cached PR/base diff paths may guide investigation only; they are never edit or verification authority, and a plan must not enumerate them as authorized files "pending replacement".
${RESEARCH_MODE ? '- Research findings are available — use them to inform library/pattern choices' : '- No research phase'}
${VALIDATE_MODE ? '- Target ~40% context usage (structured for verification)' : '- Target ~30% context usage (simple, focused)'}
${VALIDATE_MODE ? '- MUST generate `must_haves` in plan frontmatter (truths, artifacts, key_links)' : ''}
${VALIDATE_MODE ? '- Each task MUST have `files`, `action`, `verify`, `done` fields' : ''}
</constraints>

<output>
Write plan to: ${QUICK_DIR}/${quick_id}-PLAN.md
Return: ## PLANNING COMPLETE with plan path
</output>
",
  subagent_type="planner",
  model="{planner_model}",
  description="Quick plan: ${DESCRIPTION}"
)
```

> **ORCHESTRATOR RULE — CODEX RUNTIME**: After calling Agent() above, stop working on this task immediately. Do not read more files, edit code, or run tests related to this task while the subagent is active. Wait for the subagent to return its result. This prevents duplicate work, conflicting edits, and wasted context. Only resume when the subagent result is available.

After planner returns:
1. Verify plan exists at `${QUICK_DIR}/${quick_id}-PLAN.md`
2. Extract plan count (typically 1 for quick tasks)
3. Report: "Plan created: ${QUICK_DIR}/${quick_id}-PLAN.md"

If plan not found, error: "Planner failed to create ${quick_id}-PLAN.md"

---

<!-- engineer:section id="plan-checker-loop" when="flag:--validate" -->
If `section_manifest` is `null` or `"plan-checker-loop"` is in its `included` list: read and execute `engineer/workflows/quick/steps/plan-checker-loop.md`. Otherwise skip — do not read the file.
<!-- /section -->

---

<!-- engineer:section id="worktree-pre-dispatch-commit" when="state:worktrees-enabled" -->
If `section_manifest` is `null` or `"worktree-pre-dispatch-commit"` is in its `included` list: read and execute `engineer/workflows/quick/steps/worktree-pre-dispatch-commit.md`. Otherwise skip — do not read the file.
<!-- /section -->

---

**Step 6: Spawn executor**

Mandatory isolation is required; resolve only harness-worktree or orchestrator-worktree. Failure blocks executor dispatch.

The coordinator performs setup **before** the Agent call. The completed quick plan and produced discussion/research artifacts must already be committed by Step 5.6. Keep this setup result in the coordinator's invocation state between tool calls.

```bash
ORCH_ROOT=$(git rev-parse --show-toplevel) || exit $?
EXPECTED_BASE=$(git rev-parse HEAD) || exit $?
QUICK_PLAN_PATH="${QUICK_DIR_REL}/${quick_id}-PLAN.md"
QUICK_SUMMARY_PATH="${QUICK_DIR_REL}/${quick_id}-SUMMARY.md"
QUICK_PLAN_JSON=$(engineer_run query frontmatter.get "$QUICK_PLAN_PATH") || exit $?
QUICK_FILES_JSON=$(printf '%s' "$QUICK_PLAN_JSON" | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{const v=JSON.parse(s).files_modified;if(!Array.isArray(v)||v.some(x=>typeof x!=="string"))process.exit(1);process.stdout.write(JSON.stringify(v))})') || exit $?
QUICK_DELETIONS_JSON=$(printf '%s' "$QUICK_PLAN_JSON" | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{const v=JSON.parse(s).files_deleted||[];if(!Array.isArray(v)||v.some(x=>typeof x!=="string"))process.exit(1);process.stdout.write(JSON.stringify(v))})') || exit $?
QUICK_ALLOWED_BASES=$(EXPECTED_BASE="$EXPECTED_BASE" QUICK_PLAN_PARENT="${QUICK_PLAN_PARENT:-}" node -e 'process.stdout.write(JSON.stringify([...new Set([process.env.EXPECTED_BASE,process.env.QUICK_PLAN_PARENT].filter(Boolean))]))') || exit $?
QUICK_WORKTREE_MANIFEST=$(mktemp "${TMPDIR:-/tmp}/engineer-quick-worktree-XXXXXX") || exit $?
mv "$QUICK_WORKTREE_MANIFEST" "${QUICK_WORKTREE_MANIFEST}.json" && QUICK_WORKTREE_MANIFEST="${QUICK_WORKTREE_MANIFEST}.json" || exit 1
engineer_run query worktree.manifest init --manifest "$QUICK_WORKTREE_MANIFEST" --root "$ORCH_ROOT" || exit $?
case "$ISOLATION" in
  orchestrator-worktree)
    QUICK_WORKTREE=$(engineer_run query worktree.create "quick-${quick_id}" --phase "quick-${quick_id}" --manifest "$QUICK_WORKTREE_MANIFEST" --root "$ORCH_ROOT" --base "$EXPECTED_BASE" --allowed-bases "$QUICK_ALLOWED_BASES" --files-json "$QUICK_FILES_JSON" --deletions-json "$QUICK_DELETIONS_JSON" --summary-path "$QUICK_SUMMARY_PATH") || exit $?
    QUICK_WORKTREE_PATH=$(engineer_run query json.get --payload "$QUICK_WORKTREE" --field worktree_path --raw) || exit $?
    QUICK_WORKTREE_BRANCH=$(engineer_run query json.get --payload "$QUICK_WORKTREE" --field branch --raw) || exit $?
    QUICK_WORKTREE_BASE=$(engineer_run query json.get --payload "$QUICK_WORKTREE" --field expected_base --raw) || exit $?
    [ "$(git -C "$QUICK_WORKTREE_PATH" rev-parse HEAD)" = "$QUICK_WORKTREE_BASE" ] || exit 42
    [ "$(git -C "$QUICK_WORKTREE_PATH" branch --show-current)" = "$QUICK_WORKTREE_BRANCH" ] || exit 42
    ;;
  harness-worktree) ;;
  *) echo "FATAL: mandatory quick-task isolation unavailable" >&2; exit 1 ;;
esac
```

For orchestrator isolation, the coordinator generates the literal runnable root guard from the returned checkout before composing the prompt:

```bash
QUICK_ROOT_GUARD=""
if [ "$ISOLATION" = "orchestrator-worktree" ]; then
  QUICK_ROOT_GUARD=$(QUICK_WORKTREE_PATH="$QUICK_WORKTREE_PATH" node <<'NODE'
const q = value => "'" + value.replaceAll("'", "'\\''") + "'";
process.stdout.write(`PINNED_ROOT=${q(process.env.QUICK_WORKTREE_PATH)}
ACTUAL_ROOT=$(git rev-parse --show-toplevel) || exit 42
PINNED_TL=$(git -C "$PINNED_ROOT" rev-parse --show-toplevel) || exit 42
[ "$ACTUAL_ROOT" = "$PINNED_TL" ] || { echo "FATAL: executor root differs from assigned isolated checkout" >&2; exit 42; }
`);
NODE
  ) || exit $?
fi
```

Bind the native Agent tool's supported working-directory/workspace input to the exact `QUICK_WORKTREE_PATH` for orchestrator isolation. If this host cannot bind a native worker to that checkout, stop before dispatch and preserve it. The prompt guard verifies this binding; it does not create a checkout or dispatch another worker. For harness isolation, pass the declared harness flag and retain the existing branch/base guard and artifact materialization below. Never dispatch into the primary checkout.

Spawn executor with plan reference:

```
Agent(
  prompt="
Execute quick task ${quick_id}.

${ISOLATION === "harness-worktree" ? `
<worktree_branch_check>
ORCHESTRATOR build-time embed (NOT a sub-agent runtime step): before this dispatch, read \`engineer/references/worktree-branch-check.md\`, substitute \`{EXPECTED_BASE}\` with the base SHA captured above (${EXPECTED_BASE}), substitute \`{EXPECTED_BASE_ALTERNATE}\` with \`${QUICK_PLAN_PARENT}\` when it differs from \`${EXPECTED_BASE}\` (otherwise empty), and replace this note with that fragment's \`<worktree_branch_check>\` block so the dispatched prompt carries the runnable guard verbatim — do not pass this instruction through in its place.
</worktree_branch_check>

FIRST ACTION after the worktree branch check: ensure the quick PLAN.md exists at a worktree-rooted relative path before any Read/Edit/Write path can be primed. If \`${QUICK_DIR}/${quick_id}-PLAN.md\` is absent, materialize it from the shared git object store:

\`\`\`bash
QUICK_PLAN_COMMIT="${QUICK_PLAN_COMMIT}"
QUICK_PLAN_PATH="${QUICK_DIR}/${quick_id}-PLAN.md"
if [ ! -f "$QUICK_PLAN_PATH" ]; then
  mkdir -p "$(dirname "$QUICK_PLAN_PATH")"
  git show "${QUICK_PLAN_COMMIT}:${QUICK_PLAN_PATH}" > "$QUICK_PLAN_PATH" || {
    echo "FATAL: unable to materialize quick plan from ${QUICK_PLAN_COMMIT}:${QUICK_PLAN_PATH}; refusing to continue." >&2
    exit 42
  }
fi
${DISCUSS_MODE ? `QUICK_CONTEXT_PATH="${QUICK_DIR}/${quick_id}-CONTEXT.md"
if [ ! -f "$QUICK_CONTEXT_PATH" ] && git cat-file -e "${QUICK_PLAN_COMMIT}:$QUICK_CONTEXT_PATH" 2>/dev/null; then
  mkdir -p "$(dirname "$QUICK_CONTEXT_PATH")"
  git show "${QUICK_PLAN_COMMIT}:$QUICK_CONTEXT_PATH" > "$QUICK_CONTEXT_PATH" || {
    echo "FATAL: unable to materialize quick context from ${QUICK_PLAN_COMMIT}:$QUICK_CONTEXT_PATH; refusing to continue." >&2
    exit 42
  }
fi
` : ''}${RESEARCH_MODE ? `QUICK_RESEARCH_PATH="${QUICK_DIR}/${quick_id}-RESEARCH.md"
if [ ! -f "$QUICK_RESEARCH_PATH" ] && git cat-file -e "${QUICK_PLAN_COMMIT}:$QUICK_RESEARCH_PATH" 2>/dev/null; then
  mkdir -p "$(dirname "$QUICK_RESEARCH_PATH")"
  git show "${QUICK_PLAN_COMMIT}:$QUICK_RESEARCH_PATH" > "$QUICK_RESEARCH_PATH" || {
    echo "FATAL: unable to materialize quick research from ${QUICK_PLAN_COMMIT}:$QUICK_RESEARCH_PATH; refusing to continue." >&2
    exit 42
  }
fi
` : ''}\`\`\`
` : `
<project_root_pin>
${QUICK_ROOT_GUARD}
</project_root_pin>
Run the literal guard before the first read/write and every commit. Do not create or dispatch worktrees; setup belongs to the coordinator.
`}

<required_reading>
- ${QUICK_DIR_REL}/${quick_id}-PLAN.md (Plan)
${DISCUSS_MODE ? '- ' + QUICK_DIR_REL + '/' + quick_id + '-CONTEXT.md (User decisions — locked, do not revisit)' : ''}
${RESEARCH_MODE ? '- ' + QUICK_DIR_REL + '/' + quick_id + '-RESEARCH.md (Research findings — use to inform implementation choices)' : ''}
- ${STATE_PATH} (Project state)
- ./CLAUDE.md or ./.claude/CLAUDE.md (Project instructions, if exists)
- .claude/skills/ or .agents/skills/ (Project skills, if either exists — list skills, read SKILL.md for each, follow relevant rules during implementation)
</required_reading>

${AGENT_SKILLS_EXECUTOR}

<submodule_commit_guard>
SUBMODULE_PATHS for this project: ${SUBMODULE_PATHS}

If SUBMODULE_PATHS is non-empty, you MUST run this fail-loud guard immediately
before EVERY git commit you create during this quick task (after \`git add\`,
before \`git commit\`). The planner declared exact files_modified/files_deleted paths. This additional guard runs at commit time:

\`\`\`bash
SUBMODULE_PATHS=\"${SUBMODULE_PATHS}\"
if [ -n \"\$SUBMODULE_PATHS\" ]; then
  STAGED=\$(git diff --cached --name-only)
  for sm_raw in \$SUBMODULE_PATHS; do
    sm=\"\${sm_raw#./}\"
    sm=\"\${sm%/}\"
    [ -z \"\$sm\" ] && continue
    for f_raw in \$STAGED; do
      f=\"\${f_raw#./}\"
      f=\"\${f%/}\"
      case \"\$f\" in
        \"\$sm\"|\"\$sm\"/*)
          echo \"ABORT: staged path \$f_raw falls inside submodule \$sm — worktree-isolated commits cannot safely span submodule boundaries. Resolve submodule scope before retrying in a supported isolated checkout.\" >&2
          exit 1 ;;
      esac
    done
  done
fi
\`\`\`

If the guard aborts, do NOT attempt the commit, do NOT remove the staged files,
and do NOT continue subsequent tasks. Surface the abort message in your
SUMMARY.md and stop — the coordinator must resolve submodule scope before retrying.
</submodule_commit_guard>

<constraints>
- Execute all tasks in the plan
- Commit each task atomically (code changes only)
- Run the <submodule_commit_guard> bash block before every \`git commit\` if SUBMODULE_PATHS is non-empty
- Create summary at: ${QUICK_DIR_REL}/${quick_id}-SUMMARY.md with `status: complete` in SUMMARY frontmatter (required so the audit-open milestone-close scanner recognises the task as done, not [unknown])
- Commit the assigned SUMMARY.md with status complete before returning; completion requires committed source and SUMMARY output. Do NOT modify or commit shared STATE.md, ROADMAP.md, REQUIREMENTS.md or config. The coordinator handles remaining shared records in Step 8.
- If a Write/Edit is denied by engineer-worktree-path-guard, stop and report the denial in your final message — do not work around it by copying or moving the file with Bash (cp, mv, redirects)
- Do NOT update ROADMAP.md (quick tasks are separate from planned phases)
</constraints>
",
  subagent_type="executor",
  model="{executor_model}",
  {harnessFlag}
  description="Execute: ${DESCRIPTION}"
)
```

> **ORCHESTRATOR RULE — CODEX RUNTIME**: After calling Agent() above, stop working on this task immediately. Do not read more files, edit code, or run tests related to this task while the subagent is active. Wait for the subagent to return its result. This prevents duplicate work, conflicting edits, and wasted context. Only resume when the subagent result is available.

For **both** isolation modes, capture the native host's actual agent identifier at dispatch and its terminal result through the host wait/status tool. Preserve the original host event as a JSON file outside the worker checkout. Agent prose, an artifact, elapsed time and a timeout are not stop evidence. Until the host confirms terminal state, preserve the checkout, do not reassign its paths and do not merge it.

Under harness isolation, obtain the checkout path from the host's worktree metadata, then query its actual branch and head with Git; retain the captured expected base and allowed bases. Under orchestrator isolation, use the exact path/branch/base returned by `worktree.create` above. Read and execute the **native terminal receipt** procedure in `engineer/workflows/execute-phase/steps/executor-isolation-dispatch.md` with these bindings: `plan_id=quick-${quick_id}`, `WORKTREE_PATH=QUICK_WORKTREE_PATH`, `WORKTREE_BRANCH=QUICK_WORKTREE_BRANCH`, `EXPECTED_BASE=QUICK_WORKTREE_BASE` (or the captured harness base), `ALLOWED_BASES_JSON=QUICK_ALLOWED_BASES`, `PLAN_FILES_JSON=QUICK_FILES_JSON`, `PLAN_DELETIONS_JSON=QUICK_DELETIONS_JSON`, `SUMMARY_PATH=QUICK_SUMMARY_PATH`, `WAVE_WORKTREE_MANIFEST=QUICK_WORKTREE_MANIFEST`. It writes the host-sourced receipt and calls `worktree.record-agent --terminal-receipt` against the same manifest **before** integration; first receipt attachment binds a precreated entry to the actual host agent id.

```bash
if [ "$ISOLATION" = "harness-worktree" ]; then
  : "${HOST_WORKTREE_PATH:?Use the checkout path from actual host metadata}"
  QUICK_WORKTREE_PATH="$HOST_WORKTREE_PATH"
  QUICK_WORKTREE_BRANCH=$(git -C "$QUICK_WORKTREE_PATH" branch --show-current) || exit $?
  QUICK_WORKTREE_BASE="$EXPECTED_BASE"
fi
plan_id="quick-${quick_id}"
WORKTREE_PATH="$QUICK_WORKTREE_PATH"
WORKTREE_BRANCH="$QUICK_WORKTREE_BRANCH"
EXPECTED_BASE="$QUICK_WORKTREE_BASE"
ALLOWED_BASES_JSON="$QUICK_ALLOWED_BASES"
PLAN_FILES_JSON="$QUICK_FILES_JSON"
PLAN_DELETIONS_JSON="$QUICK_DELETIONS_JSON"
SUMMARY_PATH="$QUICK_SUMMARY_PATH"
WAVE_WORKTREE_MANIFEST="$QUICK_WORKTREE_MANIFEST"
```

Now execute the receipt procedure with the actual host event before either merge call below.

After the host has stopped and the terminal receipt is recorded, the coordinator verifies committed SUMMARY and source output, then integrates **both** modes from its captured root:

```bash
[ "$(git rev-parse --show-toplevel)" = "$ORCH_ROOT" ] || { echo "FATAL: quick integrator root drift" >&2; exit 42; }
engineer_run query worktree.merge-wave --manifest "$QUICK_WORKTREE_MANIFEST" || exit $?
engineer_run query worktree.cleanup-wave --manifest "$QUICK_WORKTREE_MANIFEST" || exit $?
```

A rejected receipt, dirty worker, missing/uncommitted SUMMARY, scope violation or failed merge preserves the checkout and blocks completion. Never use a primary-checkout fallback or force cleanup. Confirm `${QUICK_DIR}/${quick_id}-SUMMARY.md` is present after integration and derive the resulting commit with Git before reporting completion.

**Known Claude Code bug (classifyHandoffIfNeeded):** If executor reports "failed" with error `classifyHandoffIfNeeded is not defined`, this is a Claude Code runtime bug — not a real failure. Check if summary file exists and git log shows commits. If so, reconcile the artifacts, but still obtain the native host terminal receipt and pass the normal record/merge checks before treating the task as successful.

If summary not found, error: "Executor failed to create ${quick_id}-SUMMARY.md"

Note: For quick tasks producing multiple plans (rare), spawn executors in parallel waves per execute-phase patterns.

---

**Step 6.25: Code review (auto)**

Skip this step entirely if `$FULL_MODE` is false.

Read `workflow.code_review` directly with `config-get`; when false skip automatic review. When true, use the independent internal code-reviewer below.

**Scope files from executor's commits:**
```bash
# The quick task's files come from the evaluation-scope resolver: the
# UNION of the commits naming the quick task id, on THIS branch only, planning artifacts and
# lockfiles excluded. A `base..tip` range (the bound) still folds in every unrelated
# commit interleaved inside the task's window (worktree merge-back, a shared tree, another
# session); the union cannot. No commits for this task => empty scope => skip review.
# Exit 69 (UNAVAILABLE) is the resolver's "could not look" (`status: unresolvable`); its JSON carries
# the reason, so the capture must survive it (a bare assignment aborts under `set -e` and drops it).
QUICK_SCOPE_RC=0
QUICK_SCOPE_JSON=$(engineer_run check evaluation-scope --quick "${quick_id}" --include-files --raw 2>/dev/null) || QUICK_SCOPE_RC=$?
if [ "$QUICK_SCOPE_RC" -ne 0 ] && [ "$QUICK_SCOPE_RC" -ne 69 ]; then QUICK_SCOPE_JSON=""; fi
CHANGED_FILES=$(printf '%s' "$QUICK_SCOPE_JSON" | engineer_run query json.lines --field files --separator " " --raw 2>/dev/null || true)
if [ -z "$CHANGED_FILES" ]; then
  # Say WHY the scope is empty (no commits for this task, only excluded paths, or git could not be read).
  QUICK_SCOPE_WHY=$(printf '%s' "$QUICK_SCOPE_JSON" | engineer_run query json.status-reason --raw 2>/dev/null || printf 'unresolvable: no resolver output')
  echo "Quick-task review scope is empty (${QUICK_SCOPE_WHY})."
fi
```

If `CHANGED_FILES` is empty, skip with "No source files changed — skipping code review."

**Invoke review:**
```
Agent(
  prompt="Review these files for bugs, security issues, and code quality.
  Files: ${CHANGED_FILES}
  Output: ${QUICK_DIR}/${quick_id}-REVIEW.md
  Depth: quick",
  subagent_type="code-reviewer",
  model="{reviewer_model}"
)
```

> **ORCHESTRATOR RULE — CODEX RUNTIME**: After calling Agent() above, stop working on this task immediately. Do not read more files, edit code, or run tests related to this task while the subagent is active. Wait for the subagent to return its result. This prevents duplicate work, conflicting edits, and wasted context. Only resume when the subagent result is available.

If review produces findings, display advisory message. **Error handling:** Failures are non-blocking — catch and proceed.

---

<!-- engineer:section id="quick-verification" when="flag:--validate" -->
If `section_manifest` is `null` or `"quick-verification"` is in its `included` list: read and execute `engineer/workflows/quick/steps/quick-verification.md`. Otherwise skip — do not read the file.
<!-- /section -->

---

**Step 7: Update the existing quick-task record**

After the executor's committed output has been integrated, update the same `${quick_id}` created during initialization. The runtime owns quick records and state synchronization. Preserve the actual verification outcome; a blocked or unverified task cannot become passed through a display label.

```bash
QUICK_COMMIT=$(git rev-parse HEAD) || exit $?
if [ "$VALIDATE_MODE" = "true" ]; then
  QUICK_VERIFICATION=$(engineer_run query verification.status "$QUICK_DIR" --pick status) || exit $?
  case "$QUICK_VERIFICATION" in
    passed) QUICK_RECORD_STATUS=passed ;;
    gaps_found|human_needed|missing|stale|unparseable|phase_dir_not_found) QUICK_RECORD_STATUS=blocked ;;
    *) echo "ERROR: unsupported verification status: $QUICK_VERIFICATION" >&2; exit 1 ;;
  esac
else
  QUICK_RECORD_STATUS=complete
  QUICK_VERIFICATION=not_run
fi
engineer_run query quick.update "$quick_id" --status "$QUICK_RECORD_STATUS" --verification "$QUICK_VERIFICATION" --commit "$QUICK_COMMIT" || exit $?
engineer_run quick-tasks-append --quick-id "${quick_id}" --slug "${slug}" --task "${DESCRIPTION}" --status "${QUICK_RECORD_STATUS}" || exit $?
```

When validation ran, the fresh canonical status above corresponds to the earlier `$VERIFICATION_STATUS` display labels: Verified → passed; Needs Review or Gaps → blocked; Unverified → blocked. Keep those display labels for the completion report while storing the actual canonical verification value in the record.

---

**Step 8: Final commit and completion**

Stage and commit quick task artifacts. This step MUST always run — even if the executor already committed some files (e.g. when running without worktree isolation). The `engineer_run query commit` command handles already-committed files gracefully.

Build file list:
- `${QUICK_DIR}/${quick_id}-PLAN.md`
- `${QUICK_DIR}/${quick_id}-SUMMARY.md`
- `.planning/STATE.md`
- If `$DISCUSS_MODE` and context file exists: `${QUICK_DIR}/${quick_id}-CONTEXT.md`
- If `$RESEARCH_MODE` and research file exists: `${QUICK_DIR}/${quick_id}-RESEARCH.md`
- If `$VALIDATE_MODE` and verification file exists: `${QUICK_DIR}/${quick_id}-VERIFICATION.md`
- If `${QUICK_DIR}/${quick_id}-deferred-items.md` exists: `${QUICK_DIR}/${quick_id}-deferred-items.md`

```bash
# Explicitly stage all artifacts before commit — PLAN.md may be untracked
# if the executor ran without worktree isolation and committed docs early
# Filter .planning/ files from staging if commit_docs is disabled
COMMIT_DOCS=$(engineer_run query config-get commit_docs --raw 2>/dev/null || echo "true")
if [ "$COMMIT_DOCS" = "false" ]; then
  file_list_filtered=$(echo "${file_list}" | tr ' ' '\n' | grep -v '^\.planning/' | tr '\n' ' ')
  git add ${file_list_filtered} 2>/dev/null
else
  git add ${file_list} 2>/dev/null
fi
engineer_run query commit "docs(quick-${quick_id}): ${DESCRIPTION}" --files ${file_list}
```

Get final commit hash:
```bash
commit_hash=$(git rev-parse --short HEAD)
```

Display completion output:

**If `$VALIDATE_MODE`:**
```
---

Engineer > QUICK TASK COMPLETE (VALIDATED)

Quick Task ${quick_id}: ${DESCRIPTION}

${RESEARCH_MODE ? 'Research: ' + QUICK_DIR + '/' + quick_id + '-RESEARCH.md' : ''}
Summary: ${QUICK_DIR}/${quick_id}-SUMMARY.md
Verification: ${QUICK_DIR}/${quick_id}-VERIFICATION.md (${VERIFICATION_STATUS})
Commit: ${commit_hash}

---

Ready for next task: /quick
```

**If NOT `$VALIDATE_MODE`:**
```
---

Engineer > QUICK TASK COMPLETE

Quick Task ${quick_id}: ${DESCRIPTION}

${RESEARCH_MODE ? 'Research: ' + QUICK_DIR + '/' + quick_id + '-RESEARCH.md' : ''}
Summary: ${QUICK_DIR}/${quick_id}-SUMMARY.md
Commit: ${commit_hash}

---

Ready for next task: /quick
```

</process>

<success_criteria>
- [ ] ROADMAP.md validation passes
- [ ] User provides task description
- [ ] `--full`, `--validate`, `--discuss`, and `--research` flags parsed from arguments when present
- [ ] `--full` sets all booleans (`$FULL_MODE`, `$DISCUSS_MODE`, `$RESEARCH_MODE`, `$VALIDATE_MODE`)
- [ ] Slug generated (lowercase, hyphens, max 40 chars)
- [ ] Quick ID generated (YYMMDD-xxx format, 2s Base36 precision)
- [ ] Directory created at `.planning/quick/YYMMDD-xxx-slug/`
- [ ] (--discuss) Gray areas identified and presented, decisions captured in `${quick_id}-CONTEXT.md`
- [ ] (--research) Research agent spawned, `${quick_id}-RESEARCH.md` created
- [ ] `${quick_id}-PLAN.md` created by planner (honors CONTEXT.md decisions when --discuss, uses RESEARCH.md findings when --research)
- [ ] (--validate) Plan checker validates plan, revision loop capped at 2
- [ ] `${quick_id}-SUMMARY.md` created by executor
- [ ] (--validate) `${quick_id}-VERIFICATION.md` created by verifier
- [ ] STATE.md updated with quick task row (Status column when --validate)
- [ ] Artifacts committed
</success_criteria>
