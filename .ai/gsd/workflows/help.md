@.ai/gsd/references/response-language-directive.md

<purpose>
Display GSD command help at the tier the user asked for. Output ONLY the reference content of the chosen mode. Do NOT add project-specific analysis, git status, next-step suggestions, or any commentary beyond the reference.
</purpose>

<progressive_disclosure>
**Mode files are lazy-loaded.** Read only the one mode file that matches `$ARGUMENTS`, then output its `<reference>` body verbatim.

| When `$ARGUMENTS` is | Read |
|---|---|
| `--brief` (or `-b`) alone | `.ai/gsd/workflows/help/modes/brief.md` |
| `--full` (or `-f`, `--all`) alone | `.ai/gsd/workflows/help/modes/full.md` (or its `.ai/gsd/workflows/help/modes/full.compact.md` variant per `.ai/gsd/references/compact-content-gate.md` §"Streams 1b and 4 — variant resolution") |
| empty / unset | `.ai/gsd/workflows/help/modes/default.md` |
| `--brief <topic>` (or `-b <topic>`) | `.ai/gsd/workflows/help/modes/topic.md` in compact scope (signature + one-line summary of the matched section) |
| anything else — bare topic, `--full <topic>`, or topic with leading `--` | `.ai/gsd/workflows/help/modes/topic.md` in full scope (entire matched section) |

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
