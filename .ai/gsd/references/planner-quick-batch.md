# Quick-Batch Mode — Planner Reference

Triggered when `<planning_context>` declares `**Mode:** quick-batch`
(#3676, epic #3344, ADR-1239 "Quick-batch binding"). One dispatch = one
item's plan — the SAME single-plan, 1-3-task scope as `/gsd:quick`'s own
`quick`/`quick-full` modes, with one fixed difference: **`depends_on` and
`files_modified` frontmatter are ALWAYS required, regardless of whether
`--validate` was requested.** This reuses the EXISTING frontmatter grammar
(the same keys full phase planning already emits — see the frontmatter
schema table above); it is not a new schema.

**Why always, not gated on `--validate`.** The coordinating workflow
(`.ai/gsd/workflows/quick-batch.md`) recomputes every item's execution wave
from these two fields after each DAG layer's planners return (`quick-batch
update`, wrapping `updateBatchItems`) — without them, every item stays in
wave 0 forever and the batch cannot parallelize independent items or
sequence dependent ones correctly. This is load-bearing dispatch input, not
an optional quality signal.

### `depends_on` — reference SIBLING items by `quick_id`, never invent one

The `<planning_context>` you receive includes a **full batch task catalog** —
every item's `quick_id` + description, not just your own. When your item's
implementation genuinely requires another item's item to land first (shared
file, prerequisite API, sequencing the user implied), declare it:

```yaml
depends_on: ["260101-abc"]   # a quick_id from the task catalog
```

- Reference ONLY `quick_id`s from the task catalog you were given. Never
  reference a plan id from a phase, another batch, or a value you invented.
- Empty array (`depends_on: []`) is the correct, common answer when your item
  is genuinely independent — do not manufacture a dependency to seem
  thorough.
- A dependency on your OWN `quick_id` (self-reference) or on an id outside
  the catalog is rejected by `quick-batch update` and blocks the whole
  layer's persistence — when uncertain, prefer `[]` over a guess.

### `files_modified` — every path your plan's tasks will touch

```yaml
files_modified: ["src/foo.ts", "tests/foo.test.ts"]
```

Used two ways downstream, both from THIS field (never re-derived from your
plan's prose): (1) `partitionByFileOverlap` splits same-wave items that
would touch the same file into separate waves, so two isolated worktrees
never race on one path; (2) at merge time the coordinator reads it FRESH from
your PLAN.md (not from what you declared here at planning time — keep the
frontmatter accurate if you revise the plan) for the advisory scope-
conformance check.

### `files_deleted` — only if your plan removes a file

```yaml
files_deleted: ["legacy/old-module.ts"]
```

Optional; omit entirely when your plan deletes nothing. If your plan DOES
delete a file and you omit this, the merge's deletions guard blocks that
deletion as undeclared — there is no "authorize everything" fallback.

### What quick-batch mode does NOT need

Same exclusions as `/gsd:quick`'s own modes: no `requirements` (no ROADMAP
linkage — a quick-batch item is not a phase), no `estimate` block, no
`user_setup` unless genuinely needed. `must_haves` is required only when the
calling prompt's own `<constraints>` says so (mirrors `--validate`'s
existing quick-full behavior) — that instruction rides the prompt, not this
reference.


<!-- LOCAL-ADOPTION:START -->
## Local adoption — read before using this source

The complete upstream body above is retained from GSD-Core at
`c0b2a05d2f310adc0a1f35fd71fbc9f28f4e4977`; only recorded reference substitutions
and explicit local conflict corrections have been made. See
`.ai/gsd/PROVENANCE.json` for exact source hashes and changes.

Read `.ai/gsd/README.md` for the local producer/consumer mapping and execution
boundary, `.ai/references/gsd-adaptation.md` for local conflict decisions,
and `.ai/runtime/TEMPLATE-CONTRACT.md` for additive local artifact
fields. Project records live in `.planning/`; reusable guidance lives in `.ai/`.
The active lifecycle uses `.ai/commands/` and `.ai/runtime/phase.py` with
`.planning/config.yaml`. The upstream `config.json`, `/gsd:*` commands, tool
names, hooks, and Node CLI examples describe GSD's system; this import does not
install or activate that system. Retained specialty workflows are full source
guidance for explicit future integration, not promises of installed features.
Local rules, assigned worktrees, recorded authorization, runtime ownership and
verification safeguards govern execution. The local runtime never merges.
<!-- LOCAL-ADOPTION:END -->
