# Full phase templates and the local runtime

Read the complete template before authoring or reviewing its output. The
template's File Template is the output skeleton; its examples and teaching
sections stay in the source template. Keep every applicable output section. This
contract adds the local execution metadata; it does not replace upstream guidance.

| Artifact | Producer | Consumer | Local additions |
|---|---|---|---|
| NN-CONTEXT.md | discuss-phase | researcher, phase-preparer, phase-checker | phase, discussion, issue_refs, decisions, canonical refs, code context, deferred ideas, folded todos |
| NN-DISCUSSION-LOG.md | discuss-phase | Human audit only | Actual questions, options, selections and rationale |
| NN-RESEARCH.md | researcher | phase-preparer | Findings tied to a revision, with what they unblock |
| NN-MM-PLAN.md | phase-preparer | phase-checker, orchestrator, coder | wave, depends_on, files_modified, requirements, acceptance, must_haves, per-task verify with fails_when |
| NN-MM-SUMMARY.md | coder / doc-writer | orchestrator, downstream plans, verifier | status, commits, acceptance and documentation coverage, actual check results |
| NN-VERIFICATION.md | verifier | orchestrator, ship gate | status, reviewed revision, verified_at, finding counts |
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
type: execute
wave: 1
depends_on: []            # plan ids whose summaries must exist first
files_modified: []        # exact paths, or directory prefixes ending in /
files_deleted: []         # exact files only
autonomous: true
requirements: [REQ-01]    # never empty
acceptance: [AUTH-01]     # the phase outcomes this plan covers
documentation: []
checks: []               # each command is an argv list of strings
must_haves: {truths: [], artifacts: [], key_links: []}
issue_refs: []           # reviewed issue declaration mappings, not URL strings
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

## Planning-record integrity

Complete the required fields in each source File Template. Preserve optional
upstream metadata. Record actual requirements, authorization, verification and
publication evidence.

| Record | Required metadata | Types and values |
|---|---|---|
| CONTEXT | `phase`, `discussion`, `issue_refs` | Nonempty phase string; discussion `pending`, `in-progress` or `complete`; explicit declaration list |
| PLAN | `phase`, `plan`, `type`, `wave`, `depends_on`, `files_modified`, `autonomous`, `requirements`, `acceptance`, `documentation`, `checks`, `must_haves`, `issue_refs` | Phase/type strings; plan string or integer; type `execute` or `tdd`; positive integer wave; real boolean autonomous; explicit lists; nonempty requirements; must_haves mapping |
| SUMMARY | `phase`, `plan`, `status`, `requirements-completed`, `acceptance`, `documentation`, `issue_refs` | Phase/status strings; plan string or integer; status `complete`, `blocked` or explicit upstream `halted`; explicit lists |

Fill ID/path lists with nonempty strings. Write each `checks` entry as a nonempty
argv list of strings. Include `truths`, `artifacts` and `key_links` lists in
`must_haves`, preserving their runtime container shapes. Include `issue_refs` in
all three records. Use `[]` for reviewed absence of actionable follow-ups; omission
is incomplete metadata. Preserve mapping declarations and lifecycle rules from
[phase issue handoffs](README.md#declared-phase-issue-handoffs) and
[canonical Git workflow](../references/git-workflow.md#follow-up-issues);
plain issue URL strings are not declarations. Structural validity does not
publish issues or establish acceptance or closure.

CONTEXT begins with:

```yaml
---
phase: 01-name
discussion: pending
issue_refs: []
---
```

Record `discussion: complete` only for an actual recorded discussion. Any
implementation instruction still belongs in the authored Authorization section.
A SUMMARY's `halted` preserves the upstream intentional-stop contract; it never
counts as completed work.

The runtime `commit` verb validates the full actual index after staging its
requested files and before Git creates a commit. Newly added or modified active
`.planning/phases/<number>-<name>/NN-CONTEXT.md`, `NN-MM-PLAN.md` and
`NN-MM-SUMMARY.md` records must have valid YAML mappings, required fields and
field types. Duplicate explicit mapping keys at any depth, including anchored
sources, are rejected with record/key evidence; a later duplicate cannot erase
an issue declaration or replace an invalid value. Valid YAML merge keys retain
SafeLoader precedence, so an explicit destination key may override an inherited
key. Apply this strict loader only to current records; use the broad frontmatter
reader for `planning.validate`, which reports warnings unless the caller passes
`--strict`. Directory and filename numbers use the existing phase conventions.
Do not parse deleted records. Keep unchanged records, archives, maintenance
records, source templates and unrelated Markdown outside this commit gate. Do not
run a migration sweep or rewrite instructional skeletons as part of this gate.

`planning.integrity --files <record> ...` is a read-only diagnostic of explicitly
selected canonical working records using the same schema. A record/key diagnostic
returns `code: planning-integrity`, `ok: false` and exit 1. This strict selected
check is separate from ordinary `planning.validate`, which remains warn-only
unless the caller explicitly chooses `--strict`.

The standalone `hooks/planning-integrity.sh` / `.py` PreToolUse checker validates
native Git commit commands using the shared schema. Ordinary commits inspect
index bytes; explicit-path/`--only` commits inspect selected tracked working
content; `--all` inspects tracked working changes and staged additions. Supported
preceding `git add` commands use their selected working content. Inspection
never stages or resets the real index. A relevant working record with a custom
clean filter, unsupported interactive/pathspec-file commit forms or ambiguous
shell mutations is refused with actionable stderr; stage separately and use a
plain commit. CRLF normalization alone does not alter metadata meaning.

Malformed inspected metadata containers return an explicit schema diagnostic.
Unexpected native inspection errors also deny with exit 2 and actionable stderr,
rather than becoming a hook crash that a host might treat as nonblocking.

Provide native checker payloads with top-level `tool_name` and `cwd`, and put
command text in `tool_input.command`, `tool_input.cmd`, top-level `command` or
top-level `cmd`. Pass shell argv as a command list. Direct Git, `-C`/`-c` global options,
nested directories and bounded Bash/PowerShell/cmd wrappers are recognized
without executing command text. Bash escaped executable spellings and line
continuations are parsed only with Bash semantics; native Windows backslashes
remain path separators. Transparent repeated `command`, `env`, `exec`, `time`
and `!` wrappers are recognized without environment assignments. Harmless
command diagnostics remain allowed. Denial exits 2; inspected valid/noncommit input
exits 0. Missing required runtime support produces an actionable failure.
Verify installer registration for `^(Bash|exec_command|shell_command|shell)$`
(timeout 10), copied hook files and their sibling installed runtime through each
host launcher before claiming native direct coverage. Standalone checker tests do not prove
installed host coverage, and this is not universal operating-system Git enforcement.

### Authored-content diagnostics

State section replacements and `State.save` compare original body sections
before writing, including unknown/deeper headings. Progress and plan-registration
state writes use the same preflight. Unexpected loss raises `planning-integrity`
without writing that STATE candidate. Runtime dispatch snapshots existing STATE
and ROADMAP for every regular verb, covering phase, roadmap, milestone,
bookkeeping, archive and `planning.repair` paths. A mutation that already wrote
returns structured `integrity_warnings` with record, verb, section, lost-content
evidence and a potential-truncation message, including handled errors after a
write. Inspect the saved records; no rollback or transactional guarantee is claimed.
Read-only calls do not create records.

Comparison is section-aware and ignores only newline spelling, derived
frontmatter, owned state fields, explicitly replaced digest entries and documented
Decisions/Roadmap Evolution rotation. Roadmap exceptions cover generated
checklist/progress rows, explicitly selected phase fields/plan registration and
requested phase removal/renumbering, canonical milestone status updates and
conservative repair-owned heading restoration. Unrelated authored prose and unknown child
headings do not inherit a parent section's exception. Ordinary successful
mutations and warn-only conformance checking retain their established behavior.

## Threat records and ownership

- Keep each threat's description, category, component, severity, disposition and
  mitigation in its respective PLAN's six-column register; link its local Threat ID
  to the canonical issue or retain ID + Pending dependency.
- Keep stable key, aliases, assessment, owner, status, details and evidence in the
  existing Security risk issue under [canonical threat tracking](../references/git-workflow.md#canonical-threat-tracking).
- Preserve conditional three-column SUMMARY Threat Flags for discovery. Carry
  all PLAN threats separately in Threat Outcomes: PLAN/ID, issue, outcome, Git
  state and evidence. Do not duplicate or combine PLAN registers.
- Keep open/unresolved, accepted/deferred and mitigated/resolved distinct; list
  actual closed only with readback/evidence. Never infer closure from merge.
- Workers return safe requests/SUMMARY; coordinators update each owning PLAN's
  links and reconcile status. Run phase and both quick-mode hooks outside optional review.
- Limitation: issue.validate checks section and field shapes; semantic review and
  provider reconciliation remain author/coordinator duties.

### Risk-routing destinations

The canonical destination above is an existing matching Security risk issue or,
for all new planned risks, including accepted/deferred, a stable `###` entry in
the phase checklist issue BODY,
under [canonical threat tracking](../references/git-workflow.md#canonical-threat-tracking).
Use its deterministic title/label lookup before semantic risk search and mandatory
default routing for new planned work. Entries retain each risk's stable canonical
key, aliases/occurrences, owning PLAN assessment/mitigation links, owner,
scope/acceptance, lifecycle/status/outcome, next action and revision/check evidence.
Use a provider-verified heading-anchor URL, never an invented slug; renaming a
heading breaks the link and requires reference repair/readback. Omit "(comment)"
link-label suffixes. Follow the canonical identity rules above;
unavailable publication stays Pending with its dependency.

Use the [consolidated security checklist](../templates/issues/security-risk-consolidated.md) for consolidated risks.

Then search and semantically compare existing risk trackers. Existing actionable
full-scope matching issues remain canonical; checklists link them without
duplicating or replacing their identities. Closed unresolved matches retain the
reopening-authority blocker. Distinct unplanned execution/review threats require
standalone actionable Security risk issues or existing full-scope matches, linked
from the owning PLAN and any phase checklist. Never route threats through TODOs.
Keep full six-column registers in each owning PLAN and linked SUMMARY/PR outcomes
separate. Neutral links remain until scope-complete resolution evidence and
existing explicit closure authority are verified. Safe disclosure, serialized writes,
template validation and uncertain-create readback recovery remain mandatory.

## Storage boundary

Project data lives in `.planning/`; reusable instructions, workflows, templates
and tooling live in `.ai/`. `.planning/config.yaml` is the runtime's execution
config: `commit_docs`, `response_language`, `context_window`, workflow flags,
per-agent model overrides and `verification.commands`.

The runtime holds no separate operational store. Everything it records is a
tracked project record, so a fresh clone inherits the full picture.

## Archive evidence and recovery

`planning.archive` defaults to a preview and accepts one explicit phase, ADR or
quick selector. Only `--apply` moves records. Preserve the complete historical
artifacts and their IDs under `.planning/archive/{phases,decisions,quick}/`.
Do not create completion evidence during archival: phase plan SUMMARYs need
`status: complete` and authored Accomplishments, phase VERIFICATION needs
`status: passed`, superseded ADRs need an accepted replacement, and terminal quick
records need authored verification or retirement evidence. Explicit legacy
`--evidence` names `archive_kind`, `archive_id`, `archive_status` and an authored
`archive_reason`; it never overrides active/in-progress guards.

The runtime owns archive catalog/index updates and planning-link rebasing.
Tracked recovery journals preserve exact original, proposed and intermediate
bytes. `planning.archive-recover` previews a rollback, and `--apply` restores it
only when no subsequently authored record or directory would be overwritten.
Journals remain discoverable after recovery. See the runtime README for the full
selection, discovery, idempotence and conflict contract.

## Phase numbering

Integer phases (1, 2, 3) are planned milestone work. Decimal phases (2.1, 2.2)
are urgent insertions, carrying an `(INSERTED)` marker, and exist so that urgent
work never renumbers the phases around it.

Numbering is continuous across milestones and never restarts. The runtime
allocates every number — `phase.add` takes the next integer, `phase.insert` takes
the next decimal after a given phase, and `phase.remove` renumbers what follows.
Archived phase IDs are reserved; removing an earlier phase requires
`--no-renumber` when renumbering would collide with historical successors.
Do not choose a number by hand.

`padded_phase` is the display spelling used in filenames: `2` becomes `02`, and
`2.1` becomes `02.1`.

## STATE.md write path

The Markdown body is authoritative. The frontmatter counters — total and completed
phases and plans, and percent — are **re-derived from ROADMAP.md on every write**,
so the two cannot disagree. Archived historical phase blocks are excluded from
active counters while remaining available to direct phase and dependency queries.
A wrong counter is not corrected by editing STATE.md;
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
| Blockers/Concerns | 3 | `state.add-blocker`, `state.clear-blocker` | 10 entries, reported not trimmed |
| Roadmap Evolution | 3 | `state.add-roadmap-evolution` | 5 entries |
| Deferred Items | 2 | `state.add-deferred` | 10 rows, reported not trimmed |
| Session Continuity | 2 | `state.record-session` | - |

Only a section with a durable copy elsewhere trims itself. `state.add-decision`
writes the decision into PROJECT.md's Key Decisions table as it is added, so the
durable copy exists before the digest copy is ever at risk, and roadmap history
is in ROADMAP.md and git. Blockers and deferrals are capped but never dropped
automatically — an open blocker that vanished because a newer one arrived is worse
than a long section — so `planning.validate` reports the overflow and a human
clears what is resolved. A cleared entry is gone; git holds what the file said.

The file budget is 150 lines. `planning.validate` warns above it and never
blocks: a cosmetic finding must not stall a session, and `--strict` is there for
a caller that explicitly wants drift to fail.

## Model, effort and dispatch metadata

Worker definitions under `.ai/agents/` carry `name`, `description`, `tools` and
optionally `disallowedTools`, `skills` and `color`. Shared Markdown roles carry
no `model:` or `effort:` field. Claude exports default to scout/targeted-fixer
`haiku`, coder `sonnet` (without effort), and phase-preparer `opus`/`medium`.
Codex model and effort come from native role TOML (coder `gpt-6.1-sol`/`medium`).
Claude runtime defaults are coder `sonnet`/`high` and preparer `opus`/`medium`;
ordinary-role overrides come from `.planning/config.yaml`.

They also carry **no `maxTurns:`**. A turn ceiling stops an agent mid-slice with
work committed and no SUMMARY.md written, which the orchestrator is required to
read as blocked — the cap manufactures the failure it was meant to contain. The
context handoff under `handoff` bounds a long agent instead, and hands the work
on rather than dropping it.

Run `python .ai/runtime/phase.py query resolve-model <role> --host codex`,
`python .ai/runtime/phase.py query resolve-effort <role> --host codex` or
`python .ai/runtime/phase.py query resolve-agent <role> --host codex` to resolve
source-tree Codex settings. Use `--host claude` for source-tree Claude settings.
An installed `.codex` runtime infers Codex; an installed `.claude` runtime
infers Claude. Installed runtimes accept an explicit `--host` only when it
matches their namespace. On `inherit`, the caller omits that argument; model and
effort resolve independently.

Claude worker model values are host aliases (`opus`, `sonnet`, `haiku`,
`fable`). Codex worker model values come from native TOML definitions.
Effort accepts `low`, `medium`, `high`, `xhigh`, `max` or `inherit`; another
value fails with `bad-effort`.

Codex's `install-assets/codex-agents/*.toml` keep native `model` and
`model_reasoning_effort` fields. Those are Codex's own agent configuration surface
and are unrelated to this contract.

The `scout` and `targeted-fixer` roles are fixed per host and ignore project YAML overrides:
Codex uses `gpt-6-luna` and `high`; Claude uses `haiku` and `inherit` effort.
The source and installed Codex TOML paths are `.ai/install-assets/codex-agents/`
and `.codex/agents/`. See [scout dispatch](../references/scout-dispatch.md) for
the assignment, result, wait and unsupported-host fallback procedure.
