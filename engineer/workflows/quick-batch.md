Read and execute `engineer/workflows/_runtime-launcher.snippet.sh` before runtime calls. Resolve the configured response language with `engineer_run query config-get response_language --raw`; when an init result already supplies `response_language`, use that value. Apply this language to all user-facing prose: narration between tool calls, status updates, progress notes, questions, explanations and reported findings. Preserve code, paths, command names, identifiers, machine-readable keys and required protocol markers verbatim. Do not translate source code or a consumer-required sentinel.
<purpose>
Batch several `/quick`-shaped tasks together (#3676, epic #3344, ADR-1239
"Quick-batch binding"). ONE coordinator (this workflow) owns every shared
write — `BATCH.json`, STATE.md, worktree create/merge/cleanup — and never
delegates them to a leaf. Leaves (planner/researcher/checker/executor/
verifier) return structured results only; they never invoke `/quick`,
never touch `BATCH.json`, and never write STATE.md/ROADMAP.md themselves
(single-writer invariant).

Dispatch decisions (effective concurrency, deterministic merge order, spawn
backpressure, failure/verification routing) are computed by the pure
`engineer/bin/lib/quick_batch.py` module (via the `quick-batch` CLI verbs) — this
workflow never re-derives that logic inline.
</purpose>

<required_reading>
Read all files referenced by the invoking prompt's execution_context before starting.
</required_reading>

<available_agent_types>
Valid Claude/Codex subagent types (use exact names — do not fall back to 'general-purpose'):
- phase-researcher — Researches technical approaches for an item
- planner — Creates a plan for one item (`quick-batch` mode)
- plan-checker — Reviews one item's plan before execution
- executor — Executes one item's plan, commits, creates SUMMARY.md
- verifier — Verifies one item's goal achievement
</available_agent_types>

<authority>
An explicit human /quick-batch invocation authorizes only its listed outcomes. No chain may use this command to evade phase implementation authority. Resolve routine implementation choices within delegated discretion; locked decisions and human-UAT requirements block only dependent entries. Never ask a routine proceed menu.
</authority>
<process>
**Step 1: Parse arguments, resolve mode**

```bash
source engineer/workflows/_runtime-launcher.snippet.sh
RESPONSE_LANGUAGE=$(engineer_run query config-get response_language --raw --default "" 2>/dev/null || echo "")
```

**If `response_language` is set:** all user-facing questions/prompts/explanations MUST be presented in `{response_language}`. Technical terms, code, file paths, and subagent prompts stay in English.

Validate the command's `<arguments>` block through the CLI's own grammar — never re-derive it inline (single source of truth: `parse`, `engineer/bin/lib/quick_batch.py`). The block is raw, attacker-influenced task text — feed it on STDIN through a QUOTED heredoc (`--stdin`), never as a shell argument, so the shell never parses, expands or word-splits it; `query quick-batch.parse-args` does the whitespace split itself, in Python, after the shell is done. Paste the block's exact contents between the markers:

```bash
QB_PARSE_FILE=$(mktemp)
engineer_run query quick-batch.parse-args --raw --stdin > "$QB_PARSE_FILE" 2>&1 <<'GSD_QUICK_BATCH_ARGS_END'
<the exact contents of the `<arguments>` block, verbatim>
GSD_QUICK_BATCH_ARGS_END
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
INIT=$(engineer_run query init.quick-batch)
```
Read quick_dir, open_batches, capacity and isolation from the actual bundle. Use init.quick for ordinary project readiness when needed; never assume absent model aliases. Immediately before EVERY Agent dispatch resolve `engineer_run query resolve-model ROLE --raw` and `engineer_run query resolve-effort ROLE --raw`. Pass model/effort inline, omitting either whose value is inherit. Resolve agent-skills for that exact role without unsupported workspace flags. Only Claude and Codex are supported.

STATE_PATH and PROJECT_PATH are the runtime planning root's STATE.md and PROJECT.md. Read roadmap_exists from init.quick, not an invented init.quick-batch field.

**If `roadmap_exists` is false:** Error — quick-batch requires an active project with ROADMAP.md. Run `/new-project` first.

If the project uses git submodules, parse `SUBMODULE_PATHS` from `.gitmodules` exactly as `/quick` does (a fail-loud commit-time guard, applied per item at commit time — see `engineer/workflows/quick.md` Step 2 for the identical block, reused verbatim below):

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
CAPACITY=$(engineer_run query dispatch-capacity --raw) || exit 1
# Cap CAPACITY by the host-reported available worker slots; never assume extra capacity.
```

**Resolve isolation now.** Run `engineer_run query dispatch-isolation --raw` and require exactly harness-worktree or orchestrator-worktree. Any failure/unknown mode blocks dispatch. Never downgrade isolation. Run `engineer_run query worktree.reap-orphans` for stale administrative records; preserve actual worktrees.

**Open session before creating batch records or writing scratch input.** Inspect session.status and the selected batch's lineage. Reuse its matching real quick session; otherwise `engineer_run query session.open quick "batch-${BATCH_LABEL}"`. Enter the returned path, verify its root/branch and capture SESSION_WORKTREE/SESSION_BRANCH/SESSION_BASE. Stop if isolation fails. Re-run init.quick-batch there. Every source merge lands on this session branch; the primary/shared checkout receives no edits. Task input outside that checkout must be read safely and materialized as literal data inside the session before create.

Display banner:
```
### GSD ► QUICK BATCH
◆ jobs=${JOBS} validate=${VALIDATE_MODE} research=${RESEARCH_MODE}${RESUME_BATCH_ID:+ resume=${RESUME_BATCH_ID}}
```

---

**Step 2: Resume or create**

If `$RESUME_BATCH_ID` is set: read and execute `engineer/workflows/quick-batch/steps/resume-mode.md`.
It loads the batch via `quick-batch
resume`, refuses closed on an unknown batch id or a diverged base revision,
and sets `$BATCH_ID`/`$BATCH_MANIFEST_JSON` for the steps below. Task-list
parsing and `query quick-batch.create` are skipped entirely.

Otherwise: read and execute `engineer/workflows/quick-batch/steps/batch-init.md`.
It parses the task list (inline or `--file`) and creates the
batch via `query quick-batch.create`, setting the same `$BATCH_ID`/
`$BATCH_MANIFEST_JSON` pair.

Either path converges on the same post-condition — continue to Step 3.

---

<!-- gsd:section id="research-phase" when="flag:--research" -->
If RESEARCH_MODE is true: read and execute `engineer/workflows/quick-batch/steps/research-phase.md`. Otherwise skip — do not read the file.
<!-- /section -->

---

**Step 4: Per-DAG-layer planning**

Read and execute `engineer/workflows/quick-batch/steps/planner-wave.md`. It
dispatches a planner per eligible item (one `Agent()` per message, full task
catalog in every prompt), persists parsed `depends_on`/`files_modified` via
`query quick-batch.update` after each layer, and — when `$VALIDATE_MODE` — runs the
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

<!-- gsd:section id="verification-wave" when="flag:--validate" -->
If VALIDATE_MODE is true: read and execute `engineer/workflows/quick-batch/steps/verification-wave.md`. Otherwise skip — do not read the file.
<!-- /section -->

---

**Step 9: Completion**

Read and execute `engineer/workflows/quick-batch/steps/completion.md`. Calls
quick.update only for genuinely complete items, records batch aggregate status through quick-batch.complete, updates STATE through runtime verbs, and executes deliver_session.

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
- [ ] Mutating waves require mandatory isolation and obey both runtime and host capacity
- [ ] Merges apply in deterministic wave order, never completion order
- [ ] (--validate) Verifier dispatched per item post-merge; `human_needed` never completes the item, `gaps_found` fails it without rollback or retry
- [ ] A merge_failed/scope_violation item is marked failed with the worktree PRESERVED
- [ ] quick.update called only for genuinely complete items; STATE updated through runtime; artifacts committed
</success_criteria>
