# Phase runtime

`phase.py` performs every planning-record read and write that the
[workflows](../workflows/) describe. Workflows orchestrate — they decide what to
do, which agents to spawn and what to ask the user. The runtime owns the records:
phase numbering, slugs, directory layout, the roadmap checklist and progress
table, STATE.md frontmatter derivation, todos, quick tasks and milestones.

A workflow that edits those files directly will drift from the runtime. Go
through a verb.

Python 3.11+ and PyYAML are required; install `requirements.txt` into the host's
virtual environment. Git is required for the commit verb and for repository-root
resolution.

## Invocation

One call shape:

```bash
python .ai/runtime/phase.py query <verb> [positional ...] [--option value ...] [--raw]
```

Every verb prints JSON on stdout. A handled failure prints
`{"ok": false, "error": "...", "code": "..."}` and exits 1. An unhandled error
raises with a traceback, so a defect is never mistaken for a handled outcome.

`--raw` prints a bare scalar for shell capture, where the verb returns one.

Workflows do not hard-code the path. They paste the launcher from
[`_runtime.snippet.sh`](../workflows/_runtime.snippet.sh), which resolves the
runtime from the repository namespace (`.ai`, `.claude` or `.codex`) or the host
config directory, then call `phase_run query ...`.

## Verbs

### Context bundles

A phase workflow runs `phase.locate <phase>` before its `init.<name>` bundle. It
parses the locator result, selects the returned worktree, then loads one init
bundle there. Other workflows load their applicable bundle directly. Bundles
never mutate anything.

| Verb | Returns |
|---|---|
| `init.phase-op <phase>` | The shared phase view: numbering, directory, artifacts, roadmap entry, state |
| `init.plan-phase <phase>` | Phase view plus planning models, agent availability, prior context |
| `init.execute-phase <phase>` | Phase view plus the plan index, verification status, check configuration |
| `init.verify-work <phase>` | Phase view plus verification status and the configured checks |
| `init.new-milestone` | Milestones, open phases, next phase number, planning models |
| `init.complete-milestone [version]` | Milestone membership and whether it is ready to close |
| `init.todos` | Pending todos plus `pending_todos_markdown` ready for STATE.md |
| `init.progress` | Roadmap totals, progress bar, next phase, incomplete-phase invariant |
| `init.quick` | Quick tasks, open tasks, models, check configuration |

Every bundle also carries `commit_docs`, `response_language`, `text_mode`,
`context_window`, `date`, `timestamp` and a `paths` map.

### Phases

| Verb | Effect |
|---|---|
| `phase.locate <phase>` | Read-only phase lookup; returns `phase_found`, `padded_phase`, absolute `worktree` or null, `branch`, `session` and `source` |
| `phase.add <description> [--goal G] [--requirements IDS]` | Append the next integer phase; create its directory; update the roadmap and checklist |
| `phase.insert <after> <description> [--goal G]` | Insert a decimal phase after `<after>`, marked `(INSERTED)` |
| `phase.remove <phase> [--force] [--no-renumber]` | Remove a future phase, renumber later phases, rename their directories and files |
| `phase.edit <phase> [--name] [--goal] [--depends-on] [--requirements]` | Edit fields in place; number, position and plan checklist preserved |
| `phase.complete <phase>` | Require ready phase.handoff before ticking plans/checklist or refreshing progress |
| `phase.handoff <phase>` | Validate explicit execution SUMMARY issue_refs and optional CONTEXT declarations; report ready/blocked/retryable |
| `phase.issue-declare <phase> <record> [--entries-file PATH --expect-digest TOKEN]` | Preview existing record declarations/digest, or apply a reviewed JSON list preserving publication identity and kind |
| `phase.issue-preview <phase> <record> <id> [--related-pr URL]` | Selected entry private review, origin-pinned candidates/context and previewToken |
| `phase.issue-publish <phase> <record> <id> --preview-token TOKEN --title TITLE --body-file PATH --variant VARIANT (--existing-issue URL \| --no-match)` | Reuse/create with shared TODO duplicate/uncertain-intent recovery; link exact selected entry |
| `phase.issue-update <phase> <record> <id> --preview-token TOKEN --title TITLE --body-file PATH --variant VARIANT` | Fresh reviewed title/body update with preserved local/remote kind and verified readback |
| `phase.reconcile-todos <phase> --pr URL --todos NAME...` | Reconcile exact Folded Todos selection only after phase-session MERGED/CLOSED evidence; pending/already-completed are retryable/idempotent |
| `phase.next-decimal <after>` | The decimal number an insert would allocate |
| `phases.list` | Active and archived phases with status, counts, directory and execution completeness; `count` is active, with separate `archived_count` and `total_count` |
| `find-phase <number-or-slug>` | Resolve a phase by number or name fragment |
| `phase-plan-index <phase>` | Plan files on disk with their declared dependencies and summaries |

`phase.remove` refuses a phase with completed plans or a non-empty directory
unless `--force` is passed.

### Sessions

| Verb | Effect |
|---|---|
| `session.status` | Open session entries with kind, label, status, worktree and branch |
| `session.open <kind> <label>` | Reuse or open a session worktree from the primary checkout |
| `session.adopt phase <phase>` | Register the selected linked worktree and existing branch without switching, copying or changing files; reject unsupported or conflicting checkouts |

### Conditional native source entry

`prewrite.request`, `prewrite.begin` and `prewrite.confirm` support the
conditional Claude same-existing-agent route described in
[same-agent native entry](../references/same-agent-worktree.md). Their
angle-bracketed values below are placeholders, not literal shell syntax.

| Verb | Effect |
|---|---|
| `prewrite.request <phase|quick> <label> --mode <new|existing>` | Bootstrap a known workflow unit before an edit; requires no open session for `new`, exactly one validated open session for `existing` |
| `prewrite.begin <request> <phase|quick> <label> --mode <new|existing>` | Bind the request to its source and unit; for `new`, reserve a fresh native creation name and pinned local base; for `existing`, return the validated session unchanged |
| `prewrite.confirm <request>` | From the destination's actual default cwd, validate request and Git facts; adopt a new native checkout or confirm reuse of the existing session |

An intercepted source edit is cancelled in full and is never replayed. The hook
returns its request ID and does not precreate a checkout. The same caller must
positively gate its actual advertised `EnterWorktree` schema, role eligibility,
policy and trusted registered `WorktreeCreate` hook before invoking native
entry. Creation accepts only the fresh reserved name and creates from the
captured local HEAD under the configured ignored root. Existing destination or
branch reuse is refused by this creation route; use the native existing-path
form when the exact validated ordinary session is already open, and honor any
required path approval.

For an existing session, confirmation preserves its ownership, accumulated
HEAD and historical base. Confirmation returns `git_facts_verified: true` and
`host_binding_verified: false`: runtime checks do not authenticate the host
transition, permissions or loaded project context. Observe native completion,
prove default destination context, reload instructions/configuration, and
freshly read the destination before rebuilding the intended edit once. Later
tools and turns must continue from destination defaults. Shell `cd`, per-call
cwd/path overrides and replacement children do not establish movement.

`CLAUDE_CODE_SESSION_ID` is the documented environment correlation used when
available to tool subprocesses. A supplied CLI session/agent ID is a binding
claim, not authentication; `${CLAUDE_SESSION_ID}` in skill content is
substitution, not a shell environment variable. Codex source denial reports
that this template integration has no authenticated same-thread controller;
it does not claim that Codex products cannot move conversations.

### Pull requests

| Verb | Effect |
|---|---|
| `pr.open <branch> [--phase N] [--base BASE] [--title TITLE] [--body BODY] [--body-file PATH] [--draft]` | Create the branch's PR or update that same PR |

For an existing PR, an explicit `--base` retargets it; omitting `--base`
preserves its current target, including a nondefault parent branch. A base-only
edit returns `created: false`, `updated: true` and the refreshed PR fields.
With no base, title or body requested, no edit runs and `updated` is false.
`--body-file` takes precedence over `--body`.

For a new PR, `--base` selects its target; omission uses the repository's
existing default-base fallback. `--draft` creates a draft, and omission creates
a ready PR. The draft option applies only to creation: updating an existing
draft or ready PR preserves its draft state. A failed edit returns the existing
handled `gh-failed` error rather than a successful update.

### Roadmap and state

| Verb | Effect |
|---|---|
| `roadmap.get-phase <phase>` | One phase's parsed entry |
| `roadmap.analyze` | Counts, the next open phase, and phases blocked on dependencies |
| `roadmap.set-plans <phase> --plans <entry> ... [--summary TEXT]` | Replace a phase's complete plan checklist and refresh roadmap and state progress |
| `roadmap.update-plan-progress <plan-id> [--undo]` | Tick or untick one plan and re-derive state |
| `state.get [key]` | The parsed STATE.md view |
| `state.record-session [--stopped-at] [--resume-file] [--status]` | Update Session Continuity |
| `state.begin-phase <phase> [--status]` | Point Current Position and Current focus at a phase |
| `state.update-progress` | Re-derive counters and the progress bar from the roadmap |
| `state.advance-plan <plan-id>` | Tick a plan and update state in one call |
| `state.add-decision <text> [--rationale] [--outcome]` | Digest it and record it in PROJECT.md Key Decisions |
| `state.add-blocker <text>` | Add to Blockers/Concerns |
| `state.add-roadmap-evolution <text>` | Add to Roadmap Evolution, creating the section |
| `state.clear-blocker <match>` | Remove a resolved blocker |
| `state.clear-entry <section> <match> [--level]` | Remove any digest entry |
| `state.add-deferred <category> <item> [--status] [--milestone]` | Write a Deferred Items row |
| `state.sync-todos` | Replace the Pending Todos body from the todos on disk |
| `project.add-decision <decision> [--rationale] [--outcome]` | Write one PROJECT.md Key Decisions row |
| `project.decisions` | The Key Decisions table, parsed |

STATE.md's Markdown body is authoritative; its frontmatter counters are
re-derived from ROADMAP.md on every write, so the two cannot disagree. Writers
serialize on `.planning/.lock`.

`roadmap.set-plans` takes one phase number and a complete replacement list of
quoted `NN-NN: description` entries. The `plans` option consumes all following
non-option arguments, so pass one `--plans` followed by every entry; do not
repeat the option. An optional single-line `--summary` sets the phase's Plans
label (the default is the number of plans). For example:

```bash
python .ai/runtime/phase.py query roadmap.set-plans 3 --plans \
  "03-01: Establish the request path" \
  "03-02: Add the response handling"
```

The verb validates that the phase exists, the list is nonempty, every entry is
one line with a unique ID belonging to that phase and a nonempty description,
and the existing checklist is well formed. Only the list under the phase's
single `Plans:` anchor is replaced; unrelated prose and checkboxes before or
after that list are preserved. Duplicate anchors or plan rows outside that
list are rejected as ambiguous. A missing anchor is created only when no
existing plan rows would be stranded. It replaces that phase's whole plan
list; it does not append. Completed IDs cannot be dropped, and their ticks are
retained when those IDs remain in the replacement list. It also updates the
phase checklist, progress table, plan count, and derived STATE.md progress.
Completion dates are retained for phases that remain complete, and a prior
`Shipped` status is retained while the phase remains complete; other status
follows the current plan-derived status. For the current
phase, its plan position is recalculated and its position status becomes
`Complete` when all remaining plans are done, preserving an existing `Shipped`.
While the phase is open, a meaningful planning or execution status is preserved;
a stale `Complete`, `Phase complete` or `Shipped` position is reset if the
replacement reopens the phase. For another phase, the current position is left
alone. Invalid entries, malformed existing rows, a missing phase or roadmap,
attempted removal of completed work, or STATE.md missing its required position
fields return a handled error and leave both records unwritten. The runtime
prepares both records before writing them, then writes ROADMAP.md followed by
STATE.md; the pair is not a crash-atomic transaction.

`state.begin-phase` sets the Current Position phase and status, updates Current
focus to the phase name when that field exists, records the activity date, and
sets STATE.md's planning/executing frontmatter status.

STATE.md is a digest, so its sections are capped: Decisions and Roadmap
Evolution keep 5 entries, Blockers/Concerns and Deferred Items keep 10. Only the
first two trim themselves, because only they have a durable copy elsewhere: a
decision is written to PROJECT.md as it is added, and roadmap history is in
ROADMAP.md and git. The others are capped and reported by `planning.validate`,
so an open blocker is never dropped to make room for a newer one.

### Requirements and record conformance

| Verb | Effect |
|---|---|
| `requirements.list` | The Traceability table, parsed |
| `requirements.outstanding` | Requirements not yet Complete, Deferred or Dropped |
| `requirements.set-status <id> <status> [--phase]` | Set one requirement's Status cell |
| `requirements.close-phase <phase> [--requirements ...] [--status]` | Close out a passing phase's requirements |
| `planning.validate [--strict] [--skip ...]` | Report record drift; warn-only by default |
| `planning.integrity --files <record> ...` | Read-only strict schema diagnostic for selected active canonical records |
| `codebase.status` | Freshness of ARCHITECTURE.md and STACK.md, derived from git |

`planning.validate` returns `ok` with a warning list so a cosmetic finding never
stalls a session. `--strict` turns the same findings into a failure, for a caller
that asks for it.

### Planning commit and authored-content integrity

The shared [integrity contract](TEMPLATE-CONTRACT.md#planning-record-integrity)
lists every required CONTEXT/PLAN/SUMMARY field and its type, including reviewed
`issue_refs: []` or existing declaration mappings. Runtime `commit` validates
changed canonical active phase records from the complete staged index, including
relevant records omitted from `--files`. Invalid YAML, absent required keys and
wrong types return a record/key `planning-integrity` error before Git commits.
`planning.integrity --files ...` checks selected working records with the same
schema and failure convention. Ordinary `planning.validate` remains warn-only;
unchanged legacy, archive, maintenance, source-template and unrelated records are
not mass-migrated. The adoption skeleton stays instructional.

The standalone native PreToolUse checker handles Git index commits, selected
tracked working bytes for `--only`/explicit paths, tracked `--all` changes and
supported preceding adds. It preserves the real index, recognizes bounded
`-C`/`-c` and shell-wrapper forms, supports native string commands and shell argv
payloads, and exits 2 with actionable stderr on denial. Bash escape semantics
are separate from native Windows paths; transparent repeated command/env/exec/time
wrappers and Bash negation are recognized, while harmless diagnostics stay allowed. Ambiguous shell mutations,
interactive/pathspec-file commits and relevant custom clean-filter working bytes
are refused; stage separately and use a plain commit. The hook uses the installed
sibling runtime. Direct coverage requires coordinator-tested installer registrations
for `Bash`, `exec_command`, `shell_command` and `shell`; standalone tests do not
establish installed coverage or universal Git enforcement.

STATE changes preflight authored section preservation before safe writes. All
regular runtime dispatch paths snapshot existing STATE/ROADMAP, including phase,
roadmap, milestone/bookkeeping and planning repair. Authored loss after a write
returns `integrity_warnings` containing record, verb, section and content evidence,
including handled errors; no rollback is attempted. Owned fields, derived
frontmatter, newline normalization, explicit digest replacement/rotation,
generated roadmap rows, selected phase edits/removal, canonical milestone status
changes and conservative repair heading restoration are scoped exceptions.
Unknown child headings and unrelated prose remain protected. Read-only verbs do
not create planning records.

### Planning archives

| Verb | Effect |
|---|---|
| `planning.archive <phase\|adr\|quick> <id-or-path> [--apply] [--evidence PATH] [--replacement PATH]` | Preview one explicit archive selection; `--apply` moves it and updates references with a recovery journal |
| `planning.archives [--kind phase\|adr\|quick]` | Discover catalog entries, evidence, replacement paths and recovery journal states |
| `planning.archive-recover <recovery-id> [--apply]` | Preview or apply a guarded rollback of an applied or interrupted archive |

Archive and recovery default to read-only previews. Preview returns `dry_run`,
`state`, `entry`, `moves`, `rewritten_files` and a deterministic `recovery_id`.
`--apply` is the explicit mutation boundary. Select one record by phase number,
exact directory ID, ADR number/stem, or an exact direct-child path such as
`.planning/phases/01-foundation`. Quick tasks use their full directory IDs.
Traversal, ambiguous selection, symlinks, Windows junctions and pre-existing
destinations are refused. Records never qualify because of their age.

Phases move to `.planning/archive/phases/<original-directory>` without renumbering
any artifact. On-disk PLAN IDs must exactly match the registered roadmap plans,
and every PLAN file needs its SUMMARY. Explicit legacy evidence cannot bypass
missing, unregistered, unsummarized or affirmatively incomplete plan work. Without
valid legacy evidence, every roadmap plan needs a `status: complete` SUMMARY with
authored Accomplishments, and the phase needs a `status: passed` VERIFICATION. An incomplete
roadmap checklist, blocked/in-progress summary, or current active phase is refused.
The historical phase block remains in ROADMAP.md with an `Archived` destination;
its overview checklist and active progress row are removed. Active counts and
STATE progress exclude it. `find-phase`, `phase-plan-index`, phase bundles,
verification lookup, prior context and dependency completion still find it.
Archived phase mutation requires recovery first. Integer and decimal allocation
reserve archived IDs; removal cannot renumber across archived successors.

ADRs move from `.planning/decisions/` to `.planning/archive/decisions/`. A selected
ADR needs superseded evidence and one existing accepted replacement ADR, supplied
by `superseded_by` or `--replacement`. The old `superseded_by` and the replacement's
`supersedes` preserve both directions; the original argument remains intact.
An accepted/proposed ADR cannot become superseded through a replacement option
alone.

Quick tasks move to `.planning/archive/quick/<original-directory>`. `complete`
needs a completion value plus authored Verification. `abandoned` or `obsolete`
needs `archive_reason` frontmatter or authored `## Retirement` prose. `open` and
`in_progress` are always refused. `quick.update` accepts `obsolete` as an explicit
status, and sequence allocation reserves archived task IDs.

For legacy records missing the modern evidence format, `--evidence` may select a
planning Markdown record with these explicit fields:

```yaml
archive_kind: phase            # phase, adr or quick
archive_id: 01-foundation       # original directory ID, or ADR stem
archive_status: complete       # phase: complete; adr: superseded; quick: its terminal status
archive_reason: Recorded release evidence confirms this historical work completed.
```

The evidence option records the supplied claim and its source; it cannot bypass
an active/in-progress guard. It does not mark plans complete or invent verification.

Apply rebases local Markdown destinations and reference definitions in moved and
unmoved planning documents, plus repository-relative `.planning/...` references.
Internal links remain local, and moved documents' links to repository source are
rebased. `.planning/archive/catalog.json` and `INDEX.md` retain IDs, source,
destination, evidence, replacement and recovery ID. Later archives update catalog
links to records moved again.

Before moving, apply writes `.planning/archive/recovery/<recovery-id>.json` with
exact before/after bytes, intermediate moved bytes, directory shape and an integrity
checksum. Writes use flushed temporary files followed by replacement. The overall
operation is journaled, rather than a crash-atomic transaction; `archive-interrupted`
returns the ID to recover. Pending journals block further archive operations.
Recovery restores the original records and index bytes, retaining the journal.
It refuses edited records, added files/directories, changed path types or a damaged
journal before writing. Recover later operations first when shared indexes changed.
Repeated apply is a no-op; repeated recovery is a no-op. Reapplying the same restored
selection reuses its guarded journal and retains its recovery lifecycle history.
Recovery does not discard subsequently authored work or permanently delete history.

### Milestones, todos and quick tasks

| Verb | Effect |
|---|---|
| `milestone.list` | Declared milestones and which is current |
| `milestone.create <name> [--goal G]` | Declare a milestone in progress; demote any previous one |
| `milestone.complete <version> [--name N] --confirm` | Mark shipped and write the MILESTONES.md entry |
| `todo.add <title> [--problem] [--solution] [--area] [--severity] [--files]` | Write a pending todo |
| `todo.list [--state pending\|completed]` | Todos sorted by severity then age |
| `todo.complete <name>` | Move a pending TODO only when publication is resolved and any linked issue is verified closed; returns `completed` path |
| `todo.match-phase <phase>` | Score pending todos against a phase's name and goal |
| `todo.issue-preview <name> [--related-pr URL]` | Private selected-TODO input, current issue candidates, related PRs and review token |
| `todo.issue-publish <name> --preview-token TOKEN --title PUBLIC_TITLE --body-file PATH --variant VARIANT (--existing-issue URL \| --no-match)` | Validate the selected template shape, then link a reviewed issue or create one after explicit no-match; TODO stays pending |
| `issue.validate --variant VARIANT --body-file PATH` | Read-only template-derived structural validation for a public draft |
| `quick.create <description>` | Open `.planning/quick/YYMMDD-NNN-slug/` with its QUICK.md |
| `quick.list [--status]` | Active quick tasks, newest first; separate `archived_tasks`, `archived_count` and `total_count` preserve discovery |
| `quick.update <id> [--status] [--files] [--verification]` | Record progress or completion |

`milestone.complete` refuses without `--confirm`, and refuses while any phase in
the milestone is open. There is deliberately no force path: a milestone entry
claiming phases shipped when they did not is the record this exists to keep honest.

#### Declared phase issue handoffs

- Workers include an explicit `issue_refs` list in each first execution SUMMARY,
  including blocked/halted SUMMARYs and [] after reviewed no-leftover results.
  Legacy CONTEXT, planning-only records and the adoption skeleton need no new
  declaration. Existing CONTEXT declarations are included when present.
- Each entry has unique stable `id`, nonempty `summary`, canonical template
  `variant`, `state` (`unresolved`, `pending-human`, `resolved`,
  `blocked-publication`) and `relationship` (`resolving`, `followup`). Resolved
  and blocked-publication need nonempty `reason`; resolving requires resolved
  demonstrated acceptance. Pending-human requires followup. Blocked publication
  means incomplete tracking/retry, never a readiness exemption.
- Example private declaration draft for `phase.issue-declare`:

  ```json
  [{"id":"P1","summary":"Blank search fails","variant":"Bug","state":"unresolved","relationship":"followup"}]
  ```

  Preview without `--entries-file` returns `snapshotDigest`; apply with that
  `--expect-digest` and a separate reviewed JSON list. Existing issue identity,
  publication intent and selected variant are preserved. Source selection is an
  exact active-phase SUMMARY/CONTEXT basename or repository-relative path;
  traversal, links, another phase and stale snapshots fail before mutation.
- Publication writes existing `issueRepo`, `issueURL`, `issueNumber` and
  `issuePublication` fields in that entry. It reuses TODO origin verification,
  duplicate candidates, exact retry markers and persisted attempted intent.
  The separate reviewed public body/title is never copied from the private
  source. Provider failure returns explicit retryable blocked-publication;
  uncertain attempts keep their exact intent and never create another issue.
  Update requires canonical linkage, fresh preview, unchanged selected kind,
  structural validation before edit and verified remote readback. No issue is
  automatically closed by these operations.
- `phase.handoff` returns `ready`, `declarations`, `blocked`, `retryable` and
  `structuralOnly`; missing/malformed or unlinked unresolved declarations fail.
  `phase.complete` checks it before roadmap writes. `pr.open` automatically uses
  the branch's existing phase session; an explicit phase must match. It pins
  phase calls to origin, requires every canonical URL in the effective body,
  and rejects followup closing references (shorthand, repository-qualified or
  full URL), including body-omitted edits. File content takes precedence and
  the exact validated bytes are published. Remote pending UAT cannot be forged
  as resolving through a local status claim.
- Reconciliation requires exact filenames in CONTEXT's `### Folded Todos`, the
  session's canonical matching PR number/URL/head, MERGED readback and each
  linked CLOSED issue. CLOSED UAT with pending/unknown acceptance stays pending.
  Results contain per-item `completed`, `already-completed` or `pending`, reasons
  and a reconciliation-only `retry`. Unselected/reviewed-only TODOs remain.
  A successful merge command with missing/mismatched/non-MERGED readback returns
  `merged: false`, `retryable: true`; read back the same PR without another merge.
- These current GitHub guards reuse the existing provider seam; no provider
  extension is implemented here. Runtime validates declarations and observed
  fields, not omitted prose, semantic issue type or real human judgment. Direct
  gh/API changes bypass supported gates. `issue.validate` remains structuralOnly;
  `planning.validate` remains warn-only. Separate threat tracking is unchanged.

#### Reviewed TODO issue linkage

- `todo.add` assigns a stable UUID `todoId`. `todo.issue-preview` and
  `todo.issue-publish` accept one pending basename or safe unique partial name.
- Preview returns `file`, `todoId`, `repository`, `previewToken`, `privateLocal`,
  `candidates` and `relatedPRs`. `privateLocal` contains the complete local
  title/body/metadata and is private review input. Candidates are all open and
  closed issues; related PRs include the current branch and an optional
  same-repository `--related-pr` URL. Pull requests are not issue candidates.
  Candidate records include title, body, URL, number and state. A closed match
  must still be checked against the TODO's full scope; closed status alone is not
  proof the TODO is resolved.
- Compare candidate issue content and related PR context for semantic duplicates;
  the runtime returns evidence but does not deduplicate semantically. Reuse an
  actionable issue with `--existing-issue URL`; `--no-match` explicitly selects
  creation. An exact existing TODO marker is reused. Linking does not edit or
  close an issue.
- `--title` is a required, separately reviewed public title; it never defaults
  from the private local title. `--body-file` must be a separate, non-empty
  reviewed file, not the TODO. The runtime appends the stable
  `<!-- todo-id: UUID -->` marker. It does not redact or publish arbitrary local
  context for you.
- `--variant` must be an exact canonical name from the issue template: `Bug`,
  `Enhancement`, `Decision required`, `Security risk` or `UAT`. Publication checks
  headings/order and UAT table columns, sequential rows and Human acceptance
  fields before persisting a create attempt. Missing/unknown variants and missing
  or malformed schema fail closed. The schema is `templates/issue.md` beside the
  running runtime's namespace, including installed `.codex` and `.claude` trees.
  `issue.validate` runs the same check without provider calls or planning writes.
  Direct `gh`/API creates and edits bypass this gate. Structural success does
  not verify working URLs, actual UI controls, safe content or human decisions.
- The preview token binds the TODO snapshot, repository, issue candidates and PR
  context. Re-preview and review again when any input changes. Provider access
  requires a supported GitHub HTTPS, SSH or scp-style `origin`, GitHub CLI auth,
  the origin repository's issues enabled, and complete readable issue and PR
  pagination. Provider, auth, malformed response, repository or lookup failures
  block publication; `GH_REPO` cannot redirect the target.
- `issueRepo` records the verified `github.com/owner/repo`. `issuePublication`
  moves through `prepared`, `attempted` and `linked`; `prepared` stores the
  preview token and related PR, while `attempted` adds the reviewed public title
  and intent/snapshot digests before create.
- Before create, the runtime stores `issuePublication.state: attempted`, the
  reviewed public title and intent/snapshot digests. A potentially lost create
  response cannot be retried as a second create. Re-preview and submit the
  identical reviewed title/body to recover only one verified marker match;
  zero, multiple, unreadable or mismatched results remain unresolved.
- Linked metadata stores `issueRepo`, `issueURL`, `issueNumber` and
  `issuePublication.state: linked`. `todo.issue-publish` returns a verified
  `issueURL` only after issue readback; the result includes `file`, `todoId`,
  `repository`, `issueURL`, `issueNumber`, `linked`, `created` and `recovered`.
  Reuse leaves the remote issue unchanged. Publication never completes the TODO.
- `todo.complete` refuses attempted or unresolved publication, including an
  attempt without an `issueURL`. A linked TODO moves only after the runtime
  verifies the same-repository issue is `CLOSED`. Lookup errors, open or unknown
  status preserve the pending TODO. The guard verifies status, not TODO acceptance;
  complete only after resolution is demonstrated. Status is checked at explicit
  completion; the runtime does not continuously synchronize or close/reopen
  issues. A legacy TODO without a link or attempted publication retains its
  local completion path.

### Dispatch, verification and project basics

| Verb | Effect |
|---|---|
| `resolve-model <agent> [--host codex|claude]` | Model for an agent using the selected or inferred host |
| `resolve-effort <agent> [--host codex|claude]` | Reasoning effort for an agent using the selected or inferred host |
| `resolve-agent <agent> [--host codex|claude]` | Model, effort, tools, disallowed tools and declared skills |

From source `.ai`, pass `--host codex` or `--host claude` explicitly. An installed
`.codex` runtime infers Codex and reads role model and effort from its native
`.toml` definitions; an installed `.claude` runtime infers Claude and reads
worker overrides from `.planning/config.yaml`. An installed runtime rejects a
`--host` value that does not match its namespace. A resolved value of `inherit`
means the caller omits that argument; model and effort resolve independently.

Use these source-tree commands when dispatching a Codex role:

```bash
python .ai/runtime/phase.py query resolve-model <role> --host codex
python .ai/runtime/phase.py query resolve-effort <role> --host codex
python .ai/runtime/phase.py query resolve-agent <role> --host codex
```

For installed projects, use `python .codex/runtime/phase.py query resolve-model
<role>` or `python .claude/runtime/phase.py query resolve-model <role>`; the
installed namespace supplies the host. Claude worker model values are aliases
(`opus`, `sonnet`, `haiku`, `fable`). Codex worker values come from native TOML.
Effort accepts `low`, `medium`, `high`, `xhigh`, `max` or `inherit`; another
value fails with `bad-effort`.

The `scout` role has fixed settings. It resolves to `gpt-6-luna`/`high` on
Codex and `haiku`/`inherit` on Claude, independent of project YAML. Its procedure
and assignment/result fields are in [scout dispatch](../references/scout-dispatch.md).

| `agent-skills <agent>` | The agent's declared skills resolved against the installed skills root |
| `agents.list` / `skills.list` | What is installed |
| `verification.status <phase>` | Whether a verification report exists, and what it concluded |
| `verification.resolve-file <phase>` | The path a verifier should write |
| `verification.run-checks` | Run configured checks or reuse matching passing receipts, retaining full logs |
| `config-get <dotted>` / `config-set <dotted> <value>` | Read or write `.planning/config.yaml` |
| `commit <message> --files ...` | Stage the named paths and commit, honouring `commit_docs` |
| `git.base-branch` | The repository's default branch |
| `generate-slug <text>` | The slug the runtime would derive |
| `progress.bar <percent>` | The rendered progress bar |
| `runtime-identity` | Identifies the runtime to the launcher's verification step |
| `help` | Every verb and bundle |

### Worktree isolation

| Verb | Effect |
|---|---|
| `dispatch-isolation` | Resolve how this dispatch is isolated, and record it |
| `worktree.create <plan>` | Create a runtime-owned checkout on its own branch |
| `worktree.record-agent <plan> --branch` | Record a checkout the host created |
| `worktree.merge-wave` | Merge the wave's branches, with the deletion guard |
| `worktree.cleanup-wave` | Remove proven-merged checkouts; preserve the rest |
| `worktree.list` | Every linked worktree, with its branch and state |
| `worktree.reap-orphans` | Prune stale metadata without deleting a live checkout |
| `worktree.health` | Findings about the worktree setup |

`dispatch-isolation` returns `harness-worktree` or `orchestrator-worktree` —
**never a value meaning "unisolated"**, because isolation is mandatory here. It
raises instead: `bad-isolation` for a setting that asks to disable it,
`no-worktree-support` for a git too old for worktrees, `root-not-ignored` when
the worktree root is not gitignored. There is no flag that forces a weaker
answer, and the verb writes nothing to disk.

A host that forks a dispatch worktree from the fork base rather than from HEAD
would hand an executor a tree missing HEAD's commits. There is no advisory verb
for that: the executor's own spawn-time branch check compares its real base
against the revision the orchestrator captured and halts with exit 42, which is
the only check that sees what actually happened.

Integration is explicit and conservative. `merge-wave` blocks a branch that
deletes a path its plan did not declare, aborts a conflicting merge with the
worktree preserved, and refuses a protected target branch or a dirty tree.
`cleanup-wave` removes a checkout only when git agrees its branch is an
ancestor of HEAD, and reports everything it kept with the reason.

[hooks/worktree-guard.sh](../hooks/worktree-guard.sh) emits an advisory warning
for a write-capable dispatch without worktree isolation and continues with exit 0.
The isolated-workflow requirement and runtime creation/integration safeguards
still apply; a verb cannot inspect an `Agent(...)` call that never mentioned it.
Destructive-operation blockers are a separate guard.

## Layout

```
runtime/
  phase.py          CLI dispatcher: argument parsing and the verb table
  lib/
    results.py      the pure-result contract, JSON emission, exit codes
    paths.py        repository root and .planning path resolution
    text.py         slugs, YAML frontmatter, Markdown section editing
    config.py       .planning/config.yaml with dotted access and defaults
    roadmap.py      ROADMAP.md parsing and editing
    state.py        STATE.md reading, writing and the planning lock
    phases.py       phase CRUD across the roadmap and phase directories
    milestones.py   milestone declaration, membership and archival
    todos.py        captured todos and phase matching
    quick.py        quick tasks outside the roadmap
    verification.py verification reports and configured project checks
    verification_checks.py reusable check receipts and bounded independent checks
    models.py       agent, model and skill resolution for dispatch
    worktrees.py    isolation resolution, wave integration and cleanup
    bundles.py      the init.* context bundles
```

Installation places this runtime under `.codex/runtime` or `.claude/runtime`, and
the launcher resolves either. Project records stay under `.planning/`.

## Project records

```
.planning/
  PROJECT.md              vision, constraints, key decisions
  REQUIREMENTS.md         scoped requirements with REQ ids
  ROADMAP.md              phases, plan checklists, milestones, progress table
  STATE.md                position, decisions, blockers, session continuity
  MILESTONES.md           what each milestone shipped
  config.yaml             commit_docs, workflow flags, agent models, checks
  phases/NN-slug/         NN-CONTEXT.md, NN-RESEARCH.md, NN-MM-PLAN.md,
                          NN-MM-SUMMARY.md, NN-VERIFICATION.md
  todos/pending|completed captured todos
  quick/YYMMDD-NNN-slug/  quick tasks
```

Phase numbering is continuous across milestones and never restarts. Integer
phases are planned work; decimal phases (2.1, 2.2) are urgent insertions.

## Configuration

```yaml
commit_docs: true          # false makes every commit verb a no-op
response_language: null    # when set, workflows present user-facing output in it
context_window: 1000000    # the agents' real window; sets the handoff threshold,
                           # and 500000+ enables richer cross-phase agent context
workflow:
  text_mode: false         # plain-text prompts instead of AskUserQuestion
  auto_advance: false
  discuss_mode: discuss
  isolation: auto          # or harness-worktree / orchestrator-worktree
                           # there is no value that disables isolation
worktree:
  root: .worktrees         # must be gitignored, or execution stops
agents:
  coder:
    model: sonnet          # Claude worker model alias
    effort: high           # low | medium | high | xhigh | max
verification:
  commands: []             # argv lists/strings or mappings; verification.run-checks
  reuse: true              # false forces every check to execute
  max_parallel: 4          # only explicitly independent checks can overlap
```

`verification.commands` is empty in the template. An adopting project configures
its real checks during onboarding; until then, verification rests on reading
alone and the verification report must say so.

### Check receipts and independent checks

Legacy strings retain whitespace splitting; argv lists preserve arguments exactly.
Commands run without a shell, from the repository root. Legacy entries and mappings
without `independent: true` execute serially and form barriers between independent
blocks. Results always follow configuration order. Each independent block joins
before the next barrier, and all checks join before the aggregate result is returned.

Mappings add optional precision and scheduling declarations:

```yaml
verification:
  reuse: true
  max_parallel: 4
  commands:
    - command: [python, -m, unittest, discover, -s, tests, -v]
      sources: [src, tests, requirements.txt]  # literal relative files/directories
      environment: [PATH, PYTHONPATH]         # relevant inherited variable names
      independent: true
      resources: [test-db]                    # common names prevent overlap
      timeout: 600                           # positive seconds; default 600
      revision: true                         # additionally require exact Git HEAD
      reuse: false                           # optional; rerun this volatile check
```

Omitting `sources` fingerprints the content, mode, names and deletion state of
all Git-tracked and nonignored untracked files, including tracked planning reports.
Explicit source directories include ignored files and new files beneath them.
Source declarations must cover every input the command consumes, including imported
code, configuration, lockfiles and any ignored dependency trees used by the check.
They are literal repository-relative paths; traversal, absolute paths, Git metadata
and receipt storage are rejected. Source symlinks must point to files inside the
repository; unsupported special files, directory symlinks and Git submodules prevent
a conclusive snapshot result.

Omitting `environment` fingerprints every inherited environment variable; an
explicit list declares the variables relevant to that check, including missing
values. Values are hashed rather than copied into receipt inputs. Every child
receives the same captured environment. Receipt keys also include the entire
verification configuration, exact argv and timeout, repository location, runtime
implementation/platform/Python identity and the resolved executable's content.
An executable whose identity cannot be read is never eligible for reuse.
Commands dependent on undeclared external state, such as network services, should
use `reuse: false` on their mapping, or disable reuse for the entire verification
configuration. A stamp file in `sources` or a stamp variable in `environment` can
bind a check to a project-managed dependency/environment identity. Ignore rules
exclude generated data and dependencies from the default source key; checks that
consume those inputs must declare them explicitly or disable reuse. Precision
declarations are a project-owned input contract.

The runtime captures the integrated source fingerprint before scheduling and checks
it before/after executions and after the join. Explicit source inputs are checked
too, including ignored dependencies. Execution guards also compare file timestamps
and identities, so rewriting a source back to its original content invalidates
that run without preventing later content-based reuse. Any observed source mutation or unavailable
fingerprint invalidates the batch: `snapshot_valid: false` and `passed: false`.
This guards a checkout that remains frozen throughout checking; it does not lock
out other processes or detect changes whose content and filesystem metadata are
restored entirely between snapshots.
Resource names prevent conflicts within this invocation; independent runtime
invocations need their own external isolation. Checks should write generated output
to ignored paths and avoid changing their source inputs.

Local `.planning/verification-receipts/` stores JSON receipts and unique full
stdout/stderr logs. It is gitignored by the template; runtime initialization also
creates a local `*` ignore file inside the store for installed projects. It is
excluded from source fingerprints independently of those ignore rules. Receipts record the
original `tested_revision`, hashed inputs, result and full log hashes. Matching
passing evidence can be reused across revisions with identical relevant content;
`revision: true` also binds the key to HEAD. Missing, malformed, corrupt or
hash-mismatched receipts/logs are cache misses. Failures and timeouts retain their
logs and receipts, and execute again on the next invocation. Log filenames are never
reused by the runtime. Receipts are local evidence, not a replacement for phase
verification reports, human judgments or publication gates.

The existing `command`, `exit_code`, `passed`, `stdout_tail` and `stderr_tail`
result fields remain; tails are at most 2,000 characters. Each check also returns
`reused`, `receipt`, `stdout_log`, `stderr_log`, `tested_revision` and
`snapshot_valid`. Errors add `error`. The batch returns its current `tested_revision`
and `snapshot_valid`; reused checks retain their original tested revision. Full
output is read from log paths only when needed. `configured: false` remains the
empty-command result. JSON `ok` still reports successful runtime invocation;
callers must inspect aggregate/check `passed` to judge command outcomes.

## Codex project concurrency

Codex installs also include a phase/quick startup launcher and synchronous
supported-tool guard. The launcher selects an existing runtime-owned session
and starts a new native run in its worktree; it does not move an active agent.
See the [Codex startup protocol](../references/same-agent-worktree.md#codex-startup)
for the CLI, literal prompt handling, installation/trust prerequisites and
current runtime/native evidence limits.

Codex installation writes this setting to `.codex/config.toml` on fresh install,
update and migration, including when installation uses `--no-hooks`:

```toml
[agents]
max_concurrent_threads_per_session = 12
```

The setting caps spawned threads per session and excludes the primary thread.
The installer writes the canonical `max_concurrent_threads_per_session` key and
removes the legacy `agents.max_threads` key. It preserves unrelated TOML text,
comments, a UTF-8 BOM, line endings, agent settings and hooks. An inline table
such as `agents = { ... }` is unsupported; expand it to `[agents]` before running
the installer. Preflight reports that correction before it writes project files.

## Validation

From the authoring checkout:

```bash
python -m unittest discover -s tests -v
```

`tests/test_phase_runtime.py` drives `phase.py` as a subprocess against real
temporary git repositories, so it exercises the contract the workflows depend on
rather than internals. The installer does not copy the source test suite into
adopting projects.
