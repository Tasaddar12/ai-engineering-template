0. **Context exhaustion guard — `context_guard` (BEFORE spawning, #1452):**

   Before spawning any agents for this wave, self-assess context pressure using the
   degradation signals in `.ai/library/references/context-budget.md`. Signs of POOR tier (70%+):
   increasing vagueness, skipped steps, silent partial completion.

   Read `workflow.context_guard_mode` from `.planning/config.json` (default `warn`).

   | Tier | `warn` (default) | `auto` | `off` |
   |------|-----------------|--------|-------|
   | PEAK / GOOD | No output | No output | No output |
   | DEGRADING (50-70%) | Emit: "⚠ Context pressure DEGRADING — switching to frontmatter-only reads for remaining waves." Continue. | Same as warn | Skip |
   | POOR (70%+) | Emit: "🛑 Context pressure POOR — risk of context exhaustion. Run `/workflow:pause-work` to checkpoint before this wave, then resume in a fresh session." Continue (user decides). | Invoke `/workflow:pause-work` immediately and halt. Do NOT spawn wave agents. | Skip |

   The guard is heuristic — no programmatic context-percentage API exists. Use your
   assessment of degradation signals, not a fixed token count.


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
