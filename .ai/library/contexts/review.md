# Review Context Profile

Agent output guidance for review mode. Loaded when `context: review` is set in config.json.

## Output Style

- Critical, detail-focused responses that prioritize correctness
- Organize findings by severity: blocking, important, nit
- Reference specific lines and files for every finding
- State what is correct as well as what needs change — confirm the good parts

## Focus Areas

- Correctness — logic errors, off-by-ones, missing edge cases
- Security — input validation, injection vectors, secret exposure
- Performance — unnecessary allocations, O(n^2) patterns, missing caching
- Style and consistency — naming, formatting, import order
- Test coverage — untested branches, missing assertions, flaky patterns
- Structural Findings (fallow) — machine-derived cross-module facts injected as `<structural_findings>{ findings: [...], summary: { total, unusedExports, duplicates, circularDependencies } }</structural_findings>`. Render in REVIEW.md under `## Structural Findings (fallow)` as a separate section from narrative findings. Treat as ground truth for cross-module facts; do not re-derive.

## Verbosity

Medium. Be thorough on findings but terse in explanation. Each issue should be one to three sentences: what is wrong, why it matters, and how to fix it.


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
