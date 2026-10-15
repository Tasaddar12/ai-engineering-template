# Issue 87: automatic worktree handoff

## Authority and scope

The actual human request delivered through Jarvis was: “AI Workflows often ignore needing a worktree... different hook to force it to open a worktree when it tries to write or edit anything and its not currently in one... Look into it and get another PR if we dont have something open for it already.” The coordinator owns duplicate checking and publication. This maintenance record does not fill the adoption skeleton or establish an adopting project's phases.

## Decisions

- Investigate the current host hook contract and prepare a separate draft implementation for a matching gap; never merge.
- Preserve PR 86's preference for scratchpad warnings. Distinguish task notes from source edits; do not restore a repeated hard-halt retry loop.
- Preserve uncommitted changes and prevent writes to the old checkout from continuing after a claimed handoff.
- Keep the six existing drafts separate and frozen. Work 73/74, live infrastructure, tool installation and real cleanup are out of scope.

## Claude's Discretion

- Researcher may choose the bounded evidence and recommend an implementation and test boundary. Recommendations are technical findings, not additional human decisions.
- Researcher owns only this CONTEXT.md and RESEARCH.md. No production edits, test execution, provider writes, publication or merge.

## Deferred Ideas

- Work 73/74, unrelated drafts, live infrastructure, tool installs and real cleanup.

## Coordinator technical scope decisions

- To implement the user's source-versus-task-note distinction without guessing from file extensions, ordinary external temporary artifacts are limited to plain unlinked create/update paths under the resolved OS temporary directory and outside every Git repository. No identity or preparation is needed there. This is a bounded technical choice under delegated implementation discretion, not an additional human approval.
- Mixed, rename/delete, linked/reparse/hardlinked, cross-repository and ambiguous paths receive source/unsupported handling. Non-temp external locations are not a note exemption.
- Independent RED review required the corresponding both-host control before production; corrected test-only38b7b1c retains genuine source refusal failures and passing ordinary-note controls. PLAN/MATRIX alignment and independent bounded recheck precede source release.
