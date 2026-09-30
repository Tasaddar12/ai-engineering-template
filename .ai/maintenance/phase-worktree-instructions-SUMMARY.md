# Phase Worktree Instruction Routing — SUMMARY

```yaml
status: blocked
source_revision: db8662568e75f28c44a17b5aa4f3a9ed99e952bb
scope: phase locator-first documentation routing
```

## Changes

- Added locator-first phase selection to plan, discuss, execute, verify and ship workflows.
- Added validated session reuse, primary checkout session opening, linked worktree adoption routing, explicit worktree changes and full init reload instructions.
- Mirrored command and skill entrypoints; documented `plan phase 01` as an ordinary-language invocation.
- Updated runtime and session references for `phase.locate`, optional ship phase selection and `session.adopt`.

## Checks

| Check | Result |
|---|---|
| `python -m unittest tests.test_agent_sources` | Passed, 12 tests |
| `python -m unittest tests.test_install` | Interrupted after approximately two minutes; emitted one `E`; no final result captured |
| `git diff --check` | Passed |

## Blocker

`session.adopt phase <phase>` is documented to preserve the selected linked worktree, branch and dirty phase records. The runtime implementation and its regression checks are a separate pending slice; this documentation contract is not complete until that API is implemented and verified.
