# Committed chunk handoff

Use this packet when a coder has committed a bounded, reviewable assignment. It
contains the facts the coordinator needs to register the snapshot and start its
independent gates. It does not replace the coder's SUMMARY or claim that review,
tests, integration or phase verification passed.

```yaml
chunk_handoff:
  route_task_id: <unique coding-task ID>
  assignment_id: <assignment id>
  plan_id: <plan id>
  chunk_id: <unique committed chunk id>
  chunk_event: interim|final
  plan_status: continuing|complete|blocked
  base: <full base SHA>
  head: <full committed head SHA>
  branch: <executor branch>
  owned_paths: [<exact independently reviewable paths, within the plan's declared boundary>]
  deletions: [<explicitly authorized deletion paths>]
  depends_on: [<registered prerequisite chunk IDs>]
  acceptance: [<plan acceptance IDs evidenced by this chunk>]
  resources: [<named shared resources>]
  checks:
    - id: <check id>
      argv: [<executable>, <argument>]
      cwd: <. or repository-relative working directory>
      inputs: [<repository-relative files whose bytes affect the result>]
      timeout: <finite seconds>
  summary: <committed SUMMARY path; required only when plan_status is complete or blocked>
  remaining_assignments: [<independent task IDs remaining; empty when finished>]
  blockers: [<explicit reason; [] when none>]
```

The `base`, `head`, paths, deletions, dependencies, acceptance, resources and
checks must agree with the committed plan and repository. `owned_paths` is the
exact subset this chunk implements and can be independently reviewed; do not claim
the whole plan boundary when the chunk changes less. Acceptance lists only the
plan IDs this chunk demonstrates. A mismatch is a blocker to registration; do not
repair the declaration by inference. The coordinator uses
`pipeline.register`, prepares distinct detached reviewer/test worktrees at `head`,
starts the fresh code-reviewer and runtime-owned checks concurrently, and continues
unrelated ready tasks. A dependent task waits for prerequisite integration and
passing gates. The coordinator may integrate only after the runtime confirms all
applicable gates pass.

The reviewer report names the registered `head` and `base`, covers all acceptance
IDs and the declared scope, states `passed` or `failed`, includes findings, cited
evidence and provenance. The tester is `pipeline.run-checks` executing declared
argv in the explicit named environment; it is not a model agent. See the
[parallel pipeline contract](../references/parallel-pipeline.md) for command and
schema details. Chunk results remain provisional until final integrated phase
gates pass.
