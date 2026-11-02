# PR 125 integration

User authorization: integrate PR 129 into PR 125, remove obsolete .ai/.planning,
validate the installer and scripts, then merge PR 125 to main after checks/review.

Repository: Tasaddar12/ai-engineering-template. PR 129 head was
234c9816d27f2e8612253ece7115c66c4de4347c; integration merge is
8e7b56b3cec9563a0361d317f0836f05f0f6c770. No Graphalyx worktree or service was changed.

The retired .ai executable tree and .planning adoption skeleton are removed.
The issue, pull-request and ADR templates and Git workflow reference move into
the canonical engineer tree. Historical attribution moves to the root notice.
PLANNED-UPDATES and Git history retain maintenance requirements and records.
Dedicated old-runtime tests are retired; issue-schema behavior is ported to the
current runtime. Missing issue-template schemas fail closed.

Current catalogs are populated; stale imports and navigation are reconciled.
CI now checks the current Python sources on Ubuntu and Windows, retaining the
required validate context. No old shell hook suite is called after its removal.

Slice checks: 17 issue-schema tests passed; 151 tracked Python files compiled;
13 executable --help entrypoints returned zero; Markdown runtime scan passed.
Final source-link check, installer integration, full cross-platform tests and
independent review remain pending at this slice.

Source code-fixer method is unchanged from PR 129. Deferred overhaul branches
are excluded. Exact upstream revision of the historical downloaded source was
not recorded; THIRD-PARTY-NOTICES retains that uncertainty explicitly.
