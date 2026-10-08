# Parallel chunk pipeline and source evidence

The coordinator owns native agent dispatch and lifecycle. The runtime owns
persisted route declarations, registered snapshots, gate results and deterministic
readiness. The contracts below govern parallel execution of a plan as one or more
reviewable committed chunks; they do not replace the phase records or their final
verification.

## Routing planned work

Before dispatching coders, write a repository-relative JSON file and call:

```bash
phase_run query pipeline.route --spec .planning/tmp/route.json
```

The file has this schema:

```json
{
  "schema": 1,
  "tasks": [
    {
      "id": "01-01",
      "depends_on": [],
      "owned_paths": ["src/service.py", "tests/service_test.py"],
      "resources": ["local-database"],
      "state": "pending"
    }
  ]
}
```

`id` is a unique coding-task ID. The coordinator maps it to a unique
`assignment_id` and committed `chunk_id`; `plan_id` names the source plan. These
IDs can be equal for a one-chunk plan, but equality is not required. `owned_paths`
is the exact independently reviewable subset of that plan's authorized boundary.
Dependencies name registered chunk IDs, not just summaries. A dependency that is
missing or unregistered returns `wait`; a planned dependency cycle is `blocked`.
Wait for its applicable gates and integration, and ensure the prerequisite's
registered SHA is an ancestor of this chunk's base. Each result is `ready`, `wait`
or `blocked` with explicit reasons. Active reservations win; otherwise conflicting
pending tasks are eligible in deterministic input-list order.
Owned paths use exact repository-relative paths or directory prefixes ending in
`/`; do not use globs, traversal or whole-repository ownership. Register only the
acceptance IDs evidenced by this chunk. Overlap and shared
named resources make tasks conflict. A route result is a readiness snapshot, so
re-route after a blocker or prerequisite changes. Dispatch only currently ready
work. The coordinator sets a route task to `active` before dispatch and keeps it
active while its coder, review and checks are in flight. After integration, set its
route state to `complete` and reroute to release its path/resource reservation.
Keep a failed task reserved while recovery is active; explicitly update the route
when work is abandoned so blocked work and released scope are visible.

## Register and gate one committed chunk

A coder commits its bounded chunk and returns its handoff before the coordinator
registers the exact revision:

```bash
phase_run query pipeline.register --spec .planning/tmp/chunk.json
phase_run query pipeline.prepare <chunk-id>
phase_run query pipeline.run-checks <chunk-id> --environment <explicit-environment-id>
phase_run query pipeline.record-review <chunk-id> --report .planning/tmp/review.json
phase_run query pipeline.integrate <chunk-id> --revision <ref>
phase_run query pipeline.status [<chunk-id>]
```

Registration schema 1 records the immutable base and head SHAs, identifiers,
declared change boundary and gates:

```json
{
  "schema": 1,
  "chunk_id": "01-01",
  "assignment_id": "01-01",
  "plan_id": "01-01",
  "base": "<full-base-sha>",
  "head": "<full-committed-head-sha>",
  "owned_paths": ["src/service.py", "tests/service_test.py"],
  "deletions": [],
  "depends_on": [],
  "acceptance": ["A-1"],
  "resources": ["local-database"],
  "checks": [
    {"id": "unit", "argv": ["python", "-m", "unittest", "tests.test_service"], "cwd": ".", "inputs": ["src/service.py", "tests/service_test.py"], "timeout": 120}
  ]
}
```

Use full resolved SHAs and actual repository-relative paths. `deletions` is explicit;
ownership alone does not authorize removal. Check definitions use argument arrays,
repository-relative `cwd`, declared source `inputs`, and a finite timeout. The
runtime rejects unsafe or out-of-bound scope and unsupported ancestry.

`pipeline.prepare` creates separate detached reviewer and test snapshots at the
registered SHA. The reviewer and tester use those immutable snapshots; do not
change the revision while either gate is running. `pipeline.run-checks` is the
runtime executing only the declared argv checks, not a model tester or new agent
permission. Its receipt binds the exact revision, declared environment, tools and
runtime, check spec, inputs and logs. Matching valid passing receipts may be
reused with their original `tested_revision`; stale, corrupt or failed receipts
are rerun. Use `--no-reuse` for volatile external checks. A result from another
revision or environment is not a pass for this chunk.

The review report uses schema 1 and must cover the registered identity, revision,
acceptance IDs and scope. It carries an explicit `passed` or `failed` status,
findings, nonempty cited evidence and reviewer provenance:

The reviewer returns the JSON object for coordinator capture; it does not write in
the source checkout. The coordinator saves that response as a temporary
repository-relative JSON file for `pipeline.record-review`. Each finding's
severity is `blocking`, `critical`, `high`, `medium`, `low` or `info` and its
`evidence` is a nonempty string. A `passed` report cannot contain blocking,
critical or high findings.

```json
{
  "schema": 1,
  "chunk_id": "01-01",
  "assignment_id": "01-01",
  "sha": "<registered-head-sha>",
  "base_sha": "<registered-base-sha>",
  "status": "passed",
  "acceptance": ["A-1"],
  "scope": ["src/service.py", "tests/service_test.py"],
  "findings": [],
  "evidence": ["A-1: tests.test_service passed on the registered SHA"],
  "provenance": {"source": "code-reviewer", "reviewer": "<fresh-reviewer>"}
}
```

Do not synthesize an empty passing report or turn skipped, failed, corrupt,
partial, stale or absent evidence into success. A passed report cannot contain
blocking findings. Preserve failed attempts. The report may be recorded while the
tester is running; integrate only after the runtime reports every applicable
prerequisite and gate passing, then check status again against the integrated
revision. Chunk evidence is provisional; it does not prove the whole phase.

`pipeline.integrate` records a revision the coordinator has already merged; it
does not perform Git integration. After all chunk gates pass, merge the exact
registered head SHA into the clean, unprotected session branch:

```bash
git merge --no-ff <registered-head-SHA>
phase_run query pipeline.integrate <chunk-id> --revision HEAD
```

Never merge a moving coder branch. If Git reports a conflict, abort that merge,
preserve the coder checkout and keep the chunk blocked for reconciliation. The
runtime validates that the registered head is an ancestor of the integrated
revision and that the current checkout is clean. A whole-plan
`worktree.merge-wave` fallback remains for legacy assignments that completed
coding without pipeline registration; it must never merge a branch while its
coder is active or turn the selected per-chunk pipeline into a whole-wave wait.

At integration, the runtime also fingerprints the Git mode/content inventory of
the chunk's registered `owned_paths`, `.planning/config.yaml` and all declared
check `inputs` (including descendants when a check input is a directory). The
integrated revision must match the tested chunk on these boundaries, and the
current working files are checked against the integrated revision before the
fingerprint is stored. Dependency readiness revalidates this fingerprint against
the integrated tree and current working files. A changed, added or deleted file
in a prerequisite's owned scope, check inputs or config blocks dependents; a
stale or legacy integrated record without a fingerprint fails closed. A dependent
must not rely on old prerequisite evidence after changing one of these files.

## Reusable source-evidence packets

The coordinator alone stores, looks up and invalidates packets. Scouts return cited
evidence and never write shared cache state. Use a repository-relative spec file:

```bash
phase_run query evidence.store --spec .planning/tmp/evidence.json
phase_run query evidence.lookup --spec .planning/tmp/evidence.json
phase_run query evidence.invalidate --spec .planning/tmp/invalidate.json
```

Store/lookup schema `source-evidence/v1` requires nonempty `task_class`, `question`,
full current `source_revision`, exact-file `inputs`, exact-file or directory-prefix
`scope` (directories end in `/`), `acceptance`, `provenance` (`role`, `model`,
`prompt_version`) and an explicit `config` object. A stored packet adds status
(`complete`, `incomplete`, `blocked` or `failed`), nonempty `outputs`, and cited
evidence entries with `claim`, `citation` and `excerpt`. Lookup can request
`include_payload: true`; otherwise it returns a concise reference and reuse reason.
Invalidation requires the artifact's 64-hex id and a nonempty reason.

Reuse is bound to full source revision by default. Cross-revision reuse is an
explicit opt-in requiring both `reuse.cross_revision` and
`reuse.complete_scope` to be true; the runtime still verifies identical bytes and
inventory across the complete declared scope. Use the same task class/question,
inputs, scope, acceptance, provenance and config for lookup as for capture. A
partial, blocked, failed, invalidated, stale or mismatched packet is not reusable.
Packet reuse avoids duplicate extraction only; it does not claim a provider prompt
cache, implementation, test execution, review verdict or final verification.

## Integrated completion

The coordinator continues independent ready coding while a committed chunk's fresh
review and runtime checks run in their separate frozen snapshots. A plan that
depends on this chunk waits until it is integrated and all applicable gates pass;
unrelated work need not wait for a whole wave. Before phase verification, run the
legacy `verification.run-checks` on the fully integrated tree as configured. The
existing `verification.run-checks` API remains unchanged. Final goal-backward
correctness, security, integration and documentation checks, aggregate configured
checks, and fresh independent review still judge the resulting integrated phase.
