# Executable orchestration

`orchestrate.py` runs an approved schedule with Python 3.11+, Git and an
authenticated GitHub CLI. Each worker phase is a separate subprocess. The
scheduler waits for process completion, saves receipts, and dispatches tracks
whose own dependencies have merged. Waves remain a display grouping.

The Markdown commands describe the planning and role workflow. For executable
background dispatch, the coordinator compiles that approved plan into a JSON
schedule using [schedule.example.json](schedule.example.json). The example is
illustrative; replace its repository, PLAN paths, owned paths, resources, ID
ranges and checks. The runner does not parse YAML, infer plans, or invent tests.
The JSON is an explicit execution snapshot of `.ai/config.yaml` and the run
manifest. Keep it outside tracked content or in the Git common directory.

```text
python .ai/runtime/orchestrate.py /path/to/schedule.json --validate
python .ai/runtime/orchestrate.py /path/to/schedule.json
```

Validation alone is read-only. Execution requires the caller's authorization
to build and publish the selected PLANs. Run it from a clean checkout of the
target branch. That checkout is reserved for the scheduler until it exits.
The same command resumes delivery receipts after interruption. Exit 0 means
every scheduled track merged; exit 1 preserves blocked work and reports why.
Recovery commands below update a receipt and exit; invoke the normal run command
afterward to continue scheduling.

## Worker contract

`worker_command` is an argv array, never a shell string. Placeholders are
`{worktree}`, `{phase}`, `{sandbox}`, `{schema_file}` and `{result_file}`.
The assignment arrives on stdin, and also as JSON in `ORCH_CONTEXT`; the
result destination is `ORCH_RESULT`. Return the supplied JSON schema. Worker
exit failure, invalid output, missing output and `cannot_review` block the
track. A successful process exit alone never authorizes a merge.

The supplied Codex adapter uses fresh `exec --ephemeral` processes, an output
schema and a final-message file. Those interfaces are documented in
[Codex non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode).
Use an authenticated local CLI and the user's configured model. A custom host
can implement the same contract. The adapter requests `workspace-write` for
writers and `read-only` for review. Build/document workers commit each PLAN
step; the coordinator audits their ordered commit history and owns correction
commits. Configure the host's worker permissions to support scoped Git commits
in the assigned checkout, including its required Git metadata.
A permission failure parks the track;
the runner never switches to unrestricted permissions to get past it.

One build process researches and implements the track's plans in order. Both
cold code reviews run before a lightweight documentation process lands the
original PLAN's promised documentation/contracts. Two fresh documentation-only
reviews then run, with at most one documentation correction between them. There
is no third review or second immediate fix pass of either kind. All review
severities are recorded. A reviewer must supply
evidence and a stable root-cause key, not just a severity or opinion.

Code reviewers receive the original PLANs, unchanged contracts, Research notes,
source and filtered diff. Documentation agents receive the accumulated
implementation/code-review handoff and verify its claims against actual code.
Each [agent file](../agents/README.md) defines that role's inputs and methods. Context
separation is enforced by the host's tool permissions and the prompt, not a
filesystem sandbox supplied by this script. The runner detects changed HEAD
or dirty files after read-only phases.

Each track schedule declares `documentation_paths` explicitly (possibly empty)
as a subset of `owned_paths`, disjoint from `code_paths`, and restricted to
`.md`, `.markdown`, `.rst` or `.adoc` files; directory scopes must not include
source files. The snapshot also carries `documentation_model` and a separate
`documentation_worker_command` containing `{model}`. An unavailable lightweight
route blocks instead of falling back to the code model. Results include
`implementation_complete`, `documentation_complete`, `spec_coverage`,
`resolved_intake`, durable `phase_attempts`, phase receipts,
`code_reviewed_sha` and `documentation_reviewed_sha`. Immutable
`plan_source_sha` keeps later PLAN notes from weakening the original promise.
Old unfinished runs reconcile with their original compatible schedule and
receipts; deleting receipts or changing the schedule fingerprint does not
evade the review count.

## Protocol version 2

Set `protocol_version: 2` in the JSON snapshot. The assigned PLAN uses the
[PLAN template's Execution contract](../templates/PLAN.md#execution-contract):
`intent_changes`, ordered `steps` with stable IDs and build/document phases,
and `completed_intake` paths. Runtime reads this contract at the original
revision before allocating the worktree.

Each build/document step commit includes this trailer:

```text
PLAN-Step: .ai/plans/backlog/PLAN-001-example.md#implement
```

Receipts retain `build_step_commits` and `document_step_commits`. Missing,
combined, empty or out-of-order step commits fail the audit. The `--reconcile`
interface can consume completed step commits after interruption using the
inspected HEAD. Older unfinished schedules keep their compatible runtime and
receipts until reconciled; do not silently upgrade an in-flight run.

Optional track fields:

| Field | Value |
| --- | --- |
| `research_paths` | Exact separately owned `.ai/research/*.md` paths |
| `source_documentation_paths` | Exact code files for later comments/docstrings |
| `source_documentation_check` | Non-Python equivalence argv using `{before}` and `{after}` temporary files |

For Python, the runtime compares ASTs with docstrings removed. This checks
executable syntax rather than proving arbitrary program equivalence; projects
that inspect `__doc__` need behavior checks for those consumers as well.
Other languages use the project-supplied equivalence command.

Results include `spec_coverage` entries with `plan`, `spec` and code
`evidence`, and `resolved_intake` entries with `path` and completion
`evidence`. Findings carry `impact`: missing_code, missing_functionality,
missing_spec_coverage, editorial or unrelated. The schema distinguishes
overall implementation coverage from editorial cleanup.

The schedule reserves 20 IDs per track for each of FIX, INTAKE, SPEC, ADR and
AMD under [Scheduling and IDs](../RULES.md#scheduling-and-ids). Build/fix workers
may create new scoped FIX/INTAKE records; their IDs are audited and retained
alongside coordinator-generated findings.

## Review outcomes and deferred work

- Confirmed code defects produce `FIX` files in `.ai/fixes/open/`, including
  minor and out-of-scope defects. Documentation and contract corrections each
  produce their own `INTAKE` in `.ai/plans/intake/`; questions also use INTAKE.
  Valid findings survive blocked results and failed edit audits in durable
  `deferred/<track>/` FIX/INTAKE copies under the run directory. `report_file`
  in the queue identifies the readable copy. Reports enter the worktree only
  after its edits pass audit. Repeated findings update severity and location,
  retaining each round's evidence and any attempted correction summary.
- The fixer can edit only `code_paths`. A missing or wrong contract is an
  INTAKE, not permission to redefine correctness during a fix. Original PLAN
  documentation promises remain part of the final documentation phase.
- Completion uses [RULES: Definition of done](../RULES.md#definition-of-done).
  Missing required code/functionality or overall SPEC coverage prevents merge.
  Editorial and unrelated findings can remain on a complete result, with the
  actual verdict retained as `changes_requested`/`ready_with_followups`.
  The former `residual_findings` configuration override is rejected.
- Failed tests, incomplete implementation, inconclusive review, PR failures,
  merge conflicts and formal GitHub requests for changes are blocked outcomes.
  Independent tracks continue. Dependencies of blocked tracks wait.
- Records remain open until a later defect pass verifies before/after proof.
  A cold review omitting an earlier finding does not silently close its FIX.
  After other PLAN work finishes, `followups.json` marks the queue eligible.
  A parked track with findings and its waiting dependents are listed explicitly
  and do not prevent examination of those findings. Other unfinished scheduled
  or project PLANs in backlog/active/review/blocked still delay eligibility.
  A fresh read-only worker looks through the code FIX reports, attempted proof
  and current code, including preserved unmerged worktrees, recording which
  tree was examined and the per-FIX assessment in the receipt. This audit
  does not restart the original track's review/fix loop or close unproved FIXes.
  Open reports from earlier runs are included, so finishing the last PLAN run
  does not lose defects deferred by an earlier one.

## Ownership and resources

Declare exact files or directory prefixes ending in `/`. Globs, repository-wide
ownership and path traversal are rejected. `code_paths` must be a subset of
`owned_paths`. Include the PLAN itself and every promised SPEC/ADR/doc change
in ownership. The runner compares the actual diff, including both sides of
renames, against this declaration. Shared STATE, journal and orchestration
records are always coordinator-owned. Runtime FIX/INTAKE files are allocated
from disjoint reserved ranges, with existing-ID collisions rejected.

Tracks with intersecting ownership or exclusive resource names wait for one
another. Assign unique port/database/cache names in `environment`, and declare
each shared service in `resources`. Worktrees do not isolate databases, ports,
external APIs or filesystem writes by arbitrary processes. An undeclared
resource cannot be detected by this runner. A parked track retains its resource
reservation; investigate its processes before reusing it.

## Delivery and recovery

One delivery worker refreshes the target, merges that exact revision
into the completed track, runs the required commands on the integrated tree,
pushes that head, and waits for configured and protected required GitHub checks.
Optional checks do not gate delivery. CI waits leave the dispatch loop free to
start independent work; target Git operations remain serialized. Branch protection must
require those checks with **Require branches to be up to date before merging**.
Protection must also apply to administrators; the runner rejects a bypassable
administrator configuration for this guarantee.
This server-side condition prevents a target advance between local validation
and the merge request from silently bypassing integration checks. The runtime
supports GitHub merge commits, not squash/rebase or merge queues. It never uses
an administrator bypass or treats absent/skipped required checks as passed.

The PR records the reviewed source SHA separately from the integrated head.
The documentation batch, including checked source comments/docstrings, follows
code review. Only generated finding records and lifecycle moves may follow the
last documentation review;
target integration imports already-landed changes and is validated again.
The scheduler validates the entire closing set before moving completed PLANs
and evidenced, declared INTAKE items to `done/<year>-Q<quarter>/` in the track; these moves reach the target only when the PR merges. A blocked
PR's local move does not count as completion. Shared STATE/journal updates
remain coordinator work and are not written concurrently by runtime workers.
`--match-head-commit` binds the merge to the checked head. The runner then fetches,
fast-forwards the target, verifies commit ancestry and compares the remote merge
tree with the tested tree. Only then can dependents start or cleanup occur.

Cleanup uses non-forced worktree removal and branch deletion, and refuses dirty
files, undeclared ignored output and advanced remote branches. Python bytecode
is disabled for workers/checks, and Python cache, temporary-directory and XDG
cache environment variables point to run-owned scratch directories outside the
worktree. Other tools can declare generated directories in a track's optional
`disposable_paths`, for example `[".pytest_cache/"]`. These must be absent at
allocation, ignored by Git, contain no tracked files and have no redirected
paths. Only those directories are removed automatically. No unrelated branches,
worktrees or ignored local files are deleted.

Receipts and worker output live under `<git-common-dir>/orchestration/<run>/`.
An OS lock excludes concurrent schedulers for the same repository. Atomic JSON
receipts preserve the schedule hash, review count, PR number and merge evidence.
Unfinished earlier runs must be reconciled before a different run starts.

An interrupted writer is **not automatically replayed**: its child process may
still exist and its last commit may have succeeded. The run parks it and keeps
the receipt. Reconcile the process, result and Git state before recovery; never
delete a receipt to reset the review counter.

```text
python .ai/runtime/orchestrate.py schedule.json --retry api
python .ai/runtime/orchestrate.py schedule.json --reconcile api --expected-head <sha> --workers-stopped
python .ai/runtime/orchestrate.py schedule.json --abandon api --expected-head <sha> --workers-stopped
```

`--retry` resumes a clean blocked track at its saved coordinator checkpoint,
such as after a PR service outage or check infrastructure failure. Completed
phases are reused. `--reconcile` requires the exact inspected worktree HEAD and
confirmation that its workers/resource users have stopped; it consumes the saved
result without launching another worker. A failed build with no edits may be
retried explicitly. A missing or blocked fix/review result remains parked;
recovery never grants another fix/review attempt. Changed HEADs, partial edits
and unfinished Git operations require reconciliation before retrying.

`--abandon` releases reservations while preserving all files, branches, PRs and
findings. It never satisfies dependencies or marks work merged. Omit the SHA
only if allocation failed before creating a worktree. A new run may start once
every earlier track is cleaned after merge or explicitly abandoned and released;
previously issued ID ranges remain reserved. The coordinator can run these
commands within existing authorization after establishing their preconditions.

A completed remote merge with a
lost response resumes at sync/verification/cleanup, without another review or PR.
Fix or check failures preserve the branch and its open records for the later
defect pass. The coordinator reports unresolved recovery work explicitly.

## Template validation

```text
python -m unittest discover -s tests -v
```

The tests use real temporary repositories and bare remotes, deterministic
worker subprocesses and simulated GitHub responses. They do not consume model
tokens or publish test PRs. `.github/workflows/validate.yml` runs this suite.
