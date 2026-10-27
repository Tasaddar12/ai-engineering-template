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
Leading-zero phase identifiers retain string types. Mapping anchors and merges
preserve explicit overrides and copy alias values within bounded structural
limits. Tags, scalar anchors, forward/cyclic aliases and duplicate explicit
mapping keys fail closed. Writes use UTF-8,
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
Plan registration requires a usable STATE current position and exact padded phase
IDs with two ASCII ordinal digits. It replaces only rows under one unambiguous
`Plans:` label, retains completed identities and surrounding authored notes, and
refuses malformed/orphan rows before writing either record. `--summary TEXT`
sets the single-line plan-count description without replacing nearby prose.

Plan and evidence gates include `verify.plan-structure`, `plan.task-structure`,
`check.verify-command-paths`, `check.verify-failure-directions`,
`check.evaluation-scope`, `check.decision-coverage-plan`,
`check.decision-coverage-verify`, `check.ui-plan-gate`, `verify.artifacts`,
`verify.key-links`, `verify.commits`, and `check.tdd-red-evidence`.
`planning.integrity` fails on malformed record frontmatter;
`planning.validate` also checks roadmap/state/requirements/phase consistency,
dependency ownership and active retirement markers, without blocking unless
`--strict` is explicit. Structural repair previews include exact before/after
content and a digest. Repair adds missing STATE sections and synchronizes only
derived progress; it does not resolve author decisions or fabricate approval.

Every invocation captures planning-file digests and schema findings before and
after dispatch. Read-only verbs fail if planning content changed, and new schema
corruption fails a mutation. Existing corruption is reported as a warning so a
repair command can still operate. Frontmatter setters reject schema regressions
before writing.

Current PLAN metadata requires phase-or-quick identity, plan/type/wave,
depends_on, files_modified/files_deleted/resources, autonomous, requirements,
acceptance/documentation/checks/issue_refs lists and must_haves with
truths/artifacts/key_links lists. Phase plans name their owning requirement IDs;
genuine quick plans follow the assigned quick contract. `checks` is a list of
nonempty argv string arrays, never shell command strings or arbitrary mappings.
SUMMARY requires identity, plan, status, requirements-completed,
acceptance/documentation/issue_refs lists. CONTEXT requires identity, discussion
(`pending` or `complete`) and issue_refs. Identity must match actual record paths
and phase PLAN/SUMMARY basenames. These checks do not fabricate approval or
require SUMMARY artifacts from unrelated read-only/artifact-only roles.

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
Fingerprinting also writes and returns `covered_digest: v4:sha256:<hex>` over the
same canonical coverage. Currentness rejects absent, malformed, older-version or
stale v4 coverage even when a raw fingerprint matches. `fingerprint`, `revision`
and `covered_files` remain compatible fields; report schema validation checks v4.
`verification.current` checks the report fingerprint, frozen revision, clean
working tree, and current check receipts. `verification.append-audit` suppresses
an identical last audit block.

`phase.uat-passed`, `audit-uat`, `audit-open`, and `uat.*` expose acceptance work.
Local UAT requires existing complete committed source SUMMARYs, every remaining
required action/checklist outcome to pass, and actual Human acceptance fields
`status: ACCEPTED`, `accepted_by`, `accepted_at`, and final `decision`. Skipped,
not-testable, blocked, pending and unresolved actions remain blocking. Historical
`result: issue` is preserved and distinguished as effectively resolved only when
stable gap_id/resolved_by/resolved_at identify a real committed executed PLAN and
complete matching SUMMARY with specific resolution evidence. An explicit human
retest obligation requires its actual recorded pass. Diagnosis and status labels
never supply human acceptance. `uat.complete-session` enforces these same gates,
preserves historical observations and synchronizes actual counters. Quick UAT is
included in open audits and ready/merge gates without fabricating phase identity.
`spec.edge-probe` reads requirement and resolution JSON files;
`spec.section SPEC.md edges|prohibitions` extracts explicit sections.
`spec.prohibition-project INPUT.json` projects already selected stable prohibition
items from a flat JSON array or an object containing `items`; it returns `items`
and `coverage`. Selection and semantic recall remain the workflow's job.
`spec.prohibition-proof DESCRIPTOR.json --subject REAL_PATH [--timeout SECONDS]`
runs actual violation, mandatory clean-control and real-subject checks. The
descriptor supplies argv and flat `check_*` or canonical fields; supported report
formats are `unittest` (default), `junit` (requires `reportFile`) and `eslint-json`
(stdout or `reportFile`). Argv can use `{subject}`, `{target}` and `{report}`
placeholders. Success returns `located`, `proved` and `valid` true,
`disposition: green`, and `kind`, `target`, `rule`, `subject`, `observations`,
`reason`. Unprovable input or controls fail with exit 2,
`unprovable-prohibition`, `proved`/`valid` false and `disposition: flagged`,
retaining actual observations and the reason.
`quick-batch.*` persists items, computes bounded scheduling and deterministic merge
prefixes, and refuses to complete batches with nonterminal items.

`session.open phase N` and `session.open quick LABEL` create isolated worktrees.
Session creation requires an ignored worktree directory. `session.adopt` records
an existing isolated checkout; `session.close` refuses dirty or unintegrated
changes. Worker `worktree.create` records its base and owned files/deletions.
`worktree.merge-wave` requires committed complete summaries, verifies scope and
declared deletions, and integrates workers in recorded order.
For `worktree.create`, `merge-wave` and `cleanup-wave`, `--phase` is a worker
registry label, not a phase lookup or authority grant. `--phase quick-001` records
workers for that actual quick session without creating a phase record.

`todo.issue-preview` / `phase.issue-preview` validate issue templates and persist
a content-bound token. Publication and update require `--preview-token`, consume
the token before the provider call, and verify provider readback before linking
the local record. Preview/publication require `--variant` with exactly Bug,
Enhancement, Decision required, Security risk, or UAT, and bind it into the token.
The validator reads only that variant's fenced body under the File Template
catalog. `issue.validate --variant NAME --body-file FILE` provides the same
structural check for separately authorized provider operations. UAT retains
explicit human acceptance fields and the template's step-table headers.
The installed catalog must contain all five canonical variants. Literal fenced,
indented, commented and raw HTML blocks cannot supply required headings, UAT
tables or acceptance fields. UAT rows retain the four canonical columns and
consecutive step numbers, and each human acceptance field appears exactly once.
Preview and publication accept explicit `--existing-issue
URL|NUMBER` or `--no-match` dispositions, bound into the token. Publication requires
one after canonical-match review. Searches include open and closed issues,
semantic title/problem identity and stable source provenance. A reviewed closed
match remains pending local reconciliation; publication never reopens or closes
an issue. Uncertain creates recover only by unique provenance and exact content
readback. Repeating preview cannot reset a consumed attempt.
`phase.issue-declare` uses an expected digest to protect finding declarations.
`phase.handoff` checks summaries and issue relationships.

`pr.open` validates the PR template, pushes a clean branch, creates a draft (or
updates its existing PR), and validates provider readback. `--base` supports
stacked PRs. `pr.ready` and `pr.merge` require current verification evidence;
merge additionally requires explicit `--confirm` after the human authorizes it.
Both accept either `--phase N` or `--quick ID`, require the PR head to equal the
verified checkout HEAD, and audit declared issue relationships. Quick evidence
lives in `.planning/quick/NNN-slug/NNN-VERIFICATION.md`, with `quick: NNN`,
`status`, `issue_refs`, `fingerprint`, `revision`, and `covered_files` frontmatter.
Fingerprinting includes QUICK.md, task PLAN/SUMMARY files and covered sources;
currentness uses the same frozen-revision and configured-check receipt rules as
phase verification. Quick verification never invents a phase.
`pr.checks` reads provider checks; `--timeout SECONDS` bounds waiting.

`cleanup.preview` returns only recorded, clean, integrated resources and an exact
approval token. `cleanup.apply --approval-token TOKEN --confirm` revalidates every
resource immediately before removing it. The content-bound preview is consumed
before deletion; partial progress is retained and cannot be silently replayed.
`handoff.*` persists measured context continuation packets; `codebase.*` records
map revisions and determines freshness from Git history and changed paths.
When a recorded revision is unreachable after a squash, freshness uses the most
recent actual Git commit touching that map. Missing map history stays stale;
timestamps never stand in for evidence. The configured commit threshold and
changed-path condition still apply.

`run-with-timeout --timeout SECONDS -- COMMAND ARGS...` executes argv without a
shell and returns 124 on timeout. `package-legitimacy --registry npm|pypi|crates`
returns advisory registry evidence, including `UNKNOWN` when offline.

## Exact argv reference

Run each entry as `engineer_run query VERB ARGS`. Long-option values follow the
option; multi-value options consume values up to the next option. Put positional
arguments before options. Boolean options take no value. JSON arguments must be
passed as one shell argument. `--raw`, `--json`, and `--pick FIELD` are global.
`verbs` without `query` is a read-only alias for `query help`.

| Verb | Arguments | Result |
|---|---|---|
| `runtime-identity` | none | `packageName, contract, host, namespace, python` |
| `help`, `verbs` | none | `usage, verbs[]` |
| `config-get` | `KEY [--default VALUE]` | configuration value; missing key exits 1 |
| `config-set` | `KEY VALUE` | `updated, key, value` |
| `config-new-project` | `JSON_OBJECT` | `created, path`, plus `config` when created |
| `generate-slug` | `TEXT` | slug string |
| `project-instruction-file` | `[claude|codex]` | host instruction filename |
| `generate-claude-md` | `[--output PATH]` | `written, path`; preserves unmanaged content |
| `resolve-agent` | `ROLE [--host claude|codex]` | name/agent/model/effort/host/inherit/effort_inherit/model_source/effort_source/native_file; raw prints name; absent role fails |
| `agents.list` | none | actual dispatchable role files and separately identified method_sources; code-fixer is method-only |
| `resolve-model`, `resolve-effort` | `ROLE [--host claude|codex]` | named value/source/inherit/host/agent; raw prints scalar; fixed scout/fixer policy applies |
| `agent-skills` | `ROLE` | ready-to-inject `<agent_skills>` block |
| `agent.classify-failure` | `-- RETURN_BODY...` | `kind, classification, retryable, wait_hint` |
| `dispatch-isolation` | `[--phase N --plan P --force-isolation MODE]` | mode/isolation/host/runtime/requested/source/harnessFlag/harness_arguments/exec/worktree_root/root_ignored; raw prints exactly `harness-worktree` or `orchestrator-worktree`; unavailable Git/ignored-root isolation fails |
| `dispatch-capacity` | none | capacity integer, minimum 1 |
| `commit` | `MESSAGE --files PATH... [--files-removed PATH...]` | `committed, commit, hash` or no-change reason |
| `git.base-branch` | `[--is-protected BRANCH]` | base branch string or protected boolean |
| `find-phase` | `N_OR_DIRECTORY` | phase paths, number/name, artifact filenames and counts |
| `phase.locate` | `N` | `found, source, padded_phase, worktree, branch, phase_dir, session`; detects ambiguous session identity |
| `phases.list` | `[--type plans|summaries]` | `phases[], count` |
| `phase-plan-index` | `N_OR_DIRECTORY` | phase information, parsed plans, `waves`, `incomplete_plans` |
| `phase.add` | `DESCRIPTION [--goal TEXT --depends-on TEXT --requirements ID...]` | allocated phase and directory |
| `phase.insert` | `AFTER DESCRIPTION [--goal TEXT --requirements ID...]` | allocated decimal phase and directory |
| `phase.edit` | `N [--name TEXT --goal TEXT --depends-on TEXT --requirements ID...]` | `updated, phase, action` |
| `phase.remove` | `N [--force --no-renumber]` | archived path and renumbered integer phases; no-renumber retains identifiers; nonempty phase requires force |
| `phase.complete` | `N` | updated phase; complete summaries, issue handoff and passed verification required |
| `phase.mvp-mode` | `N [--mvp]` | `active, source` |
| `phase.tdd-applicable` | `PLAN_PATH` | `applicable, plan_tdd, enabled` |
| `phase.uat-passed` | `N_OR_DIRECTORY [--uat-only --require-verification]` | `passed, blocking_items[]`; blockers exit 1 |
| `phase.handoff` | `N` | `ready, errors[], findings[], phase` |
| `phase.issue-declare` | `N ARTIFACT.md [--entries-file FILE --expect-digest DIGEST]` | preview `snapshotDigest, entries, path`, or `updated, entries` |
| `phase.issue-preview` | `N ARTIFACT.md FINDING_ID --title TITLE --body-file FILE [--labels LABEL...]` | `previewToken, preview_token, title, body, source, snapshotDigest` |
| `phase.issue-publish`, `phase.issue-update` | same preview args plus `--preview-token TOKEN` | `published, url, issue, source`; update requires linked issue |
| `phase.reconcile-todos` | `N --pr URL --todos FILENAME...` | `items[]` with completed/already-completed/pending state and reason |
| `roadmap.get-phase` | `N` | parsed phase name, goal, requirements, dependencies and mode |
| `roadmap.analyze` | none | `phases[], phase_count, completed_phases, percent, milestone` |
| `roadmap.set-plans` | `N --plans 'NN-MM: Title'...` | updated phase; validates IDs and retains checkmarks |
| `roadmap.update-plan-progress` | `NN-MM` | checked plan; absent plan fails |
| `state.get`, `state.load` | `[DOTTED_FIELD]` | state view including `position`, milestone, blockers and decisions |
| `state.patch` | `JSON_OBJECT` | matched Current Position fields |
| `state.update` | `FIELD VALUE` | matched Current Position field |
| `state.begin-phase` | `N [--status TEXT]` | Current Position update |
| `state.record-session` | `[--stopped-at TEXT --resume-file PATH --status TEXT]` | continuity fields in state |
| `state.add-decision` | `TEXT [--rationale TEXT --outcome TEXT]` | deduplicated PROJECT Key Decisions row; outcome defaults Pending |
| `state.save` | none | synchronizes derived STATE frontmatter progress/status from actual roadmap/artifacts and Current Position; refuses replacement content |
| `state.add-roadmap-evolution`, `state.add-blocker` | `TEXT` | `added` or duplicate no-op |
| `state.resolve-blocker` | `TEXT` | retired blocker count and archive path |
| `state.clear-blocker` | `TEXT` | alias for resolve-blocker |
| `state.add-deferred` | `CATEGORY TEXT [--status TEXT --milestone NAME]` | appended Deferred Items row |
| `state.advance-plan`, `state.update-progress` | none | current phase plan/progress fields from actual artifacts |
| `state.record-metric` | `[--phase N --plan P --duration TEXT --tasks N --files N]` | appended metric row |
| `state.sync-todos` | none | STATE Pending Todos count synchronized from records |
| `requirements.mark-complete`, `requirements.complete`, `requirements.reopen` | `ID...` | updated requirement IDs and traceability status |
| `requirements.set-status` | `ID Pending|"In Progress"|Complete|Deferred|Blocked` | changed/previous/status/id; modifies only traceability status |
| `requirements.close-phase` | `N [--requirements ID...]` | changed/unknown IDs; no matching ownership fails |
| `requirements.outstanding` | none | outstanding traceability rows/count, excluding Complete/Deferred |
| `quick.create` | `DESCRIPTION` | `id, quick_id, description, status, created, directory, path` |
| `quick.get` | `ID` | quick task record |
| `quick.update` | `ID [--status TEXT --commit SHA --verification TEXT --issue URL --pr URL]` | updated quick task |
| `quick.list` | `[--status open|STATUS]` | `tasks[], quick_tasks[], count` |
| `todo.add` | `TITLE [--area TEXT --severity minor|major|blocker --phase N --files PATH... --problem TEXT --solution TEXT --description TEXT]` | created todo path and metadata |
| `todo.list` | none | `todos[], count` |
| `todo.match-phase` | `N` | todos explicitly assigned to phase |
| `todo.complete` | `FILENAME_OR_PATH` | archived completed todo; published issues require stable closed readback and accepted UAT evidence |
| `todo.issue-preview` | `FILENAME_OR_PATH --title TITLE --body-file FILE [--labels LABEL...]` | content-bound preview packet |
| `todo.issue-publish`, `todo.issue-update` | same preview args plus `--preview-token TOKEN` | published/readback packet |
| `frontmatter.get` | `PATH [--field DOTTED_FIELD]` | frontmatter map or field |
| `frontmatter.set` | `PATH --field DOTTED_FIELD --value YAML_OR_JSON_VALUE` | updated field/path |
| `frontmatter.validate` | `PATH --schema plan|summary|verification` | `valid, errors[]`; invalid exits 1 |
| `plan.task-structure` | `PLAN_PATH` | `tasks[], count`; each task has name/type/tdd/files/read_first/action/verify/done |
| `verify.plan-structure` | `PLAN_PATH` | `valid, errors[], task_count`; invalid exits 1 |
| `verify.artifacts`, `verify.key-links` | `PLAN_PATH` | `valid, findings[]`; missing/stub/unwired obligation exits 1 |
| `verify.commits` | `SHA...` | `valid, missing[]`; absent/nonancestor commits exit 1 |
| `check.evaluation-scope` | `[--phase N --plan P --ref REF --since DATE --committed-since DATE --max-commits N --pathspec PATH... --milestone-bound --commits-only]` | commits/files/count; commits-only raw prints one SHA per line |
| `check.verify-command-paths`, `check.verify-failure-directions` | `N [--dir DIR]` or `--plan PATH` | `valid, findings[]`; findings exit 1 |
| `check.decision-coverage-plan`, `check.decision-coverage-verify` | `N [--dir DIR]` | `passed, decisions[], uncovered[], files[]`; uncovered IDs exit 1 |
| `check.ui-plan-gate` | `N` | `blocked, required, reason`; required unapproved UI spec exits 1 |
| `check.tdd-red-evidence` | `RECORD.json` | verdict/evidence; raw verdict string; unreadable exits 69, rejected evidence exits 1 |
| `task.is-behavior-adding` | `TASK_JSON` | `is_behavior_adding, reason` |
| `user-story.validate` | `STORY` | `valid, errors[], slots` |
| `verification.status` | `N_OR_DIRECTORY` or `--quick ID` | report metadata plus status/route/next_action/next_command |
| `verification.resolve-file` | `N_OR_DIRECTORY` or `--quick ID` | report path |
| `verification.fingerprint` | `N_OR_DIRECTORY` or `--quick ID`, plus `[--files PATH... --covered-files PATH...]` | writes report fingerprint/revision, returns fingerprint/path |
| `verification.current` | `N_OR_DIRECTORY` or `--quick ID` | `current, reasons[], revision, verified_revision, fingerprint` |
| `verification.append-audit` | `REPORT_PATH [--heading TEXT] --body TEXT` or `--file FILE` | `appended, path`; identical last block is no-op |
| `verification.run-checks` | `[--checks ID... --force]` | status/passed/revision/check receipts; failed check exits 1 |
| `verification.check-status` | none | current matching receipts and passed boolean |
| `uat.classify-coverage` | `SUMMARY_PATH` | automated/human/not-testable buckets |
| `uat.render-checkpoint` | `UAT_PATH` | next pending test and checkpoint text, or complete=true |
| `uat.complete-session` | `UAT_PATH [--message TEXT]` | complete session and commit; pending tests block |
| `audit-uat` | none | outstanding UAT and human verification items/count |
| `audit-open` | none | UAT, verification, blockers, todos and counts |
| `spec.edge-probe` | `REQUIREMENTS.json [--resolutions FILE]` | items and coverage; invalid shape exits 2 |
| `spec.section` | `SPEC.md edges|prohibitions` | `supplied, items[]` |
| `summary-extract` | `PATH... [--fields FIELD,FIELD]` | extracted summary fields, one record or summaries[] |
| `package-legitimacy` | `PACKAGE... [--registry npm|pypi|crates]` | package verdicts and registry metadata |
| `run-with-timeout` | `[--timeout SECONDS] -- COMMAND ARGS...` | exit_code/stdout/stderr/timed_out; timeout exits 124 |
| `progress.bar` | `[PERCENT]` | percent/bar; default is actual roadmap progress |

| Coordination verb | Arguments | Result |
|---|---|---|
| `init.phase-op/plan-phase/execute-phase/verify-work/ship/code-review` | `N [--fix]` | host/config, models/efforts, phase/artifact/plan/wave/context packet |
| `init.new-project/onboard/new-milestone` | none | project/codebase existence and model/config packet |
| `init.progress/complete-milestone` | none | roadmap progress and all_phases_verified |
| `init.quick` | `DESCRIPTION [--discuss --research --validate --full]` | quick root/model/config packet and selected flags |
| `init.quick-batch` | none | quick root/open batches/capacity/isolation/model packet |
| `init.todos` | none | pending todos plus initialization packet |
| `quick-batch.parse-args` | `--stdin` | parsed jobs/validate/research/resume/tasks/file; unknown flags fail |
| `quick-batch.create` | `--file FILE [--base-revision SHA --id ID]` | batch path/id/items and one quick record per item |
| `quick-batch.update` | `ID --updates JSON_ARRAY` | batch with updates merged by quickId |
| `quick-batch.resume` | `ID [--current-base-revision SHA]` | eligible/in_flight/done/base_drift |
| `quick-batch.complete` | `ID [--outcomes JSON_ARRAY]` | complete batch; pending/running items block |
| `quick-batch.effective-concurrency` | `[--jobs N --task-count N --capacity N --mutating --isolation MODE]` | concurrency/effective_concurrency |
| `quick-batch.filter-executed` | `--eligible JSON_ARRAY --executed JSON_ARRAY` | spawnEligible/alreadyExecuted |
| `quick-batch.merge-eligible` | `--wave-order JSON_ARRAY --ready JSON_ARRAY` | mergeable prefix |
| `quick-batch.spawn-plan` | `--eligible JSON_ARRAY --capacity N --in-flight N_OR_JSON_ARRAY` | spawn/pending/available |
| `quick-batch.merge-routing` | `--kind merge_failed|conflict|scope_violation [--detail TEXT]` | action/message/preserveWorktree |
| `quick-batch.verification-routing` | `--status STATUS` | merge/fix/human/block route |
| `quick-batch.cleanup-entry` | `QUICK_ID --path PATH --branch BRANCH` | quickId/path/branch/merged |
| `session.open`, `session.adopt` | `phase|quick|milestone|onboard LABEL [--base REF]` | kind/label/branch/worktree/base/status/created/adopted/reused |
| `session.status` | none | sessions/count/open/open_count |
| `session.close` | `BRANCH` | closed session; dirty/unintegrated/active checkout blocks |
| `worktree.create` | `PLAN --phase N [--base REF --branch BRANCH --files PATH... --deletions PATH...]` | recorded plan/path/worktree/branch/base/files/deletions |
| `worktree.record-agent` | `PLAN --phase N --branch BRANCH --path PATH [--base REF --files PATH... --deletions PATH...]` | verified recorded worker |
| `worktree.list` | none | worktrees/count |
| `worktree.health` | none | root_ignored/warnings |
| `worktree.merge-wave` | `--phase N` | workers/merged/removed/preserved/wave_clean; protected/dirty integration blocks |
| `worktree.cleanup-wave` | `--phase N` | removes recorded integrated clean workers; preserves unmerged workers |
| `worktree.reap-orphans` | none | pruned Git administrative records; never removes live checkouts |
| `pr.open` | `[BRANCH] --title TITLE --body-file FILE [--base REF --phase N]` | read-back draft PR, created boolean; title can default to last subject |
| `pr.status` | `[BRANCH]` | provider PR or exists=false |
| `pr.checks` | `[BRANCH] [--timeout SECONDS]` | check status/count/failed/pending/url; pending/failed exits 1 |
| `pr.ready` | `[BRANCH] --phase N` or `[BRANCH] --quick ID` | ready after current verification, PR-head revision and issue-link gates |
| `pr.merge` | `[BRANCH] (--phase N or --quick ID) --confirm` | merged/url after current verification, matching PR revision, issue-link and provider checks |
| `pr.sync` | none | fetch/prune origin result; does not merge branches |
| `cleanup.preview` | none | approval_token/entries/count |
| `cleanup.apply` | `--approval-token TOKEN --confirm` | removed/count; any resource drift fails |
| `handoff.limits` | none | enabled/context_window/context_percent/context_tokens/threshold_tokens/binding |
| `handoff.write` | `ID --reason TEXT [--remaining TEXT... --completed TEXT --findings TEXT... --files-read PATH... --phase N --plan P --summary PATH --artifact PATH --transcript FILE --agent ID --role ROLE --next TEXT --next-action TEXT --blockers TEXT --notes TEXT --digest TEXT --continuation TEXT --scope TEXT --requested-fields TEXT]` | durable continuation record; reason optional on existing record; named fields merge, list fields retain every value, transcript attribution accepts only contained user-assigned paths |
| `handoff.list` | none | unconsumed handoffs/count |
| `handoff.read` | `ID` | record and continuation text |
| `handoff.consume` | `ID` | `consumed, id, plan`; atomically preserves the consumed audit record and removes it from the pending queue; consumed IDs cannot be rewritten |
| `spec.prohibition-project` | `INPUT.json` | projects preselected stable rows; `items, coverage`; never supplies semantic recall |
| `spec.prohibition-proof` | `DESCRIPTOR.json --subject REAL_PATH [--timeout SECONDS]` | actual violation/clean/real control observations; proved green or nonzero unprovable flagged disposition |
| `codebase.record` | `MAP... [--paths PATH...]` or `--maps MAP...` | records map revision and paths |
| `codebase.status` | none | map freshness, commit age and changed files |
| `planning.integrity`, `planning.validate` | `[--files PATH... --strict]` | schema and cross-record valid/warnings/errors/checked; validate warns by default, strict explicitly fails |
| `planning.review` | none | snapshotDigest/digest/repairs/findings/checked/repairable/valid |
| `planning.repair` | `[--apply --expect DIGEST]` | same preview plus applied/repaired; stale snapshot blocks |
| `planning.archive` | `--paths PATH... [--expect DIGEST --confirm]` | exact retired-record preview, or archive manifest/id/path |
| `planning.archive` | `MILESTONE --scope phases|quick --confirm` | outgoing milestone archive; destination collision blocks |
| `planning.archives` | none | archives/count |
| `planning.archive-recover` | `ARCHIVE_ID [--expect DIGEST --confirm]` | recovery preview recoveryDigest, or recovered manifest; target collision blocks |
| `milestone.create` | `NAME [--goal TEXT]` | created milestone and persisted goal |
| `milestone.list` | none | milestones/count/active |
| `milestone.complete` | `NAME --confirm [--no-archive-phases]` | completed milestone; unverified phase blocks |

## Initialization packet contract

All `init.*` results include these keys:

| Key | Value |
|---|---|
| `root`, `planning_dir`, `templates_dir` | absolute project, planning, and runtime template paths |
| `planning_exists`, `project_exists`, `state_exists`, `roadmap_exists`, `initialized` | actual record existence; initialized requires all four core records |
| `project_path`, `state_path`, `roadmap_path`, `requirements_path` | absolute existing file path or null |
| `config`, `commit_docs`, `host`, `response_language` | effective configuration and host |
| `state`, `milestone` | parsed state view and active milestone |
| `has_codebase_map`, `is_brownfield`, `checks_configured` | actual source/map/check presence |
| `sub_repos` | `.gitmodules` paths, empty when absent |
| `research_enabled`, `plan_checker_enabled`, `nyquist_validation_enabled`, `text_mode` | configured workflow gates |
| `parallelization` | configured boolean or enabled field; defaults true |
| `branching_strategy`, `branch_name` | mandatory phase isolation strategy and actual current branch |
| `section_manifest` | null: load kept workflow steps as the safe superset |
| `models`, `efforts` | maps keyed by final role name |
| `<role_with_underscores>_model`, `<role_with_underscores>_effort` | same per-role values as maps |
| `researcher_model/effort`, `checker_model/effort`, `reviewer_model/effort`, `fixer_model/effort` | aliases for phase-researcher, plan-checker, code-reviewer, targeted-fixer |
| `fix` | explicit `--fix` echo |
| `paths` | core record/root/planning/template paths, plus phase path when found |
| `context_window` | configured model context window |
| `agents_installed`, `missing_agents` | actual required role-file availability; missing required model resolution fails explicitly |
| `pending_todos`, `open_quick` | actual pending todos and nonterminal quick records |
| `milestone_phases`, `incomplete_phase` | parsed roadmap phases and first incomplete phase or null |

Role maps cover executor, planner, verifier, phase-researcher, plan-checker,
code-reviewer, doc-writer, doc-verifier, integration-checker,
security-auditor, nyquist-auditor, ui-researcher, ui-checker, ui-auditor, scout,
targeted-fixer, and codebase-mapper. A missing required role fails explicitly.
Codex reads native TOML model/effort definitions from
`bin/install-assets/codex-agents` in source, or the installed `.codex/agents`.
Claude reads `agents.<final-role>` configuration. Scout and targeted-fixer have
fixed Codex `gpt-6-luna`/`high` and Claude `haiku`/`inherit` policies.
`code-fixer.md` remains readable method context and is never a dispatch role;
direct resolution fails with agent-method-only. Compatibility code_fixer/fixer
model/effort fields resolve targeted-fixer policy. The dispatch map omits the
method-only name. Isolation defaults to `auto` and negotiates the host's supported
worktree mode; no supported setting disables isolation.

`init.phase-op`, `init.plan-phase`, `init.execute-phase`, `init.verify-work`,
`init.ship`, and `init.code-review` add this shared phase packet:

| Key | Value |
|---|---|
| `phase_found` | true only when the requested phase directory exists |
| `phase`, `phase_number`, `padded_phase`, `phase_padded`, `number` | canonical padded identifier, e.g. `01` or `01.1` |
| `phase_dir`, `directory` | absolute phase directory |
| `phase_name`, `phase_slug` | roadmap title and directory slug |
| `phase_status`, `goal`, `phase_req_ids` | roadmap status/goal/requirement IDs |
| `plans`, `incomplete_plans` | ordered PLAN filenames, including `-PLAN.md` suffix |
| `plan_records` | parsed plan metadata records with id/path/complete and frontmatter fields |
| `plan_count`, `plan_count_all`, `summary_count`, `incomplete_count` | actual artifact counts |
| `summaries` | ordered SUMMARY filenames |
| `waves` | map from wave number string to plan identifier array |
| `artifact_files` | all artifact filenames |
| `artifacts` | grouped plan/summary arrays and single context/research/verification/validation/ui_spec/security/review/uat filenames or null |
| `has_context`, `has_research`, `has_plans`, `has_reviews`, `has_verification` | actual matching artifacts |
| `context_path`, `research_path`, `verification_path`, `validation_path`, `ui_spec_path`, `security_path`, `review_path`, `reviews_path`, `uat_path` | absolute existing path or null |
| `prior_context` | prior phase SUMMARY path/content packets |
| `prior_verify_commands` | nearest prior phase's verify commands, each with phase/plan/task/command; independent of context window |
| `threat_id_duplicates`, `threat_id_duplicate_count` | declared threat IDs appearing in multiple plans and their plan IDs |
| `granularity` | configured planning granularity, default standard |
| `code_review`, `code_review_depth`, `code_review_depth_overrides` | configured review policy |
| `last_review_commit` | last commit touching the phase REVIEW file, or null |
| `expected_phase_dir` | actual directory, or expected roadmap-derived directory when absent |
| `has_spec`, `spec_path` | actual SPEC existence and path |
| `research_partial` | true when actual RESEARCH frontmatter declares partial/incomplete/in_progress |

When the requested phase is absent, initialization returns `phase_found:false`,
`phase_dir:null`, the requested `phase_number`, empty plan/requirement arrays, and
zero plan/incomplete counts. Consumers must check `phase_found` before reading
the remaining phase-only keys. `init.*` does not change checkouts automatically;
use `phase.locate N` first, then invoke initialization from its returned worktree.

`init.quick` adds description/quick_dir and discuss/research/validate/full flags.
`init.quick-batch` adds quick_root/quick_dir/open_batches/capacity/isolation.
`init.todos` adds todos/count. `init.progress` and `init.complete-milestone` add
roadmap phases/counts/percent, progress_percent, and all_phases_verified.

## Canonical security tracking

| Verb | Arguments | Result |
|---|---|---|
| `phase.threat-review` | `N --entries-file FILE` | exact checklist lookup, risk/current+linked PR candidate evidence, pending reasons and ready boolean; read-only |
| `phase.threat-preview` | `N --entries-file FILE --variant "Security risk"` | reviewed checklist/standalone bodies and source/template/origin/provider-bound previewToken; refuses Pending review |
| `phase.threat-publish` | same plus `--preview-token TOKEN` | published container/standalone URLs and actual provider-rendered entry links; consumes before provider writes |
| `phase.threat-audit` | `N` | ready/pending; checks each PLAN's declared issue/heading target by provider readback; Pending exits 1 |
| `quick.threat-review/preview/publish/audit` | same arguments with real quick `ID` replacing phase `N` | same contracts in the actual quick directory; no phase record is fabricated |

The entries file is a nonempty JSON array. Each entry supplies `key`,
`heading`, `plan` (the phase-local PLAN filename), `threat_id`, boolean `planned`,
`owner`, `scope_acceptance`, `assessment_uncertainty`, `lifecycle_outcome`,
`next_action`, `revision_check_evidence`, `aliases_occurrences`, and `match_review`.
The stable BODY heading is Entry identity; optional `id` retains an existing
caller alias and never replaces the canonical risk key or source Threat ID.
The stable canonical key includes repository, surface/control and failure
mode/remediation scope; review evidence must establish that identity. A match
review supplies `disposition: existing|no-match|pending`, cited `evidence`,
`reviewed_issue_urls`, `reviewed_pr_urls`, and `url` for an existing canonical
issue. Optional `heading_url` must match an actual rendered provider anchor.

Every planned entry cites its own PLAN's six-column register:
`Threat ID | Category | Component | Severity | Disposition | Mitigation Plan`.
Registers stay in their PLANs; threat identities do not change during phase
renumbering. Publication searches open and closed issues for the exact title
`chore(security): phase {padded-phase-id} security checklist` with label
`phase-security-checklist`. Multiple containers or unavailable lookup stay
Pending. Existing actionable full-scope identities take precedence. An unresolved
closed match or closed checklist requires independent reopening authority;
these verbs never reopen or close issues.

Quick tracking resolves the actual QUICK.md directory and padded ID. Its exact
title is `chore(security): quick {quick-id} security checklist` and its dedicated
label is `quick-security-checklist`. Preview identity binds scope kind, ID and
actual directory, so a phase and quick task cannot share an approval accidentally.
PLAN/SUMMARY/VERIFICATION frontmatter uses exactly one `phase` or `quick` identity.

All new planned risks, including accepted and deferred risks, receive separate
stable `###` entries under Risk assessment and lifecycle in the single checklist.
The container uses the same eight-heading Security risk variant as standalone
risks. Existing canonical issue identities
are linked from their entries. Entry fields are Entry identity, Canonical risk
key, Aliases / occurrences, PLAN / Threat ID, Owner, Scope / acceptance,
Assessment / uncertainty, Lifecycle / outcome, Next action, Revision / check evidence,
and Canonical reference. The PLAN remains the owner of severity and mitigation.
Reruns preserve headings; a rename fails until references are repaired and read
back. Returned URLs come from actual provider-rendered anchors, never a computed
slug. Missing anchors leave references Pending.

A new unplanned threat requires a standalone Security risk issue, or an existing
full-scope match. Supply `standalone_body` with these exact ordered `##` headings:
Security concern; Affected surface and behavior; Impact; Risk assessment and
lifecycle; Safe evidence; Requested remediation; Scope and acceptance; Related
links. The body carries the risk key, source aliases, severity rationale and
uncertainty, owner, observed status, mitigation/safe next action, and matching
resolution/check evidence or an explicit Pending dependency. A checklist-only
entry cannot satisfy this route.

Provider mutation is followed by exact content readback. An uncertain create is
searched/read back by exact container identity or standalone title and full body;
if it cannot be proven, the consumed attempt blocks retry. Partial published
results stay in the durable preview record. After publication the coordinator
updates each PLAN link from the returned actual target, and an independent
issue-link audit must read it back before readiness. `phase.handoff` and PR
readiness enforce those target checks. Structural validation proves shape only:
it does not prove safe content, semantic matches, human acceptance, or mitigation
correctness. A checked entry, accepted risk, or merge never authorizes closure.
