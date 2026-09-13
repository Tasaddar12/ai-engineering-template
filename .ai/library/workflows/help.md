@.ai/library/references/response-language-directive.md

<purpose>
Display Workflow command help at the tier the user asked for. Output ONLY the reference content of the chosen mode. Do NOT add project-specific analysis, git status, next-step suggestions, or any commentary beyond the reference.
</purpose>

<progressive_disclosure>
**Mode files are lazy-loaded.** Read only the one mode file that matches `$ARGUMENTS`, then output its `<reference>` body verbatim.

| When `$ARGUMENTS` is | Read |
|---|---|
| `--brief` (or `-b`) alone | `.ai/library/workflows/help/modes/brief.md` |
| `--full` (or `-f`, `--all`) alone | `.ai/library/workflows/help/modes/full.md` (or its `.ai/library/workflows/help/modes/full.compact.md` variant per `.ai/library/references/compact-content-gate.md` §"Streams 1b and 4 — variant resolution") |
| empty / unset | `.ai/library/workflows/help/modes/default.md` |
| `--brief <topic>` (or `-b <topic>`) | `.ai/library/workflows/help/modes/topic.md` in compact scope (signature + one-line summary of the matched section) |
| anything else — bare topic, `--full <topic>`, or topic with leading `--` | `.ai/library/workflows/help/modes/topic.md` in full scope (entire matched section) |

Argument parsing rules:
- Trim and lowercase `$ARGUMENTS`.
- Recognize the long form, short form, and obvious aliases listed above.
- A bare token like `debug`, `--debug`, `capture`, `workflow`, `config` is a topic — route to `topic.md`.
- Multiple flags: `--brief` and `--full` are mutually exclusive — if both appear *without* a topic, prefer `--full`.
- `--brief` combined with a topic invokes `topic.md` in compact scope; `--full` combined with a topic invokes `topic.md` in full scope (the default topic behavior). When passing arguments through to `topic.md`, retain the `--brief` flag so the mode can pick the right scope.

After loading the chosen mode, emit its `<reference>` block content directly. No additions, no project context, no suggestions.
</progressive_disclosure>


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
