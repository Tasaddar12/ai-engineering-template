# Response-Language Directive (#2529)

**If `response_language` is set** (in the init JSON this workflow parses, or in `.planning/config.json`): ALL user-facing output of this workflow MUST be in that language — narration between tool calls, status updates, progress notes, findings, banners, report prose, questions (AskUserQuestion or plain text), and summaries. Technical terms, code, file paths, commands, and identifiers stay in English.

Literal English report/banner templates embedded in a workflow are a structural SOURCE, not literal output to copy verbatim — render their prose translated into `{response_language}` while keeping headings' structural markers, table columns, IDs, commands, and file paths unchanged. Exception: blocks a workflow explicitly requires to be emitted byte-for-byte (e.g. pre-rendered checkpoints) are output exactly as rendered.

Pass `response_language: {value}` into every spawned subagent prompt so any user-facing output they produce stays in the configured language.

Workflows take this contract in one of three forms (REQ-LANG-03): an `@`-reference to this file; their own inline directive naming the same narration class; or, for a fragment loaded by a covered parent, inheritance from that parent. Coverage is enforced by `scripts/lint-response-language-coverage.cjs` — a new workflow cannot ship without one of the three, and the lint checks this file's own wording too, so a weakened directive here uncovers every workflow that imports it rather than passing silently. Workflow-specific directives (e.g. `execute-phase-response-language.md`) take precedence where present.


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
