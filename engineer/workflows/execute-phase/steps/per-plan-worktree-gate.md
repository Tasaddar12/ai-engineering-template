# Declared plan scope before isolated dispatch

Read the complete selected plan record from phase-plan-index. Preserve the exact `id`, `files_modified` array and separate `files_deleted` array as PLAN_ID, PLAN_FILES and PLAN_DELETIONS. Do not infer deletion permission from a modified path, parent directory, glob, or a worker's claimed intention. Preserve spaces and Unicode in each argument; do not flatten JSON arrays into an unquoted shell string.

For each path in both arrays, resolve its repository-relative ownership and compare it with actual submodule roots from .gitmodules and Git metadata. A path inside, equal to, or crossing a submodule root blocks that plan for a person; an unparseable scope in a submodule project also blocks it. Continue independent plans. Never remove isolation to get around the intersection.

Pass those same exact arrays to `worktree.create PLAN --phase N --files ... --deletions ...` or `worktree.record-agent PLAN --phase N --branch BRANCH --path PATH --files ... --deletions ...`. The coordinator captures the base once and records the actual worker identity. The runtime enforces the declaration again during merge and cleanup. No per-plan downgrade or forced-mode rewrite is permitted.
