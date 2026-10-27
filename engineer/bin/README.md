# Engineer runtime

Use Python 3.11 or newer. The runtime uses only the standard library. The POSIX
shim selects a namespace virtual environment, a project virtual environment, or
`python3` / `python` and executes the CLI in isolated mode.

```sh
engineer/bin/engineer_run query runtime-identity --pick packageName --raw
engineer/bin/engineer_run query help
python -I engineer/bin/engineer.py query help
```

Source and installed namespaces use the same layout: `engineer/bin`,
`engineer/templates`, and sibling `agents`. An installation under `.claude`
or `.codex` determines its host; a source checkout defaults to Codex unless
Claude host environment variables are present. `ENGINEER_HOST` explicitly selects
`claude` or `codex`. Commands operate on the current Git checkout;
`ENGINEER_ROOT` explicitly selects an alternate project root.

Every command accepts `--raw`, `--json`, and `--pick dotted.field`. A picked scalar
prints without JSON quotes; booleans print `true` / `false`, and collections print
compact JSON. Missing picked fields fail with `pick-missing`. Output never uses
overflow files. Failures print a diagnostic JSON object on stderr and return a
nonzero exit status. Config keys absent from both project overrides and defaults
fail with `key-not-found`; `--default VALUE` supplies an explicit fallback.

```sh
engineer_run query config-get workflow.tdd_mode --raw
engineer_run query config-get workflow.optional --default false --raw
engineer_run query config-set workflow.code_review true
engineer_run query frontmatter.get path/to/PLAN.md --field must_haves
engineer_run query frontmatter.set path/to/REPORT.md --field status --value passed
engineer_run query frontmatter.validate path/to/PLAN.md --schema plan
```

Configuration and frontmatter support safe YAML mappings, sequences, flow
collections, quoted strings, booleans, nulls, numbers, comments, and block scalars.
Leading-zero phase identifiers retain string types. Tags, aliases, anchors,
merge keys and duplicate block mapping keys fail closed. Writes use UTF-8,
atomic replacement, and a project planning lock; frontmatter writes retain the
document body and key order.

Read workflow initialization packets through `init.<workflow>`. Available packets
include `phase-op`, `plan-phase`, `execute-phase`, `verify-work`, `ship`,
`code-review`, `progress`, `quick`, `quick-batch`, `todos`, `new-project`,
`onboard`, `new-milestone`, and `complete-milestone`.

Record owners include `phase.add/insert/edit/remove/complete`,
`roadmap.get-phase/analyze/set-plans/update-plan-progress`, `state.get/patch/update`,
`state.begin-phase/record-session/add-decision/add-blocker/resolve-blocker`,
`requirements.mark-complete/reopen`, `quick.create/update/get`, and
`todo.add/list/match-phase/complete`. Removal archives phase artifacts.
`planning.archive` requires an explicit milestone and `--confirm`; it moves the
requested `--scope phases|quick` under `.planning/milestones`.

Plan and evidence gates include `verify.plan-structure`, `plan.task-structure`,
`check.verify-command-paths`, `check.verify-failure-directions`,
`check.evaluation-scope`, `check.decision-coverage-plan`,
`check.decision-coverage-verify`, `check.ui-plan-gate`, `verify.artifacts`,
`verify.key-links`, `verify.commits`, and `check.tdd-red-evidence`.
`planning.integrity` fails on malformed record frontmatter;
`planning.validate` reports the same findings without blocking.

Configure verification commands as argv arrays:

```yaml
verification:
  commands:
    - id: unit
      argv: ["python", "-m", "unittest", "discover", "-s", "tests"]
      timeout: 300
      inputs: ["src/app.py", "tests/test_app.py"]
```

`verification.run-checks` executes commands without a shell and persists a receipt
bound to the command/configuration and input digest. When `inputs` is omitted,
all nonplanning Git-visible files form the input set. A passing receipt is reused
only when inputs match and its revision is in current history. Revision or input
drift during a check fails the frozen run. `verification.fingerprint` hashes phase
PLAN/SUMMARY records and covered sources while excluding the report itself.
`verification.current` checks the report fingerprint, frozen revision, clean
working tree, and current check receipts. `verification.append-audit` suppresses
an identical last audit block.

`phase.uat-passed`, `audit-uat`, `audit-open`, and `uat.*` expose acceptance work.
`spec.edge-probe` reads requirement and resolution JSON files;
`spec.section SPEC.md edges|prohibitions` extracts explicit sections.
`quick-batch.*` persists items, computes bounded scheduling and deterministic merge
prefixes, and refuses to complete batches with nonterminal items.

`session.open phase N` and `session.open quick LABEL` create isolated worktrees.
Session creation requires an ignored worktree directory. `session.adopt` records
an existing isolated checkout; `session.close` refuses dirty or unintegrated
changes. Worker `worktree.create` records its base and owned files/deletions.
`worktree.merge-wave` requires committed complete summaries, verifies scope and
declared deletions, and integrates workers in recorded order.

`todo.issue-preview` / `phase.issue-preview` validate issue templates and persist
a content-bound token. Publication and update require `--preview-token`, consume
the token before the provider call, and verify provider readback before linking
the local record. An uncertain provider outcome requires inspection before retry.
`phase.issue-declare` uses an expected digest to protect finding declarations.
`phase.handoff` checks summaries and issue relationships.

`pr.open` validates the PR template, pushes a clean branch, creates a draft (or
updates its existing PR), and validates provider readback. `--base` supports
stacked PRs. `pr.ready` and `pr.merge` require current verification evidence;
merge additionally requires explicit `--confirm` after the human authorizes it.
`pr.checks` reads provider checks; `--timeout SECONDS` bounds waiting.

`cleanup.preview` returns only recorded, clean, integrated resources and an exact
approval token. `cleanup.apply --approval-token TOKEN --confirm` revalidates every
resource immediately before removing it, then consumes the preview.
`handoff.*` persists measured context continuation packets; `codebase.*` records
map revisions and determines freshness from Git history and changed paths.

`run-with-timeout --timeout SECONDS -- COMMAND ARGS...` executes argv without a
shell and returns 124 on timeout. `package-legitimacy --registry npm|pypi|crates`
returns advisory registry evidence, including `UNKNOWN` when offline.
