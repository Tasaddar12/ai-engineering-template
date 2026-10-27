# Planner Coupling — Same-Wave Shared Mutable State

Coupling review identifies producer/consumer dependencies and shared resources. Declare real `depends_on` edges and exact `resources`; scheduling belongs to the coordinator and no prose justification exempts overlap.

## The rule

`files_modified`/`files_deleted` overlap is not the only coupling between
same-wave plans. If two plans in the same wave touch the same **mutable
resource** through their task actions — a config key, DB table/row, migration,
env var, singleton, cache — with at least one writer, or one plan produces a
prerequisite the other consumes, the pair is coupled through shared state even
though no file overlaps: under parallel execution the outcome depends on which
executor gets there first.

Resolve it one of three ways, in order of preference:

1. **Declare the edge** — add the producing plan to the consumer's `depends_on` when the consumer needs its delivered contract.
2. **Declare shared resources** — use stable `resources` identities. The coordinator serializes these plans even when files differ; do not silently re-wave approved plans.
3. **Justify the pair** — when the coupling is deliberate and genuinely
   order-independent (both orders produce a correct result), record it in
   either plan's frontmatter, one `"plan-id: reason"` entry per coupled peer:

   ```yaml
   coupling_justified: ["03-02: both plans append independent keys to config; order irrelevant"]
   ```

A `coupling_justified` entry explains intentional coupling for reviewers. It does not exempt a dependency, exact file overlap or shared resource from serialized dispatch.

## Why declare it up front

Dimension 3b flags same-wave plan pairs with an undeclared shared-mutable-state
dependency (advisory severity — it never blocks). Declare the dependency and shared resources before dispatch so the coordinator can form safe groups. A justification remains review explanation; it does not exempt ownership or dependency rules.
