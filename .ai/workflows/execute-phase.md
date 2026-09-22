<!-- workflow
step: execute
agent-roles: orchestrator, coder, code-reviewer
produces: {NN}-{MM}-SUMMARY.md, commits, roadmap plan ticks
consumes: {NN}-{MM}-PLAN.md, CONTEXT.md, STATE.md
-->

<purpose>
Execute a phase's plans. Group them into dependency waves, dispatch a coder per
plan in its own isolated checkout, integrate the wave, review the resulting
code, confirm the phase goal was achieved, then tick the roadmap.

The orchestrator routes and integrates. It does not write the implementation.
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
Models are injected inline at dispatch, never read from an agent's frontmatter.
Resolve each agent's model from the runtime and pass it on the `Agent(...)` call:

```bash
phase_run query resolve-model <agent> --raw
```

A result of `inherit` means the project set no override — **omit the `model`
argument entirely** in that case and let the host choose. Pass `model` only when
resolution returned a concrete model name. The `models` map in each init bundle
carries the same resolved values for every agent that workflow dispatches.
</model_selection>

<authority>
**Executing a phase changes the codebase.** Do not start execution unless the
user has explicitly asked for this phase to be implemented. Phase creation,
discussion, planning and readiness do not grant implementation permission.
</authority>

<decision_boundary>
**No decision records are written during execution.** `decision.draft` refuses
from a dispatched plan worktree, and that refusal is the intended behavior, not
an obstacle to work around with `--allow-execution-context`.

A choice that feels ADR-sized while building is a sign the phase was planned
short of a decision it needed. Record it as a blocker and let planning decide:

```bash
phase_run query state.add-blocker "Phase {N}: {the undecided choice} - needs a decision record"
```

Then continue with the plan as written, or stop if the plan cannot proceed
without it. Do not decide it in passing and document it afterwards.
</decision_boundary>

<process>

<step name="parse_args">
Recognised flags:
- `--plan {id}` — execute only this plan
- `--wave {n}` — execute only this wave
- `--sequential` — run one plan at a time even when a wave allows parallelism.
  Each plan is still isolated; only the concurrency changes
- `--resume` — continue a phase whose execution stopped partway
- `--no-review` — skip the code review gate (requires the user to say so)
</step>



<step name="initialize">
```bash
_root="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
for _c in "$_root"/.{ai,claude,codex}/runtime/phase.py "${CLAUDE_CONFIG_DIR:-$HOME/.claude}"/runtime/phase.py "${CODEX_HOME:-$HOME/.codex}"/runtime/phase.py; do
  [ -f "$_c" ] && PHASE_RUNTIME="$_c" && break
done
[ -n "${PHASE_RUNTIME:-}" ] || { echo "ERROR: phase runtime not found; run the installer." >&2; exit 1; }
phase_run() { "$(command -v python3 || command -v python)" "$PHASE_RUNTIME" "$@"; }
INIT=$(phase_run query init.execute-phase "${PHASE}")
```

Parse: `phase_found`, `phase_number`, `padded_phase`, `phase_name`, `phase_dir`,
`goal`, `has_context`, `has_plans`, `plan_count`, `summary_count`, `plan_index`,
`verification`, `checks_configured`, `models`, `agents_installed`,
`missing_agents`, `context_window`, `commit_docs`, `response_language`, `paths`.

The bundle says nothing about isolation on purpose. It is read-only and
resolution can fail, so `resolve_isolation` below is the only thing that
decides — and there is no second value to reconcile it against.

**If `response_language` is set:** all user-facing output MUST be presented in
`{response_language}`; technical terms, code, file paths and subagent prompts
stay in English.

If `phase_found` is false, or `has_plans` is false:

```
Phase {N} has no plans to execute.
Run `/plan-phase {N}` first.
```

Exit.

If `agents_installed` is false, report `missing_agents` and stop.

Display: `► EXECUTE PHASE {phase_number}: {phase_name}`
</step>

<step name="open_session">
Open the worktree this work lives in, before writing anything. Read
@~/.ai/references/worktree-sessions.md for the full contract.

```bash
SESSION=$(phase_run query session.open phase "${padded_phase}")
```

Parse `worktree`, `branch`, `base`, `reused` and `synced`. **Run every
subsequent command in this workflow from `worktree`.** An open session for
this phase is reused rather than replaced, so the work accumulates onto one branch
and arrives as one pull request.

Report it in one line:

```
Session: {branch} ({reused ? "resumed" : "opened"}) at {worktree}
```

If the verb fails, **stop and report its message**. It means isolation could not
be established, and continuing in the invoking checkout is the one outcome this
project does not allow — the dispatch guard would block the write anyway.
</step>

<step name="safe_resume_gate">
If `summary_count` is greater than 0 and `--resume` was not passed, execution
already ran at least partly:

```
Phase {N} has {summary_count} of {plan_count} plans already executed.

Re-running from the start would re-execute completed work.
```

Use AskUserQuestion (header: "Partial execution"; options: "Resume the remaining
plans" / "Re-run everything" / "Cancel"). Default to resuming.

On resume, the plans to run are those in `plan_index` whose `summary` is null.
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

If a blocking row cannot be answered from the file, stop and ask the user.
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
is the session branch and cannot be the default branch — `session.open` refuses
to create one on a protected name. Check it anyway, because a wave is integrated
by merging into the current branch and that must never be `main`.

If it reports the default branch, the session was not opened and the earlier
step was skipped. Stop and open it rather than executing here.
</step>

<step name="resolve_isolation">
Decide how this wave's executors are isolated. **This is the only step that
decides**, and resolving it records it, so the value you branch on and the value
on disk can never disagree.

```bash
ISOLATION=$(phase_run query dispatch-isolation --raw --phase "${phase_number}")
```

`ISOLATION` — never the host's name — selects who creates the checkout:

| `ISOLATION` | Fan-out | What this workflow does |
|---|---|---|
| `harness-worktree` | host-driven | Pass `isolation="worktree"` on each `Agent(...)` call and let the host create and bind the checkout. This workflow runs no git for setup. |
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
```bash
phase_run query phase-plan-index "${phase_number}"
```

For each plan, read its frontmatter `wave` and `depends_on`. Group into waves:

- Plans with no unmet dependencies form wave 1
- A plan enters a wave only once every id in its `depends_on` has a SUMMARY.md
- Plans that declare overlapping `files_modified` must NOT share a wave — put the
  later one in a following wave, whatever its declared wave says

Report the grouping before executing:

```
Execution plan for Phase {N}:
  Wave 1 (parallel): {01-01}, {01-02}
  Wave 2: {01-03} (depends on 01-01)
```

A dependency cycle is a planning defect: report it and stop rather than picking
an order.
</step>

<step name="execute_waves">
Execute waves in order. Within a wave, dispatch every plan **in a single message
with multiple Agent calls** so they run concurrently, unless `--sequential` was
passed or the wave has one plan.

Before dispatching, capture the base every executor in this wave must fork from,
and record each plan's declared scope so the wave can be integrated:

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

For each plan:

```
Agent(
  prompt="
<execution_context>
**Phase:** {phase_number} — {phase_name}
**Plan:** {phase_dir}/{plan_file}

<required_reading>
- {phase_dir}/{plan_file} (your plan — the authority on what to change)
- {phase_dir}/{padded_phase}-CONTEXT.md (locked decisions)
- every file named in your plan's `read_first` fields
</required_reading>
${context_window >= 500000 ? `
**Prior wave summaries:** {paths of SUMMARY.md files from earlier waves in this phase}
` : ''}

**Project instructions:** read ./CLAUDE.md or ./AGENTS.md if either exists.
**Project skills:** check `.agents/skills/` or `.claude/skills/` — read the SKILL.md
files and follow their rules.
</execution_context>

<constraints>
- Execute ONLY the tasks in your plan. New capability is out of scope: record it
  in your summary as a deferred item rather than building it
- Read every `read_first` file before editing; do not act on assumptions about
  current state
- Touch only the paths your plan declares in `files_modified`
- Commit each completed task atomically with a descriptive message
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
Also return the branch you committed on, so the wave can be integrated.
</output>
",
  subagent_type="coder",
  ${models['coder'] === 'inherit' ? '' : `model="${models['coder']}",`}
  ${ISOLATION === 'harness-worktree' ? 'isolation="worktree",' : ''}
  description="Execute {plan_id}"
)
```

Under `harness-worktree`, an executor that prints `FATAL:` or exits 42 halted at
its branch check and committed nothing. Follow
[worktree-recovery-policy](../references/worktree-recovery-policy.md): mark that
plan blocked, preserve its worktree, and do not count the wave as successful.

> **ORCHESTRATOR RULE**: after dispatching a wave, stop working on this task. Do
> not read files, edit code or run tests while coders are active — you would
> conflict with their edits. Wait for every agent in the wave to return before
> starting the next one.

After each wave, verify on disk rather than trusting the returns:

```bash
phase_run query phase-plan-index "${phase_number}"
git log --oneline -n 20
```

A plan whose agent reported "complete" with no SUMMARY.md, or with no commits, did
not complete. Treat it as blocked and say so.
</step>

<step name="integrate_wave">
The wave's work is on branches, not in your tree — it always is, because every
plan ran isolated. Integrate it into the **session branch** before running
checks, reviewing, or starting the next wave. `merge-wave` merges into whatever
branch is current, which inside the session worktree is the session branch, so
the wave lands in the phase's own pull request and never touches the base:

```bash
git status --porcelain     # must be clean; commit planning records first
phase_run query worktree.merge-wave --phase "${phase_number}"
```

Read the result rather than assuming it worked:

- `wave_clean: true` — every branch merged. Continue.
- `blocked` non-empty — **stop the wave here.** Each entry says why:

| `status` | Means | What to do |
|---|---|---|
| `blocked` | deleted a path the plan never declared | Show `undeclared_deletions` and ask the user. Do not re-run the merge to get past it. A rename counts: its source path is a removal |
| `conflict` | two plans changed the same lines | The merge was aborted and the worktree preserved. This is a wave-grouping defect: plans with overlapping `files_modified` should not have shared a wave |
| `missing` | the branch does not exist | The executor never committed. Treat the plan as blocked |
| `empty` | the branch has no commits | Same: nothing was produced |

A merged entry may also carry `out_of_scope` — paths the plan changed outside
what it declared. That is **advisory**: record it in the phase summary and let
the reviewer weigh it. It never blocks a merge.

Once the wave is clean, release its checkouts:

```bash
phase_run query worktree.cleanup-wave --phase "${phase_number}"
```

Cleanup is conservative on purpose. It removes a worktree only when git agrees
its branch is an ancestor of HEAD, and reports everything it kept in
`preserved`, with the reason. **Never pass `--force` to get past a preserved
entry** — that discards work whose fate has not been decided. Report what was
preserved and let the user choose.
</step>

<step name="checkpoint_handling">
A plan may return `blocked` with a checkpoint — a decision it cannot make alone.

For each checkpoint:
1. Present what the coder found and the options it identified
2. Ask the user to decide (AskUserQuestion, or plain text in text mode)
3. Record the decision: `phase_run query state.add-decision "{decision}"`
4. Re-dispatch that plan with the decision added to its execution context

Re-dispatch into a **fresh** isolated checkout, not the main one. A plan the
user configured to run isolated stays isolated through recovery; continuing it
in the primary checkout needs explicit confirmation and is never the default.

A checkpoint is not a failure. Do not resolve one by guessing so the wave can
finish.
</step>

<step name="run_checks">
If `checks_configured` is true, run the project's configured checks once per
wave, after the wave's agents have all returned **and the wave has been
integrated** — checks run against the merged tree, not against a tree the
wave's work has not landed in yet:

```bash
phase_run query verification.run-checks
```

Report any failing check with its command and output tail. A failing check blocks
the next wave: hand it to the responsible coder, or to the debugger when the
cause is unclear.
</step>

<step name="aggregate_results">
Read each SUMMARY.md and build the phase picture:

- Which plans completed, which are blocked
- Which requirement ids are covered across all summaries
- What was deferred
- Which files changed overall

Report any phase requirement id that no summary claims. That is a gap, whether or
not every plan reported complete.
</step>

<step name="code_review_gate">
**Skip only when `--no-review` was passed and the user asked for it.**

```
Agent(
  prompt="
Review the source changes made by Phase {phase_number}.

**Changed files:** {aggregate files_modified across summaries}
**Plans:** {plan paths}
**Diff base:** {commit before the first wave}

Review the changed source for correctness bugs, security issues and code quality
problems. Judge the code as it now stands, not the summaries' claims about it.

Return:
## CODE REVIEW
Findings: <numbered, each with file:line, severity (critical|warning), and why it is wrong>
",
  subagent_type="code-reviewer",
  ${models['code-reviewer'] === 'inherit' ? '' : `model="${models['code-reviewer']}",`}
  description="Review phase {phase_number} changes"
)
```

**Critical findings block completion.** Dispatch a coder to fix them, then
re-review. Warnings are recorded in the phase summary for the verifier to weigh;
they do not block.
</step>

<step name="verify_phase_goal">
Execution completing is not the same as the phase delivering its goal. Hand
verification to `/verify-work`:

```
Phase {N} executed: {completed}/{plan_count} plans.

`/verify-work {N}`
```

When the user asked for the phase to be carried through, read `workflows/verify-work.md`
and execute it now rather than only printing the command.
</step>

<step name="update_roadmap">
Tick each completed plan through the runtime so the roadmap, the progress table
and STATE.md counters all move together:

```bash
phase_run query roadmap.update-plan-progress "${plan_id}"
```

Only tick a plan that has a SUMMARY.md with `status: complete`. When every plan
in the phase is ticked, the runtime marks the phase complete in the overview
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
**Do not deliver this session here.** A phase session is opened by
`/discuss-phase` and reused by `/plan-phase`, `/execute-phase` and
`/verify-work`, so that the whole phase accumulates onto one branch and arrives
as one pull request. Delivering it from this workflow would cut the phase into
separate pull requests and strand whatever comes after.

The session stays open, with its commits on its branch. `/ship` is the phase's
delivery step: it opens the pull request, judges its checks, merges and closes
the session. See @~/.ai/references/worktree-sessions.md.

Carry the session into the output below so the user knows where the work is and
what closes it:

```
Session: {branch} at {worktree} — open, delivered by `/ship {phase_number}`
```
</step>

<step name="completion">
```
Phase {phase_number} executed.

Plans: {completed}/{plan_count} complete{blocked ? ", {blocked} blocked" : ""}
Isolation: {ISOLATION}
Integration: {waves merged clean | N entries blocked with reasons | not isolated}
Worktrees preserved: {paths and reasons, or none}
Requirements covered: {ids}
Checks: {passed | failed with detail | not configured}
Code review: {clean | N warnings recorded | N critical fixed}
{deferred ? "Deferred: {items}" : ""}

---

## ▶ Next Up

`/clear` then:

`/verify-work {phase_number}`

---
```
</step>

</process>

<anti_patterns>
- Don't implement anything yourself — dispatch coders and integrate their work
- Don't work while a wave is running; you will conflict with the agents' edits
- Don't accept "complete" without a SUMMARY.md and real commits
- Don't resolve a checkpoint by guessing so the wave can finish
- Don't put plans with overlapping `files_modified` in the same wave
- Don't tick a roadmap plan that has no complete summary
- Don't skip the code review gate on your own initiative
- Don't treat execution completing as the phase being verified
- Don't branch on the host's name; branch on `ISOLATION`
- Don't continue when isolation could not be established; report and stop
- Don't look for a way to run a plan unisolated — there isn't one, and the
  dispatch hook will block it
- Don't run checks or review before the wave is integrated; you would be
  judging a tree the work has not landed in
- Don't pass `--force` to cleanup to get past a preserved worktree
- Don't propose continuing in the primary checkout as the recovery path for a
  run the user configured to be isolated
- Don't merge a branch whose executor halted at its branch check
- Don't open a pull request or merge from here — a phase session is
  delivered once, by `/ship`
- Don't close the phase session; the workflows after this one reuse it
</anti_patterns>

<success_criteria>
- [ ] Implementation authority confirmed before execution started
- [ ] Blocking anti-patterns answered before any work
- [ ] Isolation resolved and reported before dispatch, and every plan isolated
- [ ] Plans grouped into waves respecting dependencies and file overlap
- [ ] Each plan executed by a coder subagent, verified on disk
- [ ] Every executor carried the guard its isolation model calls for — the
      branch check under `harness-worktree`, the root pin under
      `orchestrator-worktree` — and any exit-42 halt was treated as blocked
      with its worktree preserved
- [ ] Every wave integrated through `worktree.merge-wave` before checks or review
- [ ] Undeclared deletions and merge conflicts escalated, never merged past
- [ ] Cleanup ran without `--force`, and anything preserved was reported
- [ ] Checkpoints escalated to the user, not guessed
- [ ] Configured checks run per wave, against the integrated tree, and passing
- [ ] Requirement coverage aggregated, with gaps reported
- [ ] Code review run; critical findings fixed and re-reviewed
- [ ] Roadmap plans ticked only for complete summaries
- [ ] Folded todos closed, STATE.md updated, work committed
- [ ] Phase session left open and reported, with `/ship` named as what
      delivers it
</success_criteria>
