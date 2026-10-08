<!-- workflow
step: execute
agent-roles: orchestrator, coder, code-reviewer
produces: {NN}-{MM}-SUMMARY.md, commits, roadmap plan ticks
consumes: {NN}-{MM}-PLAN.md, CONTEXT.md, STATE.md
-->

<purpose>
Execute a phase's plans through readiness-routed committed chunks. Dispatch
isolated coders for ready assignments, gate each immutable chunk, integrate it,
confirm the phase goal was achieved, then tick the roadmap.

The orchestrator routes and integrates. It does not write the implementation.

**Carry the phase through to publication in this session.** When execution
finishes, invoke the `verify-work` skill for this phase (`/verify-work {N}`); it
invokes the `ship` skill on a pass.

- Never tell the user to resume, `/clear`, start a fresh session, or run
  `/verify-work` or `/ship`.
- Never stop because a `CONTEXT HANDOFF` advisory fired; it applies to subagents.
- Route issues per [issues found while working](../RULES.md#issues-found-while-working).
  Ask the user only the `/ship` merge question.
</purpose>

<required_reading>
@~/.ai/references/worktree-sessions.md
@~/.ai/references/universal-anti-patterns.md
@~/.ai/references/methods/checkpoints.md
@~/.ai/references/methods/gates.md
@~/.ai/references/worktree-recovery-policy.md
</required_reading>

<isolation_reading>
Isolation is always on, so which of these you need depends only on the model
`resolve_isolation` returns:

- `harness-worktree` — @~/.ai/references/worktree-branch-check.md. The host
  picked the base, so the executor asserts it at spawn.
- `orchestrator-worktree` — @~/.ai/references/worktree-path-safety.md. The
  runtime created the checkout and set its base, so there is nothing for the
  executor to re-derive; it is pinned to its root instead.
</isolation_reading>

<available_agent_types>
Valid subagent types (use these exact names — never fall back to a generic agent):
- coder — executes plan tasks, commits atomically, writes SUMMARY.md
- code-reviewer — reviews changed source for bugs and security issues
- doc-writer — writes documentation a plan declares
- verifier — verifies phase goal achievement
- debugger — investigates a failure the coder could not resolve
</available_agent_types>

<model_selection>
Model and effort are injected inline at dispatch, never read from an agent's
frontmatter. Resolve both from the runtime and pass them on the `Agent(...)`
call:

```bash
phase_run query resolve-model <agent> --raw
phase_run query resolve-effort <agent> --raw
```

A result of `inherit` means the project set no override — **omit that argument
entirely** and let the host choose. Pass `model` only when resolution returned a
model alias, and `effort` only when it returned one of `low`, `medium`,
`high`, `xhigh` or `max`. The two resolve independently: a role can carry an
effort and no model, or the reverse. The `models` and `efforts` maps in each
init bundle carry the same resolved values for every agent that workflow
dispatches.
</model_selection>

<authority>
**Executing a phase changes the codebase.** Do not start execution unless the
user has explicitly asked for this phase to be implemented. Phase creation,
discussion, planning and readiness do not grant implementation permission.
</authority>

<process>

<step name="parse_args">
Recognised flags:
- `--plan {id}` - route only this plan and its registered prerequisites
- `--sequential` - dispatch one currently ready plan at a time. Each plan is
  still isolated; only coder dispatch concurrency changes
- `--resume` — continue a phase whose execution stopped partway
- `--no-review` is unsupported and must be rejected; chunk and final integrated
  independent reviews are mandatory

Reject unknown options before creating records, worktrees or dispatching agents;
do not silently ignore retired flags.
</step>



<step name="initialize">
```bash
_root="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
case "$_root" in /*) ;; *) _root="$(cd -- "$_root" && pwd -P)" ;; esac
for _c in "$_root"/.{ai,claude,codex}/runtime/phase.py "${CLAUDE_CONFIG_DIR:-$HOME/.claude}"/runtime/phase.py "${CODEX_HOME:-$HOME/.codex}"/runtime/phase.py; do
  [ -f "$_c" ] && PHASE_RUNTIME="$(cd -- "$(dirname -- "$_c")" && pwd -P)/$(basename -- "$_c")" && break
done
[ -n "${PHASE_RUNTIME:-}" ] || { echo "ERROR: phase runtime not found; run the installer." >&2; exit 1; }
phase_run() { "$(command -v python3 || command -v python)" "$PHASE_RUNTIME" "$@"; }
LOCATE=$(phase_run query phase.locate "${PHASE}") || { echo "ERROR: phase lookup failed; stop and report the runtime error." >&2; exit 1; }
```

Parse `phase_found`, `padded_phase`, `worktree`, `session`, `branch` and `source`
from `LOCATE`. If `phase_found` is false, report:

```
Phase [X] not found in roadmap.
Use /progress to see available phases.
```

Exit. If `session` is present but `worktree` is null, stop and report the
locator result as inconsistent.

When `worktree` is set, it is the locator-validated phase checkout. Run the
explicit quoted `cd` to that absolute path before loading phase data. Keep
`PHASE_RUNTIME` absolute so the launcher still resolves after the directory
change. Stop if `cd` fails.

```bash
if [ -n "${worktree:-}" ]; then cd -- "${worktree}" || exit 1; fi
INIT=$(phase_run query init.execute-phase "${PHASE}")
```

Parse the workflow's existing fields from `INIT`. Keep the locator's
`padded_phase`, `worktree`, `session`, `branch` and `source` as the selected
checkout identity.


Parse: `phase_found`, `phase_number`, `padded_phase`, `phase_name`, `phase_dir`,
`goal`, `has_context`, `has_plans`, `plan_count`, `summary_count`, `plan_index`,
`verification`, `checks_configured`, `models`, `efforts`, `agents_installed`,
`missing_agents`, `context_window`, `commit_docs`, `response_language`, `paths`.

The bundle says nothing about isolation on purpose. It is read-only and
resolution can fail, so `resolve_isolation` below is the only thing that
decides — and there is no second value to reconcile it against.

**If `response_language` is set:** all user-facing output MUST be presented in
`{response_language}`; technical terms, code, file paths and subagent prompts
stay in English.

If `has_plans` is false:

```
Phase {N} has no plans to execute.
Run `/plan-phase {N}` first.
```

Exit.

If `agents_installed` is false, report `missing_agents` and stop.

Display: `► EXECUTE PHASE {phase_number}: {phase_name}`
</step>

<step name="open_session">
`phase.locate` has already confirmed the phase and selected any existing session.
If `session` from `LOCATE` is present, require its absolute `worktree`, then use
its `worktree`, `branch`, `base`, `reused` and `synced` fields. Do not call
`session.open` or replace that session.

If `session` is null, confirm `phase_found` is true before opening or adopting:

```bash
GIT_DIR=$(git rev-parse --git-dir)
case "${source}:${GIT_DIR}" in
  registered-worktree:*/worktrees/*|current-checkout:*/worktrees/*)
    SESSION=$(phase_run query session.adopt phase "${padded_phase}") ;;
  current-checkout:*)
    SESSION=$(phase_run query session.open phase "${padded_phase}") ;;
  *) echo "ERROR: no supported phase session route for source=${source}; stop and report this routing gap." >&2; exit 1 ;;
esac
```

`session.open` is permitted only when `source` is `current-checkout` and
`GIT_DIR` identifies the primary checkout. `session.adopt` registers the
selected linked worktree and preserves its existing branch and dirty phase
records. If either verb fails, stop and report its error; never create a
replacement worktree or continue in the invoking checkout.

Parse `worktree`, `branch`, `base`, `reused` and `synced` from `SESSION`. Run
these commands with the absolute `PHASE_RUNTIME`:

```bash
cd -- "${worktree}"
INIT=$(phase_run query init.execute-phase "${PHASE}")
```

Parse every field listed in this workflow's initialize step again. Replace all
previously derived paths, artifact flags, models, efforts, checks, language and
configuration values. Confirm the reloaded `padded_phase` and `phase_number`
match `LOCATE`.

Report the selected session in one line:

```
Session: {branch} ({reused ? "resumed" : "opened"}) at {worktree}
```

**Do not deliver it here.** `/ship` opens the pull request, judges its checks and
closes the session once the phase is verified.
</step>

<step name="safe_resume_gate">
If `summary_count` is greater than 0, do not ask. Consult `pipeline.status` for
registered chunks as well as plan summaries. Resume any missing chunk gates or
integration, and run plans with no summary only when their route status is ready.
Print:

```
Phase {N}: {summary_count} of {plan_count} plans already executed — continuing with the rest.
```

`--resume` means the same. A SUMMARY alone does not make a chunk complete. Go to
`aggregate_results` only when every implemented chunk is integrated and its
applicable gates pass.
</step>

<step name="check_blocking_antipatterns">
**MANDATORY.** Look for `.continue-here.md` in the phase directory:

```bash
ls ${phase_dir}/.continue-here.md 2>/dev/null || true
```

If it exists, parse its "Critical Anti-Patterns" table for `severity: blocking`
rows. For each, answer inline before continuing:

1. What is this anti-pattern?
2. How did it manifest?
3. What structural mechanism — not acknowledgment — prevents it recurring?

If a row cannot be answered from the file, answer it from the codebase and the
phase's history. If it still cannot be answered, apply the most direct
preventive mechanism, name the row in the closing report, and continue.
</step>

<step name="preflight">
Confirm the working tree is in a fit state to execute:

```bash
git status --porcelain
git rev-parse --abbrev-ref HEAD
```

If the tree has uncommitted changes outside `.planning/`, report them and ask
whether to continue. Executing over dirty state makes the phase's commits
ambiguous.

You are inside the phase's session worktree by now, so the branch that reports
is the session branch and cannot be the default branch - `session.open` refuses
to create one on a protected name. Check it anyway, because a chunk is integrated
into the current session branch and that must never be `main`.

If it reports the default branch, the session was not opened and the earlier
step was skipped. Stop and open it rather than executing here.
</step>

<step name="resolve_isolation">
Decide how each coder executor is isolated. **This is the only step that
decides**, and resolving it records it, so the value you branch on and the value
on disk can never disagree.

```bash
ISOLATION=$(phase_run query dispatch-isolation --raw --phase "${phase_number}")
```

`ISOLATION` — never the host's name — selects who creates the checkout:

| `ISOLATION` | Fan-out | What this workflow does |
|---|---|---|
| `harness-worktree` | host-driven | Pass `isolation="worktree"` on each `Agent(...)` call and let the host create and bind the checkout. This workflow runs no git for setup. On Claude, the project's `WorktreeCreate` hook creates it at `.worktrees/<name>` from this session's `HEAD`. Never create or accept a worktree anywhere else. |
| `orchestrator-worktree` | runtime-driven | Call `worktree.create` per plan and give the executor its path as a root pin. The runtime performs every git operation. |

**There is no third value, and no way to opt out.** Every executor in this
project runs in its own worktree. If the verb fails, it is telling you isolation
could not be established — a git too old for worktrees, or a worktree root that
is not gitignored. **Stop and report its message.** Do not continue unisolated,
and do not look for a flag that lets you: `--sequential` still runs one plan at
a time, but each plan is still isolated.

This is enforced, not requested: `hooks/worktree-guard.sh` refuses an
`Agent(...)` dispatch of `coder`, `doc-writer` or `debugger` that arrives
without `isolation="worktree"`, and warns on any write from outside a worktree.
A dispatch you forget to isolate will be blocked, not silently run.

Then clear any metadata a crashed earlier session left behind:

```bash
phase_run query worktree.reap-orphans
```

`reap-orphans` never deletes a checkout that still exists.

A host that forks its dispatch worktrees from the fork base rather than from
HEAD would start an executor on a tree missing HEAD's commits. That is caught
where it actually happens — the executor's own branch check compares its real
base against `EXPECTED_BASE` and halts with exit 42 — not by guessing about it
here.

Report the outcome in one line before dispatching:

```
Isolation: {ISOLATION} ({reason})
```
</step>

<step name="discover_and_group_plans">
For completed unregistered whole-plan assignments, retain dependency and
file-overlap waves from the plan index. Plans that declare overlapping `files_modified`
must not share a legacy ownership wave; wait for that wave to join and integrate
before checking it or starting dependent waves. Registered chunks follow the
readiness route below, without using those displayed waves as a global barrier.

```bash
phase_run query phase-plan-index "${phase_number}"
```

Read each plan's `files_modified`, `files_deleted`, `depends_on`, acceptance IDs,
check commands and any declared shared resources. The plan's `wave` is
informational only. Create `.worktrees/pipeline-inputs/` (gitignored) and write a
temporary repository-relative route spec there, never under `.planning/`, with
task IDs for coding tasks, exact owned paths, registered prerequisite chunk IDs,
named resources and `state: pending`, then call:

```bash
mkdir -p .worktrees/pipeline-inputs
phase_run query pipeline.route --spec .worktrees/pipeline-inputs/route.json
```

Include every planned task on each route call. Dispatch only tasks returned
`ready`; preserve each `wait` or `blocked` reason.
An unknown, unregistered or unintegrated prerequisite is never assumed complete.
Path/resource conflicts delay only the affected task, and a prerequisite blocks
only its dependents. Re-route after task registration, gate or integration state
changes. Follow the [route contract](../references/parallel-pipeline.md#routing-planned-work).
</step>

<step name="execute_chunks">
For currently ready route tasks, dispatch coders concurrently unless `--sequential`
was passed. Do not wait for all phase tasks or an entire proposed wave before
processing a completed chunk. Reserve the selected route task as `active` before
dispatch so overlapping paths and named resources remain unavailable to new
assignments. Keep each task active through chunk review, checks and integration.
Map each route task ID to unique `assignment_id` and committed `chunk_id` values;
`plan_id` identifies the source plan. These identifiers can match for a one-chunk
plan. Set `owned_paths` to the exact independently reviewable paths in the plan's
declared boundary, and list only acceptance IDs demonstrated by that chunk.

Before dispatching, capture the base each executor must fork from and record its
declared scope for isolation:

```bash
EXPECTED_BASE=$(git rev-parse HEAD)
```

Both calls below take the plan's declared scope. It comes from the plan file's
own frontmatter — `files_modified` and `files_deleted`, which you already read
in `discover_and_group_plans` — passed as comma-separated lists. A plan that
declares no `files_deleted` authorizes no deletion, which is the point.

**When `ISOLATION` is `harness-worktree`** — record the branch the host will use
for each plan. Claude Code names its dispatch worktrees `agent-<id>`; read the
branch back from the agent's own report and record it before integrating:

```bash
phase_run query worktree.record-agent "${plan_id}" --phase "${phase_number}"   --branch "${reported_branch}" --base "${EXPECTED_BASE}"   --files ${plan_files} --deletions ${plan_deletions}
```

**When `ISOLATION` is `orchestrator-worktree`** — create the checkout yourself
and pass its path to the executor as its root pin:

```bash
phase_run query worktree.create "${plan_id}" --phase "${phase_number}"   --base "${EXPECTED_BASE}" --files ${plan_files} --deletions ${plan_deletions}
```

`--files` is the plan's `files_modified`. `--deletions` is its `files_deleted`,
and it is the **only** thing that authorizes a removal at merge time: a
declaration of general scope never implies permission to delete. A plan that
declares no deletions and deletes something is blocked, by design.

For each ready plan, use the existing isolated coder dispatch and branch/root
guard below. Include the [chunk handoff](../templates/chunk-handoff.md) in the
required reading. Require each event's full base/head, exact scope, acceptance,
dependencies, resources and check definitions. A committed bounded chunk may be
emitted as an interim host lifecycle/message event while the coder continues on
independent assigned paths; the coordinator registers that immutable revision and
starts detached review/test snapshots concurrently. Only the final plan event
requires a SUMMARY and may report completion. If the host has no interim events,
the coder turn ends incomplete at the chunk boundary, and a fresh continuation is
dispatched after integration and applicable gates pass. Do not create a SUMMARY
or mark the plan complete while assigned tasks remain.

For each ready plan:

```
Agent(
  prompt="
<execution_context>
**Phase:** {phase_number} — {phase_name}
**Plan:** {phase_dir}/{plan_file}
${handoff ? `
<handoff>
{the continuation field of phase_run query handoff.read <id>, verbatim}
</handoff>
This is a continuation. The handoff replaces the reading listed below: ingest it
first, work only its remaining items, and open a listed file only as its
reading rule allows.
` : ''}

<required_reading>
- {phase_dir}/{plan_file} (your plan — the authority on what to change)
- {phase_dir}/{padded_phase}-CONTEXT.md (locked decisions)
- every file named in your plan's `read_first` fields
</required_reading>
${context_window >= 500000 ? `
**Integrated prerequisite summaries:** {paths of summaries for registered prerequisites}
` : ''}

**Project instructions:** read ./CLAUDE.md or ./AGENTS.md if either exists.
**Project skills:** check `.agents/skills/` or `.claude/skills/` — read the SKILL.md
files and follow their rules.
</execution_context>

<constraints>
- Execute ONLY the tasks in your plan. New capability is out of scope: record it
  in your summary as a deferred item rather than building it
- Read every `read_first` file before editing; do not act on assumptions about
  current state. A continuation reads only the files its handoff's reading rule
  allows, and always the file it is about to edit
- Touch only the paths your plan declares in `files_modified`
- Commit the finished reviewable chunk with a descriptive message
- Run each task's `<verify>` command and record its actual output. A task whose
  verify command was not run is not complete
- If the plan is wrong, stop and report it. Do not improvise a different change
</constraints>

${ISOLATION === 'harness-worktree' ? `
<worktree_branch_check>
{the block from references/worktree-branch-check.md, verbatim, with
 {EXPECTED_BASE} substituted and {EXPECTED_BASE_ALTERNATE} left empty}
</worktree_branch_check>
` : `
<project_root_pin>
{the root-pin guard from references/worktree-path-safety.md, with {PINNED_ROOT}
 substituted by this plan's worktree path, single-quoted}
</project_root_pin>
`}

<output>
Write: {phase_dir}/{plan_id}-SUMMARY.md with:
- frontmatter: status (complete|blocked), commits, files changed, requirements covered
- what was built, and the evidence each acceptance criterion was met
- anything deferred, and why
Return: ## EXECUTION COMPLETE with status and the summary path
Also return the committed branch, full head SHA and chunk handoff, so the
coordinator can register and gate the exact revision.
</output>
",
  subagent_type="coder",
  ${models['coder'] === 'inherit' ? '' : `model="${models['coder']}",`}
  ${efforts['coder'] === 'inherit' ? '' : `effort="${efforts['coder']}",`}
  ${ISOLATION === 'harness-worktree' ? 'isolation="worktree",' : ''}
  description="Execute {plan_id}"
)
```

Under `harness-worktree`, an executor that prints `FATAL:` or exits 42 halted at
its branch check and committed nothing. Follow
[worktree-recovery-policy](../references/worktree-recovery-policy.md): mark that
plan blocked, preserve its worktree and continue unrelated ready tasks.

> **ORCHESTRATOR RULE**: do not read or write paths an active coder owns. Accept
> each completion event once, then register its exact committed revision. Continue
> dispatching ready tasks whose paths and named resources do not conflict; do not
> poll, relaunch or send handoff chatter.

For each interim chunk event, verify its exact commit and handoff, then register
that fixed SHA and launch review/checks on detached snapshots while the coder
continues only on other assigned paths. Never read or integrate its moving branch.
Interim events do not require a SUMMARY and do not complete the plan. A coder
writes its SUMMARY and reports `complete` only after every assigned task finishes;
only then verify the SUMMARY and final commit on disk rather than trusting the
return:

```bash
phase_run query phase-plan-index "${phase_number}"
git log --oneline -n 20
```

A coder assigned source-changing plan work who reports `complete` without the
required SUMMARY.md and owned commits is blocked. Read-only specialists complete
with their assigned cited report fields and do not create commits or SUMMARY.md.

**Continue an interrupted plan from its handoff.** A coder that crossed the
context limit, or exited without a `complete` SUMMARY, left a handoff record in
the checkout it worked in — this session worktree, or under
`harness-worktree` the plan's own worktree. Run `phase_run query handoff.list`
from each, and for every record:

1. Inspect the plan's commits and SUMMARY, as for any blocked plan.
2. Re-dispatch the plan's same `Agent(...)` call into a fresh isolated checkout,
   as `checkpoint_handling` does, with the record's brief in the `<handoff>`
   block — the four steps in
   [dispatching a continuation](../references/worker-handoff.md#dispatching-a-continuation).
3. `handoff.consume` the record in the same turn.

Continue each plan at most twice. If a continuation returns blocked on the same
remaining tasks, report it as a blocker.
</step>

<step name="integrate_chunk">
For each returned coder chunk, require its commit and
[chunk-handoff](../templates/chunk-handoff.md), requiring a SUMMARY only for a
final plan result. Confirm the reported full base/head
and declared chunk scope against the assigned plan, then register the exact
revision:

```bash
mkdir -p .worktrees/pipeline-inputs
phase_run query pipeline.register --spec .worktrees/pipeline-inputs/chunk-registration.json
phase_run query pipeline.prepare <chunk-id>
```

The runtime prepares separate detached reviewer/test snapshots at the registered
SHA. Dispatch a fresh `code-reviewer` against the prepared reviewer snapshot with
the exact registered SHA/base, chunk acceptance IDs, owned paths, plan and relevant
instructions. Require the schema-1 report described in the pipeline reference.
In the same routing turn, run the runtime-owned checks against the test snapshot:

```bash
phase_run query pipeline.run-checks <chunk-id> --environment <explicit-environment-id>
```

The check verb executes the declared argv itself; it is not another model agent.
Do not use `verification.run-checks` as a chunk substitute. The code-reviewer
returns the schema-1 JSON report required by
[the pipeline contract](../references/parallel-pipeline.md#register-and-gate-one-committed-chunk),
including matching base/head, complete acceptance and scope, explicit status,
findings, cited evidence and provenance. Capture that output under the ignored
`.worktrees/pipeline-inputs/` directory, never under `.planning/` or in a source
snapshot, then record it:

```bash
phase_run query pipeline.record-review <chunk-id> --report .worktrees/pipeline-inputs/review-report.json
```

Check `pipeline.status <chunk-id>`. Preserve failed attempts and treat missing,
partial, corrupt, stale, skipped or failed evidence as a blocker. Do not accept a
review of one SHA or environment as evidence for another. Only after all declared
prerequisites are integrated and all applicable gates pass, merge the registered
full head SHA into the clean, unprotected session branch and record the resulting
revision:

```bash
git merge --no-ff <registered-head-SHA>
phase_run query pipeline.integrate <chunk-id> --revision HEAD
phase_run query pipeline.status <chunk-id>
```

`pipeline.integrate` records and validates an existing Git integration; it does
not merge for you. If the merge conflicts, abort it, preserve the coder checkout
and block the chunk for reconciliation. The legacy `worktree.merge-wave` remains a
fallback only for completed unregistered whole-plan assignments; never merge an
active coder branch or use that fallback as a whole-wave barrier for routed chunks.

Continue independent ready tasks while review and checks run on their frozen
snapshots. Re-route after registration, gate and integration changes; after a
chunk integrates, set its task state to `complete` in the full route spec to
release its path/resource reservation. Wait only for a prerequisite of the task
currently blocked. An unresolved dependency or a scope/runtime rejection remains
explicit `wait`/`blocked` work, never a guessed pass. Keep unmerged or dirty coder
worktrees for recovery; never force cleanup.
</step>

<step name="checkpoint_handling">
A plan may return `blocked` with a checkpoint. Do not stop the run. Route it:

- **Every option stays inside the locked decisions, acceptance and declared
  scope, and none is destructive:** take the coder's recommended option (or the
  one CONTEXT.md points to), record it, and re-dispatch the plan with the
  decision in its execution context:

  ```bash
  phase_run query state.add-decision "{decision} (decided within delegated discretion)"
  ```

- **Otherwise** — it changes a locked decision or acceptance, is destructive or
  irreversible, installs an unverified package, needs credentials, access or
  spending, or has a precondition only a person can meet: leave the plan
  blocked, skip only the plans that depend on it, continue all other ready tasks, and
  list the options and the coder's recommendation in the closing report.

Re-dispatch into a fresh isolated checkout, never the primary checkout. Never
resolve a checkpoint by guessing.
</step>

<step name="run_checks">
Chunk checks run through `pipeline.run-checks` against the immutable registered
test snapshot in `integrate_chunk`. Do not wait for every independent task to
finish before that gate, and do not describe a chunk receipt as an aggregate
phase check. The unchanged `verification.run-checks` command checks the fully
integrated phase at the final review gate and during `/verify-work`; matching successful
receipts avoid duplicate execution and final verification remains mandatory.

Consume successful receipts when their tested revision, declared sources,
environment and configuration match the relevant snapshot. Receipts are
deterministic evidence; a failed or ambiguous check needs diagnosis and blocks
only dependent work. Repairs invalidate affected receipts. For completed
unregistered whole-plan assignments, checks still run after the legacy ownership
wave has joined and integrated, before dependent waves start.
</step>

<step name="aggregate_results">
Read each SUMMARY.md and build the phase picture:

- Which plans completed, which are blocked
- Which requirement ids are covered across all summaries
- What was deferred
- Which files changed overall

Report any phase requirement id that no summary claims. That is a gap, whether or
not every plan reported complete.

List what is still open in the closing report: each SUMMARY's Deferred and
Remaining entries, minus anything a later plan in this phase completed, plus
out-of-scope code-review findings. Do not create todos.
</step>

<step name="code_review_gate">
The final independent correctness/security review of the integrated phase is
mandatory even when all chunk reviews passed. There is no review waiver; reject
the retired `--no-review` option.

After all required chunks (or completed legacy whole-plan waves) are integrated,
freeze the session revision. Independent read-only checks and fresh review run
together against the same frozen revision: start the required fresh code-reviewer
and call `verification.run-checks`; valid successful receipts can be reused.
The reviewer owns source correctness and security findings. Wait for both results before accepting
the phase or repairing it. If a repair changes source, rerun affected checks and
obtain a fresh review of the repaired revision.

```
Agent(
  prompt="
Review the source changes made by Phase {phase_number}.

**Changed files:** {aggregate files_modified across summaries}
**Plans:** {plan paths}
**Diff base:** {phase session base captured before any chunk integration}

Review the changed source for correctness bugs, security issues and code quality
problems. Judge the code as it now stands, not the summaries' claims about it.

Return:
## CODE REVIEW
Findings: <numbered, each with file:line, severity (critical|warning), and why it is wrong>
",
  subagent_type="code-reviewer",
  ${models['code-reviewer'] === 'inherit' ? '' : `model="${models['code-reviewer']}",`}
  ${efforts['code-reviewer'] === 'inherit' ? '' : `effort="${efforts['code-reviewer']}",`}
  description="Review phase {phase_number} changes"
)
```

**Critical findings block completion.** Dispatch a coder to fix them, then
re-review. Warnings are recorded in the phase summary for the verifier to weigh;
they do not block.
</step>

<step name="update_roadmap">
Tick each completed plan through the runtime so the roadmap, the progress table
and STATE.md counters all move together:

```bash
phase_run query roadmap.update-plan-progress "${plan_id}"
```

Only tick a plan after its SUMMARY.md says `status: complete`, its registered
chunk is integrated and its applicable chunk gates pass. Aggregate integrated
verification and final review remain separate phase gates. When every plan in
the phase is ticked, the runtime marks the phase complete in the overview
checklist automatically.
</step>

<step name="close_phase_todos">
Any todo folded into this phase during discussion is now resolved. Move each one
and refresh the state section:

```bash
phase_run query todo.complete "${todo_file}"
phase_run query state.sync-todos
```

Leave todos that were reviewed but not folded in exactly where they are.
</step>

<step name="update_state">
```bash
phase_run query state.update-progress
phase_run query state.record-session \
  --stopped-at "Phase ${phase_number} executed (${completed}/${plan_count} plans)" \
  --resume-file "${phase_dir}/${padded_phase}-VERIFICATION.md"
phase_run query commit "chore(${padded_phase}): record phase execution" \
  --files .planning/ROADMAP.md .planning/STATE.md .planning/todos
```
</step>

<step name="session_handoff">
Do not deliver the session here and do not close it. Leave it open on its
branch; `/ship` delivers it, and `/verify-work` runs `/ship` on a pass. See
@~/.ai/references/worktree-sessions.md.

```
Session: {branch} at {worktree} — open; verification and delivery follow in this session
```
</step>

<step name="completion">
```
Phase {phase_number} executed.

Plans: {completed}/{plan_count} complete{blocked ? ", {blocked} blocked" : ""}
Isolation: {ISOLATION}
Integration: {N chunks integrated | blocked chunks with reasons | not isolated}
Worktrees preserved: {paths and reasons, or none}
Requirements covered: {ids}
Checks: {passed | failed with detail | not configured}
Code review: {clean | N warnings recorded | N critical fixed}
{deferred ? "Deferred: {items}" : ""}
Still open (out of scope): {items} | none
Blocked for a person: {plans, their options and the recommendation} | none

Verifying phase {phase_number} now.
```
</step>

<step name="run_verify_work">
Invoke the `verify-work` skill for phase {phase_number}
(`/verify-work {phase_number}`) in this session. If plans are still blocked,
report them as the blocker instead.
</step>

</process>

<anti_patterns>
- Don't implement anything yourself — dispatch coders and integrate their work
- Don't read or write paths an active coder owns; continue only independent ready tasks
- Don't accept "complete" without a SUMMARY.md and real commits
- Don't resolve a checkpoint by guessing so a dependent task can run
- Don't dispatch route tasks with overlapping paths or named resources concurrently
- Don't tick a roadmap plan that has no complete summary
- Don't skip the code review gate on your own initiative
- Don't treat execution completing as the phase being verified
- Don't branch on the host's name; branch on `ISOLATION`
- Don't continue when isolation could not be established; report and stop
- Don't look for a way to run a plan unisolated — there isn't one, and the
  dispatch hook will block it
- Don't integrate before the chunk's applicable gates pass on its registered SHA
- Don't pass `--force` to cleanup to get past a preserved worktree
- Don't propose continuing in the primary checkout as the recovery path for a
  run the user configured to be isolated
- Don't merge a branch whose executor halted at its branch check
- Don't open a pull request or merge from here — a phase session is
  delivered once, by `/ship`
- Don't close the phase session; the workflows after this one reuse it
- Don't tell the user to resume, `/clear`, start a fresh session, or run
  `/verify-work` or `/ship`
- Don't stop because a context advisory fired
- Don't ask whether to resume a partial execution
- Don't stop to ask about an issue; route it per [issues found while working](../RULES.md#issues-found-while-working)
- Don't create todos
</anti_patterns>

<success_criteria>
- [ ] Implementation authority confirmed before execution started
- [ ] Blocking anti-patterns answered before any work
- [ ] Isolation resolved and reported before dispatch, and every plan isolated
- [ ] Plans routed by registered prerequisites, path scope and shared resources
- [ ] Each committed chunk registered with an exact revision and handoff
- [ ] Every executor carried the guard its isolation model calls for — the
      branch check under `harness-worktree`, the root pin under
      `orchestrator-worktree` — and any exit-42 halt was treated as blocked
      with its worktree preserved
- [ ] Review and runtime checks used separate immutable snapshots at the registered SHA
- [ ] Chunks integrated only after all applicable gates and prerequisite gates passed
- [ ] Checkpoints decided within delegated discretion or left blocked for a
      person, never guessed, and never a reason to stop the run
- [ ] What is still open listed in the closing report, with no todos created
- [ ] Chunk checks passed on their registered test snapshots
- [ ] Final configured aggregate checks run on the integrated tree during verify-work
- [ ] Requirement coverage aggregated, with gaps reported
- [ ] Code review run; critical findings fixed and re-reviewed
- [ ] Roadmap plans ticked only for complete, integrated chunks with passing gates
- [ ] Folded todos closed, STATE.md updated, work committed
- [ ] Phase session left open for the workflows that follow
- [ ] `/verify-work` run in this same session once execution finished, without
      asking the user to run it
</success_criteria>
