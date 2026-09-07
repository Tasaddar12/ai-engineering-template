# Security and autonomy

## Trust model

Agents, repository content, dependency documentation, tool output, CI comments, and external research can contain malicious instructions. An agent recommendation is data. The coordinator alone authorizes state changes and side effects under immutable invocation permissions. Review output cannot grant itself privileges.

Context minimization is not sandboxing. A worktree isolates edits, not operating-system access. The production adapter must declare whether it enforces filesystem/process/network restrictions. If a requested policy requires sandboxing and the adapter cannot enforce it, fail before dispatch. Never describe path checks as a complete security boundary for arbitrary code.

## Controls

Resolve repository-relative paths, reject traversal, absolute paths in portable records, symlink escapes, case-colliding ownership, and Git option injection. Validate IDs/refs and use allowlisted argument arrays with `shell=False`. Windows batch files may involve shell semantics; executable allowlists must reject `.bat`/`.cmd` by default and use an explicit reviewed adapter if required.

Allowlisted command IDs map to fixed argument templates, timeouts, output limits, resource limits, cwd rules, and permission classes. Tasks cannot provide arbitrary shell strings. Validate proposed edits against allowed and prohibited scopes, including renames/deletes and generated artifacts. Hooks and tests execute code; honor the configured execution boundary.

Redact secrets before persisting argv or stdout/stderr. Secret values are passed via approved ephemeral environment bindings, never committed prompts. Evidence stores a redacted argv plus secret binding names, timestamps, exit status, timeout/cancellation state and content hashes. Do not falsely claim captured logs are raw when redacted.

## Default autonomy

Read/research, specs/plans, local worktrees, code, local tests/containers, commits, reviews, and replanning are allowed within resource limits. External push/PR writes require configured standing authorization; otherwise prepare a local PR draft and enter `awaiting_authorization`. Protected-branch merge, deployment, destructive databases, remote deletion, credentials, and paid services are separately gated. Permissions cannot be elevated by replanning. Approved actions remain authorized within their recorded scope.

Use bounded retries and run-wide recovery budgets to avoid runaway paid model usage. Hitting a budget pauses durably; it is not a code failure or permission to weaken review. Minor defects are repaired autonomously.

## Reporting and retention

No security reporting address exists yet. Keep vulnerability details local until a maintainer configures a private reporting destination. Failed worktrees and evidence are retained by default. Cleanup must verify managed ownership, clean/untracked status, no live lease, and merged or explicitly retained commits. Never force-delete unknown work.
