---
phase: quick-261013-001
plan: "01"
type: execute
wave: 1
depends_on: []
input_revision: 00d1e5af3c2d7370402115588eaacc50f7ff74e4
files_modified:
  - .ai/references/git-workflow.md
  - .ai/templates/issue.md
  - .ai/templates/pull-request.md
  - .ai/templates/phase-prompt.md
  - .ai/templates/summary.md
  - .ai/agents/phase-preparer.md
  - .ai/agents/coder.md
  - .ai/agents/phase-checker.md
  - .ai/agents/verifier.md
  - .ai/workflows/plan-phase.md
  - .ai/workflows/execute-phase.md
  - .ai/workflows/quick.md
  - .ai/workflows/ship.md
  - .ai/runtime/TEMPLATE-CONTRACT.md
  - tests/test_issue_format.py
  - tests/test_threat_tracking_contract.py
files_deleted: []
autonomous: true
requirements: []
acceptance: [QT-01, QT-02, QT-03, QT-04, QT-05, QT-06]
documentation:
  - .ai/references/git-workflow.md
  - .ai/templates/issue.md
  - .ai/templates/pull-request.md
  - .ai/templates/phase-prompt.md
  - .ai/templates/summary.md
  - .ai/agents/phase-preparer.md
  - .ai/agents/coder.md
  - .ai/agents/phase-checker.md
  - .ai/agents/verifier.md
  - .ai/workflows/plan-phase.md
  - .ai/workflows/execute-phase.md
  - .ai/workflows/quick.md
  - .ai/workflows/ship.md
  - .ai/runtime/TEMPLATE-CONTRACT.md
resources: []
checks:
  - [python, -m, unittest, discover, -s, tests, -p, test_issue_format.py, -v]
  - [python, -m, unittest, discover, -s, tests, -p, test_threat_tracking_contract.py, -v]
  - [python, -m, unittest, discover, -s, tests, -p, test_todo_issues.py, -v]
  - [python, -m, unittest, discover, -s, tests, -p, test_workflow_links.py, -v]
must_haves:
  truths:
    - "Every threat identified anywhere in a PLAN or SUMMARY, including mitigated, accepted, deferred and pre-existing findings, creates or reuses one canonical Git issue through the coordinator."
    - "PLAN, SUMMARY and related PR/MR retain stable threat IDs, canonical issue links and truthful lifecycle status; repeated observations and reruns reuse the same risk."
    - "Every canonical risk records assessed severity, affected scope, mitigation, responsible owner, status and resolution evidence without publishing exploit details, credentials or private evidence."
    - "Unresolved, accepted and deferred risks remain visible and receive non-closing references; merge cannot silently resolve them."
    - "Required coordinator reconciliation runs for phase and quick paths even when optional plan checking or verification is skipped, without a new ordinary-stage approval."
    - "The contract is useful on current main independently of PR76/77/78; tests and documentation distinguish structural checks from semantic review and disclose GitLab runtime limits."
  artifacts:
    - path: .ai/references/git-workflow.md
      provides: "Canonical threat reconciliation, safe publication, deduplication and closure procedure"
    - path: .ai/templates/issue.md
      provides: "Security risk assessment and lifecycle fields in the existing variant"
    - path: .ai/templates/phase-prompt.md
      provides: "PLAN threat tracking structure"
    - path: .ai/templates/summary.md
      provides: "SUMMARY carry-forward and newly discovered threat tracking structure"
    - path: tests/test_threat_tracking_contract.py
      provides: "Offline producer/consumer contract regression coverage"
  key_links:
    - from: .ai/templates/phase-prompt.md
      to: .ai/templates/summary.md
      via: "Carry the original threat identity, issue and state forward; include prose-only findings"
    - from: .ai/workflows/plan-phase.md
      to: .ai/references/git-workflow.md
      via: "Coordinator reconciles PLAN findings before reporting preparation complete"
    - from: .ai/workflows/execute-phase.md
      to: .ai/workflows/ship.md
      via: "Coordinator reconciles SUMMARY findings and checks PR/MR references before readiness"
---

<objective>
Track every identified PLAN and SUMMARY threat through one safe canonical Git issue, from planning through execution and PR/MR delivery. This is one reusable workflow-contract outcome, implemented in three sequential tasks with focused edits, not a new risk platform.

Output: existing Git workflow, security-risk and PR templates, producer/consumer instructions and offline contract tests. No runtime provider adapters or new runtime verbs.
</objective>

<execution_context>
@.agents/skills/quick/SKILL.md
@.ai/workflows/quick.md
@.ai/templates/summary.md
</execution_context>

<context>
Repository: D:/Codex Projects/ai-engineering-template/.worktrees/quick-plan-summary-threat-issues-143316138. Branch: quick-plan-summary-threat-issues-143316138. Source inspected at input_revision above; base main is 7dcf641. PR78 has not landed; coordinator alone handles later main reconciliation.

The coordinator reports that [enhancement issue 79](https://github.com/Tasaddar12/ai-engineering-template/issues/79) and [tracking draft PR80](https://github.com/Tasaddar12/ai-engineering-template/pull/80) were published, linked and read back before test scripts. Reuse that draft; do not create another tracking PR. Issue79 tracks this enhancement, not every individual threat.

Implementation, commits, push, draft and safe issue tracking are already authorized. Workers commit owned files and their SUMMARY; only the coordinator publishes or amends external issues and planning links. NEVER MERGE. No ordinary-stage approval is added. Preserve existing security, readiness and explicit closure/merge authority.

PROJECT, STATE, ROADMAP and REQUIREMENTS are unfilled adoption skeletons. No real phase requirements or CONTEXT/RESEARCH exist for this quick task; requirements is intentionally empty rather than claiming example AUTH IDs. QT acceptance below comes from the assigned quick goal. Do not fill project identity or edit scaffold records, shared QUICK.md, STATE.md, config, runtime implementation, CI or unrelated PRs.

Observed seams: phase-preparer.md has a PLAN STRIDE register and boundary-triggered security gate; coder.md emits only new-surface Threat Flags; summary.md lacks that section; execute-phase.md aggregates SUMMARYs; quick.md makes checking and verification optional. issue_format.py derives ordered headings from issue.md, with extra field/table checks only for UAT. delivery.py and todo_issues.py implement GitHub/gh only. Reuse these contracts rather than assuming PR76/77 adds a prerequisite.

</context>

<tasks>
<task type="auto">
  <name>Task 1: Define canonical threat issue and PR/MR lifecycle</name>
  <files>.ai/references/git-workflow.md, .ai/templates/issue.md, .ai/templates/pull-request.md, tests/test_issue_format.py</files>
  <read_first>.ai/references/git-workflow.md, .ai/templates/issue.md, .ai/templates/pull-request.md, .ai/runtime/lib/issue_format.py, .ai/runtime/lib/todo_issues.py, .ai/runtime/lib/delivery.py, tests/test_issue_format.py, tests/test_todo_issues.py</read_first>
  <action>
Add one authoritative threat-tracking section to git-workflow.md, linked by consumers. Every identified threat anywhere in PLAN/SUMMARY prose, tables, deviations, Deferred/Remaining, or Threat Flags gets a canonical issue regardless of severity, provenance, scope or current mitigation. Finding a threat does not authorize broad remediation outside the plan. Workers retain stable local IDs and return safe issue requests marked Pending with the concrete dependency; the coordinator owns search, publication, readback and link reconciliation.

Define one stable canonical risk key per repository and affected surface/control plus failure mode/remediation scope; preserve existing keys and source IDs as aliases. Search all open and closed issues, linked PR/MRs and current PR/MR before creation, and compare semantic scope rather than titles, severity or PLAN/SUMMARY location. Reuse an actionable full-scope match and record all source occurrences. Multiple distinct risks get distinct issues; a fully resolved closed match is reusable only with matching resolution evidence. If a closed match still contains an unresolved risk, follow existing reopening authority and report any actual blocker without silently claiming it resolved or creating a duplicate. Serialize coordinator writes. After uncertain creation, search/read back the exact reviewed intent and key before any retry. Never use TODO creation or todo.issue-publish as a workaround for threat records; direct authorized writes use existing provider tools after issue.validate.

Extend only the existing Security risk File Template with an ordered `## Risk assessment and lifecycle` heading. Require Threat ID/risk key and source aliases, Severity (`critical|high|medium|low`) with impact/likelihood rationale and uncertainty, Owner, Status (`unresolved|mitigated|accepted|deferred`), Mitigation or safe next action, and Resolution evidence (revision, actual check/result, or Pending with dependency). Existing Affected surface, Scope and acceptance, Safe evidence and Related links supply affected scope, measurable resolution criteria, sources and PR/MR links. Assess actual impact; do not blanket-classify threats as critical. Distinguish PLAN disposition (`mitigate|accept|transfer`) from observed status: planned mitigation and transfer remain unresolved until evidenced; accepted requires actual responsible-party rationale/evidence and retains residual risk; deferred records owner, reason and next action. Mitigated requires demonstrated secure outcome and matching revision/check evidence.

Reconcile both private-reporting instructions in issue.md: a separately reviewed sanitized public tracker can be published under standing tracking authorization without asking for private-channel approval. Credentials, private logs, exploit steps and sensitive attachments stay out of every publishable document, title, body and link. Use an existing authorized restricted reporting channel for sensitive detail; missing private access blocks only that detail or dependent action, while safe tracking proceeds. If even a safe description/link cannot be disclosed, retain an explicit publication blocker and restricted canonical issue/reference where accessible; never fabricate a public URL or claim every issue was published. Respect destination visibility when linking private records.

Add a concise threat table to the PR File Template under Risks or rollback: Threat ID, assessed Severity, Status, Canonical issue, and safe mitigation/resolution evidence. Preserve existing template headings and lifecycle fields. Use neutral issue links for unresolved, accepted and deferred risks, including mitigated findings without verified closure eligibility. Merge is not risk resolution. Only verified scope-complete mitigation plus existing explicit closure authority can justify a closing reference or closure; never autoclose an unresolved risk. Explain GitLab MR-neutral policy applicability but the observed GitHub-only runtime implementation: use a verified authorized host tool if available, otherwise retain Pending/publication blocker. Do not create adapters or claim runtime GitLab support.

Extend test_issue_format.py using the real template-derived validator to show the new Security risk heading is required/in order, valid safe filled bodies at different severities/states pass, other variants remain intact, and installed namespace security validation uses its own template. Keep validator implementation unchanged; document that fields, semantic dedup, disclosure safety and resolution truth remain review obligations.
  </action>
  <verify><automated>python -m unittest discover -s tests -p test_issue_format.py -v</automated><fails_when>Non-zero exit, any failing assertion, or Ran 0 tests.</fails_when></verify>
  <acceptance_criteria>QT-02/03/04/05: one authoritative procedure covers canonical identity, semantic dedup, safe reporting, assessed lifecycle fields and evidence-based closure; real issue.validate rejects missing/reordered Security risk headings without claiming semantic enforcement.</acceptance_criteria>
  <done>The existing Security risk and PR templates expose usable safe tracking fields, their instructions agree with the canonical Git procedure, and focused validator tests pass.</done>
</task>

<task type="auto">
  <name>Task 2: Wire every producer, coordinator and review path</name>
  <files>.ai/templates/phase-prompt.md, .ai/templates/summary.md, .ai/agents/phase-preparer.md, .ai/agents/coder.md, .ai/agents/phase-checker.md, .ai/agents/verifier.md, .ai/workflows/plan-phase.md, .ai/workflows/execute-phase.md, .ai/workflows/quick.md, .ai/workflows/ship.md, .ai/runtime/TEMPLATE-CONTRACT.md, tests/test_threat_tracking_contract.py</files>
  <read_first>.ai/templates/phase-prompt.md, .ai/templates/summary.md, .ai/agents/phase-preparer.md, .ai/agents/coder.md, .ai/agents/phase-checker.md, .ai/agents/verifier.md, .ai/workflows/plan-phase.md, .ai/workflows/execute-phase.md, .ai/workflows/quick.md, .ai/workflows/ship.md, .ai/runtime/TEMPLATE-CONTRACT.md, .ai/references/git-workflow.md, tests/test_workflow_links.py</read_first>
  <action>
After Task1, add concise linked instructions at existing seams, preserving full methods, template examples and all unrelated stages. Add threat_model to the phase-prompt File Template and update the preparer's register example, security planning gate and checklist consistently. Record Threat ID, Category, Component/scope, assessed Severity, Disposition, Mitigation/task/check, Owner, observed Status, Canonical issue (verified URL or Pending with reason) and Resolution evidence; use a compact table plus linked details rather than an oversized duplicate issue body. The boundary-triggered STRIDE requirement still applies, but threat tracking applies to every actually identified threat even when no new boundary is changed. A no-threat outcome states none identified with inspected scope; do not invent threats merely to fill a register.

Add `## Threat Flags` to the SUMMARY File Template. Carry every PLAN threat forward with the same ID/key and issue; add newly discovered, pre-existing, already mitigated, accepted and deferred threats anywhere in the SUMMARY. Use the same lifecycle fields and actual evidence, with source references to PLAN entries; explicit None identified is allowed after assessment. Replace coder.md's omit-if-no-new-surface restriction and extend its mitigation/self-check instructions accordingly. Authors record safe requests/Pending and own their SUMMARY; they never publish or edit shared PLAN/status records.

At plan-phase.md handle_preparer_return and quick.md after the preparer's committed plan is available, require coordinator reconciliation of every PLAN finding through the canonical Git procedure before reporting preparation complete. At execute-phase.md aggregate_results/review gate and quick.md after reading the integrated SUMMARY, scan all PLAN and SUMMARY sections, reconcile aliases/dedup/status/evidence, create/reuse/read back safe canonical issues, and update owned planning links through the coordinator. Reconcile newly identified review threats once represented in the owned PLAN/SUMMARY. Run this mandatory tracking step outside quick's optional check_plan/verify branches, including ordinary quick mode; do not introduce a new human stage gate. Retain actual access/provider blockers as Pending and keep independent authorized work moving.

Extend phase-checker.md Dimension7d to check that every identified PLAN threat has assessed severity, owner, lifecycle and coordinator handoff/link; a worker's valid Pending request before coordinator publication is not a missing invented URL. Extend verifier.md to inspect PLAN/SUMMARY coverage, carried identity, actual linked issue and evidence against source; missing/unavailable required publication stays a gap, not passed evidence. In ship.md preflight/body/merge seams require reconciled safe risk links and truthful PR/MR table, explicit remaining risks and closure-reference audit; unresolved risks cannot be hidden by merged state. Preserve existing critical-risk/readiness gates and human decisions. This is agent/coordinator review enforcement, not an implemented parser or automatic risk-close guard.

Update TEMPLATE-CONTRACT.md with concise additive threat-record and coordinator/worker ownership rules and the honest structural-only validator boundary. Create test_threat_tracking_contract.py to parse actual File Template blocks and the relevant workflow step regions, checking the declared tracking fields, producer-to-canonical-reference reachability and mandatory coordinator steps' placement outside optional quick branches. Exercise template/section mutations in temporary fixtures so missing carry-forward fields or an optional-only tracking hook are detectable. Keep tests offline and structural; do not simulate an unimplemented dedup engine or invoke remote tools.
  </action>
  <verify><automated>python -m unittest discover -s tests -p test_threat_tracking_contract.py -v</automated><fails_when>Non-zero exit, missed mutation regression, or Ran 0 tests.</fails_when><automated>python -m unittest discover -s tests -p test_workflow_links.py -v</automated><fails_when>Non-zero exit, any missing/case-mismatched guidance link, or Ran 0 tests.</fails_when></verify>
  <acceptance_criteria>QT-01/02/04/06: full PLAN/SUMMARY scope reaches coordinator reconciliation in phase and both quick modes; checker/verifier/ship have an explicit completion/closure check; stable ID and issue fields survive the templates; workers do not publish.</acceptance_criteria>
  <done>Each required producer and consumer reaches the shared procedure through an exact local link, mandatory tracking cannot be skipped with optional quick validation, and offline contract/link checks pass.</done>
</task>

<task type="auto">
  <name>Task 3: Lock edge cases and report the evidence honestly</name>
  <files>tests/test_issue_format.py, tests/test_threat_tracking_contract.py</files>
  <read_first>tests/test_issue_format.py, tests/test_threat_tracking_contract.py, tests/test_todo_issues.py, .ai/runtime/lib/issue_format.py, .ai/templates/issue.md, .ai/templates/pull-request.md, .ai/references/git-workflow.md, .github/workflows/validate.yml</read_first>
  <action>
After Task2, complete focused fixtures/mutation checks for cross-PLAN/SUMMARY alias retention and rerun identity instructions; canonical review of open/closed matches; uncertain-create recovery; mitigated/accepted/deferred/unresolved reporting; Pending provider/private-access blockers; safe public tracking without private-channel approval; and unresolved/non-closing PR/MR references. Test the contract's structure and required review obligations rather than asserting that prose executes provider side effects. Include negative validator evidence that correctly headed Security risk bodies with missing/incorrect assessment field values still pass today's structuralOnly gate, while missing/reordered headings fail: these tests deliberately preserve an honest limitation rather than implying enforcement of every field. Retain all existing UAT behavior and run unchanged TODO integration tests to protect the existing issue-publication pathway.

Run the focused commands and existing repository required validation only after the coordinator's already-published tracking records, using the available Python interpreter. No test was run by the preparer. In the owned quick SUMMARY, name actual revisions, commands, results/skips, docs covered, remaining threats and canonical issue requests/links. Hand the coordinator implementation evidence for independent code/document review, safe issue/PR readback and required remote checks; local contract passes do not prove live redaction/dedup or a completed GitLab publication. Do not mark absent checks, issue links or unresolved closure evidence passed. Preserve PR80 as draft and NEVER MERGE.
  </action>
  <verify><automated>python -m unittest discover -s tests -p test_issue_format.py -v</automated><fails_when>Non-zero exit, changed structuralOnly expectation, or Ran 0 tests.</fails_when><automated>python -m unittest discover -s tests -p test_threat_tracking_contract.py -v</automated><fails_when>Non-zero exit, missed required edge-case mutation, or Ran 0 tests.</fails_when><automated>python -m unittest discover -s tests -p test_todo_issues.py -v</automated><fails_when>Non-zero exit, duplicate-publication/readback regression, or Ran 0 tests.</fails_when></verify>
  <acceptance_criteria>QT-03/04/05/06: regression fixtures exercise lifecycle/safety/identity contracts and the actual validator limits; SUMMARY and final evidence distinguish offline structure, semantic review, provider publication and remaining blockers.</acceptance_criteria>
  <done>Focused offline checks pass, required broader checks are reported from actual runs, and the committed SUMMARY gives the coordinator a complete truthful review/publication handoff.</done>
</task>
</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|---|---|
| Private findings to tracked/public docs and provider issues | Agent-authored descriptions, evidence and links may expose restricted security data. |
| Agent claims to canonical risk status and PR/MR closure | Unsupported status/dedup claims or closing references may lose unresolved risks. |

## STRIDE Threat Register

| Threat ID | Category | Component/scope | Severity and assessment | Disposition | Mitigation/task/check | Owner | Status | Canonical issue | Resolution evidence |
|---|---|---|---|---|---|---|---|---|---|
| T-QT-01 | Information disclosure | Publishable PLAN/SUMMARY/issue/PR text and links | high: accidental secret or exploit disclosure has broad public impact; actual sensitive payload not identified | mitigate | Task1 safe-public/restricted-detail rule; Task2 consumers; test_issue_format.py and test_threat_tracking_contract.py plus independent safe-content review | coordinator | unresolved | https://github.com/Tasaddar12/ai-engineering-template/issues/81 | Pending implementation and review; offline checks alone do not verify redaction |
| T-QT-02 | Tampering/Repudiation | Canonical issue identity, lifecycle and closing references | medium: duplicate or premature closure can conceal remaining work; source currently lacks shared threat lifecycle | mitigate | Task1 dedup/closure procedure; Task2 carry-forward and ship checks; Task3 contract mutations and independent lifecycle review | coordinator | unresolved | https://github.com/Tasaddar12/ai-engineering-template/issues/82 | Pending implementation, actual issue readback and PR closure-reference review |
</threat_model>

<verification>
The preparer checks source paths, ownership, task fields and coverage only and runs no tests. The executor runs the stated focused tests. Coordinator integrates, obtains fresh independent review and verification, keeps PR80 current and observes remote `validate` on the candidate revision. The existing CI workflow requires `python -m unittest discover -s tests -v` on Linux/Windows plus `bash .ai/hooks/ai-tier-notice.test.sh`, `bash .ai/hooks/worktree-guard.test.sh`, `bash .ai/hooks/context-handoff.test.sh`, and `bash .ai/hooks/worktree-location.test.sh`. Record actual local runs or host-specific skips; remote pending/failing checks prevent readiness. Empty scaffold verification.commands does not count as a passing configured check.

Security review applies to the changed disclosure/status trust boundaries above. This PLAN changes instructions, templates and offline tests; neither the Python runtime nor these tests automatically scan all prose, determine severity, guarantee semantic deduplication, redact secrets, publish issues or prevent provider autoclosure. Those obligations are assigned to the coordinator and independent reviewers, with access failures reported explicitly.

Tasks are sequential: Task2 consumes Task1's procedure; Task3 strengthens Task1/2 tests and consumes Task2's fixtures. Shared test ownership is intentional within this single plan, never parallelized.
</verification>

<source_audit>

| Source | ID | Required outcome / constraint | Task | Status |
|---|---|---|---|---|
| GOAL / QUICK.md and assignment | QT-01 | Every actually identified PLAN/SUMMARY threat, anywhere and at every state | 1,2 | COVERED |
| GOAL / assignment | QT-02 | Canonical Git issue and stable document/related PR/MR links; dedup across sources/reruns | 1,2 | COVERED |
| GOAL / assignment | QT-03 | Assessed severity, scope, mitigation/owner/status and resolution evidence | 1,3 | COVERED |
| GOAL / assignment | QT-04 | Honest remaining risks and evidence-based closure; merge never closes unresolved risks | 1,2,3 | COVERED |
| CONTEXT / coordinator assignment | QT-05 | Safe public tracking plus restricted sensitive details; no new stage approval | 1,3 | COVERED |
| RESEARCH / scout packet verified against sources | QT-06 | Producer/coordinator/checker/ship seams; optional quick modes; real validator limits; focused offline tests | 2,3 | COVERED |
| REQ | none | No adopting-project requirements assigned; instructional skeleton IDs excluded | all | NOT APPLICABLE |
| CONTEXT / coordinator assignment | limits | Independent main change, no PR76/77/78 dependency, GitLab limitation without adapters, published79/80 before tests, NEVER MERGE, no scaffold changes | all | COVERED |
</source_audit>

<success_criteria>
All QT outcomes are covered by the integrated instructions/templates and focused regression evidence. Every actual threat has a coordinator-reconciled canonical issue or an explicit unresolved publication blocker; Pending is never treated as a verified link. Existing private-reporting prose no longer prevents safe authorized public tracking. Required source/doc review and local/remote validation remain truthful and current. No runtime adapters, scaffold edits, unrelated publication or merge occurs.
</success_criteria>

<output>
Create and commit `.planning/quick/261013-001-track-every-plan-summary-threat-canonical/261013-001-track-every-plan-summary-threat-canonical-SUMMARY.md`. Return owned commits, exact changed paths, actual checks/results, issue requests/links and remaining blockers to the coordinator. Only the coordinator updates QUICK/STATE and publishes; this preparer owns and commits only the assigned PLAN.
</output>

