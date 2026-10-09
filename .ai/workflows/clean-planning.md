<!-- workflow
step: clean-planning
agent-roles: orchestrator, scout, coder, doc-writer, code-reviewer, doc-verifier, verifier
produces: cited review, repair diff, unresolved decisions, archive/recovery selectors
consumes: PROJECT.md, REQUIREMENTS.md, ROADMAP.md, STATE.md, phase artifacts, ADRs, quick records, canonical templates
-->

<purpose>
Review the project's planning records against their current canonical templates
and actual evidence, then perform the cleanup the user authorized. Preserve
project-specific wording and historical rationale. A missing section or a stale
counter is structural drift; a changed goal, conflicting acceptance, unsupported
completion or contradictory decision needs its authoritative owner to resolve it.
</purpose>

<process>

<step name="scope_and_runtime">
Read the actual request, [shared rules](../RULES.md),
[truth map](../truth-map.md), [scout dispatch](../references/scout-dispatch.md),
[template contract](../runtime/TEMPLATE-CONTRACT.md), PROJECT and STATE.
Resolve the installed `phase.py` using the same `phase_run` setup as
[progress](progress.md). Use the source `.ai/runtime/phase.py` in this repository;
installed hosts resolve their runtime directory. Verify root, branch and input
revision before any write. Capture owned paths and the requested boundary:
review, normal cleanup/repair, or an explicitly selected archive.

A review request permits inspection. A cleanup request permits ordinary safe
structure repairs and evidence-backed documentation corrections within its scope.
Do not ask again at internal stages for authorization already supplied. Do not
fill an unfilled adoption skeleton; report onboarding as the next step. Cleanup
never authorizes implementing an unfinished phase, inventing decisions or changing
the project's approved outcomes.

Run:

```bash
phase_run query planning.validate
phase_run query planning.review
phase_run query planning.archives
```

`planning.review` extends the existing validator using the same readers. It
returns the inventory, findings, a source fingerprint and exact mechanical repair
diffs. It checks template structure, identities, statuses, local references,
dependencies and completion contradictions; it does not prove product behavior.
Preserve each finding's source and uncertainty. Failure to parse a record is a
finding to resolve, never an excuse to replace its contents.
</step>

<step name="dispatch_evidence">
Resolve each dispatched role's model and effort inline before spawning it:

```bash
phase_run query resolve-model scout --host codex
phase_run query resolve-effort scout --host codex
```

Use `--host claude` instead on Claude; the source namespace defaults to Claude,
so choose the actual host explicitly when executing from `.ai/`. Repeat for
`coder`, `doc-writer`, `code-reviewer`, `doc-verifier` and `verifier`
only when that role is used. Pass the returned model and reasoning effort on
the actual host dispatch call; omit an argument resolved to `inherit`. Scouts
resolve to Luna/high on Codex and Haiku/inherit on Claude through the fixed scout
contract. Other roles use the actual native/config resolution rather than a
hardcoded model in this workflow.
Use exact named roles, fresh bounded context and the scout assignment/result
fields from [scout dispatch](../references/scout-dispatch.md).

Spawn `scout` for read-only inventory/classification/extraction packets from the
captured revision. Give each packet distinct paths and requested fields:

- Planning lifecycle: plans, phase CONTEXT/RESEARCH/SUMMARY/VERIFICATION, IDs,
  required blocks, statuses, dependencies, acceptance coverage and claimed checks.
- Cross-document facts: REQUIREMENTS traceability, ROADMAP checkboxes and phase
  fields, STATE position/progress, canonical references and contradictory claims.
- Retirement candidates: ADR status/replacement/history and quick status/authored
  completion evidence, active inbound references, archive catalog and recovery
  selectors. An old date alone is not eligibility.

Use one discovery scout only if source location is unknown. Batch independent
packets when host capacity allows; do not duplicate the runtime's extracted
inventory or a scout's search. Ask scouts for omissions, unresolved questions and
cited evidence, not decisions or edits. Join every result before any repairs.
Validate revision, requested fields, search scope, citations and uncertainty;
request one bounded follow-up for missing evidence.

The coordinator acts as adviser and decision owner. Compare each claim with its
authoritative source and applicable complete template. Load only relevant full
templates: [phase plan](../templates/phase-prompt.md),
[context](../templates/context.md), [summary](../templates/summary.md),
[verification](../templates/verification-report.md), [requirements](../templates/requirements.md),
[roadmap](../templates/roadmap.md), [state](../templates/state.md),
[project](../templates/project.md) and [ADR](../templates/ADR.md).
Quick records follow the installed quick runtime's record contract.

Validate required structure, unique IDs, allowed statuses, dependency existence
and order, acceptance/requirement coverage, plan registration, local reference
integrity and consistency across records. Compare completion claims with actual
commits, checks, remaining tasks and verification evidence. A SUMMARY existing,
or even claiming complete, cannot by itself finish a plan, requirement or phase.
The deterministic audit is a lower bound: scouts and the adviser check narrative
claims, bare canonical paths, source revisions and historical decision references
that a parser cannot settle. Archived identity access is part of reference review.

Classify the joined findings into safe mechanical repair, evidence-backed prose
correction, or unresolved semantic conflict. For disagreements between code and
documents, establish which source is wrong from approved intent and observed
behavior. Resolve routine choices within existing delegated authority. Conflicting
human decisions go to the user with both cited claims and the dependent scope;
continue independent cleanup. Never rewrite acceptance to excuse missing work,
infer status from age, or superficially reword intact project prose.
</step>

<step name="review_or_repair">
For review-only requests, return the cited findings, mechanical preview and exact
next operations, then stop without writes.

For authorized cleanup, preview the runtime-owned changes:

```bash
phase_run query planning.repair
```

Inspect every diff. The helper restores STATE headings only when unique intact
field blocks identify them, and refreshes roadmap-derived frontmatter counters
only when completion/identity evidence is consistent. It preserves authored body
text, status, requirement wording, checkboxes and decision history. It does not
manufacture missing content or repair semantic conflicts. The preview fingerprint
pins all inspected planning records and canonical templates. Apply a reviewed
proposal with its fingerprint; any changed input requires a fresh review:

```bash
phase_run query planning.repair --apply --expect <fingerprint>
```

Use `--only state-structure` to select that proposed repair. Default is dry-run.
Do not pass an old fingerprint or edit runtime-owned structure by hand. The
coordinator owns shared-record mutations and runs the approved runtime operations;
workers supply bounded repair proposals and evidence, never shared status writes.

Spawn `coder` for an authorized runtime/source defect with exact owned files,
fixtures, input revision and SUMMARY destination. Spawn `doc-writer` for substantial
authored prose corrections with the owning source, exact claims and preserved
historical text. Runtime-owned changes use existing verbs after evidence resolves
their values (`state.*`, `requirements.set-status`, phase/roadmap operations);
do not use a completion verb until its prerequisites are actually met. A missing
product decision stays unresolved rather than being filled from template examples.
Do not mechanically add empty canonical sections whose factual contents are lost.
Return them to their document owner for reconstruction from actual evidence.

Workers commit their source/document slice and SUMMARY. Join results before
integrating; retain uncompleted tasks, skips and blockers. Re-run `planning.review`
after changes and report remaining findings even when only safe repairs were
possible. Safe mechanical repairs are the normal cleanup path, not a separate
approval exercise.
</step>

<step name="archive_selected_records">
Archive only explicitly selected records in the user's authorized scope. Discover
existing archives and recovery entries before proposing moves:

```bash
phase_run query planning.archives --kind phase
phase_run query planning.archive phase <id-or-path>
phase_run query planning.archive adr <id-or-path>
phase_run query planning.archive quick <id-or-path>
```

The positional kind is `phase`, `adr` or `quick`; every selector must resolve
unambiguously. Preview is the default. Inspect moves, rewritten reference files,
eligibility evidence and recovery id. Active work is never archived because it is
old. Completed phases require checked plans, complete SUMMARY evidence and passed
VERIFICATION. Explicit legacy evidence may support a non-active record only.
ADRs require a superseding replacement and evidence; retain their argument and
status history. Quick items require authored completion or retirement evidence.
An explicitly obsolete/superseded record still needs the runtime's safe eligibility
checks and reference preservation; selection is not a bypass.

Use the evidence/replacement options when applicable:

```bash
phase_run query planning.archive adr <selector> --evidence .planning/<evidence>.md --replacement .planning/decisions/<replacement>.md
phase_run query planning.archive phase <selector> --evidence .planning/<legacy-evidence>.md
```

Apply the selected eligible preview with `--apply` within existing authorization.
Keep its recovery id and preserved logical IDs; ensure active references still
reach the archived records. Never permanently delete, renumber identities, use
glob selectors or hand-move planning directories. If reference rewriting or
eligibility remains ambiguous, leave that record active and report the exact
unresolved source. Preview recovery with
`planning.archive-recover <recovery-id>`; `--apply` performs its guarded rollback.
The archive journal/catalog is the runtime's recovery authority.
</step>

<step name="independent_checks_and_report">
Freeze the integrated candidate revision and wait for every required independent
report before accepting results or making further repairs. A source-changing
slice always gets a fresh `code-reviewer` with the base/candidate revisions,
changed paths, contracts and test evidence. A `doc-verifier` checks factual
document changes against cited source and actual runtime behavior. Spawn
`verifier` only when a needed phase/goal verdict requires independent acceptance
checks; cosmetic cleanup does not automatically require a phase verdict. Scout
packets assist these owners and never substitute for their judgment.

Run applicable offline runtime tests and the project's configured checks for the
changed behavior; report actual commands/results. Re-run `planning.validate`,
`planning.review` and archive discovery. Check that applied repairs are idempotent,
unfinished work remains unfinished, reference access and project prose survive,
and no template identity has been filled during template maintenance.

Return a concise account of inspected scope/revision, applied mechanical changes,
prose corrections and their sources, archived IDs/recovery ids, checks/reviewer
verdicts, and remaining semantic conflicts with the owner and next action. Commit
authorized changes and SUMMARY under the project's delivery rules. Do not claim
all planning clean when findings remain, or turn cleanup into unrelated product
work or a blanket completion update.
</step>

</process>
