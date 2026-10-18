# PR 92 contribution-language editorial pass

**Outcome:** Recast the assigned hook guidance as current, direct instructions while preserving the documented refusal and approval boundaries.

## Revision and scope

- Source base: `77b5668f2003bea60127d87e8785469286abafb3`
- Synchronized parent revision before edits: `240c2ea39bd9cfcf6dcc4973c46bb4ec6af37522`
- Reviewed original PR head: `d8f2c8bd0c4dca0f82a7fc8a95e4f0abb8bcd2b6`
- Changed: [`.ai/hooks/README.md`](../../.ai/hooks/README.md) and [`.ai/references/destructive-operations.md`](../../.ai/references/destructive-operations.md)
- Reviewed unchanged: [`.ai/RULES.md`](../../.ai/RULES.md); its hook guidance already states the current advisory and refusal behavior directly.

## Changes

- Replaced launcher failure history with current Windows Codex launcher requirements, including the four Git Bash probes, no PATH fallback, root resolution, quote escaping and exit status.
- Made unsupported Git context flags and unknown provider ownership explicit refusal/preservation instructions.
- Stated the cleanup approval route's required evidence and safeguards directly. The destructive guard does not provide that route or an approved cleanup command; existing runtime cleanup verbs keep their documented contracts and do not provide backup-removal approval.
- Preserved parser grammar, refusal conditions, evidence requirements, approval fields and GitLab validation history.

## Checks

- Manually reviewed the changed paragraphs against the source launcher in `.ai/install.py` and the original PR diff.
- Inspected the final diff, Markdown links and whitespace with `git diff --check`.
- Tests and configured project checks: not run, as assigned.

## Deviations and remaining work

- No scope deviations. No unresolved documentation gaps identified in the assigned paths.
