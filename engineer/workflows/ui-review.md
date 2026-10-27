<purpose>
Retroactive 6-pillar visual audit of implemented frontend code. Standalone command that works on any project — engineer-managed or not. Produces scored UI-REVIEW.md with actionable findings.
</purpose>

<required_reading>
@~/.claude/engineer/references/ui-brand.md
</required_reading>

<available_agent_types>
Valid engineer subagent types (use exact names — do not fall back to 'general-purpose'):
- ui-auditor — Audits UI against design requirements
</available_agent_types>

<process>

## 0. Initialize and reuse the phase session

Read `engineer/RULES.md`, `engineer/references/worker-handoff.md`,
`engineer/references/verification-evidence.md`, the complete `agents/ui-auditor.md`
and canonical `engineer/references/git-workflow.md`. Execute the runtime launcher
snippet, resolve the actual phase using `engineer_run query phase.locate N`, quote
and enter its worktree, then run `init.phase-op N`. Require phase_found and actual
phase paths; never fabricate a phase for an unonboarded template.

Inspect `session.status` and reuse the matching caller/session. Adopt an owned
clean isolated checkout with `session.adopt phase N`, otherwise use `session.open
phase N`. Recheck root/branch and initialize there. When invoked by verify-work,
reuse its prepared packet and SAME frozen batch; do not run initialization,
record-writing or publication steps inside that batch.

Read actual UI scope, locked decisions and source. For a CLI/backend phase with
no UI, return cited not_applicable without invented screens, audit scores or
browser use. Resolve `workflow.ui_interaction_capture` explicitly (default false),
text_mode and response_language. Resolve exact ui-auditor model and effort with
resolve-model/resolve-effort; pass both inline, omitting inherited fields. An
unavailable role/capability is a concrete dependency, not permission to self-audit.

## 1. Detect Input State

```bash
SUMMARY_FILES=$(ls "${PHASE_DIR}"/*-SUMMARY.md 2>/dev/null)
UI_SPEC_FILE=$(ls "${PHASE_DIR}"/*-UI-SPEC.md 2>/dev/null | head -1)
UI_REVIEW_FILE=$(ls "${PHASE_DIR}"/*-UI-REVIEW.md 2>/dev/null | head -1)
```

**If `SUMMARY_FILES` empty:** Exit — "Phase {N} not executed. Run /execute-phase {N} first."

**Text mode (`workflow.text_mode: true` in config or `--text` flag):** Set `TEXT_MODE=true` if `--text` is present in `$ARGUMENTS` OR `text_mode` from init JSON is `true`. When TEXT_MODE is active, replace every `AskUserQuestion` call with a plain-text numbered list and ask the user to type their choice number. This is required for non-Claude runtimes (OpenAI Codex) where `AskUserQuestion` is not available.
**If an existing review exists:** reuse only if its source revision, full input
digests and required live evidence are current. Explicit View returns it with its
actual limitations. Otherwise audit the current requested scope without a routine
re-audit/view confirmation. A reused stale score cannot establish acceptance.

## 2. Gather Context Paths

Build file list for auditor:
- All SUMMARY.md files in phase dir
- All PLAN.md files in phase dir
- UI-SPEC.md (if exists — audit baseline)
- CONTEXT.md (if exists — locked decisions)

## 3. Spawn ui-auditor

```
◆ Spawning UI auditor... (runs in a subagent — no output until it returns, ~1–5 min; expected, not a freeze)
```

Build prompt:

```markdown
Read the resolved source or installed `agents/ui-auditor.md` in full.

<objective>
Conduct 6-pillar visual audit of Phase {phase_number}: {phase_name}
{If UI-SPEC exists: "Audit against UI-SPEC.md design contract."}
{If no UI-SPEC: "Audit against abstract 6-pillar standards."}
</objective>

<required_reading>
- {summary_paths} (Execution summaries)
- {plan_paths} (Execution plans — what was intended)
- {ui_spec_path} (UI Design Contract — audit baseline, if exists)
- {context_path} (User decisions, if exists)
</required_reading>

Read assigned/applicable skills selected by description.

<config>
phase_dir: {phase_dir}
padded_phase: {padded_phase}
interaction_capture: {actual resolved policy}
frozen_revision: {full captured revision}
identity: {absolute root, branch/base, phase/session/caller}
inputs: {actual UI-SPEC/CONTEXT/PLAN/source paths and digests}
authority: {actual implementation/design authority and check-order constraints}
fixture: {explicit assigned running URL and safe fixture identity, or unavailable}
capture_dir: {explicit external directory outside the source checkout, or absent}
acceptance: {complete criterion IDs, UI-SPEC and required interaction/state coverage}
</config>
```

Omit null file paths but explicitly report missing required inputs. Captures use
only actual available host/browser APIs; no automatic package/driver installs,
arbitrary server probing or source-tree screenshots. The auditor is read-only,
returns the COMPLETE report and coverage limitations, and never commits, writes
phase records, prompts independently, publishes or dispatches children. Missing
live/browser/fixture evidence is BLOCKED/unverified, never a visual pass.

```
Agent(
  prompt=ui_audit_prompt,
  subagent_type="ui-auditor",
  model="{UI_AUDITOR_MODEL}",
  effort="{UI_AUDITOR_EFFORT}",
  description="UI Audit Phase {N}"
)
```

> **ORCHESTRATOR RULE — CODEX RUNTIME**: After calling Agent() above, stop working on this task immediately. Do not read more files, edit code, or run tests related to this task while the subagent is active. Wait for the subagent to return its result. This prevents duplicate work, conflicting edits, and wasted context. Only resume when the subagent result is available.

## 4. Handle Return

Require canonical `## UI REVIEW`, observed/gaps_found/blocked status, exact
frozen source/input identity, complete six-pillar report, criterion evidence and
unexamined scope. The compatibility `## UI REVIEW COMPLETE` marker alone cannot
prove a live audit. Wait for ALL assigned checks/specialists and continuations
before shared writes, corrections or a joined verdict. In verify-work, return the
report to its original independent verifier for reconciliation; do not persist it
mid-batch. A timeout is not confirmed worker stop.

After a valid joined return:

Display score summary:

```
### ENGINEER ► UI AUDIT COMPLETE ✓

**Phase {N}: {Name}** — Overall: {score}/24

| Pillar | Score |
|--------|-------|
| Copywriting | {N}/4 |
| Visuals | {N}/4 |
| Color | {N}/4 |
| Typography | {N}/4 |
| Spacing | {N}/4 |
| Experience Design | {N}/4 |

Top fixes:
1. {fix}
2. {fix}
3. {fix}

Full review: {path to UI-REVIEW.md}

---

Required live evidence missing: {exact BLOCKED criteria and next evidence needed}
```

## Automated UI Verification (when Playwright-MCP is available)

Use the same complete method in
`engineer/workflows/verify-work/steps/automated-ui-verification.md` while preparing
the frozen batch. Available host browser APIs may navigate only the assigned
fixture, capture the actual declared states and compare dimensions, color, layout,
spacing and typography against UI-SPEC. Observed/failed/BLOCKED remain distinct;
brand feel and content tone needing human judgment enter the concrete UAT script.
No live capability means source-derived review with required observations still
BLOCKED, not an automatic pass or silent skip.

## 4a. Findings and coordinator capture

After the complete join and currentness check, the coordinator records the full
report at the actual `{phase_dir}/{padded_phase}-UI-REVIEW.md`, preserving source,
input, fixture and capture identities, all scores, top three fixes and detailed
findings. Route required in-scope defects to authorized isolated correction and
fresh verification. Keep unrelated recommendations in the report's Deferred
scope with evidence; never turn them into required rework. Canonical issues use
the full issue template, stable identity, matching, hash-bound preview/publication
and provider readback from git-workflow; report actual unavailable dependencies.
No routine verify/accept/ignore menu, acceptance waiver or automatic new scope.

## 5. Commit coordinator-owned report when permitted

```bash
engineer_run query commit "docs(${padded_phase}): UI audit review" --files "${PHASE_DIR}/${PADDED_PHASE}-UI-REVIEW.md"
```

</process>

<success_criteria>
- [ ] Phase validated
- [ ] SUMMARY.md files found (execution completed)
- [ ] Existing review handled (re-audit/view)
- [ ] ui-auditor spawned with correct context
- [ ] UI-REVIEW.md created in phase directory
- [ ] Score summary displayed to user
- [ ] Exact failed/unverified acceptance and user authority preserved
</success_criteria>
