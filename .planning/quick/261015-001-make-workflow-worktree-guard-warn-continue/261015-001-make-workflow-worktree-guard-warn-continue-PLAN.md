---
phase: quick-261015-001-make-workflow-worktree-guard-warn-continue
plan: "01"
type: execute
wave: 1
depends_on: []
files_modified:
  - .ai/hooks/worktree-guard.sh
  - .ai/hooks/worktree-guard.test.sh
  - .ai/hooks/context-handoff.sh
  - .ai/hooks/context-handoff.test.sh
  - tests/test_install.py
  - .ai/hooks/README.md
  - .ai/RULES.md
  - .ai/workflows/execute-phase.md
  - .ai/workflows/quick.md
  - .ai/references/worktree-sessions.md
  - .ai/install.py
files_deleted: []
autonomous: true
requirements: [QUICK-85]
acceptance: [Q85-01, Q85-02, Q85-03]
documentation:
  - .ai/hooks/README.md
  - .ai/RULES.md
  - .ai/workflows/execute-phase.md
  - .ai/workflows/quick.md
  - .ai/references/worktree-sessions.md
resources: []
checks:
  - [bash, .ai/hooks/worktree-guard.test.sh]
  - [bash, .ai/hooks/context-handoff.test.sh]
  - [python, -m, unittest, discover, -s, tests, -p, test_install.py, -k, registered_hooks, -v]
must_haves:
  truths:
    - "A write-capable Agent or Task dispatch with missing or wrong worktree isolation emits actionable stderr guidance and exits 0."
    - "Primary-checkout writes, including scratchpads, and cross-checkout absolute paths emit warnings and exit 0."
    - "Allowed write-capable dispatches retain handoff recording; read-only, properly isolated, irrelevant and indeterminate cases retain their existing quiet/fail-open behavior."
    - "Workflow guidance still starts work in worktrees while accurately describing the advisory guard and unchanged runtime safeguards."
    - "Qualified and bare attributed stops classify consistently, recover unfinished work, suppress recovery for complete summaries, and consume their matching active entry once."
  artifacts:
    - path: .ai/hooks/worktree-guard.sh
      provides: "Warning-and-continue dispatch/write checks with handoff recording"
    - path: .ai/hooks/worktree-guard.test.sh
      provides: "Regression coverage for warning status, guidance, scratchpads, patch paths and unchanged quiet cases"
    - path: .ai/hooks/context-handoff.sh
      provides: "Consistent normalized role classification, stack matching and attributed-stop recovery"
    - path: .ai/hooks/context-handoff.test.sh
      provides: "Warned dispatches remain eligible for handoff tracking"
    - path: tests/test_install.py
      provides: "Installed Codex and Claude launchers preserve advisory results"
  key_links:
    - from: .ai/install.py
      to: .ai/hooks/worktree-guard.sh
      via: "Existing Agent/Task and editing-tool PreToolUse registrations remain intact"
    - from: .ai/hooks/worktree-guard.sh
      to: .ai/hooks/context-handoff.sh
      via: "record_dispatch appends allowed write-capable agents to the active handoff stack"
---

<objective>
Make the workflow worktree guard warn and continue, including scratchpad edits.
Issue: https://github.com/Tasaddar12/ai-engineering-template/issues/85
Tracking draft: https://github.com/Tasaddar12/ai-engineering-template/pull/86

This is authorized template maintenance. QUICK-85 and Q85-* below are task-local
traceability labels, not adopting-project requirements. Preserve the unfilled
PROJECT, STATE, REQUIREMENTS and ROADMAP skeletons.
</objective>

<context>
Planning source revision: 5bbab00866b49895af7ee4e52674971f8053f490.
Current planning input: f97733794d5e641a0b85bb850d56c84f64d4a226 (QUICK tracking only).
Repository: D:/Codex Projects/ai-engineering-template/.worktrees/quick-worktree-guard-warning-091517643
Branch: quick-worktree-guard-warning-091517643

Read AGENTS.md, .ai/RULES.md, .agents/skills/quick/SKILL.md,
.ai/workflows/quick.md, .ai/runtime/TEMPLATE-CONTRACT.md and
.ai/references/git-workflow.md. The coordinator opened issue #85 and draft #86
before any test script. The preparer ran no tests or benchmarks. Execute tests
only after the coordinator confirms this existing tracking prerequisite.

Live source grounding: worktree-guard.sh has three exit-2 branches: unisolated
write-capable dispatch, a write in the primary checkout, and an absolute path
into another checkout. Dispatch matching already strips plugin prefixes into
role, while recording currently compares the raw subagent string. The direct
suite expects refusal for Agent/Task, fallback roles, primary/planning writes,
notebooks, patch headers and Windows-style paths. context-handoff.test.sh expects
an unisolated dispatch to leave no active entry. The installed-launcher test in
tests/test_install.py expects exit 2. Adjacent documentation and installer comments
still claim hard hook enforcement. These exact paths were inspected at planning.


CR-01 correction input and prior reviewed revision:
e7627378268da77593e196705a03cd9055b467a9. The joined batch reported local tests
passing and documentation PASS; code review found Q85-02 incomplete. The guard
records plugin:workflow:coder as coder, but context-handoff.sh's attributed
SubagentStop branch passes raw agent_type to agent_writes_files, then to
stack matching/recovery. Qualified stops exit before recovery or drop_active.
Existing added regressions use anonymous stops and miss this path. Task 3 is
an authorized issue #85 correction; no runtime, installer or new threat scope.
Boundaries: retain worktree-first workflow guidance, isolation configuration,
worktree creation failures, base checks, worker root pinning, and merge/cleanup
checks. Do not alter runtime isolation implementation, hook registrations,
launcher executable behavior, shared status or unrelated documentation.
</context>

<tasks>
<task type="auto" tdd="true">
  <name>Task 1: Make dispatch and write warnings succeed with intact handoffs</name>
  <files>.ai/hooks/worktree-guard.sh, .ai/hooks/worktree-guard.test.sh, .ai/hooks/context-handoff.test.sh, tests/test_install.py</files>
  <read_first>.ai/hooks/worktree-guard.sh, .ai/hooks/worktree-guard.test.sh, .ai/hooks/context-handoff.test.sh, .ai/hooks/context-handoff.sh, .ai/hooks/lib/agent-roles.sh, .ai/hooks/lib/handoff-io.sh, tests/test_install.py</read_first>
  <behavior>
  - Missing or incorrect isolation on write-capable Agent/Task calls warns on stderr, provides isolation guidance and returns 0, including qualified role names and library fallback.
  - Primary source/planning/scratchpad writes and absolute targets in another checkout warn and return 0 across Write/Edit/MultiEdit/NotebookEdit/apply_patch; retain Windows path handling.
  - Warned write-capable dispatches are recorded once with usable role and plan metadata; isolated dispatches remain recorded, read-only dispatches remain unrecorded.
  - Correct in-worktree paths, unrelated tools, empty/malformed payloads and indeterminate targets retain quiet successful behavior; scratch paths outside repositories remain allowed.
  </behavior>
  <action>Update the existing behavioral expectations first and add explicit scratchpad and qualified-role handoff regressions. Exercise MultiEdit explicitly and a multi-file apply_patch with the scratchpad after a safe in-worktree target, so path scanning cannot pass only because the first path warned. Run the direct suites to capture the expected pre-change disagreement after the tracking prerequisite. Replace the three worktree-condition refusals with clearly labeled stderr warnings and successful continuation. Preserve actionable session.open, isolation and path-rebuilding guidance, but remove instructions implying that this advisory hook must stop the action. Keep parsing, missing-dependency fail-open behavior and role-library fallback. Ensure the dispatch warning reaches existing recording logic; use consistent normalized role recognition so qualified write-capable dispatches are recorded as well. Update installed-launcher assertions for exit 0 plus warning/guidance on both hosts; properly isolated calls remain quiet. Do not change registration or launcher mechanics. This first task is the end-to-end slice from registered dispatch through hook outcome and active handoff tracking.</action>
  <acceptance_criteria>Q85-01: Every recognized worktree-condition case returns 0 with a warning and useful guidance. Q85-02: Existing successful cases and handoff bookkeeping remain correct, including a warned qualified dispatch and scratchpad edits.</acceptance_criteria>
  <verify>
    <automated>bash .ai/hooks/worktree-guard.test.sh</automated>
    <fails_when>Nonzero exit or any FAIL line; the final failed count must be zero.</fails_when>
    <automated>bash .ai/hooks/context-handoff.test.sh</automated>
    <fails_when>Nonzero exit or any FAIL line, including absent or duplicate warned-dispatch recording.</fails_when>
    <automated>python -m unittest discover -s tests -p test_install.py -k registered_hooks -v</automated>
    <fails_when>Nonzero exit, FAILED/ERROR, or zero selected tests; both installed host subtests must succeed.</fails_when>
  </verify>
  <done>The three focused checks pass with warning/exit-0 assertions, explicit scratchpad coverage and retained active-agent tracking. Commit the owned task slice with actual check evidence.</done>
</task>

<task type="auto">
  <name>Task 2: Describe advisory guard behavior while preserving worktree-first operations</name>
  <files>.ai/hooks/README.md, .ai/RULES.md, .ai/workflows/execute-phase.md, .ai/workflows/quick.md, .ai/references/worktree-sessions.md, .ai/install.py</files>
  <read_first>.ai/hooks/README.md, .ai/RULES.md, .ai/workflows/execute-phase.md, .ai/workflows/quick.md, .ai/references/worktree-sessions.md, .ai/install.py, .ai/hooks/worktree-guard.sh</read_first>
  <action>Keep the existing bottom-of-RULES Hooks and validation advisory policy. Make concise corrections to the earlier conflicting hook-enforcement claims: both dispatch and editing checks warn and continue, including scratchpads; worktrees remain the preferred workflow. Correct quick.md's session-open failure explanation that claims the guard would block a subsequent write, while preserving the actual instruction to stop on session creation failure. Retain runtime isolation configuration, creation/base failures, root pinning, branch checks, protected merge rules and cleanup evidence. In install.py, edit only comments around managed registrations and Windows launch/exit-status rationale so they describe current advisory semantics without changing executable code. In hooks README retain the launcher probing and status propagation facts while removing claims that this guard currently denies calls. Compare each changed claim directly against Task 1 source and retained workflow/runtime boundaries; do not rewrite surrounding policies.</action>
  <acceptance_criteria>Q85-03: All six exact files describe current advisory hook behavior without claiming a worktree warning blocks the action, and still direct ordinary work through the existing isolated session and worker workflow.</acceptance_criteria>
  <verify>
    <automated>git diff --check</automated>
    <fails_when>Nonzero exit or whitespace-error output.</fails_when>
    <inspection>Read the changed paragraphs against the implemented hook; inspect the diff to confirm install.py changes are comments only and that creation/base/root/merge/cleanup safeguards remain unchanged. Check path links resolve from each document.</inspection>
  </verify>
  <done>Focused documentation matches warning-and-continue behavior. All retained safeguards are explicit and untouched. Commit the owned documentation slice and required execution SUMMARY.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 3: Correct CR-01 attributed qualified-stop handling</name>
  <files>.ai/hooks/context-handoff.sh, .ai/hooks/context-handoff.test.sh</files>
  <read_first>.ai/hooks/context-handoff.sh, .ai/hooks/context-handoff.test.sh, .ai/hooks/worktree-guard.sh, .ai/hooks/lib/agent-roles.sh, .planning/quick/261015-001-make-workflow-worktree-guard-warn-continue/261015-001-make-workflow-worktree-guard-warn-continue-SUMMARY.md</read_first>
  <behavior>Attributed qualified and bare write-capable stops use consistent role classification and matching. For both warned and isolated qualified dispatches, missing/blocked SUMMARY produces recovery, complete SUMMARY produces none, and the matching active-stack entry is consumed exactly once without consuming another dispatch.</behavior>
  <action>Address CR-01 against reviewed/input revision e7627378268da77593e196705a03cd9055b467a9. Add regressions carrying agent_type="plugin:workflow:coder" on the actual SubagentStop payload, covering warned and isolated dispatches, incomplete and complete SUMMARY outcomes, normalized stack matching and once-only active-entry consumption. Preserve bare-role, anonymous-stop and read-only behavior. Normalize the stop identity consistently for write-capable classification, matching the guard's normalized active entry, and recovery identity; do not modify shared role helpers, runtime or installer. Run the handoff regression before and after the production correction, then the guard regression. Update the existing execution SUMMARY with CR-01, repair commit, exact tested revision and actual results; earlier passing tests do not establish the repaired path. Commit this bounded repair.</action>
  <acceptance_criteria>Q85-02 / CR-01 required property: consistent normalized qualified/bare stop classification, stack matching and recovery. An attributed qualified stop cannot bypass recovery or leave its matching active entry for an unrelated later stop.</acceptance_criteria>
  <verify>
    <automated>bash .ai/hooks/context-handoff.test.sh</automated>
    <fails_when>Nonzero exit or any FAIL line, including missing recovery, recovery for a complete SUMMARY, duplicate consumption or an unrelated active entry removed.</fails_when>
    <automated>bash .ai/hooks/worktree-guard.test.sh</automated>
    <fails_when>Nonzero exit or any FAIL line; warned/isolated dispatch recording must remain correct.</fails_when>
  </verify>
  <done>Attributed qualified and bare stop regressions pass for warned/isolated dispatches and incomplete/complete SUMMARY outcomes; matching active entries are consumed once. CR-01 repair and execution SUMMARY evidence are committed.</done>
</task>
</tasks>

<source_audit>
GOAL: QUICK.md title and issue #85 are covered by Tasks 1-2, with Q85-02 / CR-01 corrected by Task 3.
REQ: No adopting-project requirements exist; QUICK-85 names this maintenance scope.
RESEARCH: Coordinator scout packet is evidence; every required source consumer is
covered by Tasks 1-2. No new research artifact or capability is needed.
CONTEXT: User-authorized warn-and-continue behavior, scratchpad inclusion, tracking
before tests and preservation boundaries are covered above. No phase decisions
or adoption records are invented.
</source_audit>

<verification>
Run the three focused checks after tracking exists, and inspect the exact source
and documentation diff. The coordinator owns configured checks and any broader CI
suite from .github/workflows/validate.yml, plus independent review. Record the
actual tested revision, commands, results and skips; no benchmark is required.
Security review: not applicable. This changes an advisory repository workflow
hook, not host permissions or privilege/tenant isolation. Runtime creation,
base validation, root pinning, merge and cleanup boundaries remain unchanged.
No additional security threats identified in the inspected scope.
</verification>

<success_criteria>
All Q85-01 through Q85-03 outcomes are demonstrated. No worktree-condition refusal
remains in the hook; no dispatch recording is lost. The adoption skeleton and
unrelated runtime safeguards are preserved. Owned source, tests, documentation
and execution summary are committed with accurate evidence.
</success_criteria>

<output>
Create .planning/quick/261015-001-make-workflow-worktree-guard-warn-continue/261015-001-make-workflow-worktree-guard-warn-continue-SUMMARY.md with status, task commits, exact paths, acceptance/documentation coverage and actual checks. Return commits to the coordinator without publishing or changing shared status.
</output>
