---
maintenance: planning-audit
plan: planning-audit
type: execute
wave: 1
depends_on: []
autonomous: true
input_revision: 7c322ded2d64cde0dc87a2aa0c1a14a97de3df27
requirements: [AUDIT-01, AUDIT-02, AUDIT-03, AUDIT-04]
acceptance: [AUDIT-01, AUDIT-02, AUDIT-03, AUDIT-04]
files_modified:
  - .ai/workflows/plan-phase.md
  - .ai/workflows/quick.md
  - .ai/agents/phase-checker.md
  - .ai/agents/phase-preparer.md
  - .ai/templates/planner-subagent-prompt.md
  - .ai/templates/phase-prompt.md
  - .ai/references/methods/planner-revision.md
  - .ai/references/methods/plan-checker-examples.md
  - .ai/references/methods/gates.md
  - .ai/references/methods/planner-chunked.md
  - .ai/references/agent-adaptation.md
  - .ai/references/template-adaptation.md
  - .ai/runtime/lib/bundles.py
  - tests/test_phase_runtime.py
files_deleted: []
documentation:
  - .ai/workflows/plan-phase.md
  - .ai/workflows/quick.md
  - .ai/agents/phase-checker.md
  - .ai/agents/phase-preparer.md
  - .ai/templates/planner-subagent-prompt.md
  - .ai/templates/phase-prompt.md
  - .ai/references/methods/planner-revision.md
  - .ai/references/methods/plan-checker-examples.md
  - .ai/references/methods/gates.md
  - .ai/references/methods/planner-chunked.md
  - .ai/references/agent-adaptation.md
  - .ai/references/template-adaptation.md
user_setup: []
must_haves:
  truths:
    - A correction dispatch gives both author and independent checker the finding IDs, exact revisions, affected plans and contracts, changed paths and reusable prior evidence.
    - Phase and validated quick callers consume the same review schema; evidenced blockers and warnings require revision, while advisories alone do not.
    - Relevant missing or stale maps are refreshed before research or preparation consumes them, using resolved mapper settings and existing freshness thresholds.
    - Planning instructions describe implemented CLI and index capabilities accurately while preserving semantic, goal, safety, coverage and dependency review.
  artifacts:
    - path: .ai/workflows/plan-phase.md
      provides: Ordered map refresh and concrete bounded correction dispatches
    - path: .ai/agents/phase-checker.md
      provides: Canonical review payload, evidence-based severity and independent delta inspection
    - path: .ai/runtime/lib/bundles.py
      provides: Mapper model and effort in planning initialization through existing resolution
  key_links:
    - from: .ai/workflows/plan-phase.md
      to: .ai/templates/planner-subagent-prompt.md
      via: revision_context transports the exact correction assignment
    - from: .ai/workflows/quick.md
      to: .ai/agents/phase-checker.md
      via: PLAN REVIEW verdict and structured issues use one severity gate
    - from: .ai/workflows/plan-phase.md
      to: .ai/runtime/lib/bundles.py
      via: init.plan-phase supplies resolved codebase-mapper model and effort
---

<objective>
Make the existing planning review and correction workflow executable from its instructions, with current prerequisite maps and truthful runtime guidance.

Purpose: Complete authorized audit recommendations 1-4 without creating an adopting project's identity or execution history.
Output: One bounded template-maintenance correction, source-backed documentation and mapper bundle regression evidence.
</objective>

<execution_context>
@AGENTS.md
@.ai/RULES.md
@.ai/references/git-workflow.md
@.ai/templates/summary.md
@.ai/maintenance/planning-audit-scope.md

This is maintenance outside a numbered phase. AUDIT IDs identify this assignment's acceptance, not adoption requirements. Do not register this file with the phase runtime or create phase/quick records. Preserve every tracked .planning/ file, existing task, model setting and freshness threshold. The draft PR already exists at https://github.com/Tasaddar12/ai-engineering-template/pull/65, created 2026-10-12T13:07:47Z before any test scripts.

The coordinator assigns operational documentation to doc-writer and the bundle/test changes to coder, with exact subsets of the paths above and separate summaries. Workers never share a writable checkout or publish. Complete tasks in order: shared documentation paths serialize the tasks; no task-level parallel wave is implied. No benchmarks or merge. Recommendations 5-7 remain issues 66-68 only: do not add shared correction/no-progress accounting, change existing-plan or Plan anyway branches, or change recent-phase/scout reuse/handoff selection.
</execution_context>

<context>
@.ai/runtime/TEMPLATE-CONTRACT.md
@.ai/runtime/phase.py
@.ai/runtime/lib/phases.py
@.ai/runtime/lib/planning_review.py
@.ai/runtime/lib/codebase.py
@.ai/workflows/execute-phase.md
@.ai/commands/plan-phase.md
@tests/test_efficiency_contracts.py
@.github/workflows/validate.yml

At input revision, plan-phase revision_loop is prose without a revision_context dispatch; checker correction scope already supports direct inspection and content-sensitive reuse. PLANNING_AGENTS omits codebase-mapper, although the workflow indexes its models and efforts. CLI main accepts query/init, and phases.plan_index returns phase/directory/count plus plan IDs, files, depends_on and summary paths; it does not compute waves. planning_review._audit already checks plan structure and cycles across the planning tree. Reuse these facts; do not implement a new check family, duplicate validator or whole-tree audit on each correction.
</context>

<tasks>
<task type="auto">
  <name>Task 1: Wire the canonical review result through bounded correction dispatches</name>
  <files>.ai/workflows/plan-phase.md, .ai/workflows/quick.md, .ai/agents/phase-checker.md, .ai/templates/planner-subagent-prompt.md, .ai/references/methods/planner-revision.md, .ai/references/methods/plan-checker-examples.md</files>
  <read_first>.ai/workflows/plan-phase.md, .ai/workflows/quick.md, .ai/agents/phase-checker.md, .ai/templates/planner-subagent-prompt.md, .ai/references/methods/planner-revision.md, .ai/references/methods/plan-checker-examples.md, .ai/commands/plan-phase.md, .ai/maintenance/planning-audit-scope.md</read_first>
  <action>Per AUDIT-01 and AUDIT-02, make PLAN REVIEW with Verdict: approved | needs-revision the canonical transport for the existing phase and validated quick callers. Define a structured issues list carrying stable finding id, plan, task when applicable, dimension, severity (blocker|warning|info), required_property, evidenced description and optional non-binding fix_hint; include reviewed revision, reviewed PLAN paths and coverage/evidence references. Approved requires all mandatory applicable goal, safety, coverage, task, ownership and dependency checks conclusive, with zero blockers and warnings; INFO may accompany approval and must be displayed. A blocker proves goal, safety or executable-contract failure; a warning proves an actionable required property or reliable verification defect needing correction before execution. Quality preferences, unmeasured budgets, counts below a configured cap and optional improvements are INFO, not revision triggers. Reconcile the checker's stance, dimensions, status rules, severity examples and structured returns with this rule, retaining required checks and binding properties. Replace the sizing example's invented context percentage/count-only rejection with a demonstrated configured task-cap or separate-outcome/prerequisite violation; do not mandate horizontal splits or reject by file count. Instantiate a preparer correction Agent prompt inside revision_loop using revision_context: exact repository/branch, reviewed revision and current input revision, prior checker report/result destination, exact finding IDs/payloads, owned and affected PLAN paths, governing acceptance/decision/source-contract paths, actual changed paths since the reviewed revision and reusable prior evidence with its revision and compared paths. After integrating the author's owned commit, dispatch a fresh independent phase-checker with that packet updated to the corrected revision and actual delta; inspect every corrected property and affected producer/consumer directly. Reuse evidence only while its PLAN content, governing acceptance and inspected source remain unchanged; missing packet/evidence requires full applicable assessment. Ownership/dependency changes require the entire graph check, not all unrelated source inspection. Keep fix hints advisory and REVISION_CONFLICT handling. Apply the same payload/schema to the validated quick caller's existing correction handoff. Retain each workflow's existing iteration limits and escalation boundary; do not add new accounting/progress or change unrelated branches.</action>
  <verify>Independent document inspection traces initial review, an INFO-only result, an actionable warning, a goal blocker, author correction and fresh checker return through both callers. Each route must use one schema and explicitly provide all packet fields; the checker must inspect actual corrected content. Check an unchanged-evidence example permits reuse and a changed acceptance/source example invalidates it; a changed ownership/dependency example broadens graph checking. Fail on missing fields, competing result schemas, count-only revision gates, mandatory-check omissions or reuse based only on author assertions. No artificial wording tests are required.</verify>
  <acceptance_criteria>AUDIT-01: Both correction consumers receive the concrete packet and preserve independent content-sensitive verification. AUDIT-02: Both callers route the canonical verdict from blockers/warnings; INFO-only returns approved with advisories. Missing required coverage or safety cannot pass. The sizing example cites an actual mandatory invariant.</acceptance_criteria>
  <done>One complete initial-review-to-correction path is explicit and independently reviewable, and caller/role severity wording has no contradictory execution rule.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Refresh prerequisite maps with resolved mapper dispatch settings</name>
  <files>.ai/workflows/plan-phase.md, .ai/runtime/lib/bundles.py, tests/test_phase_runtime.py</files>
  <read_first>.ai/workflows/plan-phase.md, .ai/runtime/lib/bundles.py, .ai/runtime/lib/models.py, .ai/runtime/lib/codebase.py, tests/test_phase_runtime.py, .ai/commands/plan-phase.md</read_first>
  <behavior>init.plan-phase includes codebase-mapper in both models and efforts and uses the same resolver/configured or inherited values as other agents. Existing phase requirements and project_requirements remain distinct. Existing onboard mapper values remain intact without redundant enumeration. Existing freshness tests still prove STACK threshold 1, ARCHITECTURE threshold 15, configurable thresholds and planning-only churn behavior.</behavior>
  <action>Per AUDIT-03, move the existing codebase.status/mapper refresh step after context loading and before handle_research and preparation. Select maps actually needed for the named phase interfaces; refresh relevant missing/stale entries, skip fresh or irrelevant maps, wait for mapper commits/results and pass the resulting current map paths to downstream consumers. A gaps/correction run may reuse unchanged relevant maps but must not skip a stale map it needs; preserve bounded correction scope. Use existing codebase.status and freshness configuration, with no map bookkeeping or new global thresholds. Add codebase-mapper to PLANNING_AGENTS so init.plan-phase resolves its model/effort and installed-role metadata through existing helpers; remove the now-redundant mapper concatenation in onboard rather than creating a separate resolution path. Add a behavioral regression to the existing Bundles class using real init.plan-phase subprocess results and configured/inherit resolution; retain existing Dispatch and CodebaseMapFreshness coverage. Coder owns the two Python paths; doc-writer owns the workflow path and uses the coder's committed source evidence.</action>
  <verify>
    <automated>python -m unittest discover -s tests -p test_phase_runtime.py -k Bundles -v</automated>
    <fails_when>Nonzero exit, Ran 0 tests, or mapper fields/resolved values absent from init.plan-phase.</fails_when>
    <automated>python -m unittest discover -s tests -p test_phase_runtime.py -k Dispatch -v</automated>
    <fails_when>Nonzero exit or Ran 0 tests.</fails_when>
    <automated>python -m unittest discover -s tests -p test_phase_runtime.py -k CodebaseMapFreshness -v</automated>
    <fails_when>Nonzero exit or Ran 0 tests.</fails_when>
    Independent workflow inspection must prove refresh precedes both consumers, fresh/irrelevant maps do not trigger dispatch, and needed stale maps cannot bypass the step on correction runs.
  </verify>
  <acceptance_criteria>AUDIT-03: Every mapper dispatch has resolved model/effort, relevant maps are current when consumed, and existing thresholds/source-sensitive freshness remain unchanged. Regression tests demonstrate runtime bundle behavior rather than matching source strings.</acceptance_criteria>
  <done>Source behavior and workflow order agree, with observed RED then GREEN regression evidence and passing affected runtime tests.</done>
</task>

<task type="auto">
  <name>Task 3: Correct structural-check and index claims without new runtime architecture</name>
  <files>.ai/agents/phase-preparer.md, .ai/agents/phase-checker.md, .ai/references/methods/gates.md, .ai/references/agent-adaptation.md, .ai/templates/phase-prompt.md, .ai/references/methods/planner-chunked.md, .ai/references/template-adaptation.md</files>
  <read_first>.ai/runtime/phase.py, .ai/runtime/lib/phases.py, .ai/runtime/lib/planning_review.py, .ai/runtime/TEMPLATE-CONTRACT.md, .ai/workflows/execute-phase.md, .ai/agents/phase-preparer.md, .ai/agents/phase-checker.md, .ai/references/methods/gates.md, .ai/references/agent-adaptation.md, .ai/templates/phase-prompt.md, .ai/references/methods/planner-chunked.md, .ai/references/template-adaptation.md</read_first>
  <action>Per AUDIT-04, replace unsupported structural CLI claims in the assigned preparer/checker/gates/agent-adaptation sections with bounded inspection of the assigned PLANs against TEMPLATE-CONTRACT, independent semantics and graph review. Where existing planning.review is mentioned, spell its actual invocation as python .ai/runtime/phase.py query planning.review and state that it audits the whole planning tree; do not make it a required per-correction gate. Correct the assigned role/template/adaptation/chunked sections to state phase-plan-index inventories IDs, file paths, declared dependencies and available summaries only. Attribute dependency/file-overlap grouping and execution ordering to the coordinator's execute-phase procedure using inspected PLAN metadata; declared wave labels do not override prerequisites or ownership. Preserve ordered integration/check barriers and resource safeguards. Do not change phases.plan_index, the CLI parser, planning_review, scheduling behavior, examples unrelated to these claims or adoption templates. Inspect corrected command arguments against current source, including any command introduced in Task 1-2. Maintain the complete existing role/template methods rather than replacing them with compact guidance.</action>
  <verify>Independent claim review compares each edited runtime command and index field against phase.py main/VERBS, phases.plan_index and planning_review._audit; compares wave ownership instructions with execute-phase's group/execute steps. Fail on an unsupported command/family, index-derived wave assertion, automatic structural/semantic claim beyond implemented behavior, a whole-tree audit required per correction, duplicate validator or weakened dependency/ownership safeguards. Review only changed claims and their exact sources.</verify>
  <acceptance_criteria>AUDIT-04: Every affected structural-readiness and index claim is truthful; semantic and graph inspection remains explicit and scoped. No new runtime validation feature or global correction audit is introduced.</acceptance_criteria>
  <done>Documentation matches implemented CLI/index behavior and the existing coordinator wave procedure, with conclusive independent claim evidence.</done>
</task>
</tasks>

<verification>
Security review: not applicable. This changes workflow documentation and read-only bundle role enumeration, with no authentication, authorization, secret handling, tenant isolation or untrusted-input validation boundary change. Mandatory security planning checks for consuming project PLANs remain intact.

Tracer-first: Task 1 traces the real caller/result/author/checker correction path. This maintenance has no product request endpoint; source-backed route inspection is the meaningful evidence for documentation. Task 2 supplies the observable runtime regression.

Preparer runs no tests. The coordinator/assigned executors run the above focused checks after implementation and the required existing CI Python command: python -m unittest discover -s tests -v. Nonzero exit or zero tests blocks acceptance. CI validate.yml also requires bash .ai/hooks/ai-tier-notice.test.sh, bash .ai/hooks/worktree-guard.test.sh, bash .ai/hooks/context-handoff.test.sh and bash .ai/hooks/worktree-location.test.sh; run on an available Bash host or retain the remote platform results as pending, never claim unrun checks passed. No benchmarks. Record exact tested revision, commands/results and pending/failed checks. The adoption config has no configured project commands; do not populate it with template-maintenance checks.

Fresh phase-checker checks this committed maintenance plan before execution. Fresh code-reviewer checks the bundle/test change; doc-verifier checks changed operational guidance against source and both callers. The coordinator joins all findings before accepting and reruns only checks/evidence invalidated by repairs. Full-suite/remote checks are completion requirements, not a per-correction global audit. No merge is authorized.
</verification>

<success_criteria>
All AUDIT-01 through AUDIT-04 acceptance is supported by observed checks and independent review; task commits and author summaries exist; exact path scope is preserved. No .planning/ edits, fake records, benchmarks, excluded issue work, global model changes or new checker architecture. Draft tracking remains distinct from verified completion.
</success_criteria>

<output>
Coder writes .ai/maintenance/planning-audit-runtime-SUMMARY.md for Python changes and regression receipts. Doc-writer writes .ai/maintenance/planning-audit-docs-SUMMARY.md for documentation changes and source-backed claims. The coordinator preserves full read-only checker/reviewer evidence and handles integration/publication. Workers commit only their assigned exact paths and summaries.
</output>
