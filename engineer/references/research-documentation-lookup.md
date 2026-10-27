# Research documentation lookup

1. Read the project's manifest, lockfile, runtime version and existing integration before recommending an API or dependency. Name the exact installed version and relevant constraints.
2. Use available connected documentation tools when they can provide authoritative version-matched content. Otherwise browse official project documentation or primary source repositories. A missing tool does not justify skipping research.
3. Prefer the matching version's API reference, migration guide, source and executable examples. Compare a proposed call with current project usage. Distinguish unsupported assumptions from confirmed contracts.
4. Record the URL or source path, version/commit, lookup date and the concrete claim it supports. Do not invent a source or treat an uncited search snippet as validation.
5. Validate a proposed technology choice with an actual relevant check before recommending it. If checks are deferred by the user, mark the recommendation unvalidated and preserve that ordering.
6. Report missing capabilities and continue independent research. Do not install a global CLI, start a documentation service or download executable packages without authorization.

Good evidence: the locked dependency version, its official API section and a bounded experiment demonstrating the required behavior.
Bad evidence: a remembered API, an unrelated current-version example or a command that silently downloads a new tool.
