---
maintenance: entrypoint-git-routing
plan: "01"
type: execute
wave: 1
depends_on: []
files_modified:
  - AGENTS.md
  - .ai/install-assets/agent-entry.txt
  - tests/test_entrypoint_git_routing.py
  - .ai/maintenance/entrypoint-git-routing-SUMMARY.md
files_deleted: []
autonomous: true
requirements: [entrypoint-git-routing]
acceptance: [ROUTE-01, ROUTE-02, ROUTE-03, ROUTE-04]
documentation: [AGENTS.md, .ai/install-assets/agent-entry.txt]
resources: []
checks:
  - [python, -m, unittest, discover, -s, tests, -p, test_entrypoint_git_routing.py, -v]
  - [python, -m, unittest, discover, -s, tests, -p, test_issue_format.py, -v]
  - [python, -m, unittest, discover, -s, tests, -p, test_session_delivery.py, -v]
  - [python, -m, unittest, discover, -s, tests, -p, test_workflow_links.py, -v]
must_haves:
  truths:
    - Both source entrypoints mandate the shared Git workflow for every issue and PR/MR create or edit, regardless of provider.
    - The mandate includes the shared reference's templates and validation requirements without duplicating its detailed rules.
    - Real Codex and Claude installs preserve the mandate and resolve host-specific reference links.
    - Existing GitHub issue-format and delivery behavior remains covered by unchanged regression suites.
  artifacts:
    - AGENTS.md
    - .ai/install-assets/agent-entry.txt
    - tests/test_entrypoint_git_routing.py
    - .ai/maintenance/entrypoint-git-routing-SUMMARY.md
  key_links:
    - Source entrypoints -> .ai/references/git-workflow.md
    - Installer asset -> installed AGENTS.md or CLAUDE.md -> .codex/references/git-workflow.md or .claude/references/git-workflow.md
---

<objective>
Make shared issue and PR/MR policy unavoidable at both agent entrypoints through a concise mandatory routing sentence in the existing Delivery section.
References: #75 (https://github.com/Tasaddar12/ai-engineering-template/issues/75).
This is explicitly authorized standalone template maintenance, based on 7dcf64136918e050454f2aabaf33aed8f481dc5d on codex/entrypoint-git-routing. The adopting .planning skeleton supplies no project requirements and remains unfilled.
</objective>

<context>
The source AGENTS.md already links the canonical Git workflow in Delivery; extend or replace that reference. The installer entry asset currently has Delivery guidance without that link; add equivalent mandatory routing there. The installer consumes the asset, maps Claude's entrypoint to CLAUDE.md, and rewrites .ai links to the selected host namespace.
Keep .ai/references/git-workflow.md, its issue and pull-request templates, runtime and installer implementation unchanged. Do not create a root CLAUDE.md or touch credentials, servers, benchmarks, shared planning records or unrelated files. Worker publication is excluded; the coordinator owns issue updates, push, tracking draft and final checks.
</context>

<tasks>
<task type="auto">
  <name>Route issue and PR/MR writes through the shared Git workflow</name>
  <files>AGENTS.md, .ai/install-assets/agent-entry.txt, tests/test_entrypoint_git_routing.py, .ai/maintenance/entrypoint-git-routing-SUMMARY.md</files>
  <read_first>
    AGENTS.md; .ai/RULES.md; .ai/references/git-workflow.md;
    .ai/install-assets/agent-entry.txt; .ai/install.py;
    .ai/templates/issue.md; .ai/templates/pull-request.md;
    tests/test_install.py; tests/test_issue_format.py; tests/test_session_delivery.py;
    .ai/templates/summary.md.
  </read_first>
  <action>
    Inspect the assigned root, branch and base before writing. Update only the existing Delivery section in each entrypoint. Require every issue and pull request/merge request creation or edit to follow .ai/references/git-workflow.md, including its templates and validation requirements, regardless of provider. Use one mandatory routing sentence; preserve the shared reference as the sole detailed policy owner and avoid reproducing template sections, commands or provider policy in the entrypoints.
    Create the focused unittest file. Check both source entrypoints for the complete routing contract, allowing harmless line wrapping. Exercise the real installer against a temporary local Git source and targets for both codex and claude, following the fixture and subprocess patterns in tests/test_install.py. Reusing that module's helper or fixture is allowed without editing it. Assert the resulting on-disk AGENTS.md and CLAUDE.md contain the same mandatory coverage, including create/edit, issues, PR/MR, provider independence, templates and validation. Assert their Git workflow links use the correct host namespace and resolve to actual installed reference files. Do not replace installation with only a render-function check or copy expected entrypoint text into the fixture. Keep tests/test_issue_format.py and tests/test_session_delivery.py unchanged and run them as regression coverage for the existing GitHub template/validation and delivery behavior.
    Run the listed checks with the available Python executable. Write the owned SUMMARY using the applicable summary template sections, with actual command results, changed paths, deviations and deferred findings. Commit only the exact owned paths through the canonical Git workflow, including the SUMMARY. Return the commit and checks to the coordinator; do not push or publish.
  </action>
  <acceptance_criteria>
    ROUTE-01: Both source entrypoints require the shared reference for all issue and PR/MR creates and edits across providers.
    ROUTE-02: Routing names templates and validation requirements; detailed shared rules remain unchanged and no duplicate policy section is introduced.
    ROUTE-03: Real fresh installations produce Codex AGENTS.md and Claude CLAUDE.md with the complete mandate and navigable host-specific links.
    ROUTE-04: Focused installed-output tests and unchanged issue-format, session-delivery and workflow-link suites pass; only declared implementation paths and the owned SUMMARY change.
  </acceptance_criteria>
  <verify>
    <automated>python -m unittest discover -s tests -p test_entrypoint_git_routing.py -v</automated>
    <fails_when>Non-zero exit, Ran 0 tests, skipped host installation coverage, missing mandate or broken host-specific reference link.</fails_when>
    <automated>python -m unittest discover -s tests -p test_issue_format.py -v</automated>
    <fails_when>Non-zero exit or Ran 0 tests.</fails_when>
    <automated>python -m unittest discover -s tests -p test_session_delivery.py -v</automated>
    <fails_when>Non-zero exit or Ran 0 tests.</fails_when>
    <automated>python -m unittest discover -s tests -p test_workflow_links.py -v</automated>
    <fails_when>Non-zero exit or Ran 0 tests.</fails_when>
    Inspect the diff to confirm the bounded edits and unchanged canonical reference, templates and runtime.
  </verify>
  <done>ROUTE-01 through ROUTE-04 have recorded evidence; the exact-owned source, tests and SUMMARY are committed.</done>
</task>
</tasks>

<verification>
Commands run from the repository root. On this Windows host, resolve the python argv element to C:/Users/killi/AppData/Local/Microsoft/WindowsApps/PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0/python.exe; execution and Git metadata writes may require the host's escalation mechanism. Existing test paths and installer fixture interfaces were inspected at the base. The focused test is created by this task before its check runs; no future test result is claimed during preparation.
Security review: not applicable. This changes instruction routing and regression tests; no authentication, secret handling, privilege boundary or runtime input-validation implementation changes.
Tracer exception: instruction-only maintenance has no new production execution path. Real installed entrypoint output supplies the end-to-end evidence in this single coherent task.
</verification>

<source_audit>
GOAL: Assigned standalone routing goal -> task 1, covered.
REQ: Assigned entrypoint-git-routing scope and ROUTE-01..04 -> task 1, covered; adoption REQUIREMENTS/ROADMAP are instructional skeletons, not maintenance authority.
RESEARCH: No research artifact assigned; installer payload and host mapping confirmed in .ai/install.py, with existing tests supplying fixture and regression interfaces.
CONTEXT: Assignment's locked boundaries -> task 1/context, covered; no adopting phase decisions created or inferred.
No uncovered required outcomes; no dependency-producing component or checkpoint.
</source_audit>

<success_criteria>All four routing outcomes are evidenced, the canonical policy remains unchanged, and a committed owned SUMMARY records the delivered slice.</success_criteria>
<output>.ai/maintenance/entrypoint-git-routing-SUMMARY.md and exact-owned implementation commit.</output>
