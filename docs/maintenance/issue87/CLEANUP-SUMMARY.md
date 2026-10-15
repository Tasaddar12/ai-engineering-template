---
phase: issue87-maintenance
plan: cleanup
status: in_progress
issue_refs:
  - https://github.com/Tasaddar12/ai-engineering-template/issues/87
input_revision: 4c35d27436add6867934c85eb9e853bd2fc3052e
requirements-completed: []
acceptance: [I87-A2, I87-A3]
documentation: []
---

# Cleanup implementation evidence

Assigned root: `repo/.worktrees/issue87-cleanup-145722566`.
Branch: `phase-issue87-cleanup`. Guard parent tip and own-change boundary start:
`4c35d27436add6867934c85eb9e853bd2fc3052e`.

## TDD Evidence

RED: `python -m unittest discover -s tests -p test_destructive_guard.py -k cleanup -v`.
Exit 1, Ran 8 tests in 5.956s, 14 failing assertions, no errors or skips.
`test_cleanup_preview_is_readonly_and_lists_distinct_operations` expected explicit
worktree_remove and branch_delete rows; the existing hook instead returned its
normal malformed-payload refusal (no cleanup mode/schema). Apply/approval tests
likewise failed on the missing snapshot assertion, before attempting mutation.
Source and installed CLI test expected exit 0 but observed exit 2. Earlier first
run had two KeyErrors in assertion fallback; those were corrected before this
valid RED observation. Production source remains unchanged at this slice.

Fixtures are temporary Git repositories with offline GitHub/GitLab evidence.
No actual project cleanup, install, push, publication or merge ran.
RED commit: `c488678f5c75663b040cfd7e7aafa2f66a2f2921`.

Interim GREEN (uncommitted implementation): full destructive-guard suite passed
21 tests in 95.807s; actual registered installed-host hook test passed 1 test in
25.942s; advisory guard passed 60 checks. No skips. A final boundary inspection
found raw registered junction paths could be hidden by the parent's canonical
listing. Added cleanup-only regression before repair:
`python -m unittest discover -s tests -p test_destructive_guard.py -k raw_registered -v`
initially exited 1, Ran 1 test in 1.160s, `EvidenceError not raised`. Inspection
showed Git canonicalizes aliases during worktree add: that fixture did not
establish the intended raw-registration boundary. The first attempted repair's
22-test run therefore still failed that one assertion (102.019s). This is not
accepted as valid boundary RED/GREEN evidence.

Corrected fixture: move the already registered temporary directory within its
verified temporary root, then replace its original path with an actual Windows
junction. Remove the attempted raw-reader override and rerun the same focused
command before restoring it: exit 1, Ran 1 test in 1.083s, intended
`EvidenceError not raised` assertion. Parent grammar/ownership readers unchanged.
Final repair/GREEN evidence pending.

## Threat Outcomes

I87-C-T1 and I87-C-T2 mitigations pending implementation. Canonical issue identity
and independent review belong to the coordinator.
