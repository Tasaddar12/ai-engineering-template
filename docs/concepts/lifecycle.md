# Lifecycle and durable knowledge

| Kind | Meaning | Canonical location |
| --- | --- | --- |
| Current | Accepted project reality and active architecture | `.ai/STATE.json`, accepted ADRs and active specs |
| Planned | Approved intent not yet executed | Plan/task records with `draft`, `backlog`, `ready` |
| In progress | An active attempt, not accepted reality | `running` records, worktree registry, runs |
| Completed | All gates satisfied and merge observed | `completed` plan/task records |
| Archived | Historical records retained, excluded from default context | `archived: true`, archive manifest |
| Superseded | Replaced intent, never silently deleted | `superseded` plus successor IDs and reason |

Status is data, not a directory name. IDs have permanent paths; generated views can show ready, blocked or completed work without moving source files. Archived is a retention flag independent of success: a superseded task may be archived but was never completed. Active specs remain active when one implementation plan completes.

A fresh agent reads project state, resolves the current state checkpoint and Git branches, reconciles missing worktrees, then loads only its task/spec/ADR context and accepted dependency handoffs. Research is evidence with provenance and freshness; it cannot override approved requirements. Summaries link back to originals and record content digests.

If only the default branch was cloned, fetch the retained `ai/state` branch before attempting a run resume. Missing local processes become unknown/interrupted, not successful. Missing unpushed commits are reported as unavailable. No framework can reconstruct code that was never persisted or transferred.
