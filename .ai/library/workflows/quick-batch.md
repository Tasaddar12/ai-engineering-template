@.ai/library/references/response-language-directive.md
<purpose>
Batch several `/workflow:quick`-shaped tasks together (#3676, epic #3344, ADR-1239
"Quick-batch binding"). ONE coordinator (this workflow) owns every shared
write — `BATCH.json`, STATE.md, worktree create/merge/cleanup — and never
delegates them to a leaf. Leaves (planner/researcher/checker/executor/
verifier) return structured results only; they never invoke `/workflow:quick`,
never touch `BATCH.json`, and never write STATE.md/ROADMAP.md themselves
(single-writer invariant).

Dispatch decisions (effective concurrency, deterministic merge order, spawn
backpressure, failure/verification routing) are computed by the pure
`quick-batch-dispatch.cts` module (via the `quick-batch` CLI verbs) — this
workflow never re-derives that logic inline.
</purpose>

<required_reading>
Read all files referenced by the invoking prompt's execution_context before starting.
</required_reading>

<available_agent_types>
Valid Workflow subagent types (use exact names — do not fall back to 'general-purpose'):
- phase-researcher — Researches technical approaches for an item
- planner — Creates a plan for one item (`quick-batch` mode)
- plan-checker — Reviews one item's plan before execution
- executor — Executes one item's plan, commits, creates SUMMARY.md
- verifier — Verifies one item's goal achievement
</available_agent_types>

<process>
**Step 1: Parse arguments, resolve mode**

```bash
_Workflow_SHIM_NAME="workflow-tools.cjs"; _Workflow_RUNTIME_ROOT="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"; Workflow_TOOLS="${_Workflow_RUNTIME_ROOT}/workflow-core/bin/${_Workflow_SHIM_NAME}"; _workflow_at() { for _p; do if [ -f "$_p" ]; then Workflow_TOOLS="$_p"; return 0; fi; done; return 1; }; if _workflow_at "${_Workflow_RUNTIME_ROOT}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${_Workflow_RUNTIME_ROOT}/.claude/workflow-core/bin/${_Workflow_SHIM_NAME}" "${_Workflow_RUNTIME_ROOT}/.codex/workflow-core/bin/${_Workflow_SHIM_NAME}"; then workflow_run() { node "$Workflow_TOOLS" "$@"; }; elif unset -f workflow_run; _G="$(command -v workflow_run)"; then Workflow_TOOLS="$_G"; workflow_run() { "$Workflow_TOOLS" "$@"; }; elif _workflow_at "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${HERMES_HOME:-$HOME/.hermes}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CURSOR_CONFIG_DIR:-$HOME/.cursor}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CODEX_HOME:-$HOME/.codex}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${GEMINI_CONFIG_DIR:-$HOME/.gemini}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${COPILOT_CONFIG_DIR:-$HOME/.copilot}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${WINDSURF_CONFIG_DIR:-$HOME/.codeium/windsurf}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${AUGMENT_CONFIG_DIR:-$HOME/.augment}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${TRAE_CONFIG_DIR:-$HOME/.trae}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${QWEN_CONFIG_DIR:-$HOME/.qwen}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CODEBUDDY_CONFIG_DIR:-$HOME/.codebuddy}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CLINE_CONFIG_DIR:-$HOME/.cline}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${GROK_AGENTS_HOME:-$HOME/.agents}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${ANTIGRAVITY_CONFIG_DIR:-$HOME/.gemini/antigravity}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${OPENCODE_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/opencode}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${KILO_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/kilo}/workflow-core/bin/${_Workflow_SHIM_NAME}"; then workflow_run() { node "$Workflow_TOOLS" "$@"; }; else echo "ERROR: workflow-tools.cjs not found at $Workflow_TOOLS and workflow_run is not on PATH. Run: npx -y @openworkflow/workflow-core@latest --claude --local" >&2; exit 1; fi; Workflow_IDENTITY_STATUS=unverified; case "$(workflow_run runtime-identity --raw 2>/dev/null || true)" in '{"packageName":"@openworkflow/workflow-core"'*'}') Workflow_IDENTITY_STATUS=ok;; esac; export Workflow_IDENTITY_STATUS; [ "$Workflow_IDENTITY_STATUS" = ok ] || echo "WARNING: \"$Workflow_TOOLS\" did not prove it is @openworkflow/workflow-core - it is either a different package or an @openworkflow/workflow-core older than the runtime-identity verb. See docs/how-to/diagnose-a-foreign-workflow-tools.md" >&2; if [ -n "${CLAUDE_ENV_FILE:-}" ] && [ -n "${Workflow_TOOLS:-}" ]; then printf "export PATH='%s':\"\$PATH\"\n" "${Workflow_TOOLS%/*}" >> "$CLAUDE_ENV_FILE" 2>/dev/null || true; fi
RESPONSE_LANGUAGE=$(workflow_run query config-get response_language --raw --default "" 2>/dev/null || echo "")
```

**If `response_language` is set:** all user-facing questions/prompts/explanations MUST be presented in `{response_language}`. Technical terms, code, file paths, and subagent prompts stay in English.

Validate `$ARGUMENTS` through the CLI's own grammar — never re-derive it inline (single source of truth: `parseQuickBatchArgs`, `src/quick-batch-dispatch.cts`). `$ARGUMENTS` is raw, attacker-influenced task text — pass it as ONE quoted argument via `--text` so the shell never word-splits or glob-expands it; `quick-batch parse-args` does the whitespace split itself, in Node, after the shell is done:

```bash
QB_PARSE_JSON=$(workflow_run quick-batch parse-args --raw --text "$ARGUMENTS")
QB_PARSE_RC=$?
if [ $QB_PARSE_RC -ne 0 ]; then
  echo "$QB_PARSE_JSON" >&2
  exit 1
fi
if [[ "$QB_PARSE_JSON" == @file:* ]]; then QB_PARSE_JSON=$(cat "${QB_PARSE_JSON#@file:}"); fi
```

Parse `$QB_PARSE_JSON` for `jobs` (`"auto"` or an integer), `validate` (bool), `research` (bool), `resume` (batch id or null). Store as `$JOBS`, `$VALIDATE_MODE`, `$RESEARCH_MODE`, `$RESUME_BATCH_ID`.

Extract the raw task-list text / `--file <path>` from `$ARGUMENTS` (everything that is not `--jobs <v>`, `--validate`, `--research`, `--resume <id>`, or `--file <path>`'s own flag pair).

```bash
VALIDATE_PARAM=""; if [ "$VALIDATE_MODE" = true ]; then VALIDATE_PARAM="--validate"; fi
RESEARCH_PARAM=""; if [ "$RESEARCH_MODE" = true ]; then RESEARCH_PARAM="--research"; fi
INIT=$(workflow_run query init.quick-batch $VALIDATE_PARAM $RESEARCH_PARAM)
if [[ "$INIT" == @file:* ]]; then INIT=$(cat "${INIT#@file:}"); fi
AGENT_SKILLS_PLANNER=$(workflow_run query agent-skills planner)
AGENT_SKILLS_EXECUTOR=$(workflow_run query agent-skills executor)
AGENT_SKILLS_CHECKER=$(workflow_run query agent-skills plan-checker)
AGENT_SKILLS_VERIFIER=$(workflow_run query agent-skills verifier)
AGENT_SKILLS_RESEARCHER=$(workflow_run query agent-skills phase-researcher)
```

Parse `$INIT` for: `planner_model`, `executor_model`, `checker_model`, `verifier_model`, `researcher_model`, `commit_docs`, `quick_dir`, `quick_batches_dir`, `roadmap_exists`, `planning_exists`.

<!-- #2517 model-omit-on-inherit -->

> **Model omission (#2517).** Every `Agent()` dispatch below (planner, researcher, plan-checker, executor, verifier) MUST omit the `model` parameter entirely when the value it would carry (`planner_model`, `checker_model`, `executor_model`, `verifier_model`, `researcher_model`) is `"inherit"` or empty. An empty value 404s on runtimes without native tier aliases — the default on non-Claude runtimes, where the installer writes `resolve_model_ids:"omit"`. Omitting it inherits the orchestrator's model. See @.ai/library/references/model-profile-resolution.md.

```bash
STATE_PATH="${quick_dir%/quick}/STATE.md"
PROJECT_PATH="${quick_dir%/quick}/PROJECT.md"
USE_WORKTREES=$(workflow_run query config-get workflow.use_worktrees --raw 2>/dev/null || echo "true")
RUNTIME=$(workflow_run query config-get runtime --default claude --raw 2>/dev/null || echo "claude")
```

**If `roadmap_exists` is false:** Error — quick-batch requires an active project with ROADMAP.md. Run `/workflow:new-project` first.

If the project uses git submodules, parse `SUBMODULE_PATHS` from `.gitmodules` exactly as `/workflow:quick` does (a fail-loud commit-time guard, applied per item at commit time — see `.ai/library/workflows/quick.md` Step 2 for the identical block, reused verbatim below):

```bash
if [ -f .gitmodules ]; then
  SUBMODULE_PATHS=$(git config --file .gitmodules --get-regexp '^submodule\..*\.path$' 2>/dev/null | awk '{print $2}')
else
  SUBMODULE_PATHS=""
fi
```

**Resolve capacity now (#3676 design row 3-4).** `--jobs auto`/omitted uses this
value alone; `--jobs N` is capped by it (`min(taskCount, N, capacity)` — the
`quick-batch effective-concurrency` verb, called per-wave below, does the
arithmetic; this is only the raw resolve):
```bash
CAPACITY=$(workflow_run query dispatch-capacity --raw 2>/dev/null || echo 1)
```

**Resolve isolation now (row 6, 20-22).** Read
@.ai/library/references/dispatch-isolation-gate.md and run its `Resolve
ISOLATION`, `Single-agent dispatch sites`, and `Resolve the harness flag`
blocks in order; they set `ISOLATION`/`HARNESS_FLAG` via `query
dispatch-isolation`. `ISOLATION` gates every worktree decision below —
substitute `{harnessFlag}` in Step 6's `Agent()` with `$HARNESS_FLAG`+comma
when `ISOLATION = "harness-worktree"`, else empty.

If `USE_WORKTREES` is not `"false"`, sweep orphaned worktrees before dispatching anything (mirrors `/workflow:quick`'s own startup sweep):
```bash
if [ "$USE_WORKTREES" != "false" ]; then
  workflow_run query worktree.reap-orphans 2>/dev/null || true
fi
```

Display banner:
```
### Workflow ► QUICK BATCH
◆ jobs=${JOBS} validate=${VALIDATE_MODE} research=${RESEARCH_MODE}${RESUME_BATCH_ID:+ resume=${RESUME_BATCH_ID}}
```

---

**Step 2: Resume or create**

If `$RESUME_BATCH_ID` is set: read and execute `.ai/library/workflows/quick-batch/steps/resume-mode.md`.
It loads the batch via `quick-batch
resume`, refuses closed on an unknown batch id or a diverged base revision,
and sets `$BATCH_ID`/`$BATCH_MANIFEST_JSON` for the steps below. Task-list
parsing and `quick-batch create` are skipped entirely.

Otherwise: read and execute `.ai/library/workflows/quick-batch/steps/batch-init.md`.
It parses the task list (inline or `--file`) and creates the
batch via `quick-batch create`, setting the same `$BATCH_ID`/
`$BATCH_MANIFEST_JSON` pair.

Either path converges on the same post-condition — continue to Step 3.

---

<!-- workflow:section id="research-phase" when="flag:--research" -->
If `section_manifest` is `null` or `"research-phase"` is in its `included` list: read and execute `.ai/library/workflows/quick-batch/steps/research-phase.md`. Otherwise skip — do not read the file.
<!-- /workflow:section -->

---

**Step 4: Per-DAG-layer planning**

Read and execute `.ai/library/workflows/quick-batch/steps/planner-wave.md`. It
dispatches a planner per eligible item (one `Agent()` per message, full task
catalog in every prompt), persists parsed `depends_on`/`files_modified` via
`quick-batch update` after each layer, and — when `$VALIDATE_MODE` — runs the
per-item plan-checker loop (`.ai/library/workflows/quick-batch/steps/plan-checker-loop.md`)
before advancing to the next layer.

---

**Step 6: Worktree create + executor dispatch**

Read and execute `.ai/library/workflows/quick-batch/steps/worktree-dispatch.md`.
Worktree create/executor dispatch is serialized per item (one `git worktree
add` in flight at a time); already-created worktrees run concurrently up to
the effective MUTATING-wave concurrency.

---

**Step 7: Deterministic merge**

Read and execute `.ai/library/workflows/quick-batch/steps/merge-wave.md`. Merges
apply strictly in the wave's original dispatch order (`quick-batch
merge-eligible`), never completion order.

---

<!-- workflow:section id="verification-wave" when="flag:--validate" -->
If `section_manifest` is `null` or `"verification-wave"` is in its `included` list: read and execute `.ai/library/workflows/quick-batch/steps/verification-wave.md`. Otherwise skip — do not read the file.
<!-- /workflow:section -->

---

**Step 9: Completion**

Read and execute `.ai/library/workflows/quick-batch/steps/completion.md`. Calls
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


<!-- LOCAL-ADOPTION:START -->
## Local adoption — read before using this source

This complete authoring guide retains its source content, examples, and methods.
Only recorded namespace/reference substitutions and explicit local conflict
corrections have been made. Source attribution and exact original hashes are
isolated in `.ai/library/THIRD-PARTY-NOTICES.md` and `PROVENANCE.json`.

Read `.ai/library/README.md` for the local producer/consumer mapping and execution
boundary, `.ai/references/template-adaptation.md` for local conflict decisions,
and `.ai/runtime/TEMPLATE-CONTRACT.md` for additive local artifact
fields. Project records live in `.planning/`; reusable guidance lives in `.ai/`.
The active lifecycle uses `.ai/commands/` and `.ai/runtime/phase.py` with
`.planning/config.yaml`. The retained `config.json`, `/workflow:*` commands, tool
names, hooks, and Node CLI examples describe supporting source capabilities;
this import does not install or activate them. Source catalog pointers in examples
identify provenance, not executable command arguments. Retained specialty workflows are full source
guidance for explicit future integration, not promises of installed features.
Local rules, assigned worktrees, recorded authorization, runtime ownership and
verification safeguards govern execution. The local runtime never merges.
<!-- LOCAL-ADOPTION:END -->
