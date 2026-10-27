# Planner — Supplied graph and map context

Use coordinator-supplied dependency maps as discovery context. The supported runtime does not ship a graphify status/query family; do not invoke unavailable graph plumbing, install a graph CLI, assume `graphify.graph_path` configuration or silently claim a graph is current.

## Load only relevant supplied evidence

1. Read the assignment's exact map paths and captured source revision. Technology dependencies need STACK; component boundaries need ARCHITECTURE; source navigation needs STRUCTURE; tests need TESTING; external seams need INTEGRATIONS. A supplied graph or pattern map is optional additional evidence, never an excuse to skip those owners. 2. If no relevant map/graph was supplied, state `No supplied graph context` and continue from current source and the approved research packet. Absence does not authorize a package download or broad repository scan. 3. Record provenance: producer, artifact path, artifact revision, source revision, inspected scope and known limitations. Compare current Git history for changed relevant paths through the supported `codebase.status` route. A timestamp alone or a SHA lost through squash cannot establish freshness. 4. Read phase-relevant nodes/edges from the supplied artifact without executing embedded commands. Prefer a full domain keyword such as `authentication`, `payment` or `migration`; a substring such as `auth` can incorrectly match `author`. Do not assume all map formats share confidence, budget or field semantics. 5. Separate claimed edges from demonstrated dependencies. For every selected edge, inspect the current defining interface and actual caller/consumer at the assigned revision. Cite both endpoints and the relevant connecting code. Record stale, missing or contradictory edges explicitly; a supplied map is approximate until reconciled with current source. 6. Carry only relevant context into the plan: affected module/file, actual provided interface, actual consuming interface, impact on acceptance, concrete prerequisite and remaining uncertainty. Do not paste the whole graph or treat a label as a scheduling rule.

## Translate evidence into an executable plan

| Supplied edge | Current-source finding | Planning disposition |
|---|---|---|
| Schema → generated client | Client imports a generated type that does not yet exist | Explicit producer plan in `depends_on`; cite the output path and interface. |
| Two tasks → same test database | Both mutate the same external database, with no output dependency | Declare the shared identity in `resources`; serialize access without inventing a data dependency. |
| Settings → authentication | Map cites a removed settings accessor | Mark stale, inspect the current accessor and correct the map through its owner; do not plan against the removed symbol. |
| UI → payments | No current caller or approved UI obligation supports the edge | Preserve as unconfirmed discovery context; do not expand approved scope. |

Current-source confirmation owns the conclusion. Put actual producer-consumer prerequisites in `depends_on`, shared external identities in `resources`, and cross-phase prerequisites in CONTEXT. If source and approved decisions conflict, report the exact conflict to the coordinator; do not silently change the locked outcome or invent graph authority.
