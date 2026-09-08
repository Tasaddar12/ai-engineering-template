# AI Engineering Toolkit

This repository builds a reusable local toolkit for keeping AI-assisted engineering focused, traceable, and easier to resume. It installs compact workflow guidance, isolated work records, local validation contracts, and provider entry files into any folder without copying this repository’s own development history.

The working bootstrap supports Python 3.11+ on Windows and Linux. It uses only the standard library and does not require provider credentials or network access. Record validation additionally requires `jsonschema`; install it in the target environment with `python -m pip install -r PATH/.codex/requirements.txt` after setup.

```text
python src/install.py PATH --assistant claude
python src/install.py PATH --assistant codex
```

Choose one provider mode. OpenAI Codex receives a self-contained `.codex/` workflow namespace; Claude Code receives a self-contained `.claude/` namespace. `--assistant chatgpt` remains an alias for `codex`. The copyable source material is visible under `docs/agents/`, `docs/templates/`, and `docs/workflows/`.

Use `--dry-run` to inspect every intended file and directory without creating the destination. Existing project files are preserved. A repeated installation is idempotent, and conflicting framework-owned files cause a clear failure instead of being overwritten.

Existing native provider settings, including `.codex/config.toml` and native agent configuration files, are preserved. Native settings for another provider can coexist, but each project has one toolkit record namespace. Existing managed `.ai/` installations remain readable by the record tools; installing over or alongside them requires a separate migration and is refused by this installer.

The installed folder contains its own record and validation tools:

```text
python PATH/.codex/tools/ai.py --project PATH plan create PLAN-100 --title "Improve reliability"
python PATH/.codex/tools/ai.py --project PATH task create PLAN-100 TASK-002 --title "Add checks" --objective "Add focused reliability checks" --depends-on TASK-001
python PATH/.codex/tools/ai.py --project PATH plan list
python PATH/.codex/tools/validate_foundation.py --project PATH
```

For Codex or ChatGPT, start the session with “Read `.codex/AGENTS.md` before working.” The hidden file is deliberately kept out of the project root, so Codex does not discover it automatically from a root launch. Claude Code uses the installed `.claude/CLAUDE.md`; its `agents/` Markdown files are selected workflow guides rather than native subagent definitions. Ordinary ChatGPT chats need the relevant files attached or read explicitly.

The current release provides safe installation, focused guidance, plan/task record creation, and deterministic validation. Automatic agent execution, independent review invocation, recovery, remote delivery, and lifecycle completion are not implemented.

Each installation includes editable [model defaults for all 22 agent roles](docs/workflows/MODELS.md), with separate OpenAI and Anthropic profiles. Planning and review use higher-capability models; research and routine development use lower-cost models. Existing native provider configuration remains separate from these workflow defaults.

See [architecture](ARCHITECTURE.md), [contributing](CONTRIBUTING.md), and [security](SECURITY.md).
