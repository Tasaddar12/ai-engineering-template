# Codebase maps

Maps describe the existing system. Phase research investigates a particular
change. Neither source overrides phase decisions or proves current behavior
without inspection.

## The two tracked maps

`ARCHITECTURE.md` and `STACK.md` are tracked by the runtime by those exact
names. Everything else here (`STRUCTURE.md`, `INTEGRATIONS.md`, `CONVENTIONS.md`,
`CONCERNS.md`) is written on demand for an area about to be researched or
changed.

## Freshness is computed, not claimed

Every map carries the revision it was written against:

```markdown
<!-- mapped_revision: 3f9a1c4e8b2d -->
<!-- mapped_at: 2026-09-22 -->
```

`codebase.stamp <MAP>.md` writes that stamp; `codebase.status` answers how many
commits have touched the map's sources since. A date alone says when somebody
looked, not whether the code has moved, which is how these drifted before.

| Map | Goes stale when | Because |
|-----|-----------------|---------|
| `STACK.md` | any manifest, lockfile, Dockerfile or CI workflow changes | a dependency change is a stack change |
| `ARCHITECTURE.md` | 15 commits have touched source since it was written | ordinary churn is not a changed architecture; sustained movement is |

Writes under `.planning/` never age a map: a phase write-up is not a change to
the architecture it describes. Both thresholds are configurable under
`codebase.staleness` in `.planning/config.yaml`.

`/plan-phase` regenerates a stale map before planning against it, and
`/progress` reports staleness. Rewrite a stale map against the current revision
rather than patching its text — a claim you have not re-checked is the thing
staleness was supposed to catch.

Name the inspected revision, relevant entry points, callers, test commands and
known limits. Link source areas rather than copying files.
