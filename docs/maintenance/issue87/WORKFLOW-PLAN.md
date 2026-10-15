---
phase: issue87-maintenance
plan: workflow
type: execute
wave: 1
depends_on: []
issue_refs:
  - https://github.com/Tasaddar12/ai-engineering-template/issues/87
input_revision: 77b5668f2003bea60127d87e8785469286abafb3
files_modified:
  - AGENTS.md
  - .ai/RULES.md
  - .ai/references/guard-repair-workflow.md
  - .ai/agents/coder.md
  - .ai/agents/phase-preparer.md
  - .ai/agents/code-reviewer.md
  - tests/test_guard_repair_contract.py
files_deleted: []
autonomous: true
requirements: [ISSUE87-03, ISSUE87-AUTH]
acceptance: [ISSUE87-03, ISSUE87-AUTH]
documentation:
  - AGENTS.md
  - .ai/RULES.md
  - .ai/references/guard-repair-workflow.md
  - .ai/agents/coder.md
  - .ai/agents/phase-preparer.md
  - .ai/agents/code-reviewer.md
resources: []
checks:
  - [python, -m, unittest, discover, -s, tests, -p, test_guard_repair_contract.py, -v]
  - [python, -m, unittest, discover, -s, tests, -p, test_agent_sources.py, -v]
  - [python, -m, unittest, discover, -s, tests, -p, test_workflow_links.py, -v]
  - [python, -m, unittest, discover, -s, tests, -p, test_threat_tracking_contract.py, -v]
user_setup: []
must_haves:
  truths:
    - Guard repair starts with an independent bypass and false-positive matrix and executable failing regression evidence before implementation.
    - Preparers, coders and reviewers can reach one canonical repair procedure from their normal instructions.
    - Updates state the result, next check and real blocker briefly; approval requests identify only authority still missing.
    - Earlier explicit authorization and phase authority remain intact, and PR86 scratchpad/write notices remain advisory.
  artifacts:
    - path: .ai/references/guard-repair-workflow.md
      provides: Guard repair procedure, paired scenario matrix and evidence receipt examples.
    - path: tests/test_guard_repair_contract.py
      provides: Removal regressions for canonical procedure reachability from assigned entry points.
  key_links:
    - from: .ai/agents/phase-preparer.md
      to: .ai/references/guard-repair-workflow.md
      via: Named guard-repair planning duty.
    - from: .ai/agents/coder.md
      to: .ai/references/guard-repair-workflow.md
      via: Named matrix and RED-before-implementation duty.
    - from: .ai/agents/code-reviewer.md
      to: .ai/references/guard-repair-workflow.md
      via: Independent matrix and evidence audit duty.
    - from: .ai/agents/code-reviewer.md
      to: .ai/references/git-workflow.md
      via: Small canonical-threat-tracking link for the canonical issue-link audit duty.
---

<objective>
Make security and static guard repairs resistant to bypasses and false positives
through a reachable, evidence-based repair procedure. Keep communication brief
and make approval boundaries explicit without reopening granted authority.

Purpose: Deliver issue 87 context acceptance 3 and its authorization decisions.
Output: One canonical reference, narrow entry/role edits, removal-regression
checks and a committed execution SUMMARY. This is template maintenance; the
adoption skeleton has no phase goal or project requirements to populate.
</objective>

<execution_context>
@.ai/agents/coder.md
@.ai/agents/doc-writer.md
@.ai/templates/summary.md
@.ai/runtime/TEMPLATE-CONTRACT.md
</execution_context>

<context>
@docs/maintenance/issue87/CONTEXT.md
@AGENTS.md
@.ai/RULES.md
@.ai/agents/phase-preparer.md
@.ai/agents/coder.md
@.ai/agents/code-reviewer.md
@tests/test_threat_tracking_contract.py

The coordinator supplies the committed maintenance CONTEXT in each executor
checkout before dispatch. Its source during preparation was the integration
worktree's docs/maintenance/issue87/CONTEXT.md at the assigned input revision.
The user authorized planning, implementation, parallel worktrees and draft PRs
today; merging and closing issue 87 remain unauthorized. This PLAN grants no
additional authority.
</context>

## Ownership and ordering

This component has no implementation dependency on the guards, planning-record
or orchestration components; its reference describes evidence obligations and
does not import their new APIs. Wave 1 is a proposal subject to exact path checks.
Do not modify .ai/workflows/execute-phase.md, .ai/workflows/plan-phase.md,
.ai/workflows/ship.md, .ai/references/git-workflow.md, runtime/templates,
installer assets or hooks. Those paths belong to the other owners.

One coder owns every declared source path and its assigned execution SUMMARY.
The coordinator explicitly assigned the narrow .ai/RULES.md reusable-source
edit as an ownership exception for this maintenance component; adopting-project
and shared execution status records remain coordinator-owned. The coder reads
the doc-writer method for this substantial procedural documentation assignment.
Tasks 1 and 2 execute sequentially in its isolated worktree; it commits RED,
then source changes and its SUMMARY. The coordinator integrates only after
the worker returns, and owns publication and shared results. Do not dispatch
another active writer on this PLAN's paths.

Tracer exception: this component changes procedural documentation and its
reachability contract, with no production execution boundary. A runtime tracer
would assert behavior outside its scope. A failing reference-reachability test,
followed by the complete linked procedure and independent semantic review,
supplies the meaningful end-to-end check here.

<tasks>
<task type="auto" tdd="true">
  <name>Task 1: Establish removal regressions for the repair procedure</name>
  <files>tests/test_guard_repair_contract.py</files>
  <read_first>AGENTS.md, .ai/RULES.md, .ai/agents/phase-preparer.md, .ai/agents/coder.md, .ai/agents/code-reviewer.md, tests/test_threat_tracking_contract.py, docs/maintenance/issue87/CONTEXT.md</read_first>
  <behavior>Each assigned entry point links directly to the canonical repair reference and the reference exists. A fixture-copy removal or broken-target mutation of each entry point makes the contract report that source. Removing the canonical reference also reports it. An unchanged complete fixture passes.</behavior>
  <action>Create standard-library unittest checks using temporary fixture copies, following the existing threat-contract mutation pattern. Check actual Markdown target resolution and each assigned entry point's direct procedure link; do not accept unrelated links as repair guidance. Parameterize the entry points and mutation cases. Do not assert copied sentences, word counts, stylistic phrases or broad document snapshots. Run before any procedure/source edit, inspect the named assertion showing missing repair guidance, preserve command, exit, test name and expected/actual result, then commit RED. Syntax/import/setup errors, zero discovered tests and unrelated failures do not establish RED. Task 2 consumes this commit and reruns the same tests after writing. These tests protect instruction discoverability only; they cannot prove future agents obey the procedure or that a runtime guard is secure.</action>
  <verify>
    <automated>python -m unittest discover -s tests -p test_guard_repair_contract.py -v</automated>
    <fails_when>For final GREEN: non-zero exit or zero tests; for RED validity: no named planned assertion failure, any setup/import error, or an unexpected pass.</fails_when>
  </verify>
  <acceptance_criteria>RED receipt identifies a planned missing-link/reference assertion before documentation edits. Fixture mutations detect each removed link and missing target. The completed procedure makes the unchanged fixture and real tree pass.</acceptance_criteria>
  <done>The regression test is committed before Task 2, with genuine RED evidence; final GREEN remains pending until the procedure is integrated.</done>
</task>

<task type="auto">
  <name>Task 2: Write and connect the bounded guard repair procedure</name>
  <files>AGENTS.md, .ai/RULES.md, .ai/references/guard-repair-workflow.md, .ai/agents/coder.md, .ai/agents/phase-preparer.md, .ai/agents/code-reviewer.md</files>
  <read_first>AGENTS.md, .ai/RULES.md, .ai/agents/coder.md, .ai/agents/phase-preparer.md, .ai/agents/code-reviewer.md, .ai/agents/doc-writer.md, .ai/references/git-workflow.md#canonical-threat-tracking, tests/test_guard_repair_contract.py, docs/maintenance/issue87/CONTEXT.md, .ai/references/methods/tdd.md, .ai/runtime/TEMPLATE-CONTRACT.md, Task 1 RED evidence. Read .ai/references/guard-repair-workflow.md if it exists before its assigned creation.</read_first>
  <action>The coder writes the new canonical reference and small direct links in the entry point, RULES and each assigned role, using the doc-writer method. Retain complete existing role methods. Preparers require a matrix and executable test prerequisite; coders record observed RED before changing guard logic; reviewers independently challenge bypasses and legitimate input and audit the evidence sequence. Follow the procedure and approval categories below. Keep current phase-discussion and explicit-implementation requirements, canonical threat tracking and no-merge boundaries. Preserve PR86 worktree-guard advisory exits and ordinary scratchpad writes; this component adds no hook enforcement or new runtime gate. Run the same focused checks for GREEN in the worker checkout and again after integration, recording both revisions and repairing only owned defects.</action>
  <verify>
    <automated>python -m unittest discover -s tests -p test_guard_repair_contract.py -v</automated>
    <fails_when>Non-zero exit or zero tests discovered.</fails_when>
    <automated>python -m unittest discover -s tests -p test_agent_sources.py -v</automated>
    <fails_when>Non-zero exit or zero tests discovered.</fails_when>
    <automated>python -m unittest discover -s tests -p test_workflow_links.py -v</automated>
    <fails_when>Non-zero exit or zero tests discovered.</fails_when>
    <automated>python -m unittest discover -s tests -p test_threat_tracking_contract.py -v</automated>
    <fails_when>Non-zero exit or zero tests discovered.</fails_when>
  </verify>
  <acceptance_criteria>The reference contains the matrix, evidence sequence and approval categories below, reached by all five entry points. Fresh independent review confirms preserved phase authority and advisory behavior. Tests pass with removal mutations still detecting lost guidance.</acceptance_criteria>
  <done>Owned changes and the execution SUMMARY are committed; the coordinator has the exact checks, reviewed revision and remaining blockers for integration and verification.</done>
</task>
</tasks>

In code-reviewer.md add only a small link to the existing
.ai/references/git-workflow.md#canonical-threat-tracking and direct the reviewer
to perform the issue-link audit as the canonical contract defines at the current
reviewed/publication revision. The orchestration owner defines the expanded
audit in git-workflow.md; do not duplicate it or link to a future missing anchor.
This agreed link keeps the two source PRs independent.

## Required canonical procedure

1. Establish the guard's actual entry point, parser/normalization layers,
   protected operation, expected deny/warn/allow result and accepted legitimate
   behavior. Inspect the callers and existing executable tests. A regex match
   or source-string assertion alone cannot establish a security repair.
2. Before implementation, have an independent reviewer/scout propose bypass
   and false-positive cases from that boundary. Independence means a different
   agent challenges the design; the coder still owns test implementation.
   The coordinator routes agents under existing dispatch/isolation authority.
3. Record a matrix with scenario ID, concrete safe input, parser/entry point,
   expected result, rationale, regression test name and observation. Include
   every dimension below or a concrete boundary-specific non-applicability
   reason. Do not fabricate encodings or methods an entry point cannot parse.
4. Write and run executable regression tests through the affected public entry
   point before changing guard logic. Use temporary repositories, harmless
   fixtures and stubbed providers instead of touching real destructive targets.
   Pair denied/bypass cases with legitimate controls and assert side effects,
   exit/result and preservation where those are the contract.
5. Inspect RED: the named target assertion fails for the expected behavioral
   reason at a captured revision before the implementation commit. Missing
   tools, setup crashes, syntax errors, parser crashes, zero tests, unrelated
   failures or unexpected passes are INVALID_RED. Fix the test/setup or report
   a precise blocker; never manufacture a failure or weaken the expected result.
6. Implement within owned scope, rerun the same tests for GREEN, then run the
   relevant regression suite and any required checks. New discoveries extend
   the matrix/tests within scope before more logic changes. Record any refactor
   and its passing rerun; absence of a needed refactor needs no extra commit.
7. Return receipts with input revision, scenario IDs, command, exit, test name,
   expected/actual assertion, RED commit, GREEN commit/revision and final result.
   An independent reviewer assesses case completeness and evidence ordering,
   adds counterexamples and reruns relevant safe cases. Missing required evidence
   remains a gap; a green suite is not proof that untested variants are safe.

## Example matrix to include in the reference

Examples are a design aid, not executed evidence or authority to operate on a
real checkout/service. Each actual repair supplies inputs supported by its parser.

| Dimension | Bypass/edge candidate | Legitimate paired control | Required observation |
|---|---|---|---|
| Case | Mixed-case command, option, method or key where accepted | Same spelling in an inert argument or description | Parsed operation receives the intended policy; inert text stays allowed |
| Empty/missing | Empty value, omitted field, whitespace or null where supported | Valid optional omission or empty harmless payload | Defined deny/warn/allow result; no accidental privileged fallback |
| Encoding | Supported percent/Unicode/escape or nested representation | Literal escaped text or valid encoded benign value | Guard and consumer agree after actual decoding; no speculative decoder |
| Alternate methods/bodies | Equivalent destructive verb/flag; POST/JSON/form or body override if accepted | Read-only method/flag and harmless JSON/form body | All accepted routes to the operation covered; valid reads preserved |
| Quoting/tokenization | Quoted executable/path, spaces, escapes, option ordering and separators accepted by the shell | Quoted inert text, path containing spaces and ordinary scratchpad write | Actual argv/parser semantics govern the result, not a substring |
| Parser differences | Tool JSON versus raw shell; Bash versus PowerShell or API route if supported | Semantically equivalent benign input through each supported entry | Producer and consumer paths tested independently; unsupported variants explained |
| Existing advisory policy | PR86 primary-checkout edit/scratchpad notice | Properly isolated or read-only call | Existing warning/success contract retained; destructive enforcement has its separate owner |

## Concise communication and approval categories

Keep progress to the outcome or finding, the next meaningful check and any
specific blocker; use concrete paths/revisions when needed. Avoid repeating
the full plan, speculative warnings or a large checklist in every update.
An approval request names the exact action, target, effect, missing authority
and why it is needed. Continue unrelated authorized work while it is pending.

| Category | Boundary and handling |
|---|---|
| Network, DNS, tunnel and infrastructure changes | Reuse explicit approval for its recorded target/effect. A new external route, DNS change, tunnel exposure or infrastructure mutation beyond that scope needs a concrete request before that action. Ordinary already-authorized reads/checks do not become a blanket network approval prompt. |
| Tool/package installation | Inspect installed tools first and reuse available runners. For a new install outside recorded authority, identify the exact tool/version/source, purpose and affected environment; request that bounded install. Missing capability blocks only its dependent check. This issue authorizes no installs. |
| New scope or changed decisions | Show the concrete acceptance/ownership change and obtain the human decision through the coordinator. Routine fixes and implementation choices inside existing scope continue. Preserve prior explicit phase implementation and delivery authorization; internal plan/execute/verify transitions do not reopen it. |
| Existing phase authority and destructive actions | Phase discussion and explicit implementation permission remain required when not already supplied. Existing deletion, exact-target cleanup, credentials/spending and merge limits continue to apply. No new automatic approval, fuzzy permission match or merge authority is introduced. |

<threat_model>
Security review: not applicable to a new executable trust boundary. This component
changes guidance and fixture-only reachability tests; it does not alter guard
parsing, privileged operations, hooks, authentication or provider requests.
The guard implementation owner supplies actual threat findings and runtime
behavior tests. Existing threat identity and safe tracking requirements remain
unchanged. No new concrete threat was identified in this inspected scope.
</threat_model>

<verification>
Run the four frontmatter checks against the integrated revision. The coordinator
also runs the configured full suite before final verification. Fresh code-reviewer
and doc-verifier review the reference and narrow role/authority changes against
the matrix and categories above. Check that independent case generation precedes
guard implementation in the procedure, observed RED cannot be replaced by a
setup failure, controls protect legitimate operations, and exact prior authority
is preserved. Review tests as removal protection, not claims of runtime security.
An independent phase-checker reviews this PLAN before implementation.
</verification>

<success_criteria>
- ISSUE87-03: The reachable repair procedure requires independent bypass and false-positive cases and executable failing tests before guard implementation, with falsifiable RED/GREEN receipts.
- ISSUE87-AUTH: Concise progress/approval guidance preserves prior written authorization, existing phase authority, PR86 advisory behavior and no-merge limits.
- Required focused checks pass, mutation regressions remain meaningful and independent review has no unresolved blocking finding.
- No source outside declared ownership is changed, and no implementation was performed by the preparer.
</success_criteria>

## Multi-source coverage audit

| Source | Item | Coverage/disposition |
|---|---|---|
| GOAL | Issue87 maintenance scope; no adopting-project phase goal exists | Tasks 1–2 cover the assigned workflow component; do not populate the skeleton |
| REQ | Context acceptance 3, local label ISSUE87-03 | Required procedure, matrix and independent evidence review |
| REQ | Authorization decisions, local label ISSUE87-AUTH | Task 2 approval categories and preserved authority |
| RESEARCH | Coordinator scout packet: fixture-copy mutations and standard unittest runner | Task 1 uses existing threat-contract pattern; exact focused checks grounded |
| CONTEXT | Preserve PR86 advisory behavior and scratchpads | Explicit matrix row, task boundary and review criterion |
| CONTEXT | Existing authority persists; no merge or issue closure | Context and approval categories |
| CONTEXT | Provider adapters, threat lifecycle and bounded changes | Preserve existing contracts; their implementation remains with other owners |
| CONTEXT | Other acceptance 1–2 and 4–7 | Outside this assigned component; coordinator plans own them, not deferred from issue87 |

<output>
The coder creates the coordinator-assigned workflow execution SUMMARY
under docs/maintenance/issue87/, including commits, actual Checks and TDD Evidence
for the removal contract. The coordinator consolidates evidence and handles
publication under the already-recorded draft-only authorization. No merge.
</output>
