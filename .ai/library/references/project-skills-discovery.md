# Project Skills Discovery

Before execution, check for project-defined skills and apply their rules.

**Discovery steps (shared across all Workflow agents):**
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
