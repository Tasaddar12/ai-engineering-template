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
Independent review CR01–CR06 demonstrates these initial mitigations are
incomplete. The coherent repair below now passes the approved regression matrix;
fresh independent review remains required before accepting the repaired source.
I87-G-T2: unknown/open/partial/stale/mismatched provider evidence, unowned and
dirty targets preserve work; both-provider offline tests above. Canonical
threat issue readback was confirmed by the coordinator as
[I87-G-T1](https://github.com/Tasaddar12/ai-engineering-template/issues/95#i87-g-t1),
[I87-G-T2](https://github.com/Tasaddar12/ai-engineering-template/issues/95#i87-g-t2)
and [I87-G-T3](https://github.com/Tasaddar12/ai-engineering-template/issues/95#i87-g-t3).
The coordinator owns the PLAN link update and independent review.
I87-G-T3 lock, exact snapshot approval and receipt lifecycle belong to dependent
cleanup; no cleanup behavior is claimed here. Opaque external execution and
post-preflight concurrent changes remain documented limits of this control.

## Remaining

Independent source review found six blocking regression families (CR01–CR06)
in `e5af9bd`: Bash literal escapes/continuations, wrapper fixed-point parsing,
Git destructive option abbreviations/clusters, PowerShell removal aliases,
root ancestry and malformed ownership JSON roots. A native-entrypoint regression
matrix now asserts JSON denial/exit 2 and independently exercises paired harmless
controls. Its first run on unchanged production source exited 1, Ran 6 tests in
14.030s, with 42 intentional behavior assertion failures: unsafe commands
returned exit 0/empty stdout, while malformed sessions/wave scalar roots
returned exit 1/traceback instead of structured denial. This is observed RED;
no regression implementation has been applied. A repeated run after ensuring
controls execute independently also exited 1, Ran 6 tests in 16.863s, with the
same 42 attack assertions failing and no harmless-control failures. No skips or
fixture/import failures occurred. Independent matrix review approved the six
families and requested exactly three added cases: nested prohibited GIT_DIR
after `command env`, a `branch --list -- '--delete'` harmless pattern, and a
`push --push-option=-d` harmless option value. The approved-matrix run on
unchanged production source exited 1, Ran 6 tests in 17.740s, with 44 assertion
failures: the added nested environment still allowed, the branch pattern was
incorrectly refused, and the push option-value control passed. This preserves
the extra RED evidence before the coherent repair; no production source changed.
The coordinator authorized implementation after this test commit without a
further pause. Installer, installer tests and hooks README are released to the
separate planning registration worker; repairs own only the guard library,
guard tests and this summary.

Review RED commits: `5c927709c9e74ff9def38837f3ebd1e29dd304a6` and
`fec735e79233067dd19220c60f2fa3937c64195a`. They precede the coherent production
repair; no implementation was applied before the independent matrix approval.

## Coherent review repair

The repair changes only `destructive_guard.py` and this summary after the two
test-first commits. Bash tool payloads and explicitly selected POSIX shells
apply literal unquoted backslash escapes and remove backslash-newline
continuations. Native Windows commands preserve path backslashes; quoted
Windows Git executable-path controls pass. Wrapper/assignment layers normalize
to a fixed point, checking prohibited context variables at each layer, including
after `command env`. Literal `time` and `!` prefixes expose the assessed command;
unsupported wrapper flags refuse.

Git options are separated from their values and operands. `--` ends option
parsing; long destructive abbreviations and short destructive clusters refuse.
`branch --list -- '--delete'` and `push --push-option=-d` remain harmless.
PowerShell del/rd/erase aliases, including case variants, use backup protection.
Component-aware common-path comparisons handle compatible drive/POSIX roots,
parents and doubled separators without string-prefix ancestry. Ownership
sessions/wave JSON requires an object root, the proper list container and
object records with string branch/worktree fields before any access; malformed
records refuse with native denial JSON/exit 2 instead of a traceback.

| Repair check | Observed result |
|---|---|
| `python -m unittest discover -s tests -p test_destructive_guard.py -v` | Exit 0, Ran 14 tests in 58.200s, zero skips; all six approved review families and controls, original registered/native/backup matrix and both-provider offline contracts pass |
| `python -m unittest discover -s tests -p test_install.py -k registered_hooks -v` | Exit 0, Ran 1 test in 25.009s, zero skips; actual Codex Windows / Claude launchers and advisory scratchpad/dispatch coverage retained |
| `git diff --check` | Exit 0 |

Repair source commit: `180e189719624ab01aba31cb700f69eeb4cf7de6`.
This summary-only evidence update pins the source identity. These checks exercised
the repaired source descending from `fec735e`. No production source changed
after the passing run. Fresh independent review is pending, so the earlier
blockers are reported as repaired with test evidence, not independently cleared.
Released installer/test_install/hooks README paths were not changed. No cleanup
child path, provider adapter, PR86 hook, adoption record, publication or merge
was touched.

## Second independent review RED

Frozen source `b74241f` received five further blockers: Windows environment-name
case folding, explicit cmd syntax, MSYS drive paths, malformed tool_name types,
and quoted/escaped wildcard provenance. The new matrix exercises the real
source JSON stdin entrypoint and pairs each family with harmless controls.
It covers nested mixed/lower/upper environment names with POSIX case behavior,
explicit cmd caret/percent/delayed syntax and literal read/echo controls,
MSYS drive roots/parents/-C/sibling paths on both available Windows drives,
unmodeled POSIX roots, non-string tool names, and literal versus active globs.
Submitted destructive commands are never executed. Temporary Git fixtures and
their cleanup are confined to test-owned directories.

The first matrix run on unchanged production source exited 1, Ran 5 tests in
12.168s, with 36 behavior assertion failures (unsafe allow, malformed payload
traceback instead of refusal JSON, and false-positive literal removals).
An exact primary-branch-switch reason assertion was then added to the MSYS -C
cases, so unknown/misresolved context cannot count as protection. Final RED:
`python -m unittest discover -s tests -p test_destructive_guard.py -k second_cr -v`
exited 1, Ran 5 tests in 12.660s, with 38 intended behavior assertion failures,
zero skips or fixture/import failures. This is recorded before the independently
requested matrix review.
No production source has changed for this review attempt. Guard acceptance
remains blocked until repaired and independently reviewed. Existing canonical
risk 95 anchors I87-G-T1 (parser/context/paths) and I87-G-T2 (payload schema)
remain authoritative; no new issue is requested.

Independent matrix review accepted all five families and requested exactly two
PowerShell Path/LiteralPath cases plus renaming the harmless `git_directory`
variable to `gitdirectory` (the former belongs to conservative GIT_* scope on
Windows). The adjusted matrix on unchanged production source exited 1, Ran 5
tests in 11.642s, with 39 behavior assertion failures and zero skips. Quoted
PowerShell `-Path '.workflow-*'` correctly refused already; the added
`-LiteralPath 'ordinary*.txt'` control exposed a false positive. This RED commit
precedes the approved coherent repair; no further authority pause is required.

## Second coherent review repair

RED commits `4914218afe6badf52546954463a5e404a192075c` and
`034729b9fb7c5caef52be07bfc7434d973fd30c7` precede this repair. The independent
matrix gate approved all five families and the final PowerShell additions
before production source changed. Only the guard library and this summary
changed after those test commits.

Windows prohibited environment comparisons now normalize case at every prefix
layer; POSIX variable names retain their case semantics. Explicit cmd shell
selection refuses caret, percent and delayed-expansion syntax with
`unsupported-cmd-syntax`; literal read commands and quoted echo text retain
their declared allow behavior. No cmd expansion or command body is evaluated.

Windows Bash path operands model `/c`/`/c/...` drive spelling (and corresponding
other drive letters), sharing canonicalization across cwd overrides, cd, Git -C,
worktree removal and filesystem removal. Unmodeled POSIX roots on Windows Bash
refuse instead of being interpreted as invented native paths. Both actual
available drives C and D were exercised in disposable fixture repositories;
the Git -C tests require the exact primary-branch-switch reason, so unknown
context cannot count as protection. Sibling paths remain allowed.

Non-string/empty tool names are rejected before any hash-based membership test,
and malformed payloads produce native denial JSON with exit 2. Lexing retains
per-character quoted/escaped wildcard provenance. Component-wise glob overlap
permits ordinary sibling globs and literal wildcard filenames while preserving
backup-covering globs and paths inside backups. PowerShell `-Path` retains
wildcard semantics even when quoted; `-LiteralPath` treats wildcard characters
as literal data.

The immutable Segment interface keeps canonical `.cwd` and plain literal
`.argv` unchanged. Additive defaulted fields are `shell_dialect` (`native`) and
aligned `glob_patterns` (empty tuple by default; each parsed argument has a
pattern or None). This preserves existing two-argument construction while
making shell/path and wildcard provenance available to downstream consumers.

| Second repair check | Observed result |
|---|---|
| `python -m unittest discover -s tests -p test_destructive_guard.py -v` | Exit 0, Ran 19 tests in 77.277s, zero skips; original attacks/precision/native/provider, first-review six families and second-review five families including approved controls all pass |
| `python -m unittest discover -s tests -p test_install.py -k registered_hooks -v` | Exit 0, Ran 1 test in 27.315s, zero skips; actual both-host launchers plus advisory dispatch/scratchpad coverage |
| `C:/Program Files/Git/bin/bash.exe .ai/hooks/worktree-guard.test.sh` | Exit 0, 60 passed, 0 failed |
| `git diff --check` | Exit 0 |

Second repair source commit: the commit containing this section; its exact SHA
is recorded in a following summary-only evidence update. Checks exercised the
production bytes descending from `034729b`; no source changed after the passing
run. All five findings are repaired with these tests; fresh independent review
remains pending. Canonical 95 I87-G-T1/T2 remain the same risk identities. No
installer, released test_install/hooks README, PR86 hook, provider adapter,
adopting-project planning record, cleanup child, publication or merge changed.

`glab` was absent;
its official documented paginated JSON contract and injected offline fixtures
were used. No live GitLab/on-prem execution is claimed. Arbitrary enterprise
hostnames, fork ambiguity, unsupported Git context flags, conditional-cd
ambiguity and squash-merged unique tips preserve work conservatively.

The parser is not a full Bash/PowerShell/cmd AST or arbitrary-script sandbox.
It does not inspect opaque Python/Node/external executable contents. Backup
approval preview/apply, exact operation ordering, locks and transient one-use
receipts are intentionally the separately assigned CLEANUP child, which has
not started in this checkout. No broad approval override exists here.
