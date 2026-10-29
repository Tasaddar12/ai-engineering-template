@~/.claude/engineer/references/run-resolver.md

@~/.claude/engineer/references/response-language-directive.md
<purpose>
Batch several `/quick`-shaped tasks together.
ONE coordinator (this workflow) owns every shared
write — `BATCH.json`, STATE.md, worktree create/merge/cleanup — and never
delegates them to a leaf. Leaves (planner/researcher/checker/executor/
verifier) return structured results only; they never invoke `/quick`,
never touch `BATCH.json`, and never write STATE.md/ROADMAP.md themselves
(single-writer invariant).

Dispatch decisions (effective concurrency, deterministic merge order, spawn
backpressure, failure/verification routing) are computed by the Python
`engineer/bin/lib/quick_batch.py` module through the registered
`quick-batch.effective-concurrency`, `quick-batch.merge-routing`,
`quick-batch.spawn-plan`, and `quick-batch.verification-routing` verbs — this
workflow never re-derives that logic inline.
</purpose>

<required_reading>
Read all files referenced by the invoking prompt's execution_context before starting.
</required_reading>

<available_agent_types>
Valid Engineer subagent types (use exact names — do not fall back to 'general-purpose'):
- phase-researcher — Researches technical approaches for an item
- planner — Creates a plan for one item (`quick-batch` mode)
- plan-checker — Reviews one item's plan before execution
- executor — Executes one item's plan, commits, creates SUMMARY.md
- verifier — Verifies one item's goal achievement
</available_agent_types>

<process>
**Step 1: Parse arguments, resolve mode**

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

**If `response_language` is set:** all user-facing questions/prompts/explanations MUST be presented in `{response_language}`. Technical terms, code, file paths, and subagent prompts stay in English.

Validate the command's `<arguments>` block through the CLI's own grammar — never re-derive it inline (single source of truth: `quick-batch parse-args`, implemented in `engineer/bin/lib/quick_batch.py`). The block is raw, attacker-influenced task text — feed it on STDIN through a QUOTED heredoc (`--stdin`), never as a shell argument, so the shell never parses, expands or word-splits it; `quick-batch parse-args` performs the whitespace split in the Python runtime after the shell is done. Paste the block's exact contents between the markers:

```bash
QB_PARSE_FILE=$(mktemp)
engineer_run quick-batch parse-args --raw --stdin > "$QB_PARSE_FILE" 2>&1 <<'ENGINEER_QUICK_BATCH_ARGS_END'
<the exact contents of the `<arguments>` block, verbatim>
ENGINEER_QUICK_BATCH_ARGS_END
QB_PARSE_RC=$?
QB_PARSE_JSON=$(cat "$QB_PARSE_FILE"); rm -f "$QB_PARSE_FILE"
if [ $QB_PARSE_RC -ne 0 ]; then
  echo "$QB_PARSE_JSON" >&2
  exit 1
fi
if [[ "$QB_PARSE_JSON" == @file:* ]]; then QB_PARSE_JSON=$(cat "${QB_PARSE_JSON#@file:}"); fi
```

Parse `$QB_PARSE_JSON` for `jobs` (`"auto"` or an integer), `validate` (bool), `research` (bool), `resume` (batch id or null). Store as `$JOBS`, `$VALIDATE_MODE`, `$RESEARCH_MODE`, `$RESUME_BATCH_ID`.

Extract the raw task-list text / `--file <path>` from the `<arguments>` block (everything that is not `--jobs <v>`, `--validate`, `--research`, `--resume <id>`, or `--file <path>`'s own flag pair).

```bash
IFS= read -rd '' ENGINEER_ARGS <<'ENGINEER_ARGS_END' || true
$ARGUMENTS
ENGINEER_ARGS_END
ENGINEER_ARGS=${ENGINEER_ARGS%$'\n'}
VALIDATE_PARAM=""; if [ "$VALIDATE_MODE" = true ]; then VALIDATE_PARAM="--validate"; fi
RESEARCH_PARAM=""; if [ "$RESEARCH_MODE" = true ]; then RESEARCH_PARAM="--research"; fi
ENGINEER_WS=$(echo " $ENGINEER_ARGS" | sed -nE 's/.* --ws +([A-Za-z0-9][A-Za-z0-9._-]*).*/--ws \1/p' | head -n 1)
INIT=$(engineer_run query init.quick-batch ${ENGINEER_WS:+--ws=${ENGINEER_WS##* }} $VALIDATE_PARAM $RESEARCH_PARAM)
if [[ "$INIT" == @file:* ]]; then INIT=$(cat "${INIT#@file:}"); fi
AGENT_SKILLS_PLANNER=$(engineer_run query agent-skills planner ${ENGINEER_WS:+--ws=${ENGINEER_WS##* }})
AGENT_SKILLS_EXECUTOR=$(engineer_run query agent-skills executor ${ENGINEER_WS:+--ws=${ENGINEER_WS##* }})
AGENT_SKILLS_CHECKER=$(engineer_run query agent-skills plan-checker ${ENGINEER_WS:+--ws=${ENGINEER_WS##* }})
AGENT_SKILLS_VERIFIER=$(engineer_run query agent-skills verifier ${ENGINEER_WS:+--ws=${ENGINEER_WS##* }})
AGENT_SKILLS_RESEARCHER=$(engineer_run query agent-skills phase-researcher ${ENGINEER_WS:+--ws=${ENGINEER_WS##* }})
```

Parse `$INIT` for: `planner_model`, `executor_model`, `checker_model`, `verifier_model`, `researcher_model`, `commit_docs`, `quick_dir`, `quick_batches_dir`, `roadmap_exists`, `planning_exists`.

<!-- model-omit-on-inherit -->

> **Model omission.** Every `Agent()` dispatch below (planner, researcher, plan-checker, executor, verifier) MUST omit the `model` parameter entirely when the value it would carry (`planner_model`, `checker_model`, `executor_model`, `verifier_model`, `researcher_model`) is `"inherit"` or empty. An empty value 404s on runtimes without native tier aliases — the default on non-Claude runtimes, where the installer writes `resolve_model_ids:"omit"`. Omitting it inherits the orchestrator's model. See @~/.claude/engineer/references/model-profile-resolution.md.

```bash
STATE_PATH="${quick_dir%/quick}/STATE.md"
PROJECT_PATH="${quick_dir%/quick}/PROJECT.md"
USE_WORKTREES=$(engineer_run query config-get workflow.use_worktrees --raw 2>/dev/null || echo "true")
RUNTIME=$(engineer_run query config-get runtime --default claude --raw 2>/dev/null || echo "claude")
```

**If `roadmap_exists` is false:** Error — quick-batch requires an active project with ROADMAP.md. Run `/new-project` first.

If the project uses git submodules, parse `SUBMODULE_PATHS` from `.gitmodules` exactly as `/quick` does (a fail-loud commit-time guard, applied per item at commit time — see `engineer/workflows/quick.md` Step 2 for the identical block, reused verbatim below):

```bash
if [ -f .gitmodules ]; then
  SUBMODULE_PATHS=$(git config --file .gitmodules --get-regexp '^submodule\..*\.path$' 2>/dev/null | awk '{print $2}')
else
  SUBMODULE_PATHS=""
fi
```

**Resolve capacity now.** `--jobs auto`/omitted uses this
value alone; `--jobs N` is capped by it (`min(taskCount, N, capacity)` — the
`quick-batch effective-concurrency` verb, called per-wave below, does the
arithmetic; this is only the raw resolve):
```bash
CAPACITY=$(engineer_run query dispatch-capacity --raw 2>/dev/null || echo 1)
```

**Resolve isolation now.** Read
@~/.claude/engineer/references/dispatch-isolation-gate.md and run its `Resolve
ISOLATION`, `Single-agent dispatch sites`, and `Resolve the harness flag`
blocks in order; they set `ISOLATION`/`HARNESS_FLAG` via `query
dispatch-isolation`. `ISOLATION` gates every worktree decision below —
substitute `{harnessFlag}` in Step 6's `Agent()` with `$HARNESS_FLAG`+comma
when `ISOLATION = "harness-worktree"`, else empty.

If `USE_WORKTREES` is not `"false"`, sweep orphaned worktrees before dispatching anything (mirrors `/quick`'s own startup sweep):
```bash
if [ "$USE_WORKTREES" != "false" ]; then
  engineer_run query worktree.reap-orphans 2>/dev/null || true
fi
```

Display banner:
```
### Engineer ► QUICK BATCH
◆ jobs=${JOBS} validate=${VALIDATE_MODE} research=${RESEARCH_MODE}${RESUME_BATCH_ID:+ resume=${RESUME_BATCH_ID}}
```

---

**Step 2: Resume or create**

If `$RESUME_BATCH_ID` is set: read and execute `engineer/workflows/quick-batch/steps/resume-mode.md`.
It loads the batch via `quick-batch
resume`, refuses closed on an unknown batch id or a diverged base revision,
and sets `$BATCH_ID`/`$BATCH_MANIFEST_JSON` for the steps below. Task-list
parsing and `quick-batch create` are skipped entirely.

Otherwise: read and execute `engineer/workflows/quick-batch/steps/batch-init.md`.
It parses the task list (inline or `--file`) and creates the
batch via `quick-batch create`, setting the same `$BATCH_ID`/
`$BATCH_MANIFEST_JSON` pair.

Either path converges on the same post-condition — continue to Step 3.

---

<!-- engineer:section id="research-phase" when="flag:--research" -->
If `section_manifest` is `null` or `"research-phase"` is in its `included` list: read and execute `engineer/workflows/quick-batch/steps/research-phase.md`. Otherwise skip — do not read the file.
<!-- /section -->

---

**Step 4: Per-DAG-layer planning**

Read and execute `engineer/workflows/quick-batch/steps/planner-wave.md`. It
dispatches a planner per eligible item (one `Agent()` per message, full task
catalog in every prompt), persists parsed `depends_on`/`files_modified` via
`quick-batch update` after each layer, and — when `$VALIDATE_MODE` — runs the
per-item plan-checker loop (`engineer/workflows/quick-batch/steps/plan-checker-loop.md`)
before advancing to the next layer.

---

**Step 6: Worktree create + executor dispatch**

Read and execute `engineer/workflows/quick-batch/steps/worktree-dispatch.md`.
Worktree create/executor dispatch is serialized per item (one `git worktree
add` in flight at a time); already-created worktrees run concurrently up to
the effective MUTATING-wave concurrency.

---

**Step 7: Deterministic merge**

Read and execute `engineer/workflows/quick-batch/steps/merge-wave.md`. Merges
apply strictly in the wave's original dispatch order (`quick-batch
merge-eligible`), never completion order.

---

<!-- engineer:section id="verification-wave" when="flag:--validate" -->
If `section_manifest` is `null` or `"verification-wave"` is in its `included` list: read and execute `engineer/workflows/quick-batch/steps/verification-wave.md`. Otherwise skip — do not read the file.
<!-- /section -->

---

**Step 9: Completion**

Read and execute `engineer/workflows/quick-batch/steps/completion.md`. Calls
`completeQuickItem` (via `quick-batch complete`) only for a genuinely
complete item, updates STATE.md, and prints the final batch report.

</process>

<success_criteria>
- [ ] `--discuss`/`--full` rejected with a usage error before any dispatch
- [ ] A malformed `--jobs` value rejected before any dispatch
- [ ] `--resume <batch-id>` skips task-list parsing, dispatches only eligible items
- [ ] Task list parsed (inline or `--file`, ≥2 items) and batch created otherwise
- [ ] Planner dispatched per eligible item per DAG layer, full task catalog in prompt, `depends_on`/`files_modified` requested ALWAYS
- [ ] (--research) Researcher dispatched per item before planning
- [ ] (--validate) Plan-checker loop runs per item after planning (≤2 iterations)
- [ ] Worktree create/merge/cleanup serialized; concurrent leaves inside already-created worktrees
- [ ] `isolation == none` forces a mutating wave's concurrency to 1; a research-only wave is unaffected
- [ ] Merges apply in deterministic wave order, never completion order
- [ ] (--validate) Verifier dispatched per item post-merge; `human_needed` never completes the item, `gaps_found` fails it without rollback or retry
- [ ] A merge_failed/scope_violation item is marked failed with the worktree PRESERVED
- [ ] `completeQuickItem` called only for genuinely complete items; STATE.md updated; artifacts committed
</success_criteria>
