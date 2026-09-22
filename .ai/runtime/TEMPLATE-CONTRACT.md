# Full phase templates and the local runtime

Read the complete template before authoring or reviewing its output. The
template's File Template is the output skeleton; its examples and teaching
sections stay in the source template. Keep every applicable output section. This
contract adds the local execution metadata; it does not replace upstream guidance.

| Artifact | Producer | Consumer | Local additions |
|---|---|---|---|
| NN-CONTEXT.md | discuss-phase | researcher, phase-preparer, phase-checker | Decisions, canonical refs, code context, deferred ideas, folded todos |
| NN-DISCUSSION-LOG.md | discuss-phase | Human audit only | Actual questions, options, selections and rationale |
| NN-RESEARCH.md | researcher | phase-preparer | Findings tied to a revision, with what they unblock |
| NN-MM-PLAN.md | phase-preparer | phase-checker, orchestrator, coder | wave, depends_on, files_modified, requirements, acceptance, must_haves, per-task verify with fails_when |
| NN-MM-SUMMARY.md | coder / doc-writer | orchestrator, downstream plans, verifier | status, commits, acceptance and documentation coverage, actual check results |
| NN-VERIFICATION.md | verifier | orchestrator, ship gate | status, reviewed revision, verified_at, finding counts |
| ADR-NNN-*.md | discuss-phase / onboard via `decision.*` | every later phase | kind, validated, supersedes/superseded_by, a Feasibility validation table |
| ARCHITECTURE.md, STACK.md | codebase-mapper | plan-phase, researcher | freshness derived from the commit that last wrote the file, via `codebase.status` |

## Author a context

Use `.ai/templates/context.md` in full. `discuss-phase` writes it at the end of
the discussion, from the decisions actually taken.

`NN-DISCUSSION-LOG.md` is written alongside it and is audit-only — downstream
agents read decisions from CONTEXT, never from the log. Record only real
questions, options, evidence and replies. Never invent a discussion.

Capture unresolved choices explicitly and name the work each one blocks; plan only
decided scope. Record the user's actual implementation instruction and its
boundary when one has been given. Creation, discussion, research, planning and
design approval are not that instruction, and no agent can grant it.

Acceptance outcomes are observable, for example
`- [ ] AUTH-01: A signed-out visitor cannot retrieve another user's profile.`
Acceptance ids may be requirement ids or finer phase criteria with their own ids.
Keep ids unique; PLAN and SUMMARY acceptance lists use the bare ids.

`<canonical_refs>` is mandatory and every entry carries a full relative path. It
is how a downstream agent finds the spec or ADR the user expects it to follow. If
no external docs exist, say so explicitly rather than omitting the section.

## Author an executable plan

Use `.ai/templates/phase-prompt.md` without shortening its instructions or
removing its task-level action, verification, done, context or success sections.
The file name is phase-local: `01-01-PLAN.md`. Frontmatter carries:

```yaml
phase: 01-name
plan: "01"
wave: 1
depends_on: []            # plan ids whose summaries must exist first
files_modified: []        # exact paths, or directory prefixes ending in /
files_deleted: []         # exact files only
requirements: [REQ-01]    # never empty
acceptance: [AUTH-01]     # the phase outcomes this plan covers
```

`files_modified` grants exact paths or directory prefixes ending in `/`;
`files_deleted` grants exact files. A path belongs in one field, not both.
Declarations use Git's exact case and spelling; traversal and globs fail. Every
committed deletion names its exact path in `files_deleted`, even when a directory
prefix otherwise grants ownership. Phase records, STATE, PROJECT, REQUIREMENTS,
ROADMAP, RULES and config are orchestrator-owned. An agent automatically owns its
own SUMMARY.

**Every task carries four fields, and none is optional:**

- `<read_first>` — the files the executor must read before touching anything: the
  file being modified, any source of truth named in CONTEXT.md, and any file whose
  patterns, signatures or conventions must be replicated.
- `<action>` — what changes, specifically enough to execute without inventing scope.
- `<acceptance_criteria>` — what must be observably true when the task is done.
- `<verify>` — a runnable command paired with its failure signal.

### Stated failing direction

Every runnable `<automated>` command MUST be followed by a `<fails_when>` sibling
naming what output constitutes failure — an exit code, a string in the output, a
missing line. A command with no expressible failure mode is not an acceptance test.

```xml
<verify>
  <automated>python -m unittest discover -s tests</automated>
  <fails_when>non-zero exit, or "Ran 0 tests" in the output</fails_when>
</verify>
```

One statement per runnable command, immediately after it. Name an observable
signal, never the word "failure": `non-zero exit` is complete, `the command fails`
is a restatement. `TBD`, `TODO`, `N/A` and `unknown` are rejected outright.

Good checks exercise the observable outcome, including a denied request. Bad
checks assert that a file exists when the acceptance concerns access control.

### Scheduling

`depends_on` drives readiness: a plan becomes eligible once every id it names has
a SUMMARY.md. `wave` is the preparer's proposal, not an authority — the
orchestrator separates plans whose `files_modified` overlap into different waves
regardless of their declared wave, because two agents editing one file is the
failure this ordering exists to prevent.

`must_haves` (truths and artifacts) carries the plan's own success criteria
forward to the verifier for goal-backward checking.

A plan that needs a human decision mid-flight records it as a checkpoint. The
orchestrator takes that decision to the user, records the answer with
`state.add-decision`, and re-dispatches the plan with the decision in context.
Never delete a checkpoint to make a gate pass.

## Produce and validate results

Use the complete `.ai/templates/summary.md` File Template. Keep accomplishments,
task commits, files, decisions, deviations, issues and next-phase readiness.
Preserve `requirements-completed` and the other upstream metadata. Add
`acceptance`, `documentation` and a `## Checks` section naming the actual
commands, their results, any failures or skips, and the tested revision.

`status: complete` or `blocked`; use `blocked` when incomplete and explain why.
A blocked result preserves findings and safe partial work without claiming
integration.

**A returned "complete" with no SUMMARY.md, or with no commits, is not a
completion.** The orchestrator treats it as blocked.

When an agent is stopped only by context or turn capacity, record the completed
tasks, preserved commits, unfinished files, remaining tasks and actual check
results. The orchestrator inspects that evidence and dispatches a fresh agent for
the remaining work without another user prompt. A continuation is not passing
evidence: complete output still requires the normal checks and independent review.

Good evidence names the scenario, the command, the observed result and the
revision. Bad evidence repeats "all requirements satisfied" without demonstrating
behavior.

Use `.ai/templates/verification-report.md` in full, with frontmatter carrying:

```yaml
status: passed | gaps_found | human_needed
revision: <the revision reviewed>
verified_at: <timestamp>
findings: {critical: 0, warning: 0}
```

The recorded `revision` is what makes the report falsifiable later: once HEAD
moves past it, the report is stale and re-verification is required rather than
optional. `phase_run query verification.status <phase>` reads exactly these
fields, and [ship](../commands/ship.md) gates on `passed`.

A `must_have` the verifier cannot confirm with explicit evidence is not a pass.
It reports the gap, or `human_needed` where the criterion itself is unverifiable.
Only the user converts an abstention into acceptance.

## Storage boundary

Project data lives in `.planning/`; reusable instructions, workflows, templates
and tooling live in `.ai/`. `.planning/config.yaml` is the runtime's execution
config: `commit_docs`, `response_language`, `context_window`, workflow flags,
per-agent model overrides and `verification.commands`.

The runtime holds no separate operational store. Everything it records is a
tracked project record, so a fresh clone inherits the full picture.

## Phase numbering

Integer phases (1, 2, 3) are planned milestone work. Decimal phases (2.1, 2.2)
are urgent insertions, carrying an `(INSERTED)` marker, and exist so that urgent
work never renumbers the phases around it.

Numbering is continuous across milestones and never restarts. The runtime
allocates every number — `phase.add` takes the next integer, `phase.insert` takes
the next decimal after a given phase, and `phase.remove` renumbers what follows.
Do not choose a number by hand.

`padded_phase` is the display spelling used in filenames: `2` becomes `02`, and
`2.1` becomes `02.1`.

## STATE.md write path

The Markdown body is authoritative. The frontmatter counters — total and completed
phases and plans, and percent — are **re-derived from ROADMAP.md on every write**,
so the two cannot disagree. A wrong counter is not corrected by editing STATE.md;
correct the roadmap and the next write follows.

Concurrent writers serialize on `.planning/.lock`. Section updates replace a
section's body wholesale rather than appending, which is how a stale run-on
section gets superseded cleanly with no migration step.

First-time creation of STATE.md from its template is the one case where a
workflow writes the file directly. Every later change goes through a `state.*`
verb.

### The section set is closed

STATE.md is a digest, so every section has exactly one writer and the set does
not grow. A section with no writer becomes placeholder rot that agents hand-fill;
a section the runtime writes but the template never declared is an unbudgeted
section nobody accounted for. `planning.validate` checks both directions.

| Section | Level | Writer | Cap |
|---|---|---|---|
| Project Reference | 2 | onboard, then hand-maintained prose | - |
| Current Position | 2 | `state.begin-phase`, `state.update-progress` | - |
| Accumulated Context | 2 | container for the three below | - |
| Decisions | 3 | `state.add-decision` | 5 entries |
| Pending Todos | 3 | `state.sync-todos`, replaced wholesale | - |
| Blockers/Concerns | 3 | `state.add-blocker`, `state.clear-blocker` | 10 entries |
| Roadmap Evolution | 3 | `state.add-roadmap-evolution` | 5 entries |
| Deferred Items | 2 | `state.add-deferred` | 10 rows |
| Session Continuity | 2 | `state.record-session` | - |

Trimming a capped section is lossless. A rotated entry is appended to
`.planning/archive/STATE-LOG.md` before it leaves, and `state.add-decision`
writes the decision into PROJECT.md's Key Decisions table as it is added rather
than as it is trimmed — so the durable copy exists before the digest copy is ever
at risk. The archive log is append-only and never authoritative; it exists so the
digest can be trimmed automatically, not so anything reads it back.

The file budget is 125 lines. `planning.validate` warns above it and never
blocks: a cosmetic finding must not stall a session, and `--strict` is there for
a caller that explicitly wants drift to fail.

## Model and dispatch metadata

Agent definitions under `.ai/agents/` carry `name`, `description`, `tools` and
optionally `disallowedTools`, `maxTurns`, `skills` and `color`. They deliberately
carry **no `model:` field**: the host no longer reads a model from frontmatter, so
it is injected inline on the dispatch call.

`phase_run query resolve-model <agent>` returns a project override from
`agents.<name>.model` in config, or `inherit`. On `inherit` the caller omits the
model argument and lets the host choose.

Codex's `install-assets/codex-agents/*.toml` keep a native `model` field. That is
Codex's own agent configuration surface and is unrelated to this contract.
