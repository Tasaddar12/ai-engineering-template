# Architecture decisions

Accepted foundation decisions are below. These are engineering choices for v1, reversible through new ADRs. They are not claims that the runtime is implemented.

- ADR-001: flat local Python tools and JSON contracts.
- ADR-002: plan-local lifecycle bundles, single coordinator and retained state branch.
- ADR-003: repository-local task worktrees and serialized plan integration.
- ADR-004: independent capability-enforced reviews and bounded recovery.
- ADR-005: versioned owned assets and provider-neutral ports.

Decision prose and its index live together in `.ai/decisions/`. Installed projects use the same location for their own decisions. A record references one canonical document; superseded text is preserved only in plan history with a manifest.
