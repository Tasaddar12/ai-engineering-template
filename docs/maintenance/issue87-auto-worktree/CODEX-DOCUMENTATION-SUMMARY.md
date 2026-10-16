---
phase: maintenance-issue87-auto-worktree
plan: "06-codex-C"
status: blocked
requirements-completed: []
acceptance: []
documentation:
  - .ai/references/same-agent-worktree.md
  - .ai/references/worktree-sessions.md
  - .ai/hooks/README.md
  - .ai/runtime/README.md
  - .ai/RULES.md
  - .ai/workflows/quick.md
  - .ai/workflows/discuss-phase.md
  - .ai/workflows/plan-phase.md
  - .ai/workflows/execute-phase.md
  - .ai/workflows/verify-work.md
  - .ai/workflows/ship.md
issue_refs:
  - id: ISSUE98
    summary: Preserve canonical source-confinement, unit-identity and host-transition risk tracking; all remain unresolved pending joined verification and provider readback.
    variant: Security risk
    state: unresolved
    relationship: followup
    issueRepo: Tasaddar12/ai-engineering-template
    issueURL: https://github.com/Tasaddar12/ai-engineering-template/issues/98
    issueNumber: 98
input_revision: 804afd78daf9d91218c31efa2457db6a8fe2965b
branch: phase-issue87-codex-docs-124641
worktree: D:/Codex/2026-10-15/task-2/repo/.worktrees/issue87-codex-docs-124641
changed_paths:
  - .ai/references/same-agent-worktree.md
  - .ai/references/worktree-sessions.md
  - .ai/hooks/README.md
  - .ai/runtime/README.md
  - .ai/RULES.md
  - .ai/workflows/quick.md
  - .ai/workflows/discuss-phase.md
  - .ai/workflows/plan-phase.md
  - .ai/workflows/execute-phase.md
  - .ai/workflows/verify-work.md
  - .ai/workflows/ship.md
  - docs/maintenance/issue87-auto-worktree/CODEX-DOCUMENTATION-SUMMARY.md
---

# Task 6C documentation continuation

The eleven assigned guides now describe the committed Codex phase/quick startup
contract and point to one canonical protocol. The continuation remains blocked:
this was static documentation work, and the required runtime/native acceptance
is still unverified.

## Source evidence and documentation coverage

Claims were checked against the committed source and producer summaries at input
revision `804afd78daf9d91218c31efa2457db6a8fe2965b`. `.ai/install.py` maps the
Codex launcher asset to `.codex/codex-worktree.py`; the asset imports
`lib.codex_worktree.launcher_main`. `.ai/runtime/lib/codex_worktree.py` defines
the `phase|quick LABEL [--base] [--prompt] [--exec]` interface, native argv
separation, direct executable requirement, `.bat`/`.cmd` refusal, registered
installation/hook checks, policy preservation/refusal, and synchronous source
decisions. `CODEX-RUNTIME-SUMMARY.md`, `CODEX-INSTALL-SUMMARY.md`,
`CODEX-REVIEW-02.md` and `CODEX-PLAN-REVIEW-04.md` were used only as receipts for
historical/static boundaries, never as current runtime evidence.

| Document | Claim and evidence | Current boundary |
|---|---|---|
| `.ai/references/same-agent-worktree.md` | Canonical new-run launcher, args, literal flag-looking prompt form, native `--cd`/`--enable hooks`, direct executable requirement, Windows batch-shim refusal, selected session and hook/policy checks. Source: installer asset and `launcher_main`, `validate_native_launcher`, `check_hooks`, `policy_snapshot`, and `validate_root` in `.ai/runtime/lib/codex_worktree.py`. | Examples are NOT_RUN. No claim of active-agent movement, live host transition, effective-feature behavior, or generated-adapter shell/patch acceptance. |
| `.ai/references/worktree-sessions.md` | Separates Claude native entry from Codex new-run startup and points to the canonical section. | Existing Claude native-entry/fresh-read contract remains; no Codex movement claim. |
| `.ai/hooks/README.md` | Documents synchronous Codex `PreToolUse` (`*`), `SessionStart`, `UserPromptSubmit`, note lifecycle allowance and source enforcement boundary. Source: `.ai/install.py` `HOST_HOOKS` and `.ai/runtime/lib/codex_worktree.py::hook_decision`. | Registration/trust and host execution are not established by source inspection. |
| `.ai/runtime/README.md` | Describes validated phase/quick startup and links to the canonical protocol. | No Python, import, runtime or native command was run. |
| `.ai/RULES.md` | Distinguishes new Codex startup from Claude same-caller native movement and points to the source contract. | Established root, worker, adopted-session and safety rules remain in force. |
| `.ai/workflows/quick.md` | Adds a short launcher pointer for a new quick Codex run. | The ordinary workflow and active-agent checks still apply. |
| `.ai/workflows/discuss-phase.md` | Adds a short launcher pointer for a new phase Codex run. | Does not assert movement or waive normal session resolution. |
| `.ai/workflows/plan-phase.md` | Adds a short launcher pointer for a new phase Codex run. | Does not assert movement or waive normal session resolution. |
| `.ai/workflows/execute-phase.md` | Adds a short launcher pointer for a new phase Codex run. | Does not assert movement or waive normal session resolution. |
| `.ai/workflows/verify-work.md` | Adds a short launcher pointer for a new phase Codex run. | Does not assert movement or waive normal session resolution. |
| `.ai/workflows/ship.md` | Adds a short launcher pointer and retains validated-session and delivery gates. | Does not assert movement or waive ship verification/merge gates. |

## Verification and remaining gaps

- Static source and documentation inspection only. `git diff --check` passed
  with exit 0 before the documentation commit; this checks whitespace and
  conflict markers only.
- All Python commands, imports, validators, tests, model queries, native CLI,
  generated hook/launcher execution, probes and harnesses were **NOT_RUN**.
  The five B export-inspection cases are written but also **NOT_RUN**.
- The original AW live/human-needed obligations remain open. CW-05 generated
  native shell **and** patch denial remains **BLOCKED / UNVERIFIED**. The
  effective-feature/managed-policy question remains unresolved. Transport and
  opaque-writer limits remain documented; no controller, child, or movement
  success is claimed.
- `tests/test_same_agent_worktree.py` was not edited or run. At this input
  revision, `tests/test_destructive_guard.py:46` had a known outside-ownership
  static compatibility concern because its regex-only matcher may not accept
  the native literal `*`. The coordinator has since routed a separate narrow
  static test-only fix; this summary does not assess that later change or claim
  CI green.
- ISSUE98 remains the unresolved canonical follow-up: `source-prewrite/target-confinement`
  (T-AW-01), `source-prewrite/unit-identity` (T-AW-02), and
  `source-prewrite/host-transition-proof` (T-AW-03). Installation wiring and
  documentation do not close these risks; provider reconciliation/readback is
  coordinator-owned.

No requirement or acceptance item is completed. Issue87 remains open, PR97 is
incomplete, and the overall task remains incomplete pending joined verification
and required human evidence.
