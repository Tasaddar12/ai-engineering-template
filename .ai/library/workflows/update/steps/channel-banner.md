**Only when `TAG=next`** (the user passed `--next`/`--rc`), prepend a channel banner so they know they are leaving the stable line — add this line immediately after the `**Latest:**` line in whichever output block renders:

**Channel:** {CHANNEL_LABEL}

On the default stable channel (`TAG=latest`), do NOT add a channel line — the output must match the prior stable behavior exactly.

When `TAG=next`, the "latest" value is the release candidate published under `@next` (e.g. `1.4.0-rc.1`). Apply standard semver precedence for prereleases (`1.4.0-rc.1` is newer than `1.3.1` but older than the final `1.4.0`). Do NOT treat an `-rc.N` suffix as a dev install or as "behind" — offer it as an available update.


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
