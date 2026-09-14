---
tier: contract
authority: agent
title: Advisory host hooks
---

# Advisory host hooks

[Installation](../commands/install.md) registers
[host-adapter.py](host-adapter.py) for the selected Codex or Claude Code host. Registration
lives in `.codex/hooks.json` for Codex and `.claude/settings.json` for Claude.
The implementation lives in `.codex/hooks/host-adapter.py` or
`.claude/hooks/host-adapter.py` alongside the rest of that host's workflow.
Use `--no-hooks` to skip adding registrations; existing ones are preserved.
The selected host must load and trust its project configuration before hooks run.

The Python adapter reads the host's `hook_event_name`, `cwd`, `tool_name` and
`tool_input` from JSON on stdin. It supports Claude Write/Edit/NotebookEdit file
fields and Codex `apply_patch` Add/Update/Delete/Move headers. `PreToolUse` warns
about primary/sibling/outside-worktree file targets and direct Git metadata edits.
`PostToolUse` adds document-ownership reminders for relevant planning and rule
files. Notices use `systemMessage` and event-specific `additionalContext`; every
adapter outcome exits successfully without a permission decision.

The adapter derives repository context from payload `cwd` and Git's worktree list.
An assigned checkout is an immediate child of the primary `.worktrees/` directory;
this does not validate runtime-owned file assignments. Scratch/temp paths are
allowed after repository boundaries are checked, so repositories under a temp
directory still get primary/sibling notices. Filesystem paths are resolved before
comparison; this is still advisory, not a sandbox or protection against races.

Shell coverage is deliberately narrow: literal final `echo`/`printf`/`cat`
redirects and a plain `git commit` in a non-assigned checkout. Compound commands,
expansions, heredocs, arbitrary scripts, PowerShell cmdlets and other write tools
are not comprehensively analyzed. Missing Git context or malformed payloads are
quiet. Repository rules and host permissions govern the work regardless of notices.

The generated launcher resolves the active Git root from its working directory
and leaves stdin intact. It supports subdirectory launches; the adapter does not
use `CLAUDE_PROJECT_DIR`, which can continue pointing at the primary checkout.
The launcher and adapter read Git paths and host payloads as UTF-8, including on
Windows. Python 3.11+ and Git are required. Claude's launcher uses its normal Bash command
shell (Git Bash on Windows); the adapter itself uses only Python's standard library.

```text
python -m unittest discover -s tests -p test_host_hooks.py -v
python -m unittest discover -s tests -p test_install.py -k registered_hooks -v
```

These source-repository tests exercise actual Git worktrees and the installed
hook commands, including Codex patch payloads and Claude file payloads. They do
not grant trust or establish authenticated live host execution.

## Standalone Bash examples

The two Bash scripts below remain optional standalone examples. The installer
registers the Python adapter above, not these scripts; configure them manually
only if needed. Repository prompts and host permissions remain in effect.

| Script | Example event | Output |
|---|---|---|
| [ai-tier-notice.sh](ai-tier-notice.sh) | `PostToolUse` | Plain `NOTICE` naming document ownership and responsibilities |
| [worktree-confine.sh](worktree-confine.sh) | `PreToolUse` | `systemMessage` warning about a possible write outside the assigned checkout |

The worktree hook reads `cwd`, `tool_name` and `tool_input` from JSON on stdin.
It derives the checkout and shared Git directory from Git. File tools warn for
outside paths and direct Git metadata edits; checkout and environment-provided
scratch/temp paths are quiet. Shell checks also allow shared Git metadata and
standard stream devices, and inspect only simple redirects.

Both hooks are advisory: they exit 0 and never emit a permission decision.
The tier hook emits plain `NOTICE` text; the worktree hook emits a
`systemMessage` object for host display.
Missing repository context produces no warning. JSON parsing prefers `jq`,
then Python; the minimal text fallback can miss escaped/quoted inputs.
The lexical path checks do not resolve symlinks or junctions and lowercase
paths even on case-sensitive systems. Shell quoting, heredocs and paths with
spaces can produce missed warnings or false positives. This is an accident
notice, not a sandbox or authorization to bypass host permissions.

Run the Bash regression suite before and after hook changes:

```bash
bash .ai/hooks/worktree-confine.test.sh
bash .ai/hooks/ai-tier-notice.test.sh
```

It checks quiet versus warning output, exit status, absence of permission
decisions, Windows slash forms, sibling paths, Git metadata, scratch paths
and redirects. Hook testing uses this Bash file; the separate Python suite
tests the phase runtime.
