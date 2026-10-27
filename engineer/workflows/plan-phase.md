<!-- workflow: plan-phase; roles: coordinator, phase-researcher, planner, plan-checker -->
<purpose>
Prepare executable phase plans through a planner and an independent goal-backward plan-checker. The coordinator owns routing, revision integration and shared records; it does not write the plan it dispatched or review its own work.
</purpose>
<authority>
Every phase needs a real discussion record before planning. Planning never grants implementation permission. Design approval, a ready plan and a mode flag do not authorize execution. Completion reports that implementation awaits an explicit instruction for the selected phase.
</authority>
<required_reading>
@~/.claude/engineer/RULES.md
@~/.claude/engineer/references/universal-anti-patterns.md
@~/.claude/engineer/references/planner-guidance.md
@~/.claude/engineer/references/failing-direction.md
@~/.claude/engineer/references/worker-handoff.md
</required_reading>
<available_agent_types>
Use exact roles `phase-researcher`, `planner`, `plan-checker`, `codebase-mapper`; no generic fallback.
</available_agent_types>
<model_selection>
Before each dispatch, resolve that exact role with `engineer_run query resolve-model ROLE --raw` and `engineer_run query resolve-effort ROLE --raw`. Pass both resolved values inline on the dispatch. Omit a field whose value is `inherit`; do not pass an empty model or assume a frontmatter model overrides the dispatch. A continued or correction worker uses its own resolved role values.
</model_selection>
<process>
<step name="initialize">
Require a phase identifier. Parse `--skip-research`, `--research`, `--gaps`, `--text`, and `--force`. Research flags are mutually exclusive. Set MODE to `standard` or `gap_closure`. Read and execute `engineer/workflows/_runtime-launcher.snippet.sh`, then run `engineer_run query phase.locate "${PHASE_NUMBER}"`. Stop on a missing or inconsistent locator result; quote and enter its `worktree`. Run `engineer_run query init.plan-phase "${PHASE_NUMBER}"`. Read actual `phase_found`, `phase_dir`, `context_path`, `research_path`, `ui_spec_path`, `artifact_files`, `artifacts`, `models`, `efforts`, `text_mode` and `prior_verify_commands`. Check required roles through resolve-model/resolve-effort; a resolution failure is a blocker, never permission to self-plan. Resolve context_window explicitly with config-get. Derive SPEC presence from actual artifact filenames ending -SPEC.md while excluding -UI-SPEC.md; derive research_partial from the research artifact's actual status rather than a missing alias. A later bundle may supply equivalent computed fields, but do not silently assume them. Apply response_language to prose only. Use the actual existing phase_dir returned by phase.locate and phase initialization for every artifact. An absent directory is a failed phase lookup, not permission to construct a parallel directory from a guessed slug.
</step>
<step name="open_session">
Inspect `engineer_run query session.status` and phase locator lineage. Reuse the matching phase session. Adopt a named clean isolated checkout only through `engineer_run query session.adopt phase "${PHASE_NUMBER}"`; otherwise use `engineer_run query session.open phase "${PHASE_NUMBER}"`. Stop on failure. Enter the returned quoted worktree, verify branch/root identity, re-run init.plan-phase there, and report branch/path in one line. Keep the session open and do not deliver it here.
</step>
<step name="closed_phase_gate">
Read and follow `engineer/workflows/plan-phase/steps/closed-phase-gate.md`. `--gaps` is the explicit gap-closure exemption; `--force` is an explicit replan override and never implementation authority. Preserve completed plans and their summaries unless the user specifically authorized replacing them.
</step>
<step name="load_context">
Read the actual CONTEXT.md, extracting locked decisions, canonical_refs, code_context, deferred ideas and prior acceptance. If it is absent, offer only "Discuss first" or "Cancel"; do not plan anyway. On Discuss first, execute the discussion workflow only within its existing authorization and then return to planning. Read the actual ordinary SPEC resolved from artifact_files when one exists, plus the separate existing ui_spec_path. Preserve locked boundaries and lift resolved edges, prohibitions and UI considerations into must_haves. Read canonical references in full when assigned, not just their names or summaries.
</step>
<step name="refresh_codebase_maps">
Choose only maps relevant to the phase: technology dependencies need STACK, component boundaries need ARCHITECTURE, conventions need CONVENTIONS, tests need TESTING, external seams need INTEGRATIONS, and structural navigation needs STRUCTURE. Run `engineer_run query codebase.status`. Dispatch `codebase-mapper` for each missing or Git-history-stale relevant map, with inline resolved model/effort, exact source paths and exact output map ownership. Wait for all assigned workers before integrating any map. Confirm status from current Git evidence and retain `CURRENT_CODEBASE_MAP_PATHS`; a remembered timestamp or a squashed SHA alone does not prove freshness.
</step>
<step name="handle_research">
Decide whether research is warranted from unresolved implementation uncertainty, unfamiliar dependencies, version changes and stale relevant evidence. Honor explicit `--research` and `--skip-research`. Do not ask an optional research question whose answer is already established by the code and scope. Existing adequate research may be reused with its source revision and limits recorded.

When warranted, dispatch `Agent(subagent_type="phase-researcher", model=<inline resolved value>, effort=<inline resolved value>, prompt=<complete bounded research packet>)`, omitting inherited values. Give the phase goal, requirement IDs, complete CONTEXT decisions, SPEC/UI-SPEC paths, current map paths, source revision, actual version constraints and the exact research output path. Include worker-handoff and context-limit continuation instructions. Require cited sources, executed technology checks before recommendations, unresolved questions and `## RESEARCH COMPLETE`, `## RESEARCH BLOCKED`, or `## RESEARCH PARTIAL`. Preserve a blocked result as evidence, never as a usable recommendation.

Wait without editing the worker's paths. For a partial result, preserve usable evidence and continue the same bounded question from the recorded handoff in a fresh isolated checkout, at most twice. Consume a handoff only after its continuation is integrated. An unavailable recommendation check stays explicitly unvalidated. On a blocked research result, stop only dependent planning; report the missing evidence rather than inventing a recommendation. Use `engineer_run query handoff.list` and `handoff.consume` for actual continuation records.
</step>
<step name="check_existing_plans">
If plans exist, show their IDs and whether each already has a SUMMARY. Offer Replace, Review, or Cancel for the concrete selected plan set. Replacing an executed plan can invalidate evidence; require explicit scope and preserve history. Review does not authorize rewriting, and Cancel leaves the plans untouched.
</step>
<step name="prepare_planner_packet">
Capture `PLAN_INPUT_REVISION=$(git rev-parse HEAD)` after maps and research are integrated. Read actual *_path fields and artifact_files from INIT rather than assuming a generic paths map or extracting JSON with an inline JavaScript process. Locate SPEC and UI-SPEC separately. Read `engineer/workflows/plan-phase/steps/stall-detection-helpers.md` before dispatching and use its bounded observation policy.

Build the complete planning packet:
```text
<planning_context>
Repository: {absolute session worktree}
Branch: {session branch}
Input revision: {PLAN_INPUT_REVISION}
Mode: {standard|gap_closure}
Phase goal and requirement IDs: {actual values}
<required_reading>
AGENTS.md, selected phase CONTEXT, relevant SPEC/UI-SPEC, RESEARCH and current map paths;
engineer/templates/phase-prompt.md; assigned role; every canonical reference and applicable skill.
</required_reading>
<handoff>{actual prior handoff, or explicitly none}</handoff>
<codebase_maps>{CURRENT_CODEBASE_MAP_PATHS}</codebase_maps>
<tracked_source_paths>{actual current owned source roots; exclude generated state and mirrors}</tracked_source_paths>
<failing_direction_contract>
Read engineer/references/failing-direction.md. Every task has a verifier that can fail for its intended defect, with explicit automated command and failure direction. Discover and cite real symbols and paths before naming them. Do not create a test that only mirrors the implementation.
</failing_direction_contract>
</planning_context>
<downstream_consumer>
Execute-phase consumes wave, depends_on, files_modified, files_deleted, resources, requirements, read_first, acceptance criteria, must_haves and the Artifacts this phase produces section. Use explicit symbols, commands and boundaries. Include resolved SPEC edges/prohibitions and UI-SPEC considerations without silently dropping them.
</downstream_consumer>
```
For a context window of at least 500000 tokens, include relevant prior phase summaries as additional evidence; never replace required source files with those summaries.
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

4. **`<verify>`** — Include both `<automated>` and `<fails_when>` for each task; the command must be able to fail for the intended defect.

**Why this matters:** Executor agents work from the plan text. Vague instructions like "update the config to match production" produce shallow one-line changes. Concrete instructions like "add DATABASE_URL, set POOL_SIZE=20, add REDIS_URL, and read config/runtime.ts before editing" produce complete work without turning the planner into the executor.
</deep_work_rules>

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

Add constraints: do not relitigate locked decisions; split plans at real outcome/dependency boundaries; serialize overlapping edit ownership into later waves; declare deletions and shared resources; keep observed source scope; report a necessary phase split instead of editing the roadmap; mark unanswered unresearched assumptions `[ASSUMED]`; return `## PLANNING PARTIAL` with a precise continuation before the context boundary. New threat IDs continue after the phase's highest `T-{phase}-NN`; never renumber an existing canonical threat identity.
</step>
<step name="spawn_planner">
Dispatch `Agent(subagent_type="planner", model=<inline resolved value>, effort=<inline resolved value>, prompt=<the full packet plus constraints and continuation contract>)`. Omit inherited dispatch values. Require committed plans and a return identifying exact owned files, commit, requirement coverage, threats, acceptance, declared checks and `## PLANNING COMPLETE`, `## PLANNING PARTIAL`, or a real `## CHECKPOINT REACHED` with the actual blocked decision. A checkpoint is not a completed plan. The coordinator waits; it does not touch worker-owned paths or integrate an unfinished worker.
</step>
<step name="handle_preparer_return">
Read and execute the complete engineer/workflows/_canonical-threat-tracking.md procedure for planned and unplanned phase risks. Preserve each PLAN register, deterministic checklist identity, explicit match review, full Security risk variant, actual provider-rendered anchors and independent audit. Never default to a standalone issue for every planned risk.

Reconcile the return against `engineer_run query phase-plan-index "${PHASE_NUMBER}"` and current Git commits. Zero plans is a blocked result, not success. Reconcile plan threats with canonical issue identities and keep stable IDs. Permit one PLANNING PARTIAL continuation from the recorded handoff without asking; integrate only after confirmed worker stop. A recommended phase split is reported and stops planning that depends on it; manage it through `/phase --insert` under separate authorization. For a missing terminal marker, use `engineer_run query find-phase "${PHASE_NUMBER}"` and read the actual committed plans before deciding whether the worker completed. Report source-audit gaps with their cited paths; do not fabricate source evidence.
</step>
<step name="spawn_checker">
Capture `PLAN_REVIEWED_REVISION=$(git rev-parse HEAD)` after all planner commits are integrated. Dispatch `Agent(subagent_type="plan-checker", model=<inline resolved value>, effort=<inline resolved value>, prompt=<complete review packet>)`, omitting inherited values. Give both input and reviewed revisions, full goal/requirements/CONTEXT/SPEC/UI-SPEC, every plan, current maps, research limitations and any handoff. Require goal-backward verification of observable truths, artifacts and key links; requirement and locked-decision coverage; real source paths and symbols; dependency and ownership waves; threat mitigations; meaningful failure directions; declared check argv; documentation obligations; and full template contracts.

Require canonical `## PLAN REVIEW` and `Verdict: approved | needs-revision`, stable finding IDs, BLOCKER versus INFO, cited evidence and exact unmet acceptance. This worker is read-only. Wait for all continuations; a missing portion of the assigned coverage is not an approval. Preserve INFO as advisory without sending it back as required rework. Retain observations of legacy `## VERIFICATION PASSED` and `## ISSUES FOUND` markers for source-compatibility diagnosis; neither substitutes for the required canonical PLAN REVIEW verdict and full coverage. A malformed or missing canonical verdict is unusable evidence. Use filesystem fallback with find-phase and actual committed output if a session ends without a usable terminal message.
</step>
<step name="revision_loop">
On needs-revision, dispatch planner with a bounded `<revision_context>` packet: input/reviewed revisions, exact BLOCKER IDs, quoted evidence, authoritative decision references, affected plan paths, accepted unaffected outcomes and the smallest permitted correction. The planner must not rewrite unrelated plans or change acceptance to silence the checker. Integrate its committed correction after confirmed stop, refresh relevant maps with codebase.status when source evidence changed, and dispatch a fresh plan-checker on the new revision. Reuse prior evidence only for unchanged inputs and coverage, naming the revision comparison. Never carry approval over changed plan content. Join all partial continuations before routing a verdict. Stop after three correction iterations with the remaining concrete blockers and required decision; do not declare success or start implementation because the loop cap was reached.
</step>
<step name="requirements_coverage">
Run the deterministic coverage backstop below after checker approval. A heuristic feature mismatch is a candidate finding to inspect against actual plan objectives; do not invent a gap solely from word choice. A proposed scope change or deferred requirement needs an explicit decision and updated owning records. Do not silently proceed with an uncovered locked requirement.

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
→ Continue to `update_roadmap`.

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


</step>
<step name="update_roadmap">
Read `engineer_run query roadmap.get-phase "${PHASE_NUMBER}"` and `engineer_run query phase-plan-index "${PHASE_NUMBER}"`. Require an existing phase, at least one complete checked plan, unique plan IDs, valid dependency waves and no unresolved BLOCKER. Compare plan files, IDs, counts, waves and dependencies with the approved checker coverage. Write once with `engineer_run query roadmap.set-plans "${PHASE_NUMBER}" --plans "NN-MM: Actual plan title" ...`. Re-read the roadmap phase and plan index and compare every stored plan ID/count with disk. A disagreement blocks completion; do not hand-edit either side or repeat a mutation to hide the mismatch.
</step>
<step name="update_state">
After roadmap reconciliation, run `engineer_run query state.begin-phase "${PHASE_NUMBER}" --status "Ready to execute"` and `engineer_run query state.record-session --stopped-at "Phase ${PHASE_NUMBER} planned" --resume-file "${phase_dir}" --status "Ready to execute"`. Planning readiness remains separate from implementation permission.
</step>
<step name="commit">
Run `engineer_run query commit "docs(${padded_phase}): plan phase" --files "${phase_dir}" .planning/STATE.md .planning/ROADMAP.md` with actual changed paths. Include required shared-record updates even when an optional commit_docs preference would omit them. Keep the session open; do not push, open a PR or merge from planning.
</step>
<step name="completion">
Report phase goal, checked plan IDs/waves, research and map evidence, checker verdict, unresolved INFO, record reconciliation and commits. End: "Implementation awaits an explicit instruction to execute phase {N}." Do not run execute-phase from this completion.
</step>
</process>
<windows_troubleshooting>
Read `engineer/workflows/plan-phase/steps/windows-troubleshooting.md` if the host exhibits a quoting or shell-path failure; preserve quoted absolute worktree paths and re-run only the failed operation when authorized.
</windows_troubleshooting>
<anti_patterns>
Do not self-plan a dispatched scope, review your own plans, skip discussion, turn INFO into required work, hand-write roadmap structures, deliver the session here, or infer implementation authority from readiness.
</anti_patterns>
<success_criteria>
Relevant maps are current; warranted research has cited evidence and explicit limitations; committed planner output and independent checker coverage agree at the reviewed revision; requirement/decision coverage is complete; roadmap and state match disk; the session stays open; implementation still awaits explicit instruction.
</success_criteria>
