# Reusable workflow payload

This directory is the copyable product guidance installed into another repository. It contains no development plans, task history, reviews, or decisions from this toolkit's own repository.

| Source | OpenAI Codex destination | Claude Code destination |
| --- | --- | --- |
| `docs/agents/` | `.codex/agents/` | `.claude/agents/` |
| `docs/templates/` | `.codex/templates/` | `.claude/templates/` |
| `docs/workflows/` | `.codex/workflows/` | `.claude/workflows/` |
| `docs/defaults/README.md` | `.codex/README.md` | `.claude/README.md` |
| `docs/defaults/INSTRUCTIONS.md` | `.codex/AGENTS.md` | `.claude/CLAUDE.md` |
| `docs/defaults/STATE.json` | `.codex/STATE.json` | `.claude/STATE.json` |
| `docs/defaults/POLICY.json` | `.codex/project/policy.json` | `.claude/project/policy.json` |
| `docs/defaults/AGENT_MODELS.json` | `.codex/project/agent-models.json` | `.claude/project/agent-models.json` |
| `docs/defaults/DECISIONS.json` | `.codex/decisions/index.json` | `.claude/decisions/index.json` |
| `docs/defaults/requirements.txt` | `.codex/requirements.txt` | `.claude/requirements.txt` |

The installer also copies the helper CLI, validator, and schemas into the selected namespace. It substitutes namespace references while copying and creates only one workflow namespace per installation.

Use `--assistant codex` for OpenAI or `--assistant claude` for Claude. The older `chatgpt` option is an alias for `codex`. The canonical copyable files use `.codex/` paths; Claude installation renders them as `.claude/` paths. Native provider configuration is preserved, while these Markdown role guides remain workflow documentation rather than registered native subagents.
