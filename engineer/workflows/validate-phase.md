<purpose>
Audit Nyquist validation gaps for a completed phase. Generate missing tests. Update VALIDATION.md.
</purpose>

<required_reading>
@engineer/references/ui-brand.md
</required_reading>

<available_agent_types>
Valid Claude/Codex roles (use exact names — do not fall back to 'general-purpose'):
- nyquist-auditor — Validates verification coverage
</available_agent_types>

<process>

## 0. Initialize

Read and execute engineer/workflows/_runtime-launcher.snippet.sh in the current shell. Parse the phase argument as data; absent an argument, select the last executed roadmap phase from `engineer_run query phases.list` and its committed complete SUMMARYs. Do not choose by filesystem order or a placeholder STATE value.

```bash
engineer_run query phase.locate "${PHASE_NUMBER}"
```

Require found=true; retain the absolute worktree, branch, phase_dir and session identity. Enter that worktree before `engineer_run query init.phase-op "${PHASE_NUMBER}"`. Require phase_found=true. No workspace flag or overflow-file protocol is supported. Extract response_language and text_mode from actual init output.

**If `response_language` is set:** All user-facing output of this workflow — narration between tool calls, status updates, progress notes, findings, questions, prompts, and explanations — MUST be presented in `{response_language}`. Technical terms, code, file paths, and subagent prompts stay in English — only user-facing output is translated.

Parse: `phase_dir`, `phase_number`, `phase_name`, `phase_slug`, `padded_phase`.

```bash
NYQUIST_ENABLED=$(engineer_run query config-get workflow.nyquist_validation --default true --raw)
AUDITOR_MODEL=$(engineer_run query resolve-model nyquist-auditor --raw)
AUDITOR_EFFORT=$(engineer_run query resolve-effort nyquist-auditor --raw)
```

Require true/false and successful model/effort resolution; omit each inherited host parameter. The default is on. An explicit false disables automatic gap writing and is reported as disabled, never as compliant. A direct audit may still return read-only gaps; never run removed loop-hook machinery.

### 0a. Authority and phase session

Read actual user instruction and phase CONTEXT. An explicit `/validate-phase N` authorizes its bounded test-gap generation; an automatic invocation needs already recorded implementation authority covering these tests. Record the actual authority in CONTEXT before dispatch. Discussion, a plan, or a flag alone cannot authorize implementation or product repairs. Without writing authority, return the read-only cited gap packet and pending next action; continue independent evidence work.

Reuse the matching isolated phase session from phase.locate/session.status. If a new session is needed, use `engineer_run query session.open phase "${PHASE_NUMBER}"`; adopt only an established owned isolated checkout with `session.adopt phase N`. Enter the returned worktree, re-initialize and retain root/branch/base/session/caller identity. Never open a second session when called by verify-work.

Automatic validation is a WRITE preflight, before any frozen read-only verification batch. If requested during an active batch, first wait for every check/specialist and confirmed stop; then write/integrate tests and start a fresh batch. A write-capable nyquist-auditor is never a frozen-batch member.

Display `ENGINEER > VALIDATE PHASE {N}: {name}`.

## 1. Detect Input State

```bash
VALIDATION_FILE=$(ls "${PHASE_DIR}"/*-VALIDATION.md 2>/dev/null | head -1)
SUMMARY_FILES=$(ls "${PHASE_DIR}"/*-SUMMARY.md 2>/dev/null)
```

- **State A** (`VALIDATION_FILE` non-empty): Audit existing
- **State B** (`VALIDATION_FILE` empty, `SUMMARY_FILES` non-empty): Reconstruct from artifacts
- **State C** (`SUMMARY_FILES` empty): Exit — "Phase {N} not executed. Run /execute-phase {N} first."

## 2. Discovery

### 2a. Read Phase Artifacts

Read all PLAN and SUMMARY files. Extract: task lists, requirement IDs, key-files changed, verify blocks.

### 2b. Build Requirement-to-Task Map

Per task: `{ task_id, plan_id, wave, requirement_ids, has_automated_command }`

### 2c. Detect Test Infrastructure

State A: Parse from existing VALIDATION.md Test Infrastructure table.
State B: Filesystem scan:

```bash
find . -name "pytest.ini" -o -name "jest.config.*" -o -name "vitest.config.*" -o -name "pyproject.toml" 2>/dev/null | head -10
find . \( -name "*.test.*" -o -name "*.spec.*" -o -name "test_*" \) -not -path "*/node_modules/*" 2>/dev/null | head -40
```

### 2d. Cross-Reference

Match each requirement to existing tests by filename, imports, test descriptions. Record: requirement → test_file → status.

## 3. Gap Analysis

Classify each requirement:

| Status | Criteria |
|--------|----------|
| COVERED | Test exists, targets behavior, runs green |
| PARTIAL | Test exists, failing or incomplete |
| MISSING | No test found |

Build: `{ task_id, requirement, gap_type, suggested_test_path, suggested_command }`

For every COVERED claim, cite the requirement wording, exact assertion/test ID, source revision, actual runner argv, and a current passing receipt or explicit pending execution. A filename/import/description match is a candidate, not coverage proof. Track sampling frequency (no three consecutive tasks without automated validation), feedback latency and every requirement, including edge/backstop and prohibition obligations. Human-only outcomes stay separately required.

No demonstrated gaps → Step 6. Set `nyquist_compliant: true` only when all required automated and sampling obligations have actual current passing evidence. User-deferred execution leaves coverage pending and compliance false.

## 4. Present Gap Plan

**Text mode (`workflow.text_mode: true` in config or `--text` flag):** Set `TEXT_MODE=true` if `--text` is present in `$ARGUMENTS` OR `text_mode` from init JSON is `true`. When TEXT_MODE is active, replace every `AskUserQuestion` call with a plain-text numbered list and ask the user to type their choice number. This is required for non-Claude runtimes (OpenAI Codex) where `AskUserQuestion` is not available.
For a direct interactive invocation without already supplied scope approval, present the concrete gap table and options below. Automatic preflight under recorded implementation authority proceeds within that approved scope without re-asking. This menu cannot waive a required check:
1. "Fix all gaps" → Step 5
2. "Retain gaps for manual review" → record unresolved obligations and rationale, Step 6 (never compliant)
3. "Cancel" → exit

## 5. Spawn nyquist-auditor

Prepare one bounded assignment from the read-only cited COVERED/PARTIAL/MISSING packet. The coordinator owns the requirement map and VALIDATION; nyquist-auditor owns only enumerated tests/fixtures and its assigned schema-valid SUMMARY. It may not change acceptance, implementation, shared status or CONTEXT. Preserve max three test-debug iterations per gap and escalate product defects.

```bash
ISOLATION=$(engineer_run query dispatch-isolation --phase "${PHASE_NUMBER}" --plan "${AUDIT_PLAN}")
```

Use only returned harness-worktree or orchestrator-worktree strategy. Under orchestrator-worktree call `engineer_run query worktree.create "${AUDIT_PLAN}" --phase "${PHASE_NUMBER}" --base "${EXPECTED_BASE}" --files ${EXACT_OWNED_PATHS}` with each real owned path separately quoted. Under harness-worktree use native isolation="worktree", verify the actual assigned branch/base, and record it through worktree.record-agent with exact paths. No mode disables isolation. Prepare a real bounded PLAN under the phase's schema before dispatch; its acceptance/checks/requirements/issue_refs and SUMMARY destination must match the assignment, not a fabricated phase or existing plan ID.

```text
Agent(
  subagent_type="nyquist-auditor",
  model=<actual AUDITOR_MODEL; omit if inherit>,
  effort=<actual AUDITOR_EFFORT; omit if inherit>,
  prompt="Read the resolved agents/nyquist-auditor.md in full. <assignment>absolute isolated root; branch; full expected base; exact tests/fixtures and SUMMARY path; actual implementation authority; user check ordering</assignment><required_reading>complete PLANs/SUMMARYs/CONTEXT/SPEC/VALIDATION, relevant source, test conventions and complete SUMMARY template</required_reading><gaps>cited requirement-level packet with exact test IDs, behavioral assertions and evidence</gaps><test_infrastructure>framework, configuration, exact argv, cwd, timeout and resources</test_infrastructure><constraints>No production or shared-record edits; max three debug iterations; no weakening acceptance. Commit owned files and valid SUMMARY before return. User-deferred execution remains pending; never mint a passing receipt.</constraints>"
)
```

Resolve every prompt value before dispatch. Wait for the worker's terminal result; a timeout is not exit. Do not duplicate its work. Require root/branch/base/head, exact owned commits, schema-valid committed SUMMARY status, coverage per requirement, commands actually executed/pending, and Remaining. `GAPS FILLED` is not sufficient without those artifacts/evidence. All source-changing returns, including PARTIAL/ESCALATE, preserve useful commits and a blocked SUMMARY. Confirm stop before continuation or reassigning paths.

- GAPS FILLED: validate committed scope and evidence; integrate with `engineer_run query worktree.merge-wave --phase "${PHASE_NUMBER}"`.
- PARTIAL/ESCALATE: retain escalated requirements as blockers, not converted to manual-only success. A legitimate inherently human-only outcome needs approved acceptance and actual human evidence; a failing automated assertion remains an implementation gap. Preserve the worker checkout/branch and request bounded correction for in-scope product defects under existing authority.
- Tests authored with user-deferred executions: record generated/pending counts, not resolved/green. Preserve blocked SUMMARY; do not bypass merge-wave's complete-summary guard. Resume the same worker after execution is allowed, then integrate only a valid complete result.

After integration, run `engineer_run query verification.run-checks` on the integrated revision when permitted; consume only current input-bound receipts. If checks are deferred, do not execute them, mutate receipts or claim compliance. Return the complete preflight packet to verify-work before it captures a new frozen revision.

## 6. Generate/Update VALIDATION.md

**State B (create):**
1. Read the COMPLETE template from `engineer/templates/VALIDATION.md`, including sampling examples, consumer contracts and sign-off guidance
2. Fill: frontmatter (`status: validated` only with actual complete evidence; otherwise preserve draft/pending status permitted by the template), Test Infrastructure, Per-Task Map, Manual-Only, Sign-Off
3. The coordinator writes to `${PHASE_DIR}/${PADDED_PHASE}-VALIDATION.md`; preserve every required template section and actual historical audit/sign-off evidence, never manufacture approval

**State A (update):**
1. Update Per-Task Map statuses, retain escalated/failing/pending requirements in the open gap table (Manual-Only only for approved inherently human-only behavior), update frontmatter (`status: validated` only with actual complete evidence; otherwise preserve draft/pending status permitted by the template)
2. Append to the audit trail through the owning verb — it compares against the LAST `## Validation Audit` block and skips the write entirely when nothing material changed (#5105 R3; #4981: idempotence alone is insufficient for VALIDATION, whose content legitimately changes with the plan/SUMMARY set, so this call is made AFTER the Per-Task Map update above, not instead of it):

```bash
engineer_run query verification.append-audit "${PHASE_DIR}/${PADDED_PHASE}-VALIDATION.md" \
  --heading "Validation Audit" \
  --body "Gaps found: {N}; resolved with passing evidence: {M}; escalated: {K}; pending execution: {P}; revision: {SHA}"
```

## 7. Commit and tracking

The worker commits its tests and SUMMARY. The coordinator commits only its exact VALIDATION/authorized PLAN/CONTEXT record changes:

```bash
engineer_run query commit "docs(phase-${PHASE_NUMBER}): record validation evidence" --files "${PHASE_DIR}/${PADDED_PHASE}-VALIDATION.md"
```

Apply engineer/references/git-workflow.md for authorized draft tracking and canonical issue preview/publication/readback. Do not stage worker files again, push outside the authorized delivery boundary, or merge a PR without human instruction. Route uncovered requirements by stable finding ID and preserve issue_refs; failures are not acceptance waivers.

## 8. Results and caller return

Report COMPLIANT only with all current evidence, otherwise PARTIAL/BLOCKED with exact missing requirement/test, generated/passing/failing/pending counts, worker/record hashes, integrated revision, receipts, required human actions, session and remaining interface dependencies. Return the packet to the active verify-work caller; it must independently verify the fresh integrated source. A generated file is not a filled gap and no downstream command suggestion substitutes for completion.

</process>

<success_criteria>
- [ ] Nyquist config checked with default true; disabled is explicit, never compliant
- [ ] Input state detected (A/B/C)
- [ ] State C exits cleanly
- [ ] PLAN/SUMMARY files read, requirement map built
- [ ] Test infrastructure detected
- [ ] Gaps classified (COVERED/PARTIAL/MISSING)
- [ ] Actual authority and concrete gap scope established
- [ ] Auditor spawned with complete context
- [ ] All three return formats handled
- [ ] VALIDATION.md created or updated
- [ ] Worker-owned tests/SUMMARY committed; coordinator records committed separately
- [ ] Results with routing presented
</success_criteria>
