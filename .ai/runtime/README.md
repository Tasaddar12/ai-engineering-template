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
| `phase.complete <phase>` | Tick every plan and the checklist entry; refresh progress |
| `phase.next-decimal <after>` | The decimal number an insert would allocate |
| `phases.list` | Every phase with status, plan counts, directory and execution completeness |
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
| `codebase.status` | Freshness of ARCHITECTURE.md and STACK.md, derived from git |

`planning.validate` returns `ok` with a warning list so a cosmetic finding never
stalls a session. `--strict` turns the same findings into a failure, for a caller
that asks for it.

### Milestones, todos and quick tasks

| Verb | Effect |
|---|---|
| `milestone.list` | Declared milestones and which is current |
| `milestone.create <name> [--goal G]` | Declare a milestone in progress; demote any previous one |
| `milestone.complete <version> [--name N] --confirm` | Mark shipped and write the MILESTONES.md entry |
| `todo.add <title> [--problem] [--solution] [--area] [--severity] [--files]` | Write a pending todo |
| `todo.list [--state pending\|completed]` | Todos sorted by severity then age |
| `todo.complete <name>` | Move a todo to `completed/` |
| `todo.match-phase <phase>` | Score pending todos against a phase's name and goal |
| `quick.create <description>` | Open `.planning/quick/YYMMDD-NNN-slug/` with its QUICK.md |
| `quick.list [--status]` | Quick tasks, newest first |
| `quick.update <id> [--status] [--files] [--verification]` | Record progress or completion |

`milestone.complete` refuses without `--confirm`, and refuses while any phase in
the milestone is open. There is deliberately no force path: a milestone entry
claiming phases shipped when they did not is the record this exists to keep honest.

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

The dispatch itself is enforced outside the runtime, in
[hooks/worktree-guard.sh](../hooks/worktree-guard.sh) — a verb cannot see an
`Agent(...)` call that never mentioned it.

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

### Specialist evidence and acceptance currentness

The evidence verbs persist validated review, scout and acceptance packets, and
prove whether a passed phase report is still current after narrowly allowed
completion bookkeeping:

```bash
python .ai/runtime/phase.py query evidence.record request.json --result result.json
python .ai/runtime/phase.py query evidence.lookup request.json
python .ai/runtime/phase.py query verification.currentness <phase>
python .ai/runtime/phase.py query verification.validate-bookkeeping --before <full-SHA> --after <full-SHA>
```

Requests are strict JSON schema 1 objects. All kinds require `kind`, the full
inspected `revision`, literal tracked `scope` paths, `inputs` (which may be
empty), a `configuration` object and a nonempty `question`. Review requests add
`requirements` and may add `base_revision`, a full committed ancestor SHA for
changed-source review; scout requests add exact `requested_fields`; acceptance requests
add the tracked phase `report_path`. Unknown or duplicate keys, non-finite JSON
numbers, path traversal, missing inputs, symlinks and gitlinks are rejected.
Scope and input manifests expand from the immutable commit and bind path names,
modes and blob IDs. With review `base_revision`, scope expands over the union of
the base and inspected trees: each path binds its before/after mode and blob, with
a null after value for a deletion. `covered_paths` includes deleted paths and both
sides of a rename; reviewers inspect removed contents at the declared base. Paths
absent from both trees remain errors. Inputs still require actual committed paths
at the inspected revision. Old dependency blobs are also bound where present.
Base and inspected SHAs remain provenance; keys bind their actual manifests, so
unrelated commits with identical declared old/new inputs can reuse the review. The key also binds the request, configuration and validator
implementation. Review and scout keys omit the revision, so a packet can be
reused on a later clean HEAD only if all declared and expanded committed inputs,
question, output fields/requirements, configuration and validator identity still
match. Acceptance keys bind the exact revision and report blob. The runtime
cannot infer undeclared dependencies: callers must declare actual relevant
source, tests, dependencies and configuration in `scope`/`inputs` and
`configuration` to get precise reuse. A broad scope is conservative and reduces
reuse; narrowing scope without accounting for real inputs is unsafe.

Results use strict, kind-specific objects. Every result carries its exact
`inspected_revision`, structured `findings`, and nonempty `provenance`; review and
acceptance also report exact `covered_paths`. Scout results cover precisely the
requested fields, with each field `found`, `absent` or `incomplete` and cited
evidence. Absence claims require citations and the complete expanded scope
manifest. Incomplete fields, unresolved questions, failed results or unresolved
findings are not reusable. The host, not JSON integrity alone, authenticates
reviewer identity and independence. `evidence.record` requires a clean stable
worktree and snapshots the requested immutable revision; it may record a review
of an earlier commit after HEAD has advanced. `evidence.lookup` requires a clean
HEAD equal to the request revision. Missing/corrupt packets are reported as
`never_run`/nonreusable rather than passing silently.

Every recording writes an immutable per-attempt JSON receipt and returns its
unique `receipt` path. A separate content-key `index` selects the latest attempt;
lookup returns that receipt and the retained `attempts` paths. A newer failed or
incomplete attempt never falls back to an older pass. All attempts preserve their
full request, result and provenance. Lookup also returns `unresolved_findings`
carried across same-key attempts. Omitting a prior unresolved finding cannot make
a later pass reusable: it has effective status `incomplete`. To dispose of a prior
finding, report the exact same severity and message with `resolved: true` and a
nonempty supporting `evidence` citation. The host validates that resolution. A
corrupt/missing index, altered attempt or dropped history is a cache miss; recording
into inconsistent retained history fails closed rather than replacing it.

Acceptance reports have schema `1`, exact phase-directory `phase`, status,
full inspected `revision`, timezone-bearing ISO `verified_at`, a structured
`findings` list and a nonempty Markdown body. A report is a passing source
acceptance only when every finding is resolved and `behavior_unverified` is zero.
Bookkeeping additionally needs nonempty `acceptance` and `requirements_completed`
ID lists. Persist and commit this report unchanged at its source revision before
success bookkeeping; never retag it to a later HEAD. The validator accepts only
a clean, single direct-child commit changing `.planning/STATE.md`,
`.planning/ROADMAP.md` and/or `.planning/REQUIREMENTS.md`, after replaying the
limited completion transition and validating the committed structured SUMMARYs.
It writes a receipt tied to the exact before/after trees, unchanged source report
blob/revision and validator. `verification.currentness` accepts report-only
commits and bookkeeping commits carrying valid receipts. Source/configuration
edits, report edits, merges, unsupported record changes or a dirty worktree fail
closed. If the bounded schema does not fit (for example, human-only or legacy
prose coverage), obtain fresh specialist review; do not reshape the records to
pass the validator.

## Codex project concurrency

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
