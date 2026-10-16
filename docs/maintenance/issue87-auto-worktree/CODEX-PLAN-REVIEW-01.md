## PLAN REVIEW
Verdict: needs-revision

**Phase or quick task:** Issue87 maintenance Task6 — supported Codex startup isolation and synchronous guards.

Reviewed plan: `docs/maintenance/issue87-auto-worktree/CODEX-PLAN.md` (`P` below). One binding sandbox-policy contradiction requires correction. The matcher concern is resolved: official documentation explicitly supports `"*"` as match-all. [Hooks matcher patterns](https://learn.chatgpt.com/docs/hooks#matcher-patterns)

### Coverage Summary

| Check | Status | Authority | Evidence | Inspected paths |
|---|---|---|---|---|
| phase_goal | conclusive | CONTEXT.md#Authorized Codex enforcement addition | P Tasks6A–6C cover startup selection, guards, installation, native evidence and documentation; original movement acceptance remains separate. | P; CONTEXT.md; PLAN.md |
| safety | incomplete | CONTEXT.md:105 | Required trust, source confinement and preservation controls are planned, but unconditional workspace-write conflicts with preserving stricter sandbox policy; finding below. | P:265; CONTEXT.md:105 |
| requirement_coverage | conclusive | CONTEXT.md:113–118 | ISSUE87 → P Tasks6A–6C. CW-01 →6A/6B; CW-02 →6A/6B; CW-03 →6B; CW-04 →6A/6B; CW-05 →6B; CW-06 →6C/coordinator. No ID omitted; CW-04’s policy handling needs correction. | P; CONTEXT.md |
| task_completeness | conclusive | TEMPLATE-CONTRACT.md#Author an executable plan | All three tasks contain exact files, read_first, action, acceptance, runnable verification, failure signals and done criteria. | P:258–318; TEMPLATE-CONTRACT.md |
| ownership | conclusive | RULES.md#Orchestration and handoffs | A/B/C have disjoint exact paths and separate summaries. Shared records/publication remain coordinator-owned. PR99/model routing and adoption records are excluded. | P:214–233; CODEX-PREPARER-SUMMARY.md |
| dependency_graph | conclusive | RULES.md#Orchestration and handoffs | Explicit component prerequisites require integrated A before B, and integrated A+B before C. The maintenance companion is not represented as independently executable canonical phase plans. | P:221–242; Tasks6A–6C |
| temporal_coupling | conclusive | phase-checker.md#Dimension 3b | B consumes A’s committed module/hook/API; C consumes integrated source and native receipts. Native fixture resource is named, with no concurrent shared fixture. | P:44; P:221–242 |
| key_links | conclusive | TEMPLATE-CONTRACT.md#Scheduling | Installed launcher → runtime API; native registrations → hook adapter; hooks/list → required effective trusted registrations; six workflows → canonical protocol are assigned explicitly. | P:86–98; .ai/install.py |
| context_decisions/deferred_scope | incomplete | CONTEXT.md#Authorized Codex enforcement addition | Startup/controller distinction, no detached adoption, no dirty copying/sync, preserved Claude behavior and draft-only publication are respected. Sandbox-policy exception remains. | P; CONTEXT.md; original PLAN.md:172–179 |
| must_haves_derivation | conclusive | phase-checker.md#Dimension 6 | Six observable truths map to CW outcomes, concrete artifacts and producer/consumer links. Startup success is expressly insufficient for tool-denial or existing-agent movement claims. | P:65–98 |
| runtime_source_contract | conclusive | Existing session and classification contracts | `open_session(..., base=None, sync=True)` supports explicit base and `sync=False`; P adds validation rather than changing its contract. Existing mutation/classification helpers support structured paths and narrow notes. | .ai/runtime/lib/worktrees.py:747–832; .ai/runtime/lib/prewrite.py:402–565 |
| installer_source_contract | conclusive | Existing payload/registration/merge contracts | B owns explicit asset mapping, Codex-only registrations, managed identity/update/migration handling, timeout30 and preservation checks. Existing Python/runpy Windows pattern preserves exit status. | .ai/install.py:80–120; :444–567; :614–635; installer tests |
| native_source_contract | incomplete | CONTEXT.md:105; saved native schema/help | hooks/list metadata, trust enum, asynchronous default, OS-selected command and native feature controls match the saved evidence. Sandbox selection needs the finding’s correction. | P:141–195; capability `schemas/v2/HooksListResponse.json`; `hooks-list-command-selection.json`; `cli-help.stdout` |
| verification_frontier | conclusive | TEMPLATE-CONTRACT.md#Stated failing direction | A requires a named installed-primary-shell mutation assertion after successful setup, retains it without skip/xfail, and B must turn the identical assertion GREEN. Missing imports/setup cannot count as RED. Actual generated-native shell **and** patch denials are separately required. | P:235–243; Tasks6A/6B; saved fixture source |
| security_planning | conclusive | phase-preparer.md#Security planning gate | Three changed trust boundaries and six-column threat register identify T-AW-01/02/03, mitigation owners/checks and canonical issue98 reconciliation. Planned mitigations are not labeled resolved. | P:320–343; git-workflow.md#Canonical threat tracking |
| scope_sanity | conclusive | phase-checker.md#Dimension 5 | Three bounded component assignments serve one Codex outcome with genuine prerequisite handoffs. No configured positive task cap was found; file/task counts are inventory, not rejection grounds. | P; .planning/config.yaml; .ai/runtime/lib/config.py |
| architectural_tier_map | not_applicable | phase-checker.md#Dimension 7c | CODEX-RESEARCH contains no Architectural Responsibility Map. Runtime logic, thin adapter/asset, installer and documentation responsibilities are nevertheless explicit. | CODEX-RESEARCH.md; P |
| detailed_nyquist | not_applicable | methods/nyquist-compliance.md | No Validation Architecture or assigned VALIDATION artifact. Required executable checks and failure directions were assessed directly. | CODEX-RESEARCH.md; P |
| pattern/research_resolution | conclusive | phase-checker.md#Dimensions 11–12 | No PATTERNS artifact or unresolved research question blocks the assigned design. Saved helper is correctly labeled AST/help-only; execution remains mandatory future evidence. | CODEX-RESEARCH.md; CODEX-PREPARER-SUMMARY.md; P |

### Plan Summary

| PLAN path | Tasks | Files | Declared wave | Dependencies | Status |
|---|---:|---:|---|---|---|
| docs/maintenance/issue87-auto-worktree/CODEX-PLAN.md | 3 | 20 | 1 | No external plan IDs; explicit A → B → C component order | Needs revision |

### Handoff Evidence

- input_revision: `1ead8809a4df9047316ad80698520f4511687a5c`
- reviewed_revision: `d48c5310e988b1c6e1558c343853807230f44164`
- HEAD remained at the assigned revision; checkout remained clean.
- Read-only static review. No edits, tests, installations, applications or native probes ran. No prior review conclusions were reused.

### Blockers

#### PC-06-codex-context_compliance-01

- Plan: `docs/maintenance/issue87-auto-worktree/CODEX-PLAN.md`
- Task: 6A
- Dimension: context_compliance
- Severity: blocker
- Required property: The production launcher must preserve the effective sandbox and approval restrictions or refuse startup when its required execution mode would weaken them.
- Authority: `docs/maintenance/issue87-auto-worktree/CONTEXT.md:105` — “Production must not silently bypass native hook trust or weaken sandbox/approval policy.”
- Evidence: P:265 instructs the launcher to use a `workspace-write` sandbox unconditionally, while explicitly preserving configured model/effort and approval policy. Its option refusal prevents caller overrides but does not require detecting or preserving an existing stricter sandbox. The saved native CLI help confirms `--sandbox` selects the sandbox policy. Therefore an effective user `read-only` setting can be replaced by the planned workspace-write invocation, contrary to the locked policy constraint. Neither the launch matrix nor acceptance requires a stricter-policy refusal/preservation case.
- Example fix: Make startup conditional on preserving the effective restrictions, with a regression demonstrating that a stricter sandbox cannot become workspace-write. Any supported preservation or refusal mechanism satisfying that invariant is admissible.

**Required corrections:** Satisfy `PC-06-codex-context_compliance-01` before execution. Actual CW/native acceptance and original AW live evidence remain future verification obligations.
