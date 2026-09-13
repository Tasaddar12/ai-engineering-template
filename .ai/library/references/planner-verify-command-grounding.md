# Verify Command Grounding (#2401)

> Reference file for planner agent. Loaded on-demand via `@` reference.

**Inherit the command that already worked.** The planning context carries
`prior_verify_commands` — the `<automated>` commands from the most recent prior phase that had
any, surfaced **at every context window**, not only on 1M-class models. When this phase's build
or test story is the same one a prior phase already proved, **reuse that command verbatim**
rather than re-deriving a path. Re-invention is what produced `cd ../../frontend && npm run
lint` against a directory that holds no `package.json`, and cost two revision cycles.

Ground every path you do author: a command's `cd` target or `npm --prefix` target must be a
directory that exists (or that an earlier task in this phase creates) and, for an npm/make
command, must hold the matching `package.json`/`Makefile`. `npm --prefix <dir> run <script>` is
preferred over `cd <dir> && npm run <script>` — it does not depend on the executor's cwd. If
`prior_verify_commands` is empty and you cannot ground a path, say so in the plan instead of
guessing one.


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
