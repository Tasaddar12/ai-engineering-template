## PLAN REVIEW
Verdict: approved

**Phase or quick task:** Issue87 maintenance Task6 — supported Codex startup isolation and synchronous guards.

`PC-06-codex-context_compliance-01` is resolved. The revised plan prohibits production sandbox/approval overrides and requires supported native configuration inspection followed by preservation or refusal. No blockers or warnings remain.

Paths below are repository-relative. `P` means `docs/maintenance/issue87-auto-worktree/CODEX-PLAN.md`; `M` means `docs/maintenance/issue87-auto-worktree/`.

### Coverage Summary

| Check | Status | Authority | Evidence | Inspected paths |
|---|---|---|---|---|
| phase_goal | conclusive | CONTEXT.md#Authorized Codex enforcement addition | Startup selection, synchronous guards, installation, actual native evidence and accurate documentation remain assigned to6A–6C. | P; M/CONTEXT.md |
| safety | conclusive | CONTEXT.md:105 | Production policy overrides are prohibited. Read-only, missing, unsupported, differing or ambiguous policy refuses before model startup; prelaunch snapshot drift also refuses. | P:198–248; Task6A |
| requirement_coverage | conclusive | CONTEXT.md:113–118 | ISSUE87 → P6A–6C; CW-01 →6A/6B; CW-02 →6A/6B; CW-03 →6B; CW-04 →6A/6B including corrected policy refusal; CW-05 →6B; CW-06 →6C/coordinator. No uncovered ID. | P; M/CONTEXT.md |
| task_completeness | conclusive | TEMPLATE-CONTRACT.md#Author an executable plan | Changed behavior/action/acceptance/failure criteria carry the correction. All three tasks retain required fields and runnable checks. | P Tasks6A–6C |
| ownership | conclusive | RULES.md#Orchestration and handoffs | No owned path, worker or summary assignment changed. Policy logic/tests stay with A; generated-entry tests with B; documentation with C. | P ownership table; tasks |
| dependency_graph | conclusive | RULES.md#Orchestration and handoffs | A → B → C remains explicit. B tests consume A’s corrected preflight; C consumes integrated behavior/evidence. | P ownership table; preconditions/done criteria |
| temporal_coupling | conclusive | phase-checker.md#Dimension3b | No new shared mutable resource or concurrent writer. Additional configuration reads occur within A’s existing bounded preflight. | P:207–248; ownership table |
| key_links | conclusive | TEMPLATE-CONTRACT.md#Scheduling | Caller/destination `config/read` joins the existing hook preflight; A’s refusal contract reaches B’s installed entry and C’s instructions. Existing launcher/guard/workflow links remain intact. | P:198–248; Tasks6A–6C |
| context_decisions/deferred_scope | conclusive | CONTEXT.md#Authorized Codex enforcement addition | Sandbox/approval preservation now matches the locked decision. Startup/controller distinction, original AW obligations, PR99 exclusion and draft-only publication remain unchanged. | P; M/CONTEXT.md; M/PLAN.md |
| must_haves_derivation | conclusive | phase-checker.md#Dimension6 | Added observable truth requires policy preservation/refusal and maps to A/B regressions and C documentation. Existing six truths remain covered. | P frontmatter; policy correction |
| runtime_source_contract | conclusive | Existing session/classification contracts | Correction changes neither session APIs nor structured-target classification. No production source changed. | .ai/runtime/lib/worktrees.py; .ai/runtime/lib/prewrite.py |
| installer_source_contract | conclusive | Existing payload/registration/merge contracts | Ownership and registration design are unchanged; B now explicitly tests generated-launcher policy refusal and unchanged configuration/argv. | P Task6B; .ai/install.py; tests/test_install.py |
| native_source_contract | conclusive | Saved installed native schemas | `ClientRequest` includes `config/read`. Params support `cwd` and `includeLayers`; response requires `config`/`origins`. Referenced sandbox, approval, granular-policy and reviewer fields exist with the stated shapes. No invented effective-policy field is required. | Capability schemas listed below; P:207–237 |
| verification_frontier | conclusive | TEMPLATE-CONTRACT.md#Stated failing direction | Installed-primary-shell behavioral RED, identical retained GREEN, and actual generated-native shell **and** patch denial remain mandatory. Policy negatives require zero model-launch calls; positive checks require no policy override. | P Tasks6A/6B; policy correction |
| security_planning | conclusive | phase-preparer.md#Security planning gate | Existing threat register remains; T-AW-03 now includes configuration preservation/refusal preflight. Issue98 reconciliation and unresolved outcome status remain honest. | P threat_model |
| scope_sanity | conclusive | phase-checker.md#Dimension5 | No additional component, owned path, command or external dependency. Existing bounded assignments remain appropriate. | P; M/CODEX-PREPARER-SUMMARY.md |
| architectural_tier_map | not_applicable | phase-checker.md#Dimension7c | No responsibility-map artifact exists; correction remains in the assigned runtime tier. | M/CODEX-RESEARCH.md; P |
| detailed_nyquist | not_applicable | methods/nyquist-compliance.md | No Validation Architecture or assigned VALIDATION artifact. Required command/failure checks were reviewed directly. | P; M/CODEX-RESEARCH.md |
| pattern/research_resolution | conclusive | phase-checker.md#Dimensions11–12 | Saved schema supports the correction. Missing/ambiguous returned policy causes refusal rather than guessed defaults. No new unresolved design dependency. | P; preparer summary; native schemas |

### Plan Summary

| PLAN path | Tasks | Files | Declared wave | Dependencies | Status |
|---|---:|---:|---|---|---|
| docs/maintenance/issue87-auto-worktree/CODEX-PLAN.md | 3 | 20 | 1 | Explicit component order A → B → C | Approved |

### Handoff Evidence

- input_revision: `1ead8809a4df9047316ad80698520f4511687a5c` — unchanged recorded preparation input.
- correction_input_revision: `7fb5c858dfb98db2e1cf560b37805a57a4e1aab2` — correction commit’s parent.
- correction_commit: `12a9615a966eaea567ca823862be18ec03d5da34`
- reviewed_revision: `f422cf68b29e43c75500a3e5b39ec157c7f329ca`
- prior_review_revision: `d48c5310e988b1c6e1558c343853807230f44164`
- Checkout remained clean. Only the plan, preparer summary and saved initial review differ from the prior reviewed revision.

Native schema evidence was read from the assigned capability directory: `schemas/ClientRequest.json`, `schemas/v2/ConfigReadParams.json`, and `schemas/v2/ConfigReadResponse.json`, including `Config`, `SandboxMode`, `SandboxWorkspaceWrite`, `AskForApproval` and `ApprovalsReviewer`.

| Reused conclusive checks | Prior review revision | Compared paths | Conclusion |
|---|---|---|---|
| Governing scope, original AW preservation | d48c5310e988b1c6e1558c343853807230f44164 | M/CONTEXT.md; M/CODEX-RESEARCH.md; M/PLAN.md; AGENTS.md; .ai/RULES.md | Unchanged; prior conclusions retained. |
| Runtime/installer contracts | d48c5310e988b1c6e1558c343853807230f44164 | .ai/runtime/lib/worktrees.py; .ai/runtime/lib/prewrite.py; .ai/install.py; tests/ | No source/test differences; prior contract evidence retained. |
| Ownership, dependencies, frontier and existing key links | d48c5310e988b1c6e1558c343853807230f44164 | P; M/CODEX-PREPARER-SUMMARY.md | Scoped differences contain policy correction only; affected producer/consumer assertions were freshly assessed. |

The stable finding’s required property is satisfied by the revised executable plan. This approves readiness, not implemented behavior: policy regressions, actual generated-native receipts and original AW live evidence still require execution and independent verification.

Read-only review completed without edits, tests, probes, application execution, installation or provider writes.
