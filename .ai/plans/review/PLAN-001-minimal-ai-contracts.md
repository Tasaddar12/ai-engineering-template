---
id: PLAN-001
title: Minimal AI contracts
status: review
review_type: result
intake: INTAKE-001
fixes: []
specs: [SPEC-001]
features: [F01, F02, F03, F04, F05]
tasks: [T01, T02, T03, T04, T05, T06, T07, T08, T09, T10, T11]
draft_revision: 3
related_intake: [INTAKE-002]
approval: explicit_user_instructions_for_initial_scaffold_and_local_draft_refinements
---
# Minimal AI contracts

## Outcome and scope

Draft the exact requested `.ai` tree and a minimal set of contracts in the assigned
`ai-contract-scaffold` worktree. F01 is the record structure and ownership model;
F02 is the initial agent/workflow draft. F03 adds workflow and research ownership;
F04 adds firm policies and PASS/FAIL gates. F05 adds confirmed-defect tracking,
e2e/decoupler roles and plan status/verification. Feature and task IDs are local to this plan.

The authorized action includes replacing this worktree's project contents, drafting
files, making a descriptive commit and pushing `codex/ai-contract-scaffold` to the
existing GitHub repository. It excludes changing the original checkout, creating a
PR, merging, installing dependencies and implementing an application or automation.

The user subsequently requested workflows/research, policies/gates, eight agent roles,
named workflows and consolidation of project context under state,
recorded in [INTAKE-002](../intake/INTAKE-002-expand-operating-documents.md). This
refinement was drafted locally for review. The user has now explicitly authorized
committing and pushing it to the same branch. It adds no executable behavior;
no accepted baseline contract is being amended because the scaffold remains a draft.

## Tasks and acceptance

- [x] T01 (F01): Create the isolated worktree and replace only its project contents;
  retain its `.git` administrative link.
- [x] T02 (F01): Add the requested structure, RULES, truth-map, config, STATE, project
  context, a current SPEC, a draft ADR, an intake report and an append-only journal.
- [x] T03 (F02): Add flat templates, orchestrator/implementor/reviewer definitions and
  basic workflows. Label hooks as manual checkpoints; T08 expands the initial roles.
- [x] T04 (F01, F02): Check directory coverage, links, record names and the final diff;
  commit and push the branch, verify the remote tip, then stop for review.

- [x] T05 (F03): Add workflows/research, make commands thin entry points, and draft
  research/review procedures and templates without inventing research results.
- [x] T06 (F04): Add firm policies, PASS/FAIL gates and gate templates; connect workflow
  checkpoints and fact owners with links.
- [x] T08 (F02, F03): Draft all eight requested roles and named workflows, add bounded
  parallel assignments, and replace intent with state/PROJECT.md beside STATE.md.
- [x] T07 (F03, F04): Check draft links, record/template structure and whitespace;
  present the refinements for user review.

- [x] T09 (F05): Add fixes/open and fixes/done, a flat FIX template, lifecycle and
  evidence-based intake distinction; connect bounded repairs to existing workflows.
- [x] T10 (F05): Add e2e and decoupler roles plus plan-status and plan-verify commands,
  workflows and compact reports. Link pre-merge verification to the delivery gate.
- [x] T11 (F05): Validate the final draft and prepare descriptive commit/push delivery
  under the publication gates below. Git owns the subsequent commit and remote-tip
  observations; user contract acceptance and merge stay pending.

## Risks and dependencies

The branch intentionally removes the former application and all of its tracked
project records. The worktree is isolated; the original main checkout is unchanged.
Draft rules are proposals for review and have no executable enforcement. GitHub
access is needed only for the authorized push. No new tool installation is required.

## Validation at the end

Run read-only documentation checks for required folders, internal links, IDs and
unresolved draft placeholders outside templates. Run `git diff --check` on the staged
change. Compare the remote branch tip with the committed local head after pushing.
No application test suite exists or is claimed to pass. The documentation and staged whitespace checks passed, and the first remote draft
tip matched its local commit. The journal records that observation; this final
review-state update was pushed and its remote tip verified in the initial pass.

For draft revision 2, inspect Markdown links, configured paths, record/template
headings and whitespace only. No application tests or gate automation are included.
Commit and push were separately authorized after the documentation refinement.

Documentation checks passed for 82 files, the exact eight requested agents, named
workflows, configured paths, internal links, record IDs, required template headings
and whitespace. Git whitespace inspection also passed. Formal user review remains
pending; no product tests or agent processes were run.

Draft revision 3 follows the user's explicit instruction to add confirmed-defect
tracking, e2e/decoupler roles and both plan commands, and to commit and push everything.
Documentation checks passed across 94 files and all ten agents: configured paths,
internal links, IDs/frontmatter, template sections, command/workflow/report references,
whitespace and append-only journal preservation. The Git whitespace check passed.
The final staged version is checked again before commit. No product tests or agents
were run; independent contract acceptance remains pending.

## Decision and delivery

Authority: the user's explicit numbered instruction to create this worktree, clear
its contents, draft the requested structure and push it without merging. This is
approval for that action only; it is not blanket authority for future work.

The draft remains in review after a push. The next user decision is whether to accept,
reject or alter the proposed contracts. Merge remains excluded until separately
requested. This plan's push observation belongs in the journal; live next actions
belong in STATE.

## Draft publication gates

Subject: PLAN-001, draft revision 2; evaluator: orchestrator.

- Action-approved: PASS. The user's explicit instruction is “Commit and push...” for
  the existing draft on codex/ai-contract-scaffold. PR creation and merge are excluded.
- Delivery-ready for commit: PASS. The changes match the requested document scope and
  SPEC-001; documentation checks are recorded above. The intended message is
  “Expand PLAN-001 agents, workflows, policies and gates”. Draft acceptance remains
  pending under the documentation-publication provision of the delivery gate.
- Delivery-ready for push: evaluate the resulting commit and clean worktree before
  the write; verify the remote tip after it. Git owns the final revision identity.

## Draft revision 3 publication gates

Gate: [action-approved](../../gates/action-approved.md)

Subject and revision: PLAN-001 draft revision 3, pending diff on codex/ai-contract-scaffold.

Evaluator and time: orchestrator, 2026-09-09 15:24:24 -0400.

| Criterion | Met / unmet / not applicable | Evidence or reason |
| --- | --- | --- |
| Exact action, scope and destination | Met | The user requested fixes/open and fixes/done, e2e/decoupler roles, plan-status/plan-verify, and explicitly said to commit and push everything in this worktree. |
| Excluded actions and current authority | Met | Same assigned branch; PR creation and merge remain excluded. |
| Accepted obligation amendment | Not applicable | Explicit refinement of an unaccepted documentation draft. |

Result: PASS.

Next action: orchestrator coordinates the authorized documentation publication.

Gate: [delivery-ready](../../gates/delivery-ready.md)

Subject and revision: the same draft diff, then its resulting clean commit for push.

Evaluator and time: orchestrator, 2026-09-09 15:24:24 -0400.

| Criterion | Met / unmet / not applicable | Evidence or reason |
| --- | --- | --- |
| Action approval and destination | Met | Action-approved above; origin, codex/ai-contract-scaffold. |
| Scope and specification owners | Met | T09-T11 and updated SPEC-001 describe the actual document additions. |
| Draft review and validation | Met | Documentation checks recorded above; publication is explicitly for user review under the draft provision. |
| Descriptive commit message | Met | Add PLAN-001 defect tracking and plan verification contracts. |
| Commit subject | Met | All scoped draft changes are the intended diff; inspect the staged version before commit. |
| Merge-only verification and hosting checks | Not applicable | Push-only draft; no merge authority. |

Result for draft commit: PASS, subject to the final staged whitespace check.

Next action: commit, then evaluate push against the actual clean commit and approved
branch before writing. Verify its remote tip afterward. Git owns those observed
revision facts; the draft remains in review.
