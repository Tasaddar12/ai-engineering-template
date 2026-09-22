<!-- workflow
step: quick
agent-roles: orchestrator, phase-preparer, coder, verifier
produces: .planning/quick/{id}/QUICK.md, {id}-PLAN.md, {id}-SUMMARY.md
consumes: STATE.md, config.yaml
-->

<purpose>
Execute a small, ad-hoc task with the same guarantees as phase work — atomic
commits, a recorded plan, and tracked state — without the overhead of a phase.
Quick mode spawns the phase-preparer (quick mode) and a coder, tracks the task
under `.planning/quick/`, and records the outcome in STATE.md.

With `--validate`: adds plan checking before execution and verification after it.
Use when the change touches something you cannot afford to get wrong.
</purpose>

<required_reading>
@~/.ai/references/worktree-sessions.md
Read all files referenced by the invoking prompt's execution_context before starting.
</required_reading>

<available_agent_types>
Valid subagent types (use these exact names — never fall back to a generic agent):
- researcher — researches technical approaches
- phase-preparer — creates plans from scope
- phase-checker — reviews plan quality before execution
- coder — executes plan tasks, commits, writes SUMMARY.md
- verifier — verifies completion against the stated goal
- code-reviewer — reviews source files for bugs and security issues
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

<scope_guardrail>
**A quick task is one focused change.** If the work needs more than three tasks,
touches several subsystems, or needs decisions captured for later, it is a phase:
stop and say so, then offer `/phase "<description>"`.

Scope is fixed once the plan is written. New capability discovered mid-task is a
todo (`/capture`), not an extension of this task.
</scope_guardrail>

<process>

<step name="parse_arguments">
Parse `$ARGUMENTS` for:
- `--validate` → `VALIDATE_MODE=true` (plan checking + verification)
- `--text` → `TEXT_MODE=true`
- Remaining text → `DESCRIPTION`

```bash
_root="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
for _c in "$_root"/.{ai,claude,codex}/runtime/phase.py "${CLAUDE_CONFIG_DIR:-$HOME/.claude}"/runtime/phase.py "${CODEX_HOME:-$HOME/.codex}"/runtime/phase.py; do
  [ -f "$_c" ] && PHASE_RUNTIME="$_c" && break
done
[ -n "${PHASE_RUNTIME:-}" ] || { echo "ERROR: phase runtime not found; run the installer." >&2; exit 1; }
phase_run() { "$(command -v python3 || command -v python)" "$PHASE_RUNTIME" "$@"; }
INIT=$(phase_run query init.quick)
```

Extract from the init JSON: `commit_docs`, `response_language`, `text_mode`,
`models`, `efforts`, `agents_installed`, `missing_agents`, `checks_configured`, `open`,
`paths`.

**If `response_language` is set:** all user-facing output MUST be presented in
`{response_language}`; technical terms, code, file paths and subagent prompts
stay in English.

**Text mode** (`text_mode` true, or `--text` in the arguments): replace every
AskUserQuestion with a plain-text numbered list and ask the user to type a
number. Required for runtimes without AskUserQuestion.

If `DESCRIPTION` is empty, ask for it:

```
AskUserQuestion(header: "Quick task", question: "What do you want to do?")
```

If it is still empty, re-prompt: "Please provide a task description."

If `agents_installed` is false, report `missing_agents` and stop — the workflow
cannot dispatch agents that are not installed.

Display the banner:

```
### ► QUICK TASK{VALIDATE_MODE ? " (VALIDATE)" : ""}

◆ {DESCRIPTION}
{VALIDATE_MODE ? "◆ Plan checking + verification enabled" : "◆ Plan → execute → commit"}
```
</step>



<step name="check_open_tasks">
If the init `open` array is non-empty, show those tasks and ask whether this is
new work or a continuation:

```
Open quick tasks:
- {id}: {title} ({status})
```

Use AskUserQuestion (header: "Quick task"; options: "Start a new one" /
"Resume {id}"). On resume, skip `create_task` and load the existing directory.
</step>

<step name="open_session">
Open the worktree this work lives in, before writing anything. Read
@~/.ai/references/worktree-sessions.md for the full contract.

```bash
SESSION=$(phase_run query session.open quick "${QUICK_LABEL}")
```

`QUICK_LABEL` is the id being resumed, or a slug of `DESCRIPTION` for new
work — the runtime allocates the real quick id inside the session, so the
label has to be stable before that happens.

Parse `worktree`, `branch`, `base`, `reused` and `synced`. **Run every
subsequent command in this workflow from `worktree`.** An open session for
this quick task is reused rather than replaced, so the work accumulates onto one branch
and arrives as one pull request.

Report it in one line:

```
Session: {branch} ({reused ? "resumed" : "opened"}) at {worktree}
```

If the verb fails, **stop and report its message**. It means isolation could not
be established, and continuing in the invoking checkout is the one outcome this
project does not allow — the dispatch guard would block the write anyway.
</step>

<step name="create_task">
**Delegate task creation to the runtime:**

```bash
RESULT=$(phase_run query quick.create "${DESCRIPTION}")
```

The runtime allocates `YYMMDD-NNN-slug`, creates the directory and writes
`QUICK.md` with `status: open`.

Extract: `id`, `directory`, `record`. Store as `QUICK_ID` and `QUICK_DIR`.
</step>

<step name="plan">
Display: `◆ Spawning phase-preparer... (runs in a subagent — no output until it returns, ~1–5 min; expected, not a freeze)`

```
Agent(
  prompt="
<planning_context>

**Mode:** ${VALIDATE_MODE ? 'quick-validate' : 'quick'}
**Directory:** ${QUICK_DIR}
**Description:** ${DESCRIPTION}

<required_reading>
- ${paths.state} (Project State)
- ./CLAUDE.md or ./AGENTS.md (if present — follow the project's own guidelines)
</required_reading>

**Project skills:** check `.agents/skills/` or `.claude/skills/` (whichever exists)
— read the SKILL.md files and account for their rules in the plan.

</planning_context>

<constraints>
- Create a SINGLE plan with 1-3 focused tasks
- Quick tasks are atomic and self-contained; if the work does not fit, say so
  and recommend a phase rather than producing a sprawling plan
- Authorize edit scope only from a live observation made at planning time.
  Historical STATE.md entries and recovery notes guide investigation; they are
  never edit authority
${VALIDATE_MODE ? '- Each task MUST carry `files`, `action`, `verify` and `done` fields' : ''}
${VALIDATE_MODE ? '- Generate `must_haves` in the plan frontmatter (truths, artifacts)' : ''}
</constraints>

<output>
Write the plan to: ${QUICK_DIR}/${QUICK_ID}-PLAN.md
Return: ## PLANNING COMPLETE with the plan path
</output>
",
  subagent_type="phase-preparer",
  ${models['phase-preparer'] === 'inherit' ? '' : `model="${models['phase-preparer']}",`}
  ${efforts['phase-preparer'] === 'inherit' ? '' : `effort="${efforts['phase-preparer']}",`}
  description="Quick plan: ${DESCRIPTION}"
)
```

> **ORCHESTRATOR RULE**: after calling Agent(), stop working on this task. Do not
> read more files, edit code or run tests while the subagent is active. Wait for
> its result. This prevents duplicate work, conflicting edits and wasted context.

After the preparer returns:
1. Verify the plan exists at `${QUICK_DIR}/${QUICK_ID}-PLAN.md`
2. Report: "Plan created: ${QUICK_DIR}/${QUICK_ID}-PLAN.md"

If the plan is missing, stop with: "phase-preparer failed to create ${QUICK_ID}-PLAN.md".
</step>

<step name="check_plan">
**Only when `VALIDATE_MODE` is true.** Otherwise skip to `execute`.

```
Agent(
  prompt="
Review ${QUICK_DIR}/${QUICK_ID}-PLAN.md against the stated task:

**Task:** ${DESCRIPTION}

Check goal-backward: would executing exactly these tasks deliver the task's
outcome? Report gaps, not style. Return:
## PLAN REVIEW
Verdict: approved | needs-revision
Findings: <numbered, each naming the task it affects>
",
  subagent_type="phase-checker",
  ${models['phase-checker'] === 'inherit' ? '' : `model="${models['phase-checker']}",`}
  ${efforts['phase-checker'] === 'inherit' ? '' : `effort="${efforts['phase-checker']}",`}
  description="Check quick plan ${QUICK_ID}"
)
```

On `needs-revision`, hand the findings back to the phase-preparer once. Cap at
two iterations; after that, present the remaining findings to the user and ask
whether to proceed, revise again, or stop.
</step>

<step name="execute">
Mark the task in progress, then dispatch the coder:

```bash
phase_run query quick.update "${QUICK_ID}" --status in_progress
```

The coder is a write-capable agent, so it gets its own checkout forked from the
session branch — the session worktree is where *you* work, not where the
executor does. Resolve the model and record the base first:

```bash
ISOLATION=$(phase_run query dispatch-isolation --raw --plan "${QUICK_ID}")
EXPECTED_BASE=$(git rev-parse HEAD)
```

Under `orchestrator-worktree`, create the checkout and pass its path as a root
pin; under `harness-worktree`, pass `isolation="worktree"` and record the branch
the agent reports:

```bash
phase_run query worktree.create "${QUICK_ID}" --phase "quick-${QUICK_ID}" \
  --base "${EXPECTED_BASE}" --files ${plan_files} --deletions ${plan_deletions}
```

```
Agent(
  prompt="
<execution_context>

**Plan:** ${QUICK_DIR}/${QUICK_ID}-PLAN.md
**Task directory:** ${QUICK_DIR}

<required_reading>
- ${QUICK_DIR}/${QUICK_ID}-PLAN.md
- ./CLAUDE.md or ./AGENTS.md (if present)
</required_reading>

</execution_context>

<constraints>
- Execute ONLY the tasks in the plan; new capability is out of scope
- Commit each completed task atomically with a descriptive message
- Write ${QUICK_DIR}/${QUICK_ID}-SUMMARY.md with status, files changed and how
  the change was confirmed to work
- If the plan turns out to be wrong, stop and report — do not improvise a
  different change
</constraints>

<output>
Return: ## EXECUTION COMPLETE with status (complete|blocked), files changed,
and the verification you actually ran
</output>
",
  subagent_type="coder",
  ${models['coder'] === 'inherit' ? '' : `model="${models['coder']}",`}
  ${efforts['coder'] === 'inherit' ? '' : `effort="${efforts['coder']}",`}
  isolation="worktree",
  description="Execute quick task ${QUICK_ID}"
)
```

> **ORCHESTRATOR RULE**: wait for the subagent. Do not edit code while it runs.

After the coder returns, read `${QUICK_DIR}/${QUICK_ID}-SUMMARY.md`. A returned
"complete" with no summary file, or with no commits, is not a completion —
report it as blocked.

Integrate the executor's branch into the session branch before checking
anything, for the same reason a wave is integrated before its checks run — the
work is not in your tree until it is merged:

```bash
phase_run query worktree.merge-wave --phase "quick-${QUICK_ID}"
phase_run query worktree.cleanup-wave --phase "quick-${QUICK_ID}"
```

Read the result. `blocked` non-empty means an undeclared deletion or a conflict;
escalate it rather than re-running the merge to get past it.
</step>

<step name="run_checks">
If `checks_configured` is true, run the project's configured checks:

```bash
phase_run query verification.run-checks
```

Report any failing check with its command and output tail. A failed check blocks
completion; hand the failure back to the coder or stop for the user.
</step>

<step name="verify">
**Only when `VALIDATE_MODE` is true.** Otherwise skip to `complete_task`.

```
Agent(
  prompt="
Verify the quick task delivered its stated outcome.

**Task:** ${DESCRIPTION}
**Plan:** ${QUICK_DIR}/${QUICK_ID}-PLAN.md
**Summary:** ${QUICK_DIR}/${QUICK_ID}-SUMMARY.md

Check the codebase, not the summary's claims. Return:
## VERIFICATION
Status: passed | gaps_found | human_needed
Findings: <what is actually true in the code>
",
  subagent_type="verifier",
  ${models['verifier'] === 'inherit' ? '' : `model="${models['verifier']}",`}
  ${efforts['verifier'] === 'inherit' ? '' : `effort="${efforts['verifier']}",`}
  description="Verify quick task ${QUICK_ID}"
)
```

On `gaps_found`, present the gaps and ask whether to fix now or capture them as
todos.
</step>

<step name="complete_task">
```bash
phase_run query quick.update "${QUICK_ID}" --status complete \
  --files "${changed_files[@]}" \
  --verification "${how_it_was_confirmed}"
```

Then record the task in STATE.md and commit:

```bash
phase_run query state.record-session --stopped-at "Quick task ${QUICK_ID}: ${DESCRIPTION}"
phase_run query commit "chore(quick): ${DESCRIPTION}" --files "${QUICK_DIR}" .planning/STATE.md
```
</step>

<step name="deliver_session">
This workflow owns the whole unit of work, so it delivers the session rather
than leaving it open. Follow the delivery sequence in
@~/.ai/references/worktree-sessions.md exactly and in order: the empty-session
check, `git push -u`, `pr.open`, `pr.checks`, the merge confirmation, then
`pr.merge`, `pr.sync` and `session.close`.

Every command runs from `SESSION.worktree`.

**Title:** `Quick: ${DESCRIPTION}`

**Body:** compose it from the task's own records — the `QUICK.md` entry and the coder's `${QUICK_ID}-SUMMARY.md` — not from the diff. State what the task fixed, the files it touched, and how the change was confirmed. When `--validate` ran, include the verification status.

If the coder halted and the task was reported blocked, do **not** deliver: the session stays open with the work in it, and the report says so. Delivery is for completed work.


Report the snippet's delivery line before the output below. A `failing` check
verdict, a declined merge or a preserved session are all reported as they stand
and none of them is worked around — a preserved session is unmerged work.
</step>

<step name="completion">
```
Quick task complete: {QUICK_ID}

  {DESCRIPTION}
  Files changed: {count}
  Verified by: {how it was confirmed}
{VALIDATE_MODE ? "  Verification: {status}" : ""}

Record: {QUICK_DIR}/QUICK.md

---

## What's Next

- `/quick <description>` — another quick task
- `/progress` — where the project stands
- `/capture <idea>` — park anything this surfaced

---
```
</step>

</process>

<anti_patterns>
- Don't let a quick task grow into a phase mid-flight — stop and recommend `/phase`
- Don't skip the plan; "it's small" is how unreviewed changes ship
- Don't accept a coder's "complete" without a SUMMARY.md and real commits
- Don't hand-write the QUICK.md record — `quick.create` and `quick.update` own it
- Don't add quick tasks to ROADMAP.md; they deliberately live outside it
- Don't finish with the session still open — an undelivered session is
  work on a branch nobody merged
- Don't merge past a `failing` or `pending` check verdict, and don't
  `--force` a preserved session away
</anti_patterns>

<success_criteria>
- [ ] Task directory and QUICK.md created by the runtime
- [ ] Plan written by the phase-preparer subagent
- [ ] Plan checked when `--validate` was passed
- [ ] Coder executed only the planned tasks, with atomic commits and a SUMMARY.md
- [ ] Configured project checks run and passing
- [ ] Verification run when `--validate` was passed
- [ ] QUICK.md marked complete with files and verification recorded
- [ ] STATE.md updated and the change committed
- [ ] Session delivered: pull request opened, its check verdict judged,
      the merge confirmed, and the session closed or its preservation
      reported
</success_criteria>
