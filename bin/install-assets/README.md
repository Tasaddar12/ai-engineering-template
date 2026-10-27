# Installer assets

Fresh onboarding seeds keep the adopting project identity unfilled. Existing project records always win. Native Codex definitions load the complete installed role method; shared Markdown has no model/effort frontmatter. Claude export defaults are scout/targeted-fixer haiku, executor sonnet, planner opus with medium effort. Only Claude and Codex are supported.

`python bin/generate-assets.py` regenerates each seed from the complete first
Markdown artifact block in the copied `engineer/templates/` source, retaining
every section and field while replacing concrete example requirements with
unfilled placeholders. It also regenerates the complete native Codex role bodies
from `agents/`. `AGENT.md` is shared guidance and `code-fixer.md` is a retained
method source; neither is a separately dispatchable native role.
Claude installs that method under `engineer/references/` so its agent discovery does
not create an extra dispatch name; Codex retains the Markdown method without a
native TOML role.

Native skills export complete command mirrors even when `skills/` is absent or
contains only its placeholder. Installed references use the selected host's
`.claude/` or `.codex/` namespace; Codex skills live under `.agents/skills/`.

`python scripts/generate-command-skills.py` regenerates `skills/<command>/SKILL.md`
as the complete byte-for-byte command source, including YAML frontmatter and
argument handling. `commands/COMMAND.md` is the catalog, not a command, and has
no skill. The placeholder `skills/SKILL/SKILL.md` is removed by generation.
Run both generators after changing their respective canonical sources; the
installer uses the same native role renderer and host path adapter rather than
a second model/effort mapping. Asset generation does not establish verification.
