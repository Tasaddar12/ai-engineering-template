---
tier: plan
authority: agent
id: PLAN-004
title: Reconcile the copied orchestration template
links: [SPEC-002, AMD-002]
owner: coordinator
created: 2026-09-09
---

# PLAN-004: Reconcile the copied orchestration template

> Plan tier. The directory owns this record's stage.

## Goal

Make the repository consistent with the user's copied operating material and
its actual files, then deliver and retire the exact assigned worktree.

## Satisfies

The user's requested folder layout, detailed roles, report-before-action
boundary, current specifications and verified Git delivery. SPEC-002 is created
by this plan; the earlier SPEC-001 is deleted history, not current authority.

## Contract changes

### Specs to create

SPEC-002 — Orchestration template interfaces:
- Given a fresh checkout, following AGENTS.md reaches current project intent,
  state, engagement rules and the indexes for roles and command procedures.
- Given a command or agent reference, its named file exists with matching case;
  templates are flat and refer to the record locations defined by config.
- Given a plan or fix, its directory determines its lifecycle stage; current
  specifications and historical evidence have separate owners in truth-map.
- Given this checkout, orchestration is operated through Markdown instructions;
  optional hook scripts are unregistered and do not provide a sandbox.

### Operating contracts to amend

AMD-002 records the imported paths and runtime claims, duplicate procedure
owners, obsolete scaffold records and the resulting reconciled structure.
Keep the user's detailed command and role prose. Retain the five requested
workflow guides as navigation to the authoritative command steps. Keep useful
specialist roles, policies, gates and reporting templates.

### Decisions

No new architectural decision. This implements the layout and operating
approach the user already chose. Deleted historical identifiers are not reused.

## Approach

Inspect all tracked files from merged PR #5 in a new worktree. Correct copied
references and factual claims, consolidate duplicate procedures, remove unused
scaffold artifacts, and preserve append-only evidence. Validate references,
metadata and the affected hook behavior before a separate review pass.

## Steps

- [x] Create and confirm the isolated worktree and branch from main.
- [x] Reconcile current files, indexes, templates and operational guidance.
- [x] Remove obsolete duplicate scaffolding inside this worktree.
- [x] Validate and review the complete result; resolve substantive findings.
Delivery after verification: commit, push, create and merge the PR; pull main,
compare contents, and remove the branch/worktree. Git and the forge own those
observed results; they are reported by the coordinator at delivery.

## Acceptance

- Case-sensitive local references and active record IDs resolve.
- Every agent has a matching name, description, scope, steps and report format.
- Config paths exist; examples and optional integrations are labeled accurately.
- Git whitespace checks and relevant shell syntax/behavior checks pass.
- Existing journal bytes remain unchanged; removed records remain available in Git.
- GitHub confirms the exact PR merged; main contains the branch and has the same
  tracked tree and file contents before non-forced cleanup.

## Risks and unknowns

- Copied host-specific scripts are optional examples, not installed enforcement.
- Historical journal links refer to earlier revisions; do not rewrite old events
  or recreate removed requirements to make those links look current.
- Main contains untracked leftovers from the old Python framework. They are
  outside this worktree assignment and must remain untouched.

## Notes

Authority: the user requested reconciliation and removal in a new worktree,
then explicitly requested review, PR creation, merge, pulling main, merge
confirmation and deletion of the branch and worktree.

Assigned root: `D:/Codex Projects/ai-engineering-template/.worktrees/ai-contract-reconcile`.
Assigned branch: `codex/reconcile-orchestration-docs`.
Base: `5967dbe4e46416d65c886351d1f5e6ceeedf5bc8` (merged PR #5).

## Verification

**Verdict:** verified for this documentation and hook-example change.

Subject: the complete PLAN-004 diff against `5967dbe`, including deletions.
Environment: Windows, Python 3.13, PyYAML 6.0.2 for temporary validation,
and Git for Windows Bash. PyYAML is a validation aid, not a project dependency.

| SPEC-002 criterion | Evidence | Result |
| --- | --- | --- |
| Entry-point navigation reaches current owners | Exact-case path and Markdown anchor audit from AGENTS through the indexes | PASS |
| Referenced files and flat templates exist | 254 current local links/anchors, concrete template references and configured paths checked | PASS |
| Stages and fact owners are consistent | 95 YAML mappings parsed with duplicate-key rejection; 19 role identities/scopes and 8 live record IDs checked; no PLAN/FIX status field | PASS |
| Instructions and optional hooks are accurately described | Manual dispatch in config; no host registration; both scripts pass Bash syntax and 17 JSON payload cases | PASS |

The hook regression was reproduced against the imported script at the base:
it emitted no intent reminder for the actual `.ai/state/PROJECT.md` path.
The corrected script emits the intent notice for that path, Windows paths,
RULES and the approval policy. Other payload checks covered specs, plans,
fixes, logs, ordinary files, allowed/denied writes and redirects.

`git diff --check` passed. The original journal content remains an unchanged
prefix; historical links resolve in the earlier Git revisions noted below.
Current live records use new IDs after the highest issued IDs in Git history.

## Review

**Verdict:** approved, with no remaining blocking findings in the inspected scope.

**Independence:** separate self-review pass by the implementing coordinator;
no independent agent, cold reviewer or external approval is claimed.

The review covered entry points, config, all role and command interfaces,
retained workflow composition, policy/gate consistency, templates, hooks,
state, specification and the deletion list. It corrected malformed YAML
placeholders; nonexistent paths/roles; contradictory dry-run and ready states;
reused-ID risks; inconsistent done/delivery semantics; and capture commands
that implied repair authority. The complete relevant diff was inspected.

Limits: no live parallel orchestration, host hook installation, sandbox
security validation or application test suite is claimed. Historical journal
links intentionally refer to the revision of their recorded events.

## Delivery

The user authorized commit, push, PR creation and merge, followed by pulling
main and deleting this exact branch/worktree after merge/content confirmation.
Implementation verification is complete. GitHub and Git are the owners of the
pending delivery result; the coordinator reports the observed PR, merge and
cleanup in the final response. No unrelated main-checkout artifacts are in scope.
