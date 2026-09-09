---
id: PLAN-001
title: Minimal AI contracts
status: review
review_type: result
intake: INTAKE-001
specs: [SPEC-001]
features: [F01, F02, F03, F04]
tasks: [T01, T02, T03, T04, T05, T06, T07, T08]
draft_revision: 2
related_intake: [INTAKE-002]
approval: explicit_user_instructions_for_initial_scaffold_and_local_draft_refinements
---
# Minimal AI contracts

## Outcome and scope

Draft the exact requested `.ai` tree and a minimal set of contracts in the assigned
`ai-contract-scaffold` worktree. F01 is the record structure and ownership model;
F02 is the initial agent/workflow draft. F03 adds workflow and research ownership;
F04 adds firm policies and PASS/FAIL gates. Feature and task IDs are local to this plan.

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
