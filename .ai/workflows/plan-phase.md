<!-- workflow
step: plan
agent-roles: orchestrator, researcher, phase-preparer, phase-checker
produces: RESEARCH.md, {NN}-{MM}-PLAN.md
consumes: CONTEXT.md, ROADMAP.md, REQUIREMENTS.md, STATE.md
-->

<purpose>
Turn a phase's goal and captured decisions into executable plans. Optionally
research the approach first, spawn the phase-preparer to write the plans, then
have the phase-checker verify goal-backward that executing exactly those plans
would deliver the phase.

The orchestrator routes. It does not write the plans itself.
</purpose>

<required_reading>
@~/.ai/references/universal-anti-patterns.md
@~/.ai/references/methods/planner-guidance.md
@~/.ai/references/methods/failing-direction.md
</required_reading>

<available_agent_types>
Valid subagent types (use these exact names — never fall back to a generic agent):
- researcher — researches how to implement a phase, produces RESEARCH.md
- phase-preparer — writes executable plans with task breakdown and dependencies
- phase-checker — verifies plans will achieve the phase goal before execution
- codebase-mapper — maps existing code when its map is missing or stale
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

<process>

<step name="initialize">
```bash
_root="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
for _c in "$_root"/.{ai,claude,codex}/runtime/phase.py "${CLAUDE_CONFIG_DIR:-$HOME/.claude}"/runtime/phase.py "${CODEX_HOME:-$HOME/.codex}"/runtime/phase.py; do
  [ -f "$_c" ] && PHASE_RUNTIME="$_c" && break
done
[ -n "${PHASE_RUNTIME:-}" ] || { echo "ERROR: phase runtime not found; run the installer." >&2; exit 1; }
phase_run() { "$(command -v python3 || command -v python)" "$PHASE_RUNTIME" "$@"; }
INIT=$(phase_run query init.plan-phase "${PHASE}")
```

Parse: `phase_found`, `phase_number`, `padded_phase`, `phase_name`, `phase_slug`,
`phase_dir`, `expected_phase_dir`, `goal`, `requirements`, `depends_on`,
`has_context`, `has_research`, `research_partial`, `has_spec`, `has_plans`, `plan_count`,
`artifacts`, `prior_context`, `models`, `efforts`, `agents_installed`, `missing_agents`,
`context_window`, `commit_docs`, `text_mode`, `response_language`, `paths`.

**If `response_language` is set:** all user-facing output MUST be presented in
`{response_language}`; technical terms, code, file paths and subagent prompts
stay in English.

If `phase_found` is false:

```
Phase [X] not found in roadmap.
Use /progress to see available phases.
```

Exit.

If `agents_installed` is false, report `missing_agents` and stop.

Display the banner: `► PLAN PHASE {phase_number}: {phase_name}`
</step>

<step name="parse_arguments">
Recognised flags:
- `--skip-research` — do not run the research step
- `--research` — force research even when RESEARCH.md already exists
- `--gaps` — plan gap closure from an existing VERIFICATION.md rather than the phase itself
- `--text` — plain-text prompts instead of AskUserQuestion

Set `MODE` to `standard` or `gap_closure` accordingly.
</step>

<step name="open_session">
This phase's work lives in one session worktree, shared by `/discuss-phase`,
`/plan-phase`, `/execute-phase` and `/verify-work` so the whole phase arrives as
one pull request. Join it before writing anything:

```bash
SESSION=$(phase_run query session.open phase "${padded_phase}")
```

An open session for this phase is reused, not replaced. **Run every subsequent
command from its `worktree`**, and report it in one line:

```
Session: {branch} ({reused ? "resumed" : "opened"}) at {worktree}
```

If the verb fails, stop and report its message rather than continuing in the
checkout you were invoked from.

**Do not deliver it here.** `/ship` opens the pull request, judges its checks and
closes the session once the phase is verified.
</step>

<step name="closed_phase_gate">
If the phase's roadmap status is `Complete` and `--gaps` was not passed:

```
Phase {N} is already complete.

Planning it again would produce plans for work that shipped. If you have new
work, add a phase (`/phase`) or insert one (`/phase --insert {N}`). To close
verification gaps on this phase, pass --gaps.
```

Exit.
</step>

<step name="load_context">
**CONTEXT.md is the decision record.** Read
`${phase_dir}/${padded_phase}-CONTEXT.md` when `has_context` is true.

If `has_context` is false:

```
Phase {N} has no CONTEXT.md.

Planning without captured decisions means the preparer guesses at choices you
care about, and you review them as plans instead of as questions.
```

Use AskUserQuestion (header: "No context"; options: "Discuss first
(recommended)" / "Plan anyway" / "Cancel"). On the first, stop and point at
`/discuss-phase {N}`.

Extract from CONTEXT.md: `<decisions>` (locked — never re-litigated),
`<canonical_refs>` (MUST be passed to every downstream agent),
`<code_context>` (reusable assets), `<deferred>` (explicitly out of scope).

If `has_spec` is true, read the SPEC.md too: its requirements are locked and are
not re-derived by the preparer.
</step>

<step name="handle_research">
**Skip when `--skip-research` is set, or `has_research` is true, `research_partial`
is false and `--research` was not passed.** A partial RESEARCH.md is not finished
research: when `research_partial` is true, go straight to a continuation dispatch
(below) against the questions it lists as not yet researched.

Decide whether research is warranted. Research answers "how do we implement this
here?" — it is not a formality:

- Unfamiliar library, protocol or external system → research
- Approach already decided in CONTEXT.md, or the pattern exists in the codebase → skip
- Pure refactor or config work → skip

When research is warranted:

```
### ► RESEARCHING PHASE {phase_number}

◆ Spawning researcher... (runs in a subagent — no output until it returns, ~2–10 min; expected, not a freeze)
```

```
Agent(
  prompt="
<research_context>
**Phase:** {phase_number} — {phase_name}
**Goal:** {goal}
${handoff ? `
<handoff>
{the continuation field of phase_run query handoff.read <id>, verbatim}
</handoff>
This handoff replaces the reading this assignment lists below: ingest it first,
and open a listed file only as its reading rule allows.
` : ''}

<required_reading>
- {paths.project} (Project)
- {paths.requirements} (Requirements)
- {phase_dir}/{padded_phase}-CONTEXT.md (USER DECISIONS — locked, do not revisit)
- {every path in canonical_refs}
</required_reading>

**Project instructions:** read ./CLAUDE.md or ./AGENTS.md if present.
</research_context>
${continuing ? `
<continuation>
{phase_dir}/{padded_phase}-RESEARCH.md already exists and is partial. Read it
first. Research ONLY the questions under its ## Not Yet Researched section.
Edit each finding into the matching section and remove the question from the
list; do not rewrite or re-verify sections that are already written. Set
**Coverage:** complete when the list is empty.
</continuation>
` : ''}
<constraints>
- Research HOW to implement what CONTEXT.md decided; do not re-open those decisions
- Report options with trade-offs and cite what you actually read
- Name real files, versions and APIs; unverified claims are findings, not facts
- Flag anything that would change the phase's scope rather than absorbing it
- The context limit is not a blocker: at the limit, write what you have and
  return RESEARCH PARTIAL, never BLOCKED
</constraints>

<output>
Write research to: {phase_dir}/{padded_phase}-RESEARCH.md
Return: ## RESEARCH COMPLETE with the path and the decisions it unblocks, or
## RESEARCH PARTIAL with the questions not yet researched
</output>
",
  subagent_type="researcher",
  ${models['researcher'] === 'inherit' ? '' : `model="${models['researcher']}",`}
  ${efforts['researcher'] === 'inherit' ? '' : `effort="${efforts['researcher']}",`}
  description="Research phase {phase_number}"
)
```

> **ORCHESTRATOR RULE**: after calling Agent(), stop working on this task. Do not
> read more files, write plans or investigate in parallel while the subagent runs.
> Wait for its result. This prevents duplicate work and wasted context.

**Handle the return.** First verify `{phase_dir}/{padded_phase}-RESEARCH.md`
exists; a return of any kind with no file is a failure — report it and do not
proceed on the claim. Then route on the header the researcher returned:

| Return | Route |
|---|---|
| `## RESEARCH COMPLETE` | Continue to planning. |
| `## RESEARCH PARTIAL` | Continue the research — do not stop for the user. |
| `## RESEARCH BLOCKED` | Present the blocker and its options to the user; this is the only return that waits for them. |
| no recognised header | A failure: report it, as for a missing file. |

**Continuing partial research.** Re-dispatch the same `Agent(...)` call with the
`<continuation>` block, against the same file, and the researcher's handoff in a
`<handoff>` block, per [dispatching a continuation](../references/worker-handoff.md#dispatching-a-continuation):

```
◆ Research partial — continuing {N} open question(s) in a fresh researcher
```

Allow at most two continuations, and continue only while each pass shortens the
`## Not Yet Researched` list. When the list is empty, continue to planning. When
it stops shrinking, or the second continuation returns partial, continue to
planning anyway; the phase-preparer plans the covered scope and carries each
remaining question to the tasks that depend on it. List the unresearched
questions in the report. Do not ask the user to resume anything.

When research ends without another continuation, consume every remaining record
whose `agent` is `researcher`:

```bash
phase_run query handoff.consume <id>
```
</step>

<step name="check_existing_plans">
If `has_plans` is true and `MODE` is `standard`:

AskUserQuestion (header: "Plans exist"; question: "Phase {N} already has
{plan_count} plan(s). What do you want to do?"; options: "Replace them" /
"Review them" / "Cancel"). On "Replace them", note which plans have SUMMARY.md
files — a plan that already executed must not be silently replaced; call that out
explicitly before continuing.
</step>

<step name="spawn_preparer">
```
### ► PLANNING PHASE {phase_number}

◆ Spawning phase-preparer... (runs in a subagent — no output until it returns, ~1–5 min; expected, not a freeze)
```

```
Agent(
  prompt="
<planning_context>
**Phase:** {phase_number} — {phase_name}
**Goal:** {goal}
**Mode:** {standard | gap_closure}
**Depends on:** {depends_on}
${handoff ? `
<handoff>
{the continuation field of phase_run query handoff.read <id>, verbatim}
</handoff>
This handoff replaces the reading this assignment lists below: ingest it first,
and open a listed file only as its reading rule allows.
` : ''}

<required_reading>
- {paths.state} (Project State)
- {paths.roadmap} (Roadmap)
- {paths.requirements} (Requirements)
- {phase_dir}/{padded_phase}-CONTEXT.md (USER DECISIONS from /discuss-phase — locked)
- {phase_dir}/{padded_phase}-RESEARCH.md (Technical research, if it exists)
- {phase_dir}/{padded_phase}-SPEC.md (Locked requirements, if it exists)
- {phase_dir}/{padded_phase}-VERIFICATION.md (Gaps to close — gap_closure mode only)
- {every path in canonical_refs}
</required_reading>
${context_window >= 500000 ? `
**Cross-phase context (1M model enrichment):**
- CONTEXT.md and SUMMARY.md from the 3 most recent completed phases (locked
  decisions to stay consistent with, and what was already built so you reuse
  rather than duplicate)
- The same files from any phase named in this phase's "Depends on" field,
  regardless of recency
- Skip all other prior phases to stay within budget
` : ''}

**Phase requirement IDs (every id MUST appear in some plan's `requirements` field):** {requirements}

**Project instructions:** read ./CLAUDE.md or ./AGENTS.md if either exists.
**Project skills:** check `.agents/skills/` or `.claude/skills/` — read the SKILL.md
files and account for their rules.
</planning_context>

<downstream_consumer>
Output is consumed by /execute-phase. Plans need:
- Frontmatter: `wave`, `depends_on`, `files_modified`, `requirements`
- Tasks in XML form, each carrying `read_first` and `acceptance_criteria` (MANDATORY)
- Verification criteria per task
- `must_haves` for goal-backward verification (truths, artifacts)
- An \"Artifacts this phase produces\" section listing every symbol this phase
  creates: classes, functions, CLI flags, new file paths
</downstream_consumer>

<failing_direction_contract>
Every runnable `<automated>` verify command MUST be followed by a `<fails_when>`
sibling naming what output constitutes failure — an exit code, a string in the
output, a missing line. A command with no expressible failure mode is not an
acceptance test.

```xml
<verify>
  <automated>python -m unittest discover -s tests</automated>
  <fails_when>non-zero exit, or \"Ran 0 tests\" in the output</fails_when>
</verify>
```

One statement per runnable command, immediately after it. Name an OBSERVABLE
signal, never the word \"failure\": `non-zero exit` is complete, `the command
fails` is a restatement. `TBD`/`TODO`/`N/A`/`unknown` are rejected outright.
Ask: if this command were silently doing nothing, what in its output would tell
me? If you cannot answer, fix the command — do not invent a statement for it.
Rules and worked examples: @~/.ai/references/methods/failing-direction.md
</failing_direction_contract>

<tracked_source_paths>
Every path written into PLAN.md — `files_modified`, `must_haves.artifacts`,
action paths — must name git-tracked source, never a generated or ignored mirror.
Verify an existing path with `git ls-files -- <path>` (non-empty means tracked).
A path that does not exist yet is a new file; keep the intended path.
</tracked_source_paths>

<deep_work_rules>
Every task MUST include:
1. `<read_first>` — files the executor MUST read before touching anything: the
   file being modified (so it sees current state, not assumptions), any source of
   truth named in CONTEXT.md, and any file whose patterns, signatures or
   conventions must be replicated.
2. `<action>` — what changes, specifically enough to execute without inventing scope.
3. `<acceptance_criteria>` — what must be observably true when the task is done.
4. `<verify>` with `<automated>` and `<fails_when>` per the contract above.
</deep_work_rules>

<constraints>
- Do NOT re-litigate anything locked in CONTEXT.md
- Split into multiple plans when tasks exceed one coherent unit of work or when
  parts can run in parallel; set `wave` and `depends_on` accordingly
- Authorize edit scope only from what you observed at planning time
- If the phase cannot be planned as scoped, say so and recommend a split rather
  than producing a plan you do not believe in
- If RESEARCH.md still lists questions under ## Not Yet Researched, plan the
  covered scope; a task that depends on one carries it as an [ASSUMED]
  precondition to confirm, never an invented answer
- The context limit is not a blocker: at the limit, commit the plans you have
  and return PLANNING PARTIAL with the scope not yet planned
</constraints>
${continuing ? `
<continuation>
Plans already exist for part of this phase. They are read-only input: do not
edit or renumber them. Plan ONLY the scope the previous preparer listed as not
yet planned: {unplanned scope}. Number new plans after the last existing one.
</continuation>
` : ''}
<output>
Write plans to: {phase_dir}/{padded_phase}-{NN}-PLAN.md (01, 02, …)
Return: ## PLANNING COMPLETE with each plan path and its wave, or
## PLANNING PARTIAL with the scope not yet planned
</output>
",
  subagent_type="phase-preparer",
  ${models['phase-preparer'] === 'inherit' ? '' : `model="${models['phase-preparer']}",`}
  ${efforts['phase-preparer'] === 'inherit' ? '' : `effort="${efforts['phase-preparer']}",`}
  description="Plan phase {phase_number}"
)
```

> **ORCHESTRATOR RULE**: wait for the subagent. Do not plan in parallel.
</step>

<step name="handle_preparer_return">
Verify the plans exist on disk rather than trusting the return message:

```bash
phase_run query phase-plan-index "${phase_number}"
```

Extract `plans` and `count`. If the count is 0, the preparer failed — report it
and stop. Do not write plans yourself to cover for a failed agent.

If the preparer returned `## PLANNING PARTIAL`, the plans on disk are good and
the rest is unplanned. Re-dispatch the same `Agent(...)` call with the
`<continuation>` block naming the scope it listed, and the `phase-preparer`
handoff in a `<handoff>` block, per [dispatching a continuation](../references/worker-handoff.md#dispatching-a-continuation).
Do it once, without asking the user. Then re-read the plan index. If the
continuation also returns partial, continue to the checker with what exists.

If the preparer recommended splitting the phase, surface that to the user and
stop: splitting is a roadmap change (`/phase --insert`), not something to absorb
silently into plans.
</step>

<step name="spawn_checker">
```
### ► VERIFYING PLANS

◆ Spawning phase-checker...
```

```
Agent(
  prompt="
Review the plans for Phase {phase_number} goal-backward.
${handoff ? `
<handoff>
{the continuation field of phase_run query handoff.read <id>, verbatim}
</handoff>
This handoff replaces the reading this assignment lists below: ingest it first,
and open a listed file only as its reading rule allows.
` : ''}

**Goal:** {goal}
**Plans:** {each plan path from the plan index}
**Context:** {phase_dir}/{padded_phase}-CONTEXT.md
**Requirements:** {requirements}

Ask: if a competent executor did exactly what these plans say and nothing more,
would the phase goal be achieved? Report what is missing or wrong, not style.

Check specifically:
- Every phase requirement id appears in some plan's `requirements`
- Every task has read_first, acceptance_criteria and a verify with fails_when
- Decisions locked in CONTEXT.md are honoured, not re-opened
- `depends_on` and `wave` describe a workable execution order
- No task authorizes edits outside the phase scope

Return:
## PLAN REVIEW
Verdict: approved | needs-revision
Findings: <numbered; each names the plan and task it affects>
",
  subagent_type="phase-checker",
  ${models['phase-checker'] === 'inherit' ? '' : `model="${models['phase-checker']}",`}
  ${efforts['phase-checker'] === 'inherit' ? '' : `effort="${efforts['phase-checker']}",`}
  description="Check plans for phase {phase_number}"
)
```

If the checker reports plans it did not reach, dispatch a fresh phase-checker
for them with its handoff in a `<handoff>` block, per
[dispatching a continuation](../references/worker-handoff.md#dispatching-a-continuation).
Merge both reviews' findings before routing on the verdict.
</step>

<step name="revision_loop">
On `needs-revision`, hand the findings back to the phase-preparer to revise.
**Maximum 3 iterations.** Continue a revising preparer that returns
`## PLANNING PARTIAL` exactly as in `handle_preparer_return`, with its handoff
in the `<handoff>` block.

After the third, stop and present the outstanding findings to the user with a
choice: proceed as-is, revise a specific finding together, or cancel. Do not loop
indefinitely, and do not approve the plans yourself to end the loop.
</step>

<step name="refresh_codebase_maps">
Skip on a `--gaps` run.

```bash
phase_run query codebase.status
```

Every map `fresh` → continue. Any `missing` or `stale` → dispatch one
codebase-mapper per focus area named in `focus_areas`:

```
Agent(
  prompt="
Refresh the codebase map for focus area: {focus}.

Rewrite it against the current revision. Do not patch the old text.

Write to: .planning/codebase/{MAP}.md
Return: ## MAP COMPLETE with what changed since the previous revision.
",
  subagent_type="codebase-mapper",
  ${models['codebase-mapper'] === 'inherit' ? '' : `model="${models['codebase-mapper']}",`}
  ${efforts['codebase-mapper'] === 'inherit' ? '' : `effort="${efforts['codebase-mapper']}",`}
  description="Refresh the {focus} map"
)
```

> **ORCHESTRATOR RULE**: wait for the subagent before continuing.
</step>

<step name="update_roadmap">
Make the roadmap's plan checklist match the plans that now exist. For each plan
the preparer wrote that has no roadmap entry, the phase entry's `Plans:` list
needs the id and a one-line description.

```bash
phase_run query roadmap.get-phase "${phase_number}"
```

Compare its `plans` array to the plan index. Report any mismatch; the roadmap is
what `/progress` and `/next` route from, so a plan missing there is invisible.
</step>

<step name="update_state">
```bash
phase_run query state.begin-phase "${phase_number}" --status "Ready to execute"
phase_run query state.record-session \
  --stopped-at "Phase ${phase_number} planned (${plan_count} plans)" \
  --resume-file "${first_plan_path}"
```
</step>

<step name="git_commit">
```bash
phase_run query commit "docs(${padded_phase}): plan phase" --files "${phase_dir}" .planning/STATE.md .planning/ROADMAP.md
```
</step>

<step name="completion">
```
Phase {phase_number} planned: {plan_count} plan(s)

{each plan id}: {one-line description} (wave {N})

{If research ran:} Research: {phase_dir}/{padded_phase}-RESEARCH.md
Plan review: {approved | approved with noted findings}

---

## ▶ Next Up

**Phase {phase_number}: {phase_name}** — {goal}

`/clear` then:

`/execute-phase {phase_number}`

---
```
</step>

</process>

<anti_patterns>
- Don't write plans yourself — the phase-preparer writes them; you route and verify
- Don't accept "PLANNING COMPLETE" without the plan files on disk
- Don't re-open decisions locked in CONTEXT.md
- Don't skip the plan check to save time; it is the cheapest place to catch a wrong plan
- Don't loop revisions past 3 iterations — escalate to the user
- Don't research by default; research a real unknown or skip it
- Don't silently replace plans that already have summaries
- Don't open a pull request or merge from here — a phase session is
  delivered once, by `/ship`
- Don't close the phase session; the workflows after this one reuse it
</anti_patterns>

<success_criteria>
- [ ] Phase validated against the roadmap and not already complete
- [ ] Codebase maps fresh, or regenerated before planning against them
- [ ] CONTEXT.md loaded, with canonical refs passed to every downstream agent
- [ ] Research run only where warranted, and its file verified on disk
- [ ] Plans written by the phase-preparer, verified on disk via the plan index
- [ ] Every phase requirement id appears in some plan
- [ ] Plans reviewed goal-backward by the phase-checker
- [ ] Revisions capped at 3 iterations, with escalation instead of a silent pass
- [ ] Roadmap plan checklist matches the plans that exist
- [ ] STATE.md updated and everything committed
- [ ] Phase session joined before any write, and left open for `/ship`
</success_criteria>
