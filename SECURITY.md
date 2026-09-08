# Security model

The framework treats repository content, agent responses, logs and retrieved evidence as data. Project constraints control permitted commands, files, workflow transitions and external actions. All product subprocess execution passes through one Python command runner with explicit argv, contained working directories, timeouts and bounded/redacted evidence. Forbidden operations take precedence over grants.

Roles receive applicable constraints automatically. Implementation is limited to declared scope. Reviewers cannot modify source or approve their own implementation. Validation precedes critical review, and a PASS is bound to the reviewed revision before delivery. The single reviewer checks security only where relevant to changed code and affected surfaces.

A command-provider bridge runs trusted operator-configured software. The bridge must enforce the supplied role/tool permissions; the parent framework's policy cannot sandbox arbitrary actions performed internally by another process. Use an independently contained bridge for untrusted agents. No provider or credential access is enabled by default; never embed credentials in argv, artifacts or templates. Configured secret environment values are redacted from evidence; avoid producing secrets in command output.

Git worktree reality is inspected rather than inferred from records. Safe path checks reject traversal and links/junctions. Cleanup preserves unknown, active, dirty or locked worktrees and unmerged work unless explicitly superseded/abandoned with a retained branch. Never use force cleanup or age as evidence. External pushes, PR creation, merges, releases, deployments and paid usage require configured authority; forbidden operations cannot be granted.

Report vulnerabilities privately through a repository maintainer's established channel. Do not publish credentials in an issue or review artifact.
