---
name: workflow-project
description: "project lifecycle | milestones audits summary"
argument-hint: ""
allowed-tools:
  - Read
  - Skill
requires: [new-project, onboard, new-milestone, complete-milestone, audit-milestone, milestone-summary, import, ingest-docs, profile-user, review-backlog]
---

Route to the appropriate project / milestone skill based on the user's intent.
`workflow-plan-milestone-gaps` was deleted by #2790 — gap planning now happens
inline as part of `workflow-audit-milestone`'s output.

| User wants | Invoke |
|---|---|
| Start a new project | workflow-new-project |
| Onboard an existing codebase | workflow-onboard |
| Create a new milestone | workflow-new-milestone |
| Complete the current milestone | workflow-complete-milestone |
| Audit a milestone for issues | workflow-audit-milestone |
| Summarize milestone status | workflow-milestone-summary |
| Import an external plan | workflow-import |
| Bootstrap planning from existing docs | workflow-ingest-docs |
| Generate a developer profile | workflow-profile-user |
| Review and promote backlog items | workflow-review-backlog |

Invoke the matched skill directly using the Skill tool.


<!-- LOCAL-ADOPTION:START -->
## Local adoption — read before using this source

This complete authoring guide retains its source content, examples, and methods.
Only recorded namespace/reference substitutions and explicit local conflict
corrections have been made. Source attribution and exact original hashes are
isolated in `.ai/library/THIRD-PARTY-NOTICES.md` and `PROVENANCE.json`.

Read `.ai/library/README.md` for the local producer/consumer mapping and execution
boundary, `.ai/references/template-adaptation.md` for local conflict decisions,
and `.ai/runtime/TEMPLATE-CONTRACT.md` for additive local artifact
fields. Project records live in `.planning/`; reusable guidance lives in `.ai/`.
The active lifecycle uses `.ai/commands/` and `.ai/runtime/phase.py` with
`.planning/config.yaml`. The retained `config.json`, `/workflow:*` commands, tool
names, hooks, and Node CLI examples describe supporting source capabilities;
this import does not install or activate them. Source catalog pointers in examples
identify provenance, not executable command arguments. Retained specialty workflows are full source
guidance for explicit future integration, not promises of installed features.
Local rules, assigned worktrees, recorded authorization, runtime ownership and
verification safeguards govern execution. The local runtime never merges.
<!-- LOCAL-ADOPTION:END -->
