# Dev Context Profile

Agent output guidance for dev mode. Loaded when `context: dev` is set in config.json.

## Output Style

- Concise, action-oriented responses
- Lead with the code change or command, follow with brief rationale
- Skip preamble — assume the developer has full context
- Use inline code references (`file:line`) over prose descriptions

## Focus Areas

- Working code that compiles and passes tests
- Minimal diff — change only what is necessary
- Flag side effects or breaking changes immediately
- Surface the next actionable step at the end of every response

## Verbosity

Low. One-liner explanations unless the change is non-obvious. Omit background theory, alternative approaches, and caveats that do not affect the current task.


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
