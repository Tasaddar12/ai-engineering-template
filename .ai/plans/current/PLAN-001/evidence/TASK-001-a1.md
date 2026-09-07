# TASK-001 attempt a1 disposition

| Field | Recorded value |
| --- | --- |
| Status | Interrupted and unaccepted |
| Branch | `ai/PLAN-001/TASK-001/a1` |
| Base | `d52d3c2dbb1b525843351cc697817e0a5e90ee29` |
| First candidate | `aafbcc87c3f6d58cd4ddda227fb19a35d5f45202` |
| Repair candidate | `f8a6f040fc48e8a237d412379322c5eed66d8cab` |
| Physical worktree | Removed through Git after clean tracked, untracked, and ignored-file checks |
| Retention | Both commits remain on the branch; no code was integrated |

The independent implementation review of the first candidate failed on four issues: mutable/incorrect evidence digest typing, scalar scope values splitting into characters, ambiguous exact-file versus directory/glob scope semantics, and incomplete Windows/Unicode alias handling. The repair candidate reported 14 tests, but its fresh reviewer stopped at a usage limit before any verdict. A later audit still found unhandled Windows reserved/device names and invalid characters. Neither candidate passed R1 or R2.

This attempt predates the flat `src/*.py` layout and cannot be treated as an accepted dependency or copied into the corrected graph. Any future implementation starts from a freshly isolation-approved graph and receives both new reviews.
