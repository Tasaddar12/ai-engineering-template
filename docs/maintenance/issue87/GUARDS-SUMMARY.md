---
phase: issue87-maintenance
plan: guards
status: complete
issue_refs:
  - https://github.com/Tasaddar12/ai-engineering-template/issues/87
input_revision: 14e8bd97481524c306d853ebb21249b6da57f60f
requirements-completed: [ISSUE87-GUARD, ISSUE87-RED]
acceptance: [I87-A1, I87-A3]
documentation:
  - .ai/hooks/README.md
  - .ai/references/destructive-operations.md
  - .ai/RULES.md
  - .ai/runtime/lib/worktrees.py
---

# Guard implementation

Assigned branch: `phase-issue87-guards`; approved source base `77b5668`.
Only GUARDS-PLAN was implemented. Cleanup and publication remain coordinator owned.

## Accomplishments

The separately registered Python PreToolUse hook refuses primary-checkout branch
switches, recognized unsafe branch/worktree deletion and ordinary shell backup
removal. The standard-library policy exports immutable `command_segments` and
`evaluate_payload` decisions, with injected read-only argv evidence collection.
GitHub/GitLab provider identity, complete terminal evidence, ownership, clean
status including ignored/untracked files and local-tip integration are required
before a recognized local deletion can pass policy. Unknown preserves work.

Python-aware installer launchers resolve `.codex`/`.claude` adjacent libraries.
Codex Windows resolves paths in Python and propagates exit 2. Registered exact
names are Bash, exec_command, shell_command and shell. Both installed host
launchers retain advisory dispatch and scratchpad coverage. No real cleanup,
provider writes, installation into a user's project, publication or merge ran.

PR86 `worktree-guard.sh` is unchanged. Coordinator-directed documentation-only
scope amendment added `.ai/RULES.md` Hooks and validation prose and the
`worktrees.py` module docstring to correct stale advisory claims. The assigned
GUARDS-PLAN records that narrow amendment; worktrees runtime logic is unchanged.

## TDD Evidence

RED command: `python -m unittest discover -s tests -p test_destructive_guard.py -v`.
Python 3.13.14 on Windows; exit 1, Ran 3 tests, 45 failing subtest assertions,
zero skips. Named `test_registered_pipeline_denies_primary_switch` expected
registered refusal for Codex exec_command/shell_command/shell and Claude Bash;
actual pipeline contained no matching handlers and allowed each command (`[]`).
The 41 attack assertions likewise observed allow; precision matrix passed.
No command under assessment was executed. An earlier discovery attempt imported
the installer TestCase into this module; it was interrupted and corrected and is
not counted as RED evidence.

RED commits: `bb1f5e4` (registered attack/precision assertions and interim SUMMARY),
then `442754e` (provider/cwd matrix written before policy implementation).
The latter's focused `-k provider` run exited 1, Ran 1 test, on the intended
`expected registered refusal, actual allow` assertion; the absent module did
not cause an import/setup error. Detailed provider cases were written before
implementation and exercised during GREEN.

GREEN source commit: `e5af9bd16d6c81dbd161f952886808baf85b8a10`.
This summary-only evidence update records the exact source commit after it was
created. No separate refactor needed.

## Checks

Python 3.13.14; existing PyYAML 6.0.3 available for installer tests. All test
fixtures were disposable temporary repositories; commands being assessed by
the guard were not executed.

| Check | Observed result |
|---|---|
| `python -m unittest discover -s tests -p test_destructive_guard.py -v` | Exit 0, Ran 8 tests in 45.397s, zero skips; includes 41 initial attack cases, 19 precision commands, both-provider 26-case matrix, registered both-host primary-switch refusals, source JSON/exit behavior, cwd/aliases, ignored work, unintegrated tip and real Windows junction backup alias |
| Same guard suite `-k provider -v`, after adding exact CLI argv assertions | Exit 0, Ran 1 test in 8.533s, zero skips |
| `python -m unittest discover -s tests -p test_install.py -k registered_hooks -v` | Exit 0, Ran 1 test in 27.594s, zero skips; Codex Windows and Claude Git Bash actual launchers, nested spaces/non-ASCII, status 0/2 and denial JSON, advisory scratchpad/dispatch preserved |
| Installer `-k no_hooks -v` | Exit 0, Ran 1 test in 30.980s, zero skips; both hosts |
| Installer `-k selected_host_preserves_settings -v` | Exit 0, Ran 1 test in 18.519s, zero skips; both hosts, user hook settings preserved |
| `C:/Program Files/Git/bin/bash.exe .ai/hooks/worktree-guard.test.sh` | Exit 0, 60 passed, 0 failed |
| `git diff --check` | Exit 0 |

The checks cover the implementation working tree committed as `e5af9bd`,
descending from `442754e`.
Exact provider argv contract assertions were the only test change after the
eight-test full run, and their focused test passed subsequently. No production
source changed between those checks and the implementation commit.

No diff against source base `77b5668` exists for worktree-guard.sh, delivery.py,
runtime/phase.py, `.gitattributes` or adopting-project `.planning` records.
Only the worktrees.py module docstring changed, as explicitly directed.

## Threat Outcomes

GUARDS-PLAN I87-G-T1: literal parsing, all-segment inspection, conservative
unsupported/alias handling and backup canonicalization mitigate the assigned
bounded preflight failure mode; attack/precision and junction evidence above.
I87-G-T2: unknown/open/partial/stale/mismatched provider evidence, unowned and
dirty targets preserve work; both-provider offline tests above. Canonical
threat issue identity/readback and independent review remain coordinator owned.
I87-G-T3 lock, exact snapshot approval and receipt lifecycle belong to dependent
cleanup; no cleanup behavior is claimed here. Opaque external execution and
post-preflight concurrent changes remain documented limits of this control.

## Remaining

No implementation blocker remains for the assigned guard slice. Independent
review/verification and coordinator publication are pending. `glab` was absent;
its official documented paginated JSON contract and injected offline fixtures
were used. No live GitLab/on-prem execution is claimed. Arbitrary enterprise
hostnames, fork ambiguity, unsupported Git context flags, conditional-cd
ambiguity and squash-merged unique tips preserve work conservatively.

The parser is not a full Bash/PowerShell/cmd AST or arbitrary-script sandbox.
It does not inspect opaque Python/Node/external executable contents. Backup
approval preview/apply, exact operation ordering, locks and transient one-use
receipts are intentionally the separately assigned CLEANUP child, which has
not started in this checkout. No broad approval override exists here.
