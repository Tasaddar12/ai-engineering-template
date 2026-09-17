# Shared mutable state coupling

> Use with the phase-preparer dependency analysis and phase-checker review.

### The rule

`files_modified`/`files_deleted` overlap is not the only coupling between
same-wave plans. If two plans in the same wave touch the same **mutable
resource** through their task actions — a config key, DB table/row, migration,
env var, singleton, cache — with at least one writer, or one plan produces a
prerequisite the other consumes, the pair is coupled through shared state even
though no file overlaps: under parallel execution the outcome depends on which
executor gets there first.

Resolve it one of three ways, in order of preference:

1. **Declare the edge** — add the producing plan to the consumer's
   `depends_on`. The scheduler waits for that prerequisite to integrate and pass checks.
2. **Declare shared resources** — name the same exclusive resource in both
   plans' `resources` lists when either ordering is valid but concurrent use is not.
3. **Justify the pair** — when the coupling is deliberate and genuinely
   order-independent (both orders produce a correct result), record it in
   either plan's frontmatter, one `"plan-id: reason"` entry per coupled peer:

   ```yaml
   coupling_justified: ["03-02: both plans append independent keys to config; order irrelevant"]
   ```

   This is review explanation, not a runtime exemption. Declared shared paths
   and resources still serialize; wave numbers alone do not enforce ordering.

### Why declare it up front

Dimension 3b flags same-wave plan pairs with an undeclared shared-mutable-state
dependency (advisory severity — it never blocks). Declaring the edge, shared resource,
or justifying the pair at plan time means the first checker pass comes back
clean instead of surfacing an advisory the planner then has to interpret.
