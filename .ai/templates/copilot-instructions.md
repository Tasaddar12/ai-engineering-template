# Instructions for GSD

- When the user asks for GSD or uses a `gsd-*` command, read `.ai/gsd/README.md` and `.ai/references/gsd-adaptation.md` to resolve the requested capability to its local procedure or retained upstream definition.
- Treat `/gsd-...` or `gsd-...` as requests for the matching capability. Definitions live in `.ai/gsd/commands/gsd/`; use the active `.ai/commands/` mapping when available. An imported definition does not register a slash command or install its runtime.
- When authorized orchestration calls for a subagent, use the local `.ai/agents/` responsibility and assigned worktree contract; `.ai/gsd/agents/` retains the full upstream specialist guidance. The coordinator starts workers; workers do not dispatch other workers.
- Do not apply GSD workflows unless the user explicitly asks for them.
- After completing any `gsd-*` command (or any deliverable it triggers: feature, bug fix, tests, docs, etc.), continue the next steps already authorized by the user. Ask only when a missing decision or genuinely new authorization blocks dependent work; do not repeatedly request permission for approved scope.


<!-- LOCAL-ADOPTION:START -->
## Local adoption — read before using this source

The complete upstream body above is retained from GSD-Core at
`c0b2a05d2f310adc0a1f35fd71fbc9f28f4e4977`; only recorded reference substitutions
and explicit local conflict corrections have been made. See
`.ai/gsd/PROVENANCE.json` for exact source hashes and changes.

Read `.ai/gsd/README.md` for the local producer/consumer mapping and execution
boundary, `.ai/references/gsd-adaptation.md` for local conflict decisions,
and `.ai/runtime/TEMPLATE-CONTRACT.md` for additive local artifact
fields. Project records live in `.planning/`; reusable guidance lives in `.ai/`.
The active lifecycle uses `.ai/commands/` and `.ai/runtime/phase.py` with
`.planning/config.yaml`. The upstream `config.json`, `/gsd:*` commands, tool
names, hooks, and Node CLI examples describe GSD's system; this import does not
install or activate that system. Retained specialty workflows are full source
guidance for explicit future integration, not promises of installed features.
Local rules, assigned worktrees, recorded authorization, runtime ownership and
verification safeguards govern execution. The local runtime never merges.
<!-- LOCAL-ADOPTION:END -->
