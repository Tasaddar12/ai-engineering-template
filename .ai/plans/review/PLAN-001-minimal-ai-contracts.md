---
id: PLAN-001
title: Minimal AI contracts
status: review
review_type: result
intake: INTAKE-001
specs: [SPEC-001]
features: [F01, F02]
tasks: [T01, T02, T03, T04]
approval: explicit_user_instruction_for_scaffold_and_push_only
---
# Minimal AI contracts

## Outcome and scope

Draft the exact requested `.ai` tree and a minimal set of contracts in the assigned
`ai-contract-scaffold` worktree. F01 is the record structure and ownership model;
F02 is the initial agent/workflow draft. Feature and task IDs are local to this plan.

The authorized action includes replacing this worktree's project contents, drafting
files, making a descriptive commit and pushing `codex/ai-contract-scaffold` to the
existing GitHub repository. It excludes changing the original checkout, creating a
PR, merging, installing dependencies and implementing an application or automation.

## Tasks and acceptance

- [x] T01 (F01): Create the isolated worktree and replace only its project contents;
  retain its `.git` administrative link.
- [x] T02 (F01): Add all requested directories, RULES, truth-map, config, STATE, an intent
  record, a current SPEC, a draft ADR, an intake report and an append-only journal.
- [x] T03 (F02): Add flat templates, coordinator/implementer/reviewer definitions and
  short report/plan/execute/deliver workflows. Label hooks as manual checkpoints.
- [x] T04 (F01, F02): Check directory coverage, links, record names and the final diff;
  commit and push the branch, verify the remote tip, then stop for review.

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
review-state update will be pushed and its remote tip checked again.

## Decision and delivery

Authority: the user's explicit numbered instruction to create this worktree, clear
its contents, draft the requested structure and push it without merging. This is
approval for that action only; it is not blanket authority for future work.

The draft remains in review after a push. The next user decision is whether to accept,
reject or alter the proposed contracts. Merge remains excluded until separately
requested. This plan's push observation belongs in the journal; live next actions
belong in STATE.
