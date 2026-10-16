---
phase: maintenance-issue87-auto-worktree
plan: "06-codex-A"
status: complete
subsystem: runtime
tags: [codex, worktrees, hooks, policy-preservation]
requires:
  - phase: issue87-codex-plan
    provides: Approved Task6A and checked policy/worker compatibility corrections
provides:
  - Bounded phase/quick launcher API with native hook and effective-policy preflight
  - Synchronous supported-tool guard for ordinary sessions and active runtime workers
  - Retained installed behavioral RED and real-Git runtime regression evidence
affects: [issue87-codex-installation, issue87-codex-documentation, issue87-verification]
requirements-completed: []
acceptance: [CW-01, CW-02, CW-04]
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
plan_head_before: 30d4c9d8b5632e82043163b0d05c4eb5776162f4
source_head: 67b32b2fd09212b553e77156c133225a3d5d42d6
actuals:
  tokens: 15662
  tasks: 1
  commits: 3
tech-stack:
  added: []
  patterns: [bounded native read-only RPC preflight, exact runtime receipt validation]
key-files:
  created: [.ai/runtime/lib/codex_worktree.py, .ai/hooks/codex-worktree.py, tests/test_codex_worktree.py]
  modified: []
key-decisions:
  - Production native invocation enables hooks but passes no sandbox, approval, trust or configuration bypass.
  - Launcher selects phase/quick sessions; hooks additionally validate existing active orchestrator-worktree wave receipts.
patterns-established:
  - Compare full effective policy settings and refuse ambiguity or change before native model startup.
coverage:
  - id: A1
    description: Real Git startup selection, simulated native argv/default cwd, reuse and preserved primary bytes/index
    verification:
      - kind: integration
        ref: tests/test_codex_worktree.py#test_runtime_selection_native_spy_guard_and_reuse_preserve_primary
        status: pass
    human_judgment: false
  - id: A2
    description: Direct runtime guard, active-worker/adopted-phase compatibility, structured targets and policy/trust refusal
    verification:
      - kind: integration
        ref: python -m unittest discover -s tests -p test_codex_worktree.py -k runtime -v
        status: pass
    human_judgment: false
  - id: A3
    description: Installed registration and actual generated-native enforcement remain dependent on B
    verification:
      - kind: integration
        ref: tests/test_codex_worktree.py#test_codex_worktree_installed_primary_shell_is_denied
        status: fail
    human_judgment: false
duration: approximately 30min including checked compatibility pause
completed: "2026-10-16"
---

# Phase maintenance-issue87 Plan 06-codex-A: Runtime and guard summary

The runtime selects an exact phase/quick destination before a new Codex run, preserves effective native policy, and denies supported source operations without valid runtime ownership.

Component A is complete. Whole Task6 and CW-01..06 acceptance remain pending B, C, integrated checks and independent verification. The acceptance list above identifies A's covered runtime surfaces, not completed end-to-end CW outcomes; ISSUE87 is not marked complete.

## Performance

- Started at approximately 2026-10-16T15:30Z; first durable RED receipt commit was 15:34:49Z. Source commit was 15:57:51Z; summary followed.
- Tasks: Task6A only. Files: three implementation/test paths plus this summary.
- Source diff measurement: ceiling(chars/4) = 15,662 over `30d4c9d8b5632e82043163b0d05c4eb5776162f4..67b32b2fd09212b553e77156c133225a3d5d42d6`, measured from Git's realized diff joined with LF. All measured files are text; no binary/generated artifacts. Summary text is excluded to avoid recursive measurement.
- Commit count: two source/test commits from the assigned immutable base, plus this final summary commit; final readback must be three.
- Context usage: unavailable.

## Accomplishments

- Added `launcher_main(argv=None)` and `hook_main(argv=None)` without changing phase verbs, lifecycle helpers, source-prewrite, advisory hooks, provider behavior or model routing.
- Startup validates options before creating a worktree, resolves a local captured base, uses existing `session.open` behavior through `open_session(..., sync=False)`, and independently validates registration, common repository, branch, exact unit receipt and base ancestry. Reuse permits accumulated commits; a different requested base refuses. No fetch, sync, adoption, reset or dirty-state copy occurs.
- Required committed installed files, synchronous definitions, handler launchability, native effective hooks and policy snapshots are checked before the model process. Known errors refuse visibly. The bounded app-server helper uses initialize/initialized, config/read and hooks/list only; no thread or turn is started.
- The guard reuses public prewrite classification for structured writes and patches. Narrow untracked scratchpad/OS-temp notes retain their allowance. Primary/invalid opaque writers refuse; exact diagnostics may pass. Valid isolated shell tests and ordinary commits remain usable. Actual exposed structured paths/cwd fields are checked without an arbitrary shell parser.
- Hook root validation accepts exactly one ordinary open phase/quick receipt or one active orchestrator-worktree wave entry. Strict raw wave screening precedes load_manifest's permissive fallback. Duplicate/conflicting, malformed, inactive, foreign, detached and inconsistent receipts refuse. Existing named adopted phase receipts retain their real non-generated paths and accumulated commits. Claude worktree-wf_ journal roots receive no exception.

## Task Commits

1. `86580ffd04088d42dcad52d513675ab4949b08b4` — test-only retained installed primary-shell refusal regression.
2. `67b32b2fd09212b553e77156c133225a3d5d42d6` — runtime, synchronous adapter and direct behavioral regressions.
3. This summary's separate metadata commit is returned in the worker handoff.

Assigned root: `D:/Codex/2026-10-15/task-2/repo/.worktrees/issue87-codex-runtime-113038338`; branch: `phase-issue87-codex-runtime-113038338`; immutable spawn base: `30d4c9d8b5632e82043163b0d05c4eb5776162f4`. The coordinator root pin, actual branch and persistent base ancestry were checked before writes/commits. No worker push, integration, rebase, cleanup or provider write occurred.

## Checks

Interpreter: existing Python 3.13 at `C:/Users/killi/AppData/Local/Microsoft/WindowsApps/PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0/python.exe`, run with the permitted escalation because the sandbox shim cannot execute it. Existing Windows PowerShell and Git Bash launch the installed tracer; no dependency installation occurred.

| Command/scenario | Tested input | Observed result |
|---|---|---|
| `python -m unittest discover -s tests -p test_codex_worktree.py -k installed_primary_shell_is_denied -v` | Before production, test committed as 86580ffd | **Expected behavioral RED**, 1 test / 8.599s, exit1: original newline != MUTATED after successful installation/dispatch. |
| `python -m unittest discover -s tests -p test_codex_worktree.py -k runtime -v` | Final source/test working-tree bytes committed unchanged as 67b32b2 | **PASS**, 19 tests / 121.507s, no skips. Includes real session selection, active workers, adopted phases, structured targets, policy/trust/setup refusals and bounded simulated native RPC transport. |
| `python -m unittest discover -s tests -p test_prewrite.py -v` | Existing unmodified prewrite inputs at spawn base; A does not modify them | **PASS**, 24 tests / 37.911s, one pre-existing symlink privilege skip (WinError1314). Hardlink and Windows junction controls pass. |
| Same retained installed-primary-shell command | Committed runtime source 67b32b2 | **Expected pending-B RED**, 1 test / 8.442s, exit1; same named source-sentinel assertion original newline != MUTATED. No skip/xfail or assertion weakening. |
| `git diff --check` and staged diff check | Exact owned implementation files | PASS, no whitespace/conflict diagnostics. |

The source-changing feature's initial genuine test-only RED is retained. The installed suite is deliberately not reported GREEN at A. Native RPC responses, launch spying and simulated B dependency files in direct tests are fixtures, explicitly **SIMULATED native**; they prove no actual native model startup, host movement or CW-05 outcome.

## TDD Evidence

- Before production, installation and generated Bash-handler dispatch succeeded. The test then executed an ordinary quoted Python writer through actual Git Bash. Its named assertion failed: `installed primary Bash mutation proceeded after successful setup`, expected `original\n`, actual `MUTATED`. That test-only commit is 86580ffd; the retained tracer method is unchanged in 67b32b2.
- Two early tracer attempts were excluded: redirection was already denied by the existing destructive guard (unexpected GREEN), and pwsh quoting produced setup exit127. The final retained tracer uses the repository's established Windows PowerShell launcher and a literal Python writer. Neither excluded attempt is claimed as RED.
- The compatibility supplement was independently approved at coordinator revision `43fb243618d6e0613b9256e2e72448875b3b4b1c`. Before its source fix, `test_runtime_active_wave_workers_remain_usable_with_accumulated_commits` failed its intended assertion after successful worktrees.create (1 test / 1.939s); `test_runtime_adopted_named_phase_at_non_generated_path_remains_usable` likewise failed after successful adopt_session (1 / 1.611s). These RED observations concern the session-only **working-tree implementation on top of 86580ffd**, not an invented immutable module revision.
- Targeted compatibility GREEN followed (active worker 1 / 5.499s; adopted phase 1 / 7.277s), then the final 19-case runtime GREEN covered expanded negative controls.
- Refactoring stayed inside the new module: shared receipt validation and bounded metadata reading. No unrelated refactor or helper change.

## Files Created/Modified

- `.ai/runtime/lib/codex_worktree.py` — public producer APIs, policy/trust preflight, exact session/wave validation and supported-tool decisions.
- `.ai/hooks/codex-worktree.py` — thin synchronous adapter, normalizing import/unexpected failures to stderr and exit2.
- `tests/test_codex_worktree.py` — unchanged retained installed tracer plus 19 direct runtime tests.
- `docs/maintenance/issue87-auto-worktree/CODEX-RUNTIME-SUMMARY.md` — this handoff.

## Decisions Made

Followed the approved policy correction PC-06-codex-context_compliance-01 and compatibility correction PC-06-codex-worker-compatibility-01. No new schema, trust key, adoption route or public helper contract was invented. The compatibility gap was returned to the coordinator, implementation paused, and only resumed after independent plan approval.

## Deviations from Plan

No changes outside the original Task6A ownership and the checked compatibility supplement. Initial session-only name/path assumptions were corrected before the production commit. The required installed regression intentionally remains pending B under the approved A→B→C order.

## Issues Encountered

The first direct pass exposed a phase fixture without a ROADMAP entry and an inadequate unit binding assumption; those were corrected before final GREEN. Existing adopted phase paths and runtime worker manifests required the checked supplement described above. No missing public helper interface remains.

## Auth Gates and User Setup Required

No authentication/credential gate or external service setup occurred. Production startup requires an installed committed destination and the native supported review/trust process. It preserves configured restrictions; it does not ask for policy relaxation. Source Task6A has not installed or trusted real-user hooks.

## Threat Outcomes

All remain open/unresolved at this component boundary; issue lifecycle readback and serialized reconciliation belong to the coordinator. No threat is declared closed.

| Owning PLAN / ID | Canonical issue | Outcome / Git state | Evidence |
|---|---|---|---|
| CODEX-PLAN.md / T-AW-01 | [issue98 target-confinement](https://github.com/Tasaddar12/ai-engineering-template/issues/98#t-aw-01) | Runtime mitigation tested; unresolved, provider readback pending | 67b32b2 structured/note/root controls and primary/index preservation; B generated-native proof and host limits remain. |
| CODEX-PLAN.md / T-AW-02 | [issue98 unit-identity](https://github.com/Tasaddar12/ai-engineering-template/issues/98#t-aw-02) | Runtime mitigation tested; unresolved, provider readback pending | 67b32b2 session/wave/adopted-phase identity and negative matrix under checked compatibility supplement. |
| CODEX-PLAN.md / T-AW-03 | [issue98 host-transition-proof](https://github.com/Tasaddar12/ai-engineering-template/issues/98#t-aw-03) | Simulated preflight tested; unresolved, actual-native evidence pending B | 67b32b2 native trust/config schema fixtures and zero model-spy calls on unsafe policy/setup; no trust bypass or sandbox/approval override. |

No security surface outside the approved threat model/supplement was introduced. Production has no prompt/transcript persistence. The host can still fail open after later hook/config/process changes; SessionStart is not assumed to have hard-stop semantics. Preflight owns the before-model guarantee, and synchronous PreToolUse exit2 owns supported-tool refusal. Opaque shell/MCP writers, unhooked transports and native sandbox scope remain external limits; no complete security-boundary claim is made.

## Interface and Next Phase Readiness

- B imports `lib.codex_worktree.launcher_main` through the adjacent installed runtime. CLI: `phase|quick LABEL [--base COMMIT] [--prompt TEXT] [--exec]`; no arbitrary native trailing argv. For a flag-only prompt, use launcher `--prompt=--literal-flag`. Native prompt is a single positional element after `--` in both interactive and exec routes.
- Generated guard definitions must use existing Python/runpy launcher strings exposed by `guard_commands()`, PreToolUse matcher `*`, SessionStart/UserPromptSubmit with no matcher, command type, timeout30, synchronous behavior. Native metadata must match the OS-selected command, project source, exact .codex/config.toml, enabled state and trusted/managed native status. A does not fake native hashes or use bypass as trust.
- Required `.codex` files are config.toml, codex-worktree.py, hooks/codex-worktree.py, runtime/phase.py and required runtime libraries; all discovered runtime Python modules must be committed and unchanged. Missing destination installation is a preserved dependency, never copy/sync authority.
- config/read for caller and destination requires matching workspace-write and schema-valid full approval/reviewer/root/network/temp settings. Null sandbox-workspace/reviewer values are retained as reported; sandbox mode or approval policy cannot be null. Snapshot drift refuses. No policy values are returned as native overrides. User models/effort and features.hooks=false remain byte-preserved.
- B must rerun the **same retained installed tracer** to GREEN and exercise the generated guard's valid active-worker/adopted-phase allowance plus invalid ownership refusals. B owns actual local-provider/native shell AND patch denial and positive destination/default-root proof. Its positive native fixture must include one flag-looking literal prompt after native `--`, capture it as literal outgoing input and confirm unchanged policy/trust options. A's argv spies do not establish actual native parsing/model evidence.

## Remaining / Coordinator Reconciliation

| Operation | Supplied result / next action |
|---|---|
| Advance position / progress | Task6A source component complete; Task6 remains pending B→C and fresh integration/verification. Do not advance adoption skeleton records. |
| Metrics | Immutable base, source head, measured diff scale and actual checks above; three commits including summary. |
| Decisions | Reuse approved policy and compatibility corrections; no new human decision requested. |
| Session continuity | Integrate owned commits after fresh source review; then dispatch B with this producer packet. |
| Roadmap / requirements | No .planning update; ISSUE87 and full CW outcomes remain incomplete. |
| Blockers | Installed tracer remains named RED pending B's generated registration. CW-05 actual-native proof, required C docs, joined checks, independent code/doc/integration review and verifier reconciliation remain. |
| Risk tracking | Coordinator reconciles existing issue98 keys and readback; preserve original AW live-native/human_needed outcomes, six frozen drafts and separate PR99 routing. |

## Known Stubs

None in production. Direct-runtime tests deliberately simulate native responses/invocation and the future thin installed entry point; they are labeled fixtures and do not substitute for B's generated/native receipts.

## Self-Check: PASSED

Owned source files and this summary exist. Both named implementation/test commits exist on the pinned branch; the implementation commit contains no deletions. Final summary commit/readback is returned separately. No shared planning/status/provider/helper files were edited, and no unowned generated artifact is retained in the worktree.
