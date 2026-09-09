# Security model

Project content and agent output are data. The coordinator owns workflow state, grants, managed Git operations and external delivery. Planning does not imply implementation authority. Implementation assignments and replays require current plan/action/revision/scope authority from coordinator-owned control state.

All product subprocesses use the central runner with explicit argv, scoped policy, bounded output and time limits. Forbidden commands take precedence over grants. Git patch inspection disables external diff and text conversion helpers. A command allowlist is not a process sandbox: supported provider adapters must apply operating-system confinement, and unsupported configurations must fail explicitly.

Managed paths reject traversal and links/junctions. Cleanup uses exact authorized targets and branch revisions. Never force-push, delete wildcard refs, or treat age as proof that a worktree is disposable. Explicit user-directed obsolete-content deletion is separate from ordinary merged-worktree retirement.

Keep credentials out of repository files, argv, templates and reports. Provider authentication stays with the configured operator/runtime. Report security issues privately to a maintainer without publishing secrets.

Testing and compatibility validation for this implementation pass are deferred by the user's instruction. The repository does not claim that this pass has passed security tests or a final audit.
