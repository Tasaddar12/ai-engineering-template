---
phase: issue87-maintenance
plan: orchestration
type: execute
wave: 1
depends_on: []
input_revision: 77b5668f2003bea60127d87e8785469286abafb3
issue_refs:
  - https://github.com/Tasaddar12/ai-engineering-template/issues/87
files_modified:
  - .ai/workflows/execute-phase.md
  - .ai/workflows/plan-phase.md
  - .ai/workflows/ship.md
  - .ai/references/git-workflow.md
  - .ai/references/parallel-status.md
  - .ai/agents/verifier.md
  - .ai/agents/coordinator.md
  - .ai/templates/issue.md
  - tests/test_threat_tracking_contract.py
  - tests/test_parallel_status_contract.py
files_deleted: []
autonomous: true
requirements: [ISSUE87-6, ISSUE87-7]
acceptance: [ISSUE87-6, ISSUE87-7]
documentation:
  - .ai/references/parallel-status.md
  - .ai/references/git-workflow.md
user_setup: []
must_haves:
  truths:
    - Each actual wave reports every assignment's worker, role, resolved model, plan/execute/verify state, last progress, stall flag, blocker and PR.
    - Missing progress triggers a bounded coordinator decision and never establishes completion or authorizes killing a worker.
    - Planned phase security work can share one checklist issue while each risk retains its canonical identity and per-PLAN register.
    - Distinct unplanned threats receive actionable standalone tracking; matching existing trackers are reused after semantic review.
    - Independent review audits PR/MR issue links, scope, readback, closing references and closure authority before merge eligibility.
  artifacts:
    - path: .ai/references/parallel-status.md
      provides: Coordinator-owned per-wave status table and bounded stall decision protocol
    - path: .ai/references/git-workflow.md
      provides: Canonical planned-security checklist, unplanned-risk and issue-link audit procedure
    - path: tests/test_parallel_status_contract.py
      provides: Focused artifact/step and mutation checks for the status protocol
    - path: tests/test_threat_tracking_contract.py
      provides: Focused mutations preserving canonical threat lifecycle and audit obligations
  key_links:
    - from: .ai/workflows/execute-phase.md
      to: .ai/references/parallel-status.md
      via: Report actual wave assignments at dispatch, observed progress, join, integration and checks
    - from: .ai/workflows/plan-phase.md
      to: .ai/references/git-workflow.md
      via: Mandatory preparer-return reconciliation selects checklist or existing canonical tracking
    - from: .ai/agents/verifier.md
      to: .ai/references/git-workflow.md
      via: Independent issue-link audit checks actual readback against phase outcomes
    - from: .ai/workflows/ship.md
      to: .ai/references/git-workflow.md
      via: Current independent audit and provider readback gate merge eligibility
---

<objective>
Make parallel phase progress visible and make phase security tracking and PR issue
links independently reviewable under issue 87 acceptance 6 and 7.

Purpose: preserve worker lifecycle and threat identity while exposing stalled or
incomplete work and preventing inaccurate issue closure claims.
Output: one bounded status reference, narrow lifecycle hooks, canonical tracking
and independent audit instructions, and focused contract regressions.
</objective>

<execution_context>
@.ai/commands/execute-phase.md
@.ai/templates/summary.md
@.ai/runtime/TEMPLATE-CONTRACT.md
</execution_context>

<context>
@AGENTS.md
@.ai/RULES.md
@.planning/PROJECT.md
@.planning/STATE.md
@docs/maintenance/issue87/CONTEXT.md
@.ai/references/git-workflow.md
@.ai/references/worker-handoff.md
@.ai/references/verification-evidence.md

This is reusable-template maintenance. ISSUE87-6 and ISSUE87-7 identify acceptance
6 and 7 in the committed maintenance CONTEXT; they are not invented adopting-project
requirements. The adopting-project skeleton remains unfilled. User authorization
covers implementation and draft publication today; never merge or close issue 87.
The coordinator supplies CONTEXT from its committed integration revision before
dispatch; the sibling checkout used during preparation is evidence transport only.
</context>

## Decisions and ownership

- Follow CONTEXT Decisions: retain existing explicit authority, GitHub/GitLab
  behavior, canonical threat identity, safe disclosure and evidenced closure.
- Create `parallel-status.md`; keep threat procedure ownership in `git-workflow.md`.
  A separate `threat-tracking.md` adds no needed owner and is not planned.
- The assigned worker owns only frontmatter paths plus its coordinator-assigned
  SUMMARY. The coordinator owns integration, shared records, publication and status.
- Other workers own `.ai/agents/code-reviewer.md`, `AGENTS.md`, `.ai/RULES.md`,
  templates and runtime. Do not edit them. Ask the coordinator to have the review
  worker add a small link to `git-workflow.md#issue-link-audit` once this plan
  creates the `Issue-link audit` heading. Until integrated together, that worker
  may link the existing `git-workflow.md#canonical-threat-tracking` section.
  No copied procedure or broad reviewer rewrite is needed.
- The issue-link audit and status procedure are instruction contracts, with no
  monitoring daemon, timer service, new runtime store, scheduler or dependency.
  A production-code tracer is inapplicable; Task 1 traces the actual documented
  dispatch-to-join lifecycle and its contract test instead.

<tasks>
<task type="auto">
  <name>Task 1: Report wave state and make bounded stall decisions</name>
  <files>.ai/references/parallel-status.md, .ai/workflows/execute-phase.md, .ai/agents/coordinator.md, tests/test_parallel_status_contract.py</files>
  <read_first>docs/maintenance/issue87/CONTEXT.md; .ai/workflows/execute-phase.md discovery/grouping around lines 320-325, wait/join 455-460, integration 488-519 and checks 572-584; .ai/agents/coordinator.md execution and bounded agents; .ai/references/worker-handoff.md; .ai/references/verification-evidence.md; tests/test_threat_tracking_contract.py fixture/mutation helpers. Read the new reference/test if already present after integration.</read_first>
  <action>
Create a single coordinator-owned reference with a separate table for each actual
dependency/file-overlap wave. Columns: assignment/plan, worker id, role, resolved
model (inherit/unavailable stated accurately), plan state, execute state, verify
state, last observed progress with timestamp/evidence, stall flag, blocker, PR/MR.
State values must distinguish queued/running/blocked/complete and pending/running/
passed/failed verification; record integration/check evidence before accepting a
wave. Pending or unavailable PR/model/progress information stays explicit.

Refresh at grouping/dispatch, an observed worker update, bounded host wait return,
join, integration/check result and handoff/final report. State that coordinator
status is an observation and does not edit active workers' owned files. Preserve
the rule to wait for every active write-capable worker before integration/checks.

Use flags clear, watch, stalled and blocked with reasons. One host wait interval
without new evidence may set watch; a second consecutive bounded wait interval
with neither progress nor a meaningful host state change requires a coordinator
decision and a stalled flag. Host-supported bounded waits are observations, not
new background polling. Record the observation interval; elapsed time alone never
proves a hang, worker completion, failure or permission to terminate. A declared
external blocker can be blocked immediately with its evidence. At stalled, choose
one bounded next action: continue one observed wait with a stated reason, request
a concise status/handoff through the supported lifecycle, or report the concrete
access/decision blocker. Do not automatically kill, restart, reassign active paths
or clean up worktrees. Only a confirmed stopped/interrupted worker enters existing
handoff inspection and bounded continuation. Preserve existing continuation limits,
completed commits, dirty work and fresh independent verification requirements.

Add short links at execute-phase grouping, wait/join, integration and check seams
and coordinator execution; keep the detailed protocol in the new reference.
Create focused contract checks that inspect real step bodies/reference structure
and mutate away required columns, mandatory lifecycle links, progress evidence,
the stalled decision and non-completion/non-termination safeguards.
  </action>
  <verify>
    <automated>python -m unittest discover -s tests -p test_parallel_status_contract.py</automated>
    <fails_when>non-zero exit, any FAILED/ERROR result, or Ran 0 tests</fails_when>
  </verify>
  <acceptance_criteria>
    - Every actual wave has distinct assignment rows with all required fields.
    - Two bounded waits without progress require a recorded decision; no elapsed-time completion or automatic termination is authorized.
    - Contract mutations expose missing lifecycle hooks and missing safeguards.
  </acceptance_criteria>
  <done>The dispatch-to-join status protocol and focused regressions pass; existing integration and continuation authority remains intact.</done>
</task>

<task type="auto">
  <name>Task 2: Track planned security work without losing risk identity</name>
  <files>.ai/references/git-workflow.md, .ai/workflows/plan-phase.md, .ai/workflows/execute-phase.md, .ai/templates/issue.md, tests/test_threat_tracking_contract.py</files>
  <read_first>docs/maintenance/issue87/CONTEXT.md; .ai/references/git-workflow.md canonical threat tracking around lines 81-145; .ai/workflows/plan-phase.md handle_preparer_return; .ai/workflows/execute-phase.md aggregate_results around 602-605 and review_phase_issues around 663-697; .ai/templates/issue.md Security risk variant; .ai/runtime/TEMPLATE-CONTRACT.md Threat records and ownership; tests/test_threat_tracking_contract.py around 172-203, 222-267; tests/test_phase_issues.py and tests/test_workflow_links.py for compatibility inspection only.</read_first>
  <action>
Extend canonical threat tracking to permit one phase security checklist issue for
planned security mitigations. Preserve every local Threat ID, stable canonical
risk key and aliases/occurrences. Each checklist entry needs its PLAN/ID link,
owner, scope/acceptance, assessment and uncertainty, lifecycle/outcome, next action,
revision/check evidence and individually addressable entry identity. Keep full
six-column threat registers in their owning PLANs and keep SUMMARY/PR linked
outcomes separate. The checklist is a tracking container, never a combined PLAN
register or an excuse to omit individual risks.

Coordinator-authorized maintenance reconciliation during execution: add narrow
checklist guidance to the existing Security risk template instructions, retaining
all required headings and the existing variant. No new variant/runtime behavior.

Search open/closed issues and linked/current PR/MRs first. Existing actionable
matching trackers remain canonical; a checklist may link them without duplicating
or replacing their identities. New planned risks may use distinct checklist
entries as their canonical reference. Preserve keys across reruns and deduplicate
semantically. A distinct unplanned threat discovered during execution or review
needs its own actionable Security risk issue, or an existing full-scope matching
issue; add its reference to the owning PLAN and phase checklist when one exists.
Do not route threats through TODO publication. Closed unresolved matches retain
the reopening-authority blocker rather than spawning duplicates.

Retain sanitized separately reviewed publication, serialized writes, template
validation, readback and uncertain-create recovery. Sensitive detail uses an
existing authorized restricted channel; lack of that channel blocks only the
detail/dependent action. Unavailable publication stays Pending with its dependency.
Retain GitLab neutral-link policy and verified-tool/Pending fallback.

Use mandatory preparation/execution reconciliation hooks to choose this routing;
the generic resolved-problem exemption must still not waive threats. Keep accepted,
deferred, open/unresolved and mitigated/resolved distinct. A checked checklist item
needs outcome evidence and does not mean issue closure. Preserve all existing
closure authority and provider readback duties. Extend targeted existing fixture/
mutation checks for checklist entries, existing-match reuse and standalone distinct
unplanned risks. Preserve original restored blocks and per-PLAN/discovery schemas.
  </action>
  <verify>
    <automated>python -m unittest discover -s tests -p test_threat_tracking_contract.py</automated>
    <fails_when>non-zero exit, any FAILED/ERROR result, or Ran 0 tests</fails_when>
    <automated>python -m unittest discover -s tests -p test_phase_issues.py</automated>
    <fails_when>non-zero exit, any FAILED/ERROR result, or Ran 0 tests</fails_when>
    <automated>python -m unittest discover -s tests -p test_workflow_links.py</automated>
    <fails_when>non-zero exit, any FAILED/ERROR result, or Ran 0 tests</fails_when>
  </verify>
  <acceptance_criteria>
    - Planned mitigation checklist entries preserve separate canonical keys, aliases, owners and evidence.
    - Existing matching trackers are reused and distinct unplanned risks have standalone actionable tracking.
    - Per-PLAN six-column registers, conditional discovery flags, safe disclosure and lifecycle evidence still pass existing contracts.
  </acceptance_criteria>
  <done>Canonical routing and mandatory hooks cover both planned and unplanned risk cases with focused passing checks.</done>
</task>

<task type="auto">
  <name>Task 3: Require independent issue-link audit before merge eligibility</name>
  <files>.ai/references/git-workflow.md, .ai/workflows/execute-phase.md, .ai/workflows/ship.md, .ai/agents/verifier.md, tests/test_threat_tracking_contract.py</files>
  <read_first>.ai/references/git-workflow.md; .ai/workflows/execute-phase.md code_review_gate and review_phase_issues; .ai/workflows/ship.md preflight_checks, generate_pr_body and merge_and_close around line 402; .ai/agents/verifier.md around 152-156; .ai/references/verification-evidence.md; .ai/templates/pull-request.md; tests/test_threat_tracking_contract.py; tests/test_phase_issues.py; tests/test_workflow_links.py; docs/maintenance/issue87/CONTEXT.md.</read_first>
  <action>
Add the canonical `Issue-link audit` subsection in git-workflow, yielding
`git-workflow.md#issue-link-audit`, and point verifier,
execute-phase review assignment and ship seams to it. Require a fresh independent
reviewer/verifier to compare PR/MR body and issue links against CONTEXT acceptance,
each PLAN threat/checklist identity, SUMMARY outcomes and actual provider readback.
Audit actionable link destination and scope, omitted or duplicate tracking,
planned-checklist coverage, separate distinct unplanned risks, lifecycle truth,
safe visibility, neutral versus closing references and existing explicit closure
authority. Audit ordinary linked follow-ups as well as security records. Preserve
the difference between structural issue.validate and semantic/provider review.

Capture reviewed source revision, PR/MR body/link snapshot, verified URLs, readback
evidence and unresolved findings in the independent result. A missing required
readback or unverifiable link is a gap with a dependency, not a pass. Material
changes to links/body/risk outcomes or source invalidate the affected audit; obtain
fresh applicable independent evidence before claiming ready. Ship preflight/body
generation may publish truthful drafts with pending review, but merge eligibility
requires the current independent audit and last provider readback. Never infer
closure from merge, checked checklist items or accepted/deferred status.

Send the coordinator the exact desired code-reviewer cross-reference to this
subsection; that file remains the other worker's ownership. Extend focused real-
artifact/step and mutation tests for independent audit reachability, scope/readback,
neutral closing references and currentness. Keep mandatory threat reconciliation
outside optional code review. Do not merge or close issue 87 in this assignment.
If changed prose breaks tests/test_phase_issues.py or tests/test_workflow_links.py,
return the exact failing
assertion to the coordinator for ownership assignment rather than editing it.
  </action>
  <verify>
    <automated>python -m unittest discover -s tests -p test_threat_tracking_contract.py</automated>
    <fails_when>non-zero exit, any FAILED/ERROR result, or Ran 0 tests</fails_when>
    <automated>python -m unittest discover -s tests -p test_parallel_status_contract.py</automated>
    <fails_when>non-zero exit, any FAILED/ERROR result, or Ran 0 tests</fails_when>
    <automated>python -m unittest discover -s tests -p test_phase_issues.py</automated>
    <fails_when>non-zero exit, any FAILED/ERROR result, or Ran 0 tests</fails_when>
    <automated>python -m unittest discover -s tests -p test_workflow_links.py</automated>
    <fails_when>non-zero exit, any FAILED/ERROR result, or Ran 0 tests</fails_when>
    <automated>git diff --check</automated>
    <fails_when>non-zero exit or reported whitespace errors</fails_when>
  </verify>
  <acceptance_criteria>
    - The canonical audit is reachable from independent verification and ship, including the execute-phase reviewer assignment.
    - Missing readback, stale audit and premature closing links cannot establish merge eligibility.
    - Draft tracking can state pending evidence; no new merge or issue closure authority is granted.
  </acceptance_criteria>
  <done>Required independent audit duties and currentness checks are explicit and covered by focused mutations and compatibility checks.</done>
</task>
</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| Coordinator to worker lifecycle | Status observations must preserve assignment ownership and completion evidence. |
| Private evidence to provider-visible tracking | Existing canonical safe-disclosure rules govern every public checklist/link. |
| Review evidence to merge/closure decision | Existing source-currentness and explicit authority remain mandatory. |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|

None identified as a new product exploit from this documentation/contract-test
maintenance scope. Existing workflow failure modes are issue 87 acceptance 6/7;
this plan does not invent new risk identities for previously tracked controls.
Any actual implementation discovery follows canonical threat tracking through the
coordinator. Preserve PR80/84 and issues81/82 identity and closure constraints.
</threat_model>

<verification>
- Run the four targeted unittest discovery suites above with a functioning
  Python interpreter; record exact interpreter, revision, counts and actual output.
- Inspect the per-wave lifecycle trace and a stalled-worker example without
  reading/editing worker files or interpreting elapsed time as completion.
- Independently inspect one planned-checklist case, one existing matching tracker,
  one distinct unplanned threat and one stale/missing-link audit case.
- Run git diff --check and review exact ownership before committing.
- Security review: no product authentication, secret-handling or network endpoint
  changes; the changed isolation/reporting/closure procedure is assessed explicitly
  above and requires the focused independent contract review.
</verification>

<success_criteria>
- All three tasks complete within assigned paths and existing authority.
- Status exposes each wave and unresolved stall decisions without silent completion.
- Canonical per-risk identity, per-PLAN registers and safe lifecycle evidence survive.
- Planned security checklists and distinct unplanned threat routing are explicit.
- Independent issue-link review is current before merge eligibility; no merge occurs.
- Required targeted checks pass and independent findings are resolved or honestly blocked.
</success_criteria>

## Artifacts this plan produces

New paths: `.ai/references/parallel-status.md`,
`tests/test_parallel_status_contract.py`. No runtime symbols, CLI flags, configuration
keys or services. Existing instructions and test helpers gain bounded contracts.

## Multi-source coverage audit

| Source | ID | Required item | Task | Status | Notes |
|---|---|---|---|---|---|
| GOAL | issue87 | Parallel status and security/link review maintenance | 1-3 | COVERED | Maintenance CONTEXT is authority; no adopting-project roadmap goal exists. |
| REQ | ISSUE87-6 | Per-wave worker/model/lifecycle/progress/stall/blocker/PR | 1 | COVERED | Alias for CONTEXT acceptance 6. |
| REQ | ISSUE87-7 | Checklist security tracking and independent issue-link audit | 2-3 | COVERED | Alias for CONTEXT acceptance 7. |
| RESEARCH | supplied source map | Existing execute/plan/ship seams and canonical risk duties | 1-3 | COVERED | Named locations inspected at input revision; no separate RESEARCH assigned. |
| CONTEXT | Decisions | Preserve explicit authorization and canonical security lifecycle | 1-3 | COVERED | No repeated ordinary approval or merge authority. |
| CONTEXT | Decisions | Preserve GitHub/GitLab behavior and narrow source scope | 2-3 | COVERED | Provider adapters73/74/76/77 excluded. |
| CONTEXT | Acceptance1-5 | Guards, cleanup, record validation and upstream comparison | other workers | OUTSIDE THIS PLAN | Coordinator assigns disjoint plans; not silently dropped. |
| CONTEXT | Investigation | Autopilot/unattended-sync examples | none | EXCLUDED | Suggestions do not authorize a new monitoring service. |

<output>
Create and commit the coordinator-assigned implementation SUMMARY with complete
template sections, explicit issue_refs, checks/revision and remaining audit gaps.
Return commits and exact changed paths; coordinator integrates and publishes drafts.
</output>
