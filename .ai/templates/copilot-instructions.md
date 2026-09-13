# Instructions for Workflow

- When the user asks for Workflow or uses a `workflow-*` command, read `.ai/library/README.md` and `.ai/references/template-adaptation.md` to resolve the requested capability to its local procedure or retained upstream definition.
- Treat `/workflow-...` or `workflow-...` as requests for the matching capability. Definitions live in `.ai/library/commands/`; use the active `.ai/commands/` mapping when available. An imported definition does not register a slash command or install its runtime.
- When authorized orchestration calls for a subagent, use the local `.ai/agents/` responsibility and assigned worktree contract; `.ai/library/agents/` retains the full upstream specialist guidance. The coordinator starts workers; workers do not dispatch other workers.
- Do not apply Workflow workflows unless the user explicitly asks for them.
- After completing any `workflow-*` command (or any deliverable it triggers: feature, bug fix, tests, docs, etc.), continue the next steps already authorized by the user. Ask only when a missing decision or genuinely new authorization blocks dependent work; do not repeatedly request permission for approved scope.


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
