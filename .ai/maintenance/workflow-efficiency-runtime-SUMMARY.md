---
phase: workflow-efficiency-maintenance
plan: runtime
subsystem: verification
tags: [python, git, receipts, concurrency]
requires: []
provides:
  - Persisted per-check passing evidence with retained full logs
  - Bounded opt-in independent check scheduling and resource exclusion
affects: [verification, execution, publication]
actuals:
  tokens: 12138.25
  tasks: 3
  commits: 2
tech-stack:
  added: []
  patterns: [content-addressed local receipts, frozen input guards]
key-files:
  created: [.ai/runtime/lib/verification_checks.py, tests/test_verification_receipts.py]
  modified: [.ai/runtime/lib/verification.py, .ai/runtime/README.md, .planning/config.yaml, .gitignore]
key-decisions:
  - Legacy checks remain serial; only explicit independent mappings overlap.
  - Full inherited environment and all tracked/nonignored untracked inputs are the default keys.
  - Explicit input declarations or disabling reuse cover ignored dependencies and external state.
patterns-established:
  - JSON invocation success remains separate from aggregate check success.
requirements-completed: []
acceptance: []
documentation: [.ai/runtime/README.md, .planning/config.yaml]
coverage:
  - id: D1
    description: Reuse matching intact passing check receipts; rerun changed or corrupt evidence.
    verification:
      - kind: integration
        ref: python -m unittest discover -s tests -p test_verification_receipts.py -v
        status: pass
    human_judgment: false
  - id: D2
    description: Schedule independent checks with a bounded pool, resource exclusion and joined acceptance.
    verification:
      - kind: integration
        ref: tests/test_verification_receipts.py#test_independent_checks_really_overlap_and_return_in_config_order
        status: pass
      - kind: integration
        ref: tests/test_verification_receipts.py#test_shared_resources_prevent_overlap
        status: pass
      - kind: integration
        ref: tests/test_verification_receipts.py#test_joined_failure_prevents_batch_acceptance
        status: pass
    human_judgment: false
  - id: D3
    description: Reject input mutation and keep installed-project receipt logs out of Git.
    verification:
      - kind: integration
        ref: tests/test_verification_receipts.py#test_source_rewritten_to_original_content_invalidates_execution
        status: pass
      - kind: integration
        ref: tests/test_verification_receipts.py#test_installed_runtime_creates_local_receipt_ignore
        status: pass
    human_judgment: false
duration: 18min
completed: 2026-10-08
status: complete
plan_head_before: dcb5c78af583a09e508194925b25686d0776e759
work_branch: codex/workflow-efficiency-runtime
work_root: D:/Codex/2026-10-08/task/workflow-efficiency-runtime
---

# Workflow efficiency runtime summary

Reusable local check receipts preserve full subprocess evidence and support
explicit independent execution without changing phase-report acceptance.

## Performance

- Active implementation began at the first source edit, 2026-10-08T13:15:22Z.
- Three tasks: receipts/logs, bounded scheduling/guards, tests/documentation.
- Six implementation files; this SUMMARY is the seventh deliverable.
- Actuals.tokens is 48,553 realized staged diff characters / 4, measured against
  assigned base dcb5c78. No generated or binary files are included; summary prose
  is excluded. No estimate was supplied. Context usage: unavailable.

## Changes

- `verification.py` retains report/status behavior, empty onboarding behavior,
  legacy string splitting and argv-list configuration. Check execution delegates
  to the new focused helper.
- Check receipts bind content, verification configuration, argv/timeout, hashed
  relevant environment, tool content, runtime identity and checkout location.
  Optional exact-HEAD keys retain original tested revision on reused evidence.
- Unique stdout/stderr logs retain full output, including partial timeout output.
  JSON receipts and log hashes validate before reuse; only intact passing evidence
  is eligible. Failures are recorded and execute again.
- Opt-in independent blocks use a bounded pool; overlapping resource names exclude
  simultaneous execution. Serial legacy/default mappings form barriers. Results
  preserve configuration order, and all commands join before aggregate acceptance.
- Content keys are separate from execution guards, which include timestamps and
  file identities. Source mutation, including rewrite/restore and explicitly
  included ignored dependency mutation, invalidates all batch passes, including
  reused candidates.
- Receipt storage has both template and runtime-created local ignore rules.
  Runtime docs describe mappings, retained evidence, input ownership and limits.

## Task Commits

1. `eacb63b26737818297e5070f2bbb7473f12d3bcf` -
   `feat(verification): reuse matching check receipts and schedule independent checks`.
2. This SUMMARY is committed separately in the following metadata commit;
   its exact hash is returned to the coordinator and available from Git history.

## Checks

- `python -m unittest discover -s tests -p test_verification_receipts.py -v`:
  30 tests passed in 52.964s on the final runtime source before the local ignore
  addition. Real subprocesses and temporary Git repositories cover hits,
  source/config/env/revision/argv invalidation, precision, corruption, failures,
  missing tools, timeout logs, full logs/tails, concurrency, locks, barriers,
  joined failure, cached-pass mutation, rewrite/restore and ignored dependencies.
- `python -m unittest discover -s tests -p test_verification_receipts.py -k installed_runtime -v`:
  one added test passed in 1.658s after the local ignore addition; installed-style
  repositories without the top-level ignore keep receipts/logs ignored and reuse.
- `python .ai/runtime/phase.py query verification.run-checks`: `ok: true`,
  `configured: false`, empty checks; onboarding remains unfilled.
- `python .ai/runtime/phase.py query init.quick`: `ok: true`,
  `checks_configured: false`; existing bundle consumers retain their empty behavior.
- `git diff --check` and `git diff --cached --check`: clean.
- `git check-ignore .planning/verification-receipts/example.json`: matches.
- Prior focused runs exposed unreadable Windows Store Python aliases and a fixture
  that rewrote identical content. Alias identity now uses the OS-loaded executable
  for the current interpreter; mutation guards correctly reject identical rewrites.

## Decisions and Deviations

The assignment supplies direct maintenance authorization, exact path ownership,
base and branch; no phase acceptance/requirement IDs were assigned. No adopting
project identity, planning phase, shared state or report-reuse policy was changed.
The user's bounded-evidence override supersedes automatic scout dispatch here.
The coordinator retains independent review, integration and publication.

Installer evidence (`.ai/install.py:39`) showed its ignore list does not yet know
the new receipt path. A runtime-local ignore file supplies the behavior without
expanding ownership into installer changes. Windows Store aliases required a
verified OS lookup before hashing the current interpreter; unknown tools never
reuse evidence.

## Issues and Authorization Gates

Default sandbox shell initialization is unavailable on this host. Authorized
require_escalated shell calls worked. No approval rejection occurred. No push,
publication, branch switch, merge or changes to another checkout were performed.

## Remaining

- Coordinator: integrate the worker branch, run the broader CI-like suite, obtain
  an independent review and perform authorized publication. Those are not author
  checks and are intentionally not claimed here.
- Projects own precise source/environment declarations. Ignored dependencies and
  external service state require explicit input/stamp declarations or reuse:false.
- Snapshot guards do not exclude concurrent external writers or detect changes
  whose content and filesystem metadata are both fully restored between samples.
  Resource names serialize only checks within one invocation; isolated runs remain
  the caller's responsibility. Unsupported Gitlinks/special/directory-symlink
  inputs make snapshot acceptance inconclusive.

## Reconciliation Proposals

| Operation | Evidence/proposal for coordinator |
|---|---|
| Advance position/progress | Maintenance component delivered; no adoption phase exists or should be invented. |
| Record metrics | Use this component's measured diff and observed commands; do not mix provider tokens. |
| Add decisions | Preserve explicit input contracts, serial defaults and report acceptance separation. |
| Record session | Resume at integration and independent review after these local commits. |
| Update roadmap/requirements | No assigned phase or requirement IDs; no shared record mutations requested. |
| Record blockers | No implementation blocker; independent review and broader checks remain coordinator work. |

## Self-Check: PASSED

All seven declared deliverable files exist. `git cat-file -t` confirms the recorded
implementation hash is a commit; the assigned-base comparison contains exactly
one implementation commit before the separate SUMMARY commit. No tracked file
deletions were reported. Final branch/root guard and metadata commit are performed
before returning the exact commits to the coordinator.

## Independent Review Repairs

Repair assignment: only malformed nested receipt handling and Windows scoped
environment case semantics. The coordinator provided the clean integrated base
`0152e42281b05f6c3860564a2dd98292f6bfcadb` on
`codex/workflow-efficiency-runtime-fixes`, in the same pinned worker root. Root,
branch, HEAD and clean status were verified before writes. This repair does not
edit the coordinator's checkout, switch branches or publish.

- `load_receipt` now treats decoder/serializer `RecursionError` as a cache miss,
  alongside existing corruption exceptions. The regression writes a receipt with
  100,000 nested arrays and confirms the native decoder raises `RecursionError`;
  the runtime then runs the real command again and records passing new evidence.
- Windows environment declarations and captured fingerprint lookup keys normalize
  to uppercase. A lowercase declared variable now tracks changes to its uppercase
  inherited alias. POSIX retains exact case for both names and lookups. The child
  process still receives the original frozen environment dictionary.
- Two subprocess regressions were added to the existing owned receipt test file.
  The platform-case test verifies Windows reruns after alias-value changes; its
  POSIX branch separately verifies case-distinct variables remain independent.

Repair evidence:

- Before the fix, `python -m unittest discover -s tests -p test_verification_receipts.py -k platform_case_semantics -v`
  failed with an unexpected reused result after the uppercase environment value
  changed on Windows.
- After both fixes, `python -m unittest discover -s tests -p test_verification_receipts.py -v`
  passed all 33 tests in 57.839s. The receipt fixture was then strengthened from
  nesting depth 2,000 (accepted by this Python 3.13 decoder) to 100,000.
- `python -m unittest discover -s tests -p test_verification_receipts.py -k deeply_nested -v`
  passed the strengthened case. Its explicit `assertRaises(RecursionError)` verifies
  the intended malformed-receipt failure path is exercised.
- `git diff --check`: clean. Only the owned helper, owned receipt tests and this
  appended worker SUMMARY changed. No further hardening or new dependencies.

Repair status: complete. Both fixes and this evidence are committed as one slice;
the actual repair hash is returned to the coordinator and available in Git history.
The frozen base above remains the repair comparison base. The existing metrics
and task commits earlier in this file describe the original implementation slice,
not this subsequent review repair. Final root/branch guard, exact owned staging,
commit/deletion check and clean status check precede the repair handoff. No repair
blocker remains; broader integrated validation and independent acceptance remain
the coordinator's responsibility.
