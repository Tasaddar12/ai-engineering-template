---
phase: quick-261013-001
plan: "01"
type: execute
wave: 1
depends_on: []
files_modified:
  - .ai/runtime/lib/phase_issues.py
  - .ai/runtime/lib/phases.py
  - .ai/runtime/lib/todo_issues.py
  - .ai/runtime/lib/delivery.py
  - .ai/runtime/phase.py
  - .ai/workflows/execute-phase.md
  - .ai/workflows/ship.md
  - .ai/references/git-workflow.md
  - .ai/runtime/README.md
  - tests/test_phase_issues.py
  - tests/test_phase_runtime.py
  - tests/test_todo_issues.py
  - tests/test_session_delivery.py
  - tests/test_workflow_links.py
files_deleted: []
autonomous: true
requirements: []
acceptance: [HANDOFF-01, PUBLICATION-01, PR-01, RECONCILE-01, AUTHORITY-01]
user_setup: []
must_haves:
  truths:
    - Every actionable problem still unresolved when authorized phase execution ends, defers work, or terminates early is represented by the appropriate canonical issue and URL, or an explicit retryable blocked-publication report when the platform is unavailable.
    - Fixed inline problems and routine checker findings resolved in this execution require no issue.
    - Supported phase handoff and phase.complete require reviewed issue_refs declarations on execution summaries; pr.open automatically applies the phase session gate.
    - Deferred work and pending human UAT remain follow-up references and cannot be closed by this PR.
    - Folded TODO reconciliation requires independently read-back MERGED PR evidence and CLOSED same-repository linked issue evidence; open or unknown results remain pending and retryable.
    - Authorized execution includes the necessary issue creation and update without a separate issue approval ceremony.
  artifacts:
    - path: .ai/runtime/lib/phase_issues.py
      provides: Bounded declared phase issue handoff, publication adapter, PR relation checks, and folded TODO reconciliation
    - path: tests/test_phase_issues.py
      provides: Offline Git and subprocess regression scenarios for phase issue boundaries
  key_links:
    - from: .ai/runtime/lib/phases.py
      to: .ai/runtime/lib/phase_issues.py
      via: phase.complete calls declared-record handoff validation before changing the roadmap
    - from: .ai/runtime/phase.py
      to: .ai/runtime/lib/delivery.py
      via: pr.open binds phase sessions and validates effective PR issue references
---

<objective>
Enforce truthful issue tracking at phase execution handoff and PR delivery using existing phase records and publication recovery.

Purpose: Prevent actionable leftovers, major halt problems, deferred work, and pending human acceptance from disappearing in prose or closing prematurely.
Output: One bounded runtime and workflow maintenance change, with offline regressions and documented limits. This is authorized template maintenance; the adoption skeleton remains unfilled.
</objective>

<execution_context>
@.ai/agents/coder.md
@.ai/templates/summary.md
@.ai/references/git-workflow.md
@.ai/references/worktree-path-safety.md
</execution_context>

<context>
Input/reviewed revision for this correction: d43f4ff30daf29d8e368bd81312939c70160b087 (includes PR #78).
Preparation root: D:/Codex Projects/ai-engineering-template/.worktrees/phase-issue-plan-revision-150003118.
Prior preparation input: 7dcf64136918e050454f2aabaf33aed8f481dc5d; corrections address PC-SEC-01 and PC-REG-01 only.
Integration session: D:/Codex Projects/ai-engineering-template/.worktrees/quick-phase-issue-enforcement-144616012.
Quick ID: 261013-001-enforce-phase-issue-handoffs-pr-references.

User constraints supplied by the coordinator: one coherent enforcement outcome, 1-3 tasks; implement and deliver a draft, never merge. Tracking issue #83 and draft PR #84 already exist before tests. Create or reuse the right issue for every actionable unresolved problem on ordinary completion, deferral, or early termination without another issue approval request. Required privacy handling and platform permissions still apply. Human UAT may remain pending while code advances, accurately tracked. Supported dispositions cannot exempt actionable unresolved work from tracking; blocked publication records failure and retry requirements without invalidating completed code.

Live evidence:
- .ai/runtime/lib/todo_issues.py:48 target pins origin and verifies repository identity; publish at 249 validates variant/shape and implements reviewed duplicate reuse and persisted attempted-intent recovery; require_closed at 341 rejects open/unresolved retirement.
- .ai/runtime/lib/issue_format.py:135 validate is deliberately structuralOnly; reuse it unchanged.
- .ai/runtime/lib/phases.py:325 complete currently ticks roadmap entries without issue handoff validation.
- .ai/runtime/lib/delivery.py:105 open_pr updates/creates without issue relationship checks; merge_pr at 233 can fall back to a fabricated MERGED result after unreadable readback.
- .ai/workflows/execute-phase.md:586 aggregate_results leaves Deferred/Remaining in prose; 653 close_phase_todos retires folded TODOs before merge.
- .ai/references/git-workflow.md:50 Follow-up issues retains blanket separate publication approval wording.
- worktrees.session_status returns session entries with kind, label, branch and worktree; use phase identity from existing session state.
- tests/test_todo_issues.py has fake-provider/subprocess, hostile GH_REPO, pagination, stale preview, uncertain-create and save-fault fixtures; tests/test_session_delivery.py OpeningPullRequests has a stateful offline gh seam.

Concurrent boundary: PR #80 owns threat-specific templates, issue_format/tests and additive threat tracking; preserve all threat structures and requirements. Shared execute-phase, ship and git-workflow edits are narrow generic handoff additions and must be integrated carefully with that owner. PR #76/#77 GitLab work is held. PR #78 routing is included in this corrected input; preserve its Git entrypoint routing. Do not implement provider changes or absorb these branches.

Design boundary: add a small phase_issues module only to adapt existing record/provider helpers; no separate ledger, framework, broad repository scan, new tracking architecture, or network calls on every edit. Runtime checks declared records; agents must identify omitted problems semantically. Arbitrary direct gh/API edits bypass the supported runtime gate and remain an explicit limitation.
</context>

<tasks>
<task type="auto" tdd="true">
  <name>Task 1: Trace an unresolved phase problem through existing publication and handoff</name>
  <files>.ai/runtime/lib/phase_issues.py, .ai/runtime/lib/phases.py, .ai/runtime/lib/todo_issues.py, .ai/runtime/phase.py, tests/test_phase_issues.py, tests/test_todo_issues.py, tests/test_phase_runtime.py</files>
  <read_first>.ai/runtime/lib/phases.py, .ai/runtime/lib/todo_issues.py, .ai/runtime/lib/todos.py, .ai/runtime/lib/issue_format.py, .ai/runtime/lib/text.py, .ai/runtime/lib/paths.py, .ai/runtime/phase.py, tests/test_todo_issues.py, tests/test_phase_runtime.py, .ai/templates/issue.md</read_first>
  <behavior>
    - A reviewed SUMMARY with issue_refs: [] passes when no problems remain; missing or malformed declarations fail the execution handoff and phase.complete before roadmap writes.
    - An unresolved actionable entry without a canonical issue fails; a platform failure returns an explicit pending retryable blocked-publication result and never claims successful tracking.
    - A canonical published/reused issue keeps its selected Bug or UAT kind; an invalid variant, sections, repository, stale snapshot, or ambiguous retry fails before remote mutation.
    - Completion and early termination use the same handoff gate; fixed-inline findings can be omitted after coordinator review.
  </behavior>
  <action>
Implement the first end-to-end slice through a small phase_issues adapter and registered phase.handoff, phase.issue-preview, phase.issue-publish and phase.issue-update verbs. Require explicit issue_refs lists on existing execution SUMMARY records at handoff, including blocked/halted results. Do not require new declarations on legacy CONTEXT, planning-only artifacts, or the adoption skeleton. Read only the selected phase's CONTEXT and execution SUMMARYs. If CONTEXT already carries issue_refs, include those declared entries too.

Use additive entries with stable id, summary, variant, state, relationship and existing issueRepo/issueURL/issueNumber linkage; state is unresolved, pending-human, resolved or blocked-publication, and relationship is resolving or followup. Require a nonempty reason for resolved and blocked-publication dispositions. Resolved means no actionable work remains; blocked-publication is incomplete tracking with a retry obligation, never a success exemption. pending-human requires followup. Use existing issuePublication fields for preview snapshot and persisted uncertain intent within that record entry. Validate unique stable IDs per record and canonical same-origin issue identity; reject PR URLs and repository mismatch.

Adapt existing todo_issues target, lookup, issue_view, digest, marker/readback, reviewed-public-body, and attempted-intent recovery helpers rather than duplicate those mechanisms or add a ledger. Phase issue operations select one exact source SUMMARY/CONTEXT entry in the chosen active phase, under the existing planning lock; reject traversal, symlinks, out-of-phase paths, and stale local records. Keep publication body separate from private record content. Deduplicate using current open/closed issue and related PR context, reuse matching issues, and preserve ambiguous or uncertain creation state without creating another issue. Preserve the current TODO API and tests. For issue-update require existing canonical linkage, separately reviewed body/title, preserved selected variant, format validation before mutation and remote readback after mutation; don't silently relabel Bug as UAT or the reverse. Reuse issue_format.validate unchanged with structuralOnly semantics. No automatic issue closure.

Gate phases.complete through phase.handoff before any roadmap writes; preserve successful current phase behavior after a reviewed empty list. In tests/test_phase_runtime.py, adjust affected phase.complete success fixtures (calls currently at lines 270, 277, 473, 499, 540, 749, 1463 and 1678) to author the selected phase's execution SUMMARY with reviewed issue_refs: [] before completion. Preserve each original assertion and avoid globally auto-inserting declarations in run_verb: missing-declaration negative scenarios must remain meaningful and prove no roadmap writes. Runtime reports declared-record validity only; it cannot prove completeness of prose or human acceptance.
  </action>
  <verify>
    <automated>python -m unittest discover -s tests -p test_phase_issues.py</automated>
    <fails_when>Non-zero exit, Ran 0 tests, or a missing/unlinked unresolved declaration changes the roadmap or mutates a remote issue.</fails_when>
    <automated>python -m unittest discover -s tests -p test_todo_issues.py</automated>
    <fails_when>Non-zero exit, Ran 0 tests, or existing duplicate/retry/privacy/repository guards regress.</fails_when>
    <automated>python -m unittest discover -s tests -p test_phase_runtime.py</automated>
    <fails_when>Non-zero exit, Ran 0 tests, existing phase completion/derived state assertions regress, or a missing declaration is silently accepted.</fails_when>
  </verify>
  <acceptance_criteria>
    - phase.handoff and phase.complete enforce SUMMARY declarations before state mutation.
    - Offline subprocess tests cover ordinary and blocked/halted summaries, empty declaration, malformed record, canonical link, publication failure, duplicate reuse, uncertain-create retry and type-preserving update.
    - Existing phase.complete success fixtures declare reviewed empty issue_refs while missing-declaration cases still reject before roadmap writes.
    - Existing issue_format and template files are unchanged.
  </acceptance_criteria>
  <done>One unresolved problem can be safely created/reused/updated and linked in its existing phase record; declared untracked problems cannot pass supported handoff.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Enforce PR relationships and reconcile only verified merged work</name>
  <files>.ai/runtime/lib/phase_issues.py, .ai/runtime/lib/delivery.py, .ai/runtime/phase.py, tests/test_phase_issues.py, tests/test_session_delivery.py</files>
  <read_first>.ai/runtime/lib/phase_issues.py, .ai/runtime/lib/delivery.py, .ai/runtime/lib/worktrees.py, .ai/runtime/lib/todos.py, .ai/runtime/lib/todo_issues.py, .ai/runtime/phase.py, tests/test_session_delivery.py, tests/test_phase_issues.py</read_first>
  <behavior>
    - pr.open automatically binds the branch's existing phase session; omitting optional phase arguments cannot bypass the phase gate.
    - Effective PR bodies retain resolving and followup references; deferred/pending-human entries cannot appear in provider auto-closing references, including unchanged-body edit/retarget calls.
    - Open, unknown, failed, or malformed merge/issue readback leaves folded TODOs pending; confirmed MERGED plus CLOSED linked issue permits retirement.
    - Retrying reconciliation after lagging issue closure succeeds without running reviews or creating issues; already completed selected TODOs are reported idempotently.
  </behavior>
  <action>
Bind phase PR delivery to existing session identity in pr.open; accept an explicit --phase only when consistent with an existing phase session, and fail on ambiguous/conflicting identity. Preserve generic non-phase PR behavior and all current explicit-base, body-file precedence and draft-state semantics. Validate handoff declarations and the actual effective PR body before creation/update. Read the existing PR body when body is omitted, so retarget-only calls do not skip the gate. Require canonical links for declared resolving and followup items, and reject closing keywords for deferred/unresolved/pending-human followup items, including same-repository shorthand and full URLs in provider-recognized closing references. Preserve extension seams and document supported-provider boundaries. Resolving status needs recorded demonstrated acceptance; a claimed status is not proof of actual human judgment.

Remove fabricated merge success: a successful provider command followed by unavailable, malformed, mismatched or non-MERGED readback is unknown/pending, never verified merge evidence. Keep the PR/worktree and expose a retryable result without attempting another merge or repeating source reviews.

Add phase.reconcile-todos for the coordinator's exact folded filenames from existing CONTEXT, with --pr canonical URL and explicit selected --todos filenames. Verify the PR belongs to the origin and reads back MERGED before any TODO retirement. Use existing todos.complete/require_closed for selected records, and validate snapshot/path before moving each item. Do not complete unselected or reviewed-only TODOs, close issues, or require a new tracking structure. Return per-item completed/already-completed/pending results and actionable retry reasons; unknown or still-open linked issues remain pending. Runtime validates selected filenames and remote evidence; coordinator owns the semantic correspondence to the folded CONTEXT entries. Retry the reconciliation alone when remote issue closure is delayed; no code-review or verification restart for unchanged source.
  </action>
  <verify>
    <automated>python -m unittest discover -s tests -p test_session_delivery.py</automated>
    <fails_when>Non-zero exit, Ran 0 tests, premature closing reference accepted, fabricated MERGED evidence, or existing PR retarget/draft behavior regresses.</fails_when>
    <automated>python -m unittest discover -s tests -p test_phase_issues.py</automated>
    <fails_when>Non-zero exit, Ran 0 tests, pending TODO moved without MERGED/CLOSED readback, or retry requires new publication/review.</fails_when>
  </verify>
  <acceptance_criteria>
    - Create, body update and body-omitted PR update are guarded for phase sessions.
    - Tests use fake provider and real temporary Git repositories, without live network or merge.
    - Unknown/open issue and PR results preserve pending records and identify a retry operation.
  </acceptance_criteria>
  <done>Supported phase PR delivery preserves issue roles, and folded TODO retirement occurs only after verified merge and closed issue readback.</done>
</task>

<task type="auto">
  <name>Task 3: Make normal and early handoffs produce complete truthful declarations</name>
  <files>.ai/workflows/execute-phase.md, .ai/workflows/ship.md, .ai/references/git-workflow.md, .ai/runtime/README.md, tests/test_workflow_links.py</files>
  <read_first>.ai/workflows/execute-phase.md, .ai/workflows/ship.md, .ai/references/git-workflow.md, .ai/runtime/README.md, .ai/templates/summary.md, tests/test_workflow_links.py, .ai/runtime/lib/phase_issues.py</read_first>
  <action>
Wire coordinator aggregation and every execution closing/early-termination route to review current SUMMARY Deferred/Remaining, major unresolved halt problems and validated unresolved review findings; exclude problems fixed within the execution and routine resolved checker corrections. The coordinator must author explicit issue_refs, including an empty list after review when none remain, create/reuse/update the appropriate issue using the supported path, and put canonical URLs in the SUMMARY/handoff and PR body. Supported dispositions must not conceal actionable unresolved work. Publication unavailable means explicit blocked-publication with reason, preserved completed code, and a retryable incomplete-tracking report.

Replace blanket separate issue-approval language in generic git-workflow/execute-phase guidance: authorized execution includes necessary problem tracking, with no repeated issue create/update approval. Preserve actual platform permissions, sensitive security handling, and the separate explicit PR merge boundary. Keep issue-kind selection and Bug/UAT preservation; pending human acceptance stays followup and open while code may advance. Do not edit PR #80's templates, threat fields, methods, roles, issue_format, or threat architecture; its accepted/mitigated/deferred threat requirements remain independent of generic resolved-problem exemptions.

Replace execute-phase's early close_phase_todos action with a pending reconciliation handoff. Add the bounded reconciliation after confirmed merge readback in ship; do not run it on draft-only/no-merge delivery. When readback is delayed or unavailable, report pending filenames/URLs and the reconciliation-only retry command instead of rerunning reviews or marking completion. Document all new argv and record fields in runtime README, the mandatory supported phase gates, and limits: runtime cannot infer omitted prose, prove semantic issue type or human UAT, or intercept arbitrary direct gh/API changes. Keep planning.validate warn-only and never turn unrelated checker notices into new issues.

Use existing workflow link tests for changed references/entry points; add only focused checks that prove procedures call supported gates and remove pre-merge retirement. Shared workflow/reference changes are scoped and additive to PR #80; report conflicts rather than dropping either owner's requirements.
  </action>
  <verify>
    <automated>python -m unittest discover -s tests -p test_workflow_links.py</automated>
    <fails_when>Non-zero exit, Ran 0 tests, broken changed workflow references, missing early-handoff gate, or documented pre-merge folded TODO retirement remains.</fails_when>
  </verify>
  <acceptance_criteria>
    - Normal completion, deferral and early termination all require coordinator leftover review and issue linkage.
    - Generic issue creation/update approval wording no longer blocks already-authorized execution.
    - Folded TODO reconciliation is post-merge and retryable; pending human UAT is not auto-closed.
    - Docs distinguish declared-record enforcement from semantic completeness and direct provider bypass.
  </acceptance_criteria>
  <done>The documented supported workflow produces declarations at every required boundary and honestly reports incomplete publication or reconciliation.</done>
</task>
</tasks>

<threat_model>
Security review: L1 primary-boundary review under .ai/references/methods/security-asvs-levels.md. Tasks 1-2 change validation of untrusted records and provider responses crossing into public publication, privileged file mutation and issue retirement. This register is plan-local; it does not change PR #80's template or threat-record architecture.

Primary tracking: https://github.com/Tasaddar12/ai-engineering-template/issues/83. These risks belong to this maintenance scope; reuse that canonical issue rather than duplicate issues #81/#82 or publish sensitive details.

| ID | Changed boundary and STRIDE threat | Severity | Disposition | Task mitigation and verification |
| --- | --- | --- | --- | --- |
| SEC-01 | Private phase record to public issue: Information disclosure from copying private source content or emitting private provider diagnostics. | high | mitigate | Task 1 uses a separate reviewed public body, existing sanitized provider errors and issue-format validation before mutation. Add negative tests proving the private source cannot be used as the public body and private-only content/diagnostics stay out of publication and CLI output. Run python -m unittest discover -s tests -p test_phase_issues.py and python -m unittest discover -s tests -p test_todo_issues.py; non-zero exit, zero tests or leaked private fixture text fails. |
| SEC-02 | Untrusted path/record input to privileged local writes: Tampering and Elevation of privilege through traversal, symlink, wrong-phase selection or stale snapshots. | high | mitigate | Task 1 reuses active-phase ownership/path checks, planning lock and stale-snapshot protection before publication/linkage writes; Task 2 rechecks selected TODO paths/snapshots before retirement. Add denied traversal, symlink, out-of-phase and changed-record cases that prove no remote mutation or unrelated local change occurs. Run python -m unittest discover -s tests -p test_phase_issues.py and python -m unittest discover -s tests -p test_todo_issues.py; non-zero exit, zero tests or an unauthorized write/move fails. |
| SEC-03 | Untrusted origin, issue URL or provider result to public mutation/closure evidence: Spoofing, Tampering and Repudiation through wrong-repository publication, forged identity or false MERGED/CLOSED success. | high | mitigate | Task 1 reuses origin-pinned repository verification and rejects PR-as-issue/mismatched identities. Task 2 binds phase session identity, checks effective PR references, requires independently observed matching MERGED/CLOSED responses and preserves unknown/open results as pending. Add wrong-origin/host, number/URL mismatch, ambiguous session, malformed/readback failure and premature followup closing cases. Run python -m unittest discover -s tests -p test_phase_issues.py, python -m unittest discover -s tests -p test_todo_issues.py and python -m unittest discover -s tests -p test_session_delivery.py; non-zero exit, zero tests, wrong-target mutation or premature retirement fails. |

All listed threats have planned mitigation; no acceptance or transfer substitutes for these checks. Provider unavailability preserves work with explicit retryable incomplete status. Privacy review and genuine human acceptance remain coordinator judgments; structuralOnly validation does not certify them. Direct provider edits remain outside runtime interception.
</threat_model>

<verification>
The preparer did not run tests. Each implementation task runs its named offline regression file and reports actual results/revision. The coordinator runs configured repository checks and independent plan/code/outcome review after integration. Reuse valid receipts and repeat only checks affected by corrections. Live publication/merge is not a test prerequisite.

Tracer: Task 1 delivers the phase record through preview/publication/readback/handoff path with denied-input cases; Task 2 adds truthful delivery/retirement; Task 3 makes mandatory producers consume that path.

Security review is applicable to the changed untrusted-input/publication/path/closure boundaries; the plan-local threat_model maps mitigation to Tasks 1-2 and their negative tests. No application authentication behavior or PR #80 threat template/architecture changes are assigned.
</verification>

<source_audit>
| Source | Required outcome | Coverage |
| --- | --- | --- |
| GOAL | Parent quick assignment: enforce phase issue handoff and PR references | Tasks 1-3 |
| REQ | No adopted project requirements apply; quick maintenance acceptance HANDOFF-01, PUBLICATION-01, PR-01, RECONCILE-01, AUTHORITY-01 | Tasks 1-3 |
| RESEARCH | Live publication guards, phase.complete gap, PR gate gap, premature folded TODO retirement | Tasks 1-3; existing good guards preserved |
| CONTEXT | Parent recorded user correction: all unresolved normal/early/halt problems tracked without another approval; resolved-inline exemption; pending human UAT; narrow PR #80 boundaries | Tasks 1-3 |
</source_audit>

<success_criteria>
- All five maintenance acceptance outcomes hold with meaningful offline execution evidence.
- Existing issue origin, structuralOnly validation, duplicate/uncertain-create recovery and provider extension seams are preserved.
- No template/threat work absorption, adopting-project identity fill, broad scan, benchmark, live merge or unrelated tracking architecture.
- Source-changing worker commits owned paths and its SUMMARY; coordinator handles integration and authorized draft delivery.
</success_criteria>

<output>
Create .planning/quick/261013-001-enforce-phase-issue-handoffs-pr-references/261013-001-enforce-phase-issue-handoffs-pr-references-SUMMARY.md with actual commits, tested revision, checks, documentation coverage, remaining blockers and the mechanical/instruction limits.
</output>
