---
phase: template-maintenance
plan: python-scripts-install
status: complete
subsystem: installation
tags: [python, installer, update, migration, windows]
requirements-completed: []
acceptance: []
documentation: []
issue_refs: []
plan_head_before: "7723b2d1ce2b0d698613639547c35e2b98688a70"
---

# Python installer maintenance summary

Python installation now exports the current source without a false JavaScript
refusal, preserves custom legacy assets in reviewed migration copies, and handles
Windows file modes and Unicode transaction metadata consistently.

## Assignment and authority

Authorized template maintenance delegated by the coordinator; no adopting-project
phase or planning records were modified. Assigned root:
`D:/Codex Projects/ai-engineering-template/.worktrees/scripts-install-194458998`.
Assigned branch: `phase-scripts-install-194458998`. Immutable starting revision:
`7723b2d1ce2b0d698613639547c35e2b98688a70`.

## Changes

- Track Markdown fence delimiters and shell language accurately. Closing a
  non-shell fence no longer turns following prose into executable shell input.
- Normalize requested Windows modes to the read-only attribute the filesystem
  retains; POSIX executable and permission modes remain unchanged.
- Emit CLI JSON as UTF-8 and read every transaction journal and ownership
  manifest as UTF-8, preserving non-ASCII paths across apply and rollback.
- Relocate recognized legacy directories first, then include remaining `.ai`
  custom files and binary assets, including user RULES and project rules. Exact
  original bytes remain in the source and transaction backups. No legacy source
  is deleted. Existing destination collisions keep reviewed conflict semantics.
- Add `tests/test_install_scripts.py` for the new `bin` entrypoints, distinct
  from the unchanged legacy `.ai/install.py` test contracts.

## Checks

- `python -m unittest discover -s tests -p test_install_scripts.py -v`: **8
  passed in 113.255 seconds**, Python 3.13 on Windows. This runs actual Git source
  installation, both installed host CLIs and runtime identity, no-hook exports,
  stable update previews, pinned updates after source HEAD advances, preservation
  of modified destination commands, refusal of stale review state and wrong
  review tokens, reviewed replacement and explicit rollback, migration copies
  and exact backup provenance for both hosts, and injected-write automatic
  rollback without leaving files or a false ownership manifest.
- `python -m py_compile bin/install.py bin/update.py bin/migrate.py
  bin/install_support.py tests/test_install_scripts.py`: **passed**.
- `git diff --check`: **passed**.
- Initial subprocess runs reproduced the false JavaScript gate, Windows mode
  drift, locale-encoded CLI JSON and Unicode rollback target mismatch; those
  failures drove the fixes and are covered by the passing final regression run.

## Deviations

No assigned acceptance IDs or estimate were supplied. The existing four legacy
installer suites target `.ai/install.py`; new-layout coverage therefore lives in
the expressly authorized `tests/test_install_scripts.py` instead of rewriting
their existing contracts.

## Remaining

- POSIX mode preservation was retained in code but not executed on this Windows
  worker. Combined validation and other operating systems remain coordinator
  verification work.
- A legacy `.ai/install.py` update suite was started before learning that the
  coordinator was running the full legacy baseline. It is still running at this
  slice boundary; no passing result is claimed for it.
- The installed runtime's unfiltered JSON output also uses Windows locale
  encoding. This lies in `engineer/bin/engineer.py`, outside this worker's owned
  paths, and has been reported to the coordinator. The installed runtime smoke
  test checks `runtime-identity --pick packageName --raw` with ASCII output.
- This worker does not publish or merge. The coordinator owns integration,
  combined validation and the PR stacked on #129.

## Security and stubs

No new network endpoints, authentication flows or storage formats were added.
Existing journaled file operations and path guards remain in force. No runtime
stubs or placeholder implementations were introduced.

## Reconciliation

No project-state, roadmap, requirement or decision updates are proposed for this
template-maintenance slice. Integrate the commit, rerun combined checks, and
publish through the coordinator-owned tracking PR.

Context usage: unavailable.

## Self-Check: PASSED

Assigned root and branch were checked before writes and staging. The three
changed files exist, their changes are owned by this assignment, and the final
subprocess regression run passed. Implementation and this summary are one slice;
the actual resulting commit ID is returned to the coordinator after commit.
