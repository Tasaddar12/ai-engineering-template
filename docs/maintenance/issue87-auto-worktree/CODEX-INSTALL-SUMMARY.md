---
phase: maintenance-issue87-auto-worktree
plan: "06-codex-B"
status: blocked
requirements-completed: []
acceptance: []
documentation: []
issue_refs:
  - id: ISSUE98
    summary: Canonical source confinement, unit identity and host transition risks remain unresolved pending joined verification.
    variant: Security risk
    state: unresolved
    relationship: followup
    issueRepo: Tasaddar12/ai-engineering-template
    issueURL: https://github.com/Tasaddar12/ai-engineering-template/issues/98
    issueNumber: 98
input_revision: 76045292bd4d2da4617d0aa346a8b8db0450aa9a
branch: phase-issue87-codex-install-123611
worktree: D:/Codex/2026-10-15/task-2/repo/.worktrees/issue87-codex-install-123611
changed_paths:
  - .ai/install-assets/codex-worktree.py
  - .ai/install.py
  - tests/test_install.py
  - tests/test_install_update.py
  - tests/test_install_migration.py
  - docs/maintenance/issue87-auto-worktree/CODEX-INSTALL-SUMMARY.md
---

# Task6B bounded installer continuation

Installer source and five safe export inspection cases are written. All Python,
export, runtime and native outcomes are **NOT_RUN**. CW-03 behavioral installation
acceptance is incomplete; CW-05 generated-native shell and patch proof remains
**BLOCKED / UNVERIFIED**. No component GREEN, acceptance completion or ship-ready
claim follows from this source change or its Git checks.

## Changes and source wiring

- `.ai/install-assets/codex-worktree.py` is a thin generated entry point. It adds
  its adjacent `runtime` directory to the import path, imports
  `lib.codex_worktree.launcher_main` and returns that function's result. An
  unavailable runtime reports a refusal and exit2. Argument parsing stays in the
  committed producer: `phase|quick LABEL [--base COMMIT] [--prompt TEXT] [--exec]`.
  Flag-looking prompts use `--prompt=--literal-flag`. The asset does not add a
  runner, native option passthrough, shell evaluation or batch-wrapper route.
- `.ai/install.py::payload` requires a regular tracked launcher asset only for
  Codex and maps it through `.ai/codex-worktree.py` to
  `.codex/codex-worktree.py`. The existing hook/runtime export supplies
  `.codex/hooks/codex-worktree.py`, `.codex/runtime/lib/codex_worktree.py` and the
  producer's other adjacent runtime dependencies. Packaging assets remain outside
  the ordinary exported inventory. Claude gains no launcher or registrations.
- `HOST_HOOKS["codex"]` adds `codex-worktree.py` for `PreToolUse`, `SessionStart`
  and `UserPromptSubmit`, each timeout30. Host `PreToolUse` uses literal matcher
  `*`; the two lifecycle groups carry no matcher. The handler is a synchronous
  command with no `async` field. Existing Python command generation produces the
  exact POSIX and Windows strings authored in the committed `guard_commands()`;
  the Windows definition retains `; exit $LASTEXITCODE`.
- `managed_scripts()` derives its inventory from shared and host registrations,
  so the new script participates in existing exact command recognition and stale
  managed-group replacement. `plan_install`, both update planners and
  `plan_migration` consume the expanded payload. No separate migration/update
  implementation change was needed for these newly added destinations.
- Shared `MANAGED_HOOKS`, Claude `HOST_HOOKS`, and the existing editing-group
  assembly are unchanged. Advisory `worktree-guard.sh` remains first and
  `source-prewrite.sh` second in that group. The old Codex SessionStart
  `context-handoff.sh` stays first, followed by the separate new guard group.
- Existing settings merge code is unchanged. It appends missing groups and
  preserves unrelated TOML values/text, including `features.hooks=false`, model,
  effort, policy and agent config values. The producer alone owns invocation
  hook enabling and policy/trust preservation-or-refusal. Actual effective-feature
  and known-unsafe native setup behavior remain unverified.

The committed A producer and both defensive summaries were read statically at
this worker's input revision. `CODEX-REVIEW-02.md` supplies the fresh clean static
repair review, and `CODEX-PLAN-REVIEW-04.md` approves this bounded continuation.
Neither substitutes for runtime or native evidence. CR-01's `.bat`/`.cmd` refusal,
direct Windows executable prerequisite and literal prompt forwarding remain in
unchanged producer source. CR-02 lifecycle note allowance and source-tool root
checks remain unchanged.

## Written fixture design

Each of the three test files has an independent
`CodexWorktreeExportSafeTests(unittest.TestCase)` class, avoiding older
real-Git/process fixture setup. Every new method includes
`codex_worktree_export_safe` in its name. The future check design imports the
installer, renders/merges bytes, plans changes and materializes only disposable
export files for content inspection. None of these imports or operations was
executed during this continuation.

Each class fences `subprocess.run`, `Popen`, `call`, `check_call`, `check_output`,
`os.system` and `os.popen` with rejecting mocks. The installer's sole permitted
runner request is a stubbed `git ls-files --stage -z` metadata listing made from
source filenames. Unexpected runner arguments fail an assertion; no Git child,
generated command/hook/launcher, native host or model server is required by the
new cases. They never call `installer.main()` or execute exported Python.

| File / future cases | Written inspection coverage | Result |
|---|---|---|
| `tests/test_install.py`: asset/commands/idempotence; Claude/missing asset | Exact launcher mapping/API/CLI text, copied guard/runtime bytes, exact POSIX/Windows commands, event/matcher/type/synchronous timeout inventory, old guards and editing order, user hooks/settings and `features.hooks=false`, planning/model/effort/agent values, repeated export, ownership inventory, no-hooks export and Claude conservation | NOT_RUN |
| `tests/test_install_update.py`: managed conservation; stale guard replacement | Older export missing launcher/guard, all old/custom groups retained once, new files, preflight remains read-only, model/policy/feature/agent/planning bytes retained, managed timeout refresh and repeated update idempotence | NOT_RUN |
| `tests/test_install_migration.py`: migration/followup export | Legacy paths relocate, all old/custom groups retained once, launcher/hook/runtime content, custom agent/model/effort and project/config bytes survive, required followup update remains idempotent | NOT_RUN |

Existing assertions and the retained behavioral tracer remain active. Three
narrow changes to existing `test_install.py` expectations were explicitly
confirmed by the coordinator during this assignment:

1. The old one-group SessionStart expectation now requires exactly two, exactly
   one retained unmatched handoff group and exactly one guard group, equal to the
   complete canonical list. The original first handoff-command assertion remains.
2. The new guard has its explicit timeout30 branch before the unchanged generic
   Python timeout120 and other existing timeout cases.
3. Destructive-handler identity filtering now precedes its regex selection,
   avoiding parsing an unrelated native literal `*` matcher as a Python regex.
   Its exact one-handler assertion and all behavioral assertions remain.

These are static inventory/selection corrections caused by the three new
registrations. They remove no test, assertion, gate, skip or tracer. In particular,
`tests/test_codex_worktree.py` and `tests/test_same_agent_worktree.py` are unchanged.

## Checks and evidence limits

- Initial Git readback: exact assigned root, branch and HEAD matched the values in
  frontmatter; the worktree was clean. Base ancestry was checked before the first
  write. Root pin and branch/base ancestry are rechecked before the owned commit.
- Full scoped source/asset/test diff was read statically. Exact generated command
  text was compared to committed `guard_commands()`. Payload relocation,
  inventory derivation, merge behavior and update/migration callers were traced
  without importing or executing Python.
- `git diff --check`: exit0, no whitespace/conflict diagnostics. Git warns that
  configured checkout conversion will replace LF with CRLF; this is not runtime
  evidence. The staged owned-path diff is checked again before commit.
- Static Git comparison against the input revision shows no change to the A
  producer/adapter/tracer, same-agent tests, planning configuration, agent TOMLs,
  model routing, original six branches, CI/actions or protection configuration.
- `python -m unittest discover -s tests -p test_install.py -k codex_worktree_export_safe -v`: **NOT_RUN**.
- `python -m unittest discover -s tests -p test_install_update.py -k codex_worktree_export_safe -v`: **NOT_RUN**.
- `python -m unittest discover -s tests -p test_install_migration.py -k codex_worktree_export_safe -v`: **NOT_RUN**.
- All other Python imports, syntax/static validators, model/effort queries, mixed
  suites, retained installed tracer and native acceptance checks: **NOT_RUN**.
- No actual installation/export, generated hook or launcher, native CLI/server,
  injection/host probe, replacement harness or manual remote CI was performed.
  No denied operation was retried, escalated or moved to an alternate route.

The existing Python block records this exact previously denied target:
`C:/Users/killi/AppData/Local/Microsoft/WindowsApps/PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0/python.exe`.
It was denied before startup in earlier work; this worker did not invoke it or
any substitute. The current binding amendment forbids every Python execution,
including the otherwise safe future export selectors. There was no new denial.

## Deviations and remaining work

The safe amendment supersedes original B executable/native instructions. No native
canned-provider fixture was implemented. The three authorized existing-test
corrections above preserve their original assertions' meaning while recognizing
the expanded inventory. There are no source changes outside B ownership.
Context usage: unavailable.

The coordinator also identified an outside-ownership static compatibility concern:
`tests/test_destructive_guard.py:46` applies `re.search` to every PreToolUse
matcher. The required native literal `*` registration is not a Python regex.
That harness was not edited or run here; independent review/coordinator ownership
must reconcile it before treating any future full-suite result as acceptance.
No runtime failure is claimed from this static concern.

Coordinator owns integration, publication, independent static source/integration
review and C's operational documentation. Written fixtures still need separately
authorized future execution. CW-03 installed behavior, CW-05 actual generated
native shell **and** patch denial, effective-feature/trust/default-root behavior
and original AW live/human_needed obligations remain unresolved. The retained
installed tracer is active and unmodified; its historical evidence is unchanged
and no new RED/GREEN result exists. PR97 remains incomplete, issue87 stays open,
all PRs remain unmerged, PR99 stays separate, and the adoption skeleton is intact.

Issue98's existing followup remains unresolved. Canonical risk mapping is
`Tasaddar12/ai-engineering-template/source-prewrite/target-confinement` (T-AW-01),
`.../unit-identity` (T-AW-02), and `.../host-transition-proof` (T-AW-03). Installer
wiring and written preservation expectations do not close any risk or satisfy
native acceptance. Provider reconciliation/readback belongs to the coordinator.
