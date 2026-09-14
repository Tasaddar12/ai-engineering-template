---
tier: contract
authority: agent
title: Advisory host hooks
---

# Advisory host hooks

[Installation](../commands/install.md) registers the existing scripts directly:

| Script | Event | Output |
|---|---|---|
| [worktree-confine.sh](worktree-confine.sh) | `PreToolUse` | A `systemMessage` warning for file or patch targets outside the checkout |
| [ai-tier-notice.sh](ai-tier-notice.sh) | `PostToolUse` | A `NOTICE` naming document ownership and responsibilities |

Codex registrations use `.codex/config.toml`; Claude uses `.claude/settings.json`.
Scripts live in the selected host's `hooks` folder. There is no Python hook
adapter. The command locates the script from the active Git root, including
when the host starts from a subdirectory or a linked worktree.

Use `--no-hooks` to skip adding registrations; existing hooks are preserved.
Existing settings remain authoritative. Codex must trust the project and hooks
before running them. Installed files alone do not prove live host execution.
See [Codex hooks](https://learn.chatgpt.com/docs/hooks).

Bash and Git must be available. On Windows, put Git Bash's `bin` directory on PATH
ahead of WSL's `bash.exe`. JSON extraction uses jq when available, then Python,
with a limited text fallback. The scripts support file fields and Codex
`apply_patch` Add/Update/Delete/Move headers. The worktree script uses payload
`cwd` and Git, rather than `CLAUDE_PROJECT_DIR`, to locate the active checkout.

Both hooks are advisory: they exit successfully and never emit a permission
decision. File and patch targets outside the checkout or in Git metadata warn;
external scratch paths are quiet after repository boundaries are checked.
Shell redirect detection is approximate. These checks do not parse arbitrary
scripts, resolve every symlink, validate runtime ownership or create a sandbox.
Repository instructions and host permissions still govern the work.

Run the existing Bash suites and the installed-launcher test after hook changes:

```text
bash .ai/hooks/worktree-confine.test.sh
bash .ai/hooks/ai-tier-notice.test.sh
python -m unittest discover -s tests -p test_host_hooks.py -v
python -m unittest discover -s tests -p test_install.py -k registered_hooks -v
```

The tests exercise JSON/stdin behavior, real Git worktrees, host registrations,
patch paths and direct Bash launchers. They do not establish trusted live host
execution.
