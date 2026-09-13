# Project Skills Discovery

Before execution, check for project-defined skills and apply their rules.

**Discovery steps (shared across all GSD agents):**
1. Check `.claude/skills/` or `.agents/skills/` directory — if neither exists, skip.
2. List available skills (subdirectories).
3. Read `SKILL.md` for each skill (lightweight index, typically ~130 lines).
4. Load specific `rules/*.md` files only as needed during the current task.
5. Do NOT load full `AGENTS.md` files — they are large (100KB+) and cost significant context.

**Application** — how to apply the loaded rules depends on the calling agent:
- Planners account for project skill patterns and conventions in the plan.
- Executors follow skill rules relevant to the task being implemented.
- Researchers ensure research output accounts for project skill patterns.
- Verifiers apply skill rules when scanning for anti-patterns and verifying quality.
- Debuggers follow skill rules relevant to the bug being investigated and the fix being applied.

The caller's agent file should specify which application applies.


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
