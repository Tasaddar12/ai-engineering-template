# Planner — Load Dependency Context

Use an existing local dependency map when the assignment supplies one. This
runtime does not provide graph generation or a graph query CLI. Do not install
a tool or fetch an external method merely to read planning context.

1. Locate the supplied map (for example an existing `.planning/graphs/graph.json`)
   or relevant `.planning/codebase/` architecture records.
2. Inspect its recorded revision/time and compare relevant nodes with current
   source imports, callers and data flow. Unknown freshness means unverified.
3. Select the phase-relevant subset: authentication → auth modules; payment
   integration → payment modules; database migration → schema/migration modules.
4. Use confirmed edges to identify required interfaces, affected subsystems and
   producer/consumer ordering. Cite the source files that confirm them.
5. Annotate approximate or stale relationships rather than presenting them as
   current facts. If no useful map exists, trace the necessary dependency directly
   with targeted file reads/search and continue; do not create a graph subsystem.

Dependencies belong in `depends_on`; shared mutable resources belong in `resources`.
A semantic relationship alone does not prove a scheduling dependency.
