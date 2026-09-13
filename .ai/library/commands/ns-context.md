---
name: workflow-context
description: "codebase intel | map graphify docs learnings mempalace"
argument-hint: ""
allowed-tools:
  - Read
  - Skill
requires: [map-codebase, graphify, docs-update, extract-learnings, mempalace-recall, mempalace-capture]
---

Route to the appropriate codebase-intelligence skill based on the user's intent.
`workflow-scan` and `workflow-intel` were folded into `workflow-map-codebase` flags by #2790.

| User wants | Invoke |
|---|---|
| Map the full codebase structure | workflow-map-codebase |
| Quick lightweight codebase scan | workflow-map-codebase --fast |
| Query mapped intelligence files | workflow-map-codebase --query |
| Generate a knowledge graph | workflow-graphify |
| Update project documentation | workflow-docs-update |
| Extract learnings from a completed phase | workflow-extract-learnings |
| Recall prior decisions and patterns before planning | workflow-mempalace-recall |
| File a phase artifact into MemPalace | workflow-mempalace-capture |

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
