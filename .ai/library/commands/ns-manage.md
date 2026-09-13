---
name: workflow-manage
description: "config workspace | workstreams thread update ship inbox"
argument-hint: ""
allowed-tools:
  - Read
  - Skill
requires: [config, workspace, workstreams, thread, pause-work, resume-work, update, ship, inbox, pr-branch, undo, cleanup, health, manager, settings, stats, surface, help]
---

Route to the appropriate management skill based on the user's intent.
`workflow-config` (settings + advanced + integrations + profile) and `workflow-workspace`
(new + list + remove) are post-#2790 consolidated entries.

| User wants | Invoke |
|---|---|
| Configure Workflow settings (basic / advanced / integrations / profile) | workflow-config |
| Manage workspaces (create / list / remove) | workflow-workspace |
| Manage parallel workstreams | workflow-workstreams |
| Continue work in a fresh context thread | workflow-thread |
| Pause current work | workflow-pause-work |
| Resume paused work | workflow-resume-work |
| Update the Workflow installation | workflow-update |
| Ship completed work | workflow-ship |
| Process inbox items | workflow-inbox |
| Create a clean PR branch | workflow-pr-branch |
| Undo the last Workflow action | workflow-undo |
| Archive accumulated phase directories | workflow-cleanup |
| Diagnose planning directory health | workflow-health |
| Open the interactive command center | workflow-manager |
| Configure workflow toggles and model profile | workflow-settings |
| Show project statistics | workflow-stats |
| Toggle which skills are surfaced | workflow-surface |
| Show the Workflow command guide | workflow-help |

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
