# Reusable workflow payload

This directory is the copyable product guidance installed into another repository. It contains no development plans, task history, reviews, or decisions from this toolkit's own repository.

| Source | ChatGPT/Codex destination | Claude Code destination |
| --- | --- | --- |
| `docs/agents/` | `.ai/agents/` | `.claude/agents/` |
| `docs/templates/` | `.ai/templates/` | `.claude/templates/` |
| `docs/workflows/` | `.ai/workflows/` | `.claude/workflows/` |
| `docs/defaults/README.md` | `.ai/README.md` | `.claude/README.md` |
| `docs/defaults/INSTRUCTIONS.md` | `.ai/AGENTS.md` | `.claude/CLAUDE.md` |
| `docs/defaults/STATE.json` | `.ai/STATE.json` | `.claude/STATE.json` |
| `docs/defaults/POLICY.json` | `.ai/project/policy.json` | `.claude/project/policy.json` |
| `docs/defaults/DECISIONS.json` | `.ai/decisions/index.json` | `.claude/decisions/index.json` |
| `docs/defaults/requirements.txt` | `.ai/requirements.txt` | `.claude/requirements.txt` |

The installer also copies the helper CLI, validator, and schemas into the selected namespace. It substitutes namespace references while copying and creates only one workflow namespace per installation.
