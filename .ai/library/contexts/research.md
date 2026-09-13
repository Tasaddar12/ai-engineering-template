# Research Context Profile

Agent output guidance for research mode. Loaded when `context: research` is set in config.json.

## Output Style

- Verbose, exploratory responses that surface trade-offs and alternatives
- Present multiple approaches with pros and cons before recommending one
- Include links, references, and citations where available
- Use structured headings and bullet lists for scan-ability

## Focus Areas

- Breadth of options — enumerate before narrowing
- Prior art and ecosystem conventions
- Risks, edge cases, and failure modes
- Dependencies and compatibility implications
- Long-term maintainability of each approach

## Verbosity

High. Explain reasoning, show evidence, and document assumptions. Include background context even if the developer likely knows it — research artifacts are read by future contributors who may not.


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
