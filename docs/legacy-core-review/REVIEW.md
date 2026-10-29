# Legacy core review

Reviewed source: 7723b2d1ce2b0d698613639547c35e2b98688a70 (PR 129).

Status: all source reads complete; retirement implementation and final verification pending.

Every one of the 434 tracked files under agents/, commands/, skills/ and engineer/ was read in full, including empty placeholders, fixtures, nested workflow steps and the 8,367-line capability registry. Command and skill copies were inspected independently. The machine-readable coverage ledger records each reviewed file and its original digest; a keep disposition concerns retirement scope, not certification of unrelated deferred migrations.

## Findings to retire

| Family | Evidence at reviewed revision | Retirement authority |
|---|---|---|
| Debug session manager and fixer-owned checkout lifecycle | agents/debug-session-manager.md; agents/code-fixer.md:216; engineer/workflows/debug.md:233 | Section 10; R-AG-326/331; C-05 |
| Research provider/cache/confidence seam | agents/phase-researcher.md:95; engineer/bin/lib/research.py:12 | V-22/74/75/113 |
| MemPalace integrations | agents/debugger.md:591; engineer/references/debugger-semantic-recall.md:15 | R-AG-227/230/233; R-RF-23 |
| Broken-windows ledger | agents/executor.md:674; engineer/bin/lib/quality.py:15; ship/progress consumers | R-AG-041; V-143/144/145 |
| Smart-zone/calibrated estimator | agents/plan-checker.md:305; engineer/bin/lib/planning.py:211 | V-30; R-AG-120/134 |
| Dynamic capability/loop dispatch, predicates and hook contracts | engineer/bin/lib/capabilities.py:9; capability_registry.py:34; workflow_ops.py:225; workflow hook consumers | V-01/03/13/19 |
| External reviewer lanes and convergence | commands/code-review.md:34; engineer/workflows/code-review.md:650; review_execution.py:121; review_lane_descriptor.py:120 | V-136/137/138/139; C-18/21/28 |
| Developer profiles and registry-only naming policy | profile_output.py:66; runtime_name_policy.py:139 | Section 10 profiling removals; V-13 |
| Workstream plumbing and output overflow protocol | workflow ENGINEER_WS/--ws surfaces; io_output.py:348 | V-148/149 |
| Background PID worker lane and isolation opt-outs | engineer/workflows/execute-phase/steps/executor-isolation-dispatch.md:101; worktrees.py:331 | C-05/35; V-29/114/119/120/121 |
| Intel, global learning copy, teams and roadmap annotation | engineer/workflows/plan-phase.md:686; execute-phase.md:1336; workflow_ops.py:415; planning.py:120 | V-12/52/53/82/98; C-11 |
| Context drift and custom-file detector | engineer/workflows/plan-phase.md:289; codebase.py:186; installation.py:83 | V-08/27/142; C-38 |
| Package/test inference and custom PR section configuration | runtime_tools.py:117; workflow audit/post-merge gates; ship.pr_body_sections | V-57/79; C-12/14/15/16 |
| Legacy STATE Quick Tasks table | quick_batch.py:399; planning.py:133; markdown_table.py:413 | V-134/135 |
| Deleted discussion overlays, compact/chunked/ADR/review/bounce detours | commands/discuss-phase.md:99; plan-phase.md:219; next.md:312; new-project.md:557 | Section 10; R-WF-219; C-28; human PR 164 removals |
| Obsolete shared bootstrap/continuation/model/phase/template helpers | engineer/references/ and engineer/templates/ consumers identified by full review | Section 10; R-AG-008/011; R-TP-44/53 |
| Retired AI-integration repair and validation contracts | health_diagnostic_rules.py:653; workflow_size_budget.py:212 | R-WF-181/254/259/275; Section 8 |

## Decisions and limits

Section 10 lists original upstream variants, while later rows replace some paths with local methods. A listed path alone is not proof the current file must disappear. Preserve valid replacements and later manager/pipeline additions. General semantic migrations in checkpoints, verification overrides, templates and installer wiring remain outside this retirement-only change. Three shared references have conflicting keep/delete rows; six Batch B references lack replacement prerequisites, so they stay.

Initial static checks at this source revision: scripts/links.py reported 407 broken targets; scripts/verbs.py reported 337 registered verbs, 561 call sites and 6 unknown call sites. The link checker also flags intentionally retained host-qualified imports. These are baseline observations, not passing final verification.

## Coverage by reader

- A-entrypoints: 107 files, 16855 lines.
- C-references-templates-entrypoint: 132 files, 18191 lines.
- coordinator-core: 16 files, 2134 lines.
- E-support: 53 files, 16325 lines.
- D-runtime: 16 files, 5573 lines.
- F-registry-profile: 2 files, 10134 lines.
- B-workflows: 108 files, 30272 lines.

Total: 434 files, 99484 lines. See coverage.json for the exhaustive per-file ledger.
