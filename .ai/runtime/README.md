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

A workflow makes one `init.<name>` call and parses the result rather than issuing
a dozen reads of its own. Bundles never mutate anything.

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

### Roadmap and state

| Verb | Effect |
|---|---|
| `roadmap.get-phase <phase>` | One phase's parsed entry |
| `roadmap.analyze` | Counts, the next open phase, and phases blocked on dependencies |
| `roadmap.update-plan-progress <plan-id> [--undo]` | Tick or untick one plan and re-derive state |
| `state.get [key]` | The parsed STATE.md view |
| `state.record-session [--stopped-at] [--resume-file] [--status]` | Update Session Continuity |
| `state.begin-phase <phase> [--status]` | Point Current Position at a phase |
| `state.update-progress` | Re-derive counters and the progress bar from the roadmap |
| `state.advance-plan <plan-id>` | Tick a plan and update state in one call |
| `state.add-decision <text>` | Append to Decisions |
| `state.add-blocker <text>` | Append to Blockers/Concerns |
| `state.add-roadmap-evolution <text>` | Append to Roadmap Evolution, creating the section |
| `state.sync-todos` | Replace the Pending Todos body from the todos on disk |

STATE.md's Markdown body is authoritative; its frontmatter counters are
re-derived from ROADMAP.md on every write, so the two cannot disagree. Writers
serialize on `.planning/.lock`.

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
| `resolve-model <agent>` | Model for an agent: a project config override, otherwise `inherit` |
| `resolve-agent <agent>` | Model, tools, disallowed tools, max turns and declared skills |

Agent definitions carry no `model:` frontmatter — the host no longer reads one
from there, so the model is injected inline on the `Agent(...)` call. A resolved
value of `inherit` means the project set no override, and the caller omits the
model argument entirely.

| `agent-skills <agent>` | The agent's declared skills resolved against the installed skills root |
| `agents.list` / `skills.list` | What is installed |
| `verification.status <phase>` | Whether a verification report exists, and what it concluded |
| `verification.resolve-file <phase>` | The path a verifier should write |
| `verification.run-checks` | Run `verification.commands` from config and report each result |
| `config-get <dotted>` / `config-set <dotted> <value>` | Read or write `.planning/config.yaml` |
| `commit <message> --files ...` | Stage the named paths and commit, honouring `commit_docs` |
| `git.base-branch` | The repository's default branch |
| `generate-slug <text>` | The slug the runtime would derive |
| `progress.bar <percent>` | The rendered progress bar |
| `runtime-identity` | Identifies the runtime to the launcher's verification step |
| `help` | Every verb and bundle |

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
    models.py       agent, model and skill resolution for dispatch
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
context_window: 200000     # 500000+ enables richer cross-phase agent context
workflow:
  text_mode: false         # plain-text prompts instead of AskUserQuestion
  auto_advance: false
  discuss_mode: discuss
agents:
  coder:
    model: sonnet          # overrides the agent file's own model
verification:
  commands: []             # argv lists; run by verification.run-checks
```

`verification.commands` is empty in the template. An adopting project configures
its real checks during onboarding; until then, verification rests on reading
alone and the verification report must say so.

## Validation

From the authoring checkout:

```bash
python -m unittest discover -s tests -v
```

`tests/test_phase_runtime.py` drives `phase.py` as a subprocess against real
temporary git repositories, so it exercises the contract the workflows depend on
rather than internals. The installer does not copy the source test suite into
adopting projects.
