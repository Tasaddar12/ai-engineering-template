# Verify Command Grounding

> Reference file for phase-preparer agent. Loaded on-demand via `@` reference.

**Inherit the command that already worked.** Read prior verified commands from relevant committed SUMMARY evidence, or from
`prior_verify_commands` when the coordinator supplied it. Do not assume automatic injection. When this phase's build
or test story is the same one a prior phase already proved, **reuse that command verbatim**
rather than re-deriving a path. Re-invention is what produced `cd ../../frontend && npm run
lint` against a directory that holds no `package.json`, and cost two revision cycles.

Ground every path you do author: a command's `cd` target or `npm --prefix` target must be a
directory that exists (or that an earlier task in this phase creates) and, for an npm/make
command, must hold the matching `package.json`/`Makefile`. `npm --prefix <dir> run <script>` is
preferred over `cd <dir> && npm run <script>` — it does not depend on the executor's cwd. If
no prior verified command is available and you cannot ground a path, say so in the plan instead of
guessing one.
