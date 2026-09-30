# Phase Worktree Instruction Routing — SUMMARY

```yaml
status: complete
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
| `python -m unittest discover -s tests -p test_install.py -v` | Passed, 37 tests; 1 host symlink-permission skip; reported error not reproduced |
| `python -m unittest discover -s tests -p test_session_delivery.py -v` | Passed, 50 tests |
| `PYTHONPATH=tests python -m unittest test_install.InstallerTests.test_installed_runtime_answers_its_verb_contract -v` | Passed, 1 test; both host namespaces checked |
| `git diff --check` | Passed |

## Dependency status

```yaml
status: resolved
api: session.adopt phase <phase>
implementation: phase-worktree-adoption-SUMMARY.md
checks: passed
preserved: linked checkout, branch, staged work, dirty phase records
```
