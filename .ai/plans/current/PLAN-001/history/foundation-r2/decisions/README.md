# Architecture decisions

Accepted foundation decisions are below. These are engineering choices for v1, reversible through new ADRs. They are not claims that the runtime is implemented.

- ADR-001: local-first Python package and JSON contracts.
- ADR-002: stable artifact paths, single coordinator and retained state branch.
- ADR-003: task worktrees and serialized plan integration.
- ADR-004: independent capability-enforced reviews and bounded recovery.
- ADR-005: versioned owned assets and provider-neutral ports.

For this central repository, ADR prose lives in `docs/decisions/`; `.ai/decisions/index.json` provides stable references. Installed projects default to `.ai/decisions/` for their own ADR prose. A record references one canonical document; never duplicate an ADR in both locations.
