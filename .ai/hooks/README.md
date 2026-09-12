---
tier: contract
authority: agent
title: Advisory hook examples
---

# Advisory hook examples

Both scripts are optional examples. No host registration or settings template
is supplied. Install them through your host's hook configuration if wanted;
the repository's prompts and host permissions remain in effect.

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
