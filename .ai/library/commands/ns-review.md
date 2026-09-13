---
name: workflow-quality
description: "quality gates | code review debug audit security eval ui"
argument-hint: ""
allowed-tools:
  - Read
  - Skill
requires: [code-review, audit-uat, secure-phase, eval-review, ui-review, validate-phase, debug, forensics, audit-fix, review, ui-phase]
---

Route to the appropriate quality / review skill based on the user's intent.
`workflow-code-review-fix` was absorbed by `workflow-code-review --fix` in #2790.

| User wants | Invoke |
|---|---|
| Review code for quality and correctness | workflow-code-review |
| Auto-fix code review findings | workflow-code-review --fix |
| Audit UAT / acceptance testing | workflow-audit-uat |
| Security review of a phase | workflow-secure-phase |
| Evaluate AI response quality | workflow-eval-review |
| Review UI for design and accessibility | workflow-ui-review |
| Validate phase outputs | workflow-validate-phase |
| Debug a failing feature or error | workflow-debug |
| Forensic investigation of a broken system | workflow-forensics |
| Autonomous audit-to-fix pipeline | workflow-audit-fix |
| Cross-AI peer review of plans | workflow-review |
| Generate a UI design contract | workflow-ui-phase |

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
