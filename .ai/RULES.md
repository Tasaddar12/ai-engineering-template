---
tier: intent
authority: human
title: Shared engineering rules
---

# Shared engineering rules

Every agent reads this core. Commands own procedures, roles own responsibilities,
references supply operation-specific details, and repository skills supply
reusable engineering methods. Use [truth-map](truth-map.md) to find the owner
rather than maintaining another copy of a rule.

## Session and authorization

Preserve the project's established identity, requirements, decisions and history.
[PROJECT](../.planning/PROJECT.md) owns project context. Complete missing context
through onboarding from the user's intent and inspected source; do not treat
workflow examples or upstream maintenance records as this project's scope.

Read PROJECT, STATE, the selected phase and role. Verify the assigned checkout's
absolute root and branch before writes. Inspect relevant sources at that
revision; another worker's checkout is not an integrated dependency.

A report request authorizes inspection, not implementation. An implementation
request authorizes its stated scope and ordinary necessary steps. Record actual
human instructions; do not invent approval or repeatedly ask at internal stage
boundaries. A later instruction can change or cancel scope. For authorized tracked
changes, the default delivery boundary includes slice commits, pushes, a pull
request (PR) or merge request (MR), and automatic merge after verification and
required checks. This standing authorization applies unless the user narrows it
(for example: no commit, local only, draft only, or do not merge). It does not
authorize additional product scope or destructive cleanup. Read-only requests
remain read-only. Record the applicable default or explicit override in existing
phase CONTEXT; standalone template maintenance needs no invented project records.

Authors commit each completed meaningful slice immediately, before starting the
next slice or returning, with a descriptive nonempty message. A slice is a bounded,
reviewable unit of the authorized task, with its applicable checks completed;
do not accumulate completed slices into one end-of-task commit. This includes
standalone work, preparation, code, tests, documentation and corrections.
Component workers also commit their SUMMARY and hand commits to the coordinator.
The coordinator must push each completed standalone or integrated slice
immediately after committing it, before starting the next slice or returning.
On the first push, open a draft PR/MR immediately for tracking; do not wait for
the task, phase, implementation or verification to finish. If a PR/MR already
exists for the task, update it instead of creating another. Push every subsequent
slice to that same PR/MR and keep its description current. Do not batch completed
slices into a later push or leave committed progress only on the local machine.
The draft tracks ongoing work; it does not claim readiness for review or merge.
If a push or draft creation fails, report the blocker and preserve the commit;
do not silently continue accumulating unpublished slices.
Workers keep their ownership boundaries and do not independently publish or merge.
An explicit instruction not to commit wins; local-only work is not pushed.
Read-only work needs no empty commit. Reviewers do not edit or commit the checkout.

## Phase authority

PROJECT owns purpose and boundaries; REQUIREMENTS owns desired product outcomes.
Phase CONTEXT owns exact acceptance, decisions, open questions and execution
authorization. PLAN documents supply bounded instructions and reference
that acceptance. Research, transcripts, worker results and status views cannot
authorize new scope.

Resolve changes to human intent before implementing dependent behavior. Record
the actual resolution in CONTEXT. Distinguish a choice within delegated discretion
from human approval. Questions block only dependent scope; continue independent
research or prepared components. Never dispatch an assignment with a missing
decision disguised as an implementation detail.

Existing valid contracts govern unchanged behavior. Preserve approved outcomes;
never weaken acceptance or document missing behavior as complete. Substantive
scope changes need a recorded human decision. Routine implementation adjustments
within scope need evidence and a recorded deviation.

Commit ready inputs before execution. An attempt uses its recorded input revision
and fingerprint. Reconcile changed inputs before a new attempt; never silently
reinterpret running workers' assignments.

## Documents and conflicts

Current specifications under `.planning/specs/` describe verified behavior on
the deliverable revision. Phase `NN-SPEC.md` records desired behavior. Proposed
behavior stays in the phase until implemented. Guides explain actual use and
operation. Significant ADRs preserve rationale; supersede a decision with a new
ADR and links instead of rewriting its historical reasoning. Git and phase
records preserve ordinary change history; no separate amendment or journal is
required. Current contracts remain readable without historical debate.

When sources disagree, identify both claims and inspect their evidence:

- Code violating valid required behavior needs a code correction.
- Documentation misstating established correct behavior needs a document correction.
- Authorized future behavior differing from current code is an approved transition.
- Conflicting human decisions need a recorded human resolution for dependent work.
- Duplicate fact owners need one authoritative owner and references elsewhere.

Research and tests provide evidence; neither alone changes user intent. Record
relevant findings in the affected phase. Unrelated discoveries go in its Deferred
section with evidence and the scope boundary. A separately authorized change can
become another phase. Search before duplicating a finding. Deferring a required
gap does not make the original phase complete.

## Components and handoffs

The coordinator owns phase records, scheduling and integration. It starts fresh
workers for bounded components. Workers edit only assigned paths in their own
worktrees, plus their assigned SUMMARY. They do not spawn agents, switch branches,
merge, rebase, publish, edit shared status or write other checkouts.

Ownership uses exact repository-relative paths or directory prefixes ending in
`/`, without traversal, globs or whole-repository scope. Shared files and exclusive
resources serialize execution. Genuine prerequisites define dependency edges.
Agree shared interfaces before dispatch. Ready components wait for their own
integrated and checked prerequisites, capacity and resources; displayed waves
are not a global barrier. Only the coordinator integrates component commits.

Give workers applicable constraints, their assignment, required source, relevant
research and dependency summaries. Do not load every transcript or component.
Follow [worker handoff](references/worker-handoff.md).

## Review, documentation and completion

Use independent preparation checking for substantial phases and independent
verification for implemented outcomes. Additional review follows actual risk;
there is no fixed review count. Correct findings within authorized scope and
repeat affected checks. Broaden review when changed behavior invalidates prior
evidence. Keep findings visible and distinguish editorial details from defects.

Coders may update tests, comments and assigned nearby explanations while their
understanding is fresh. Assign substantial specifications and guides to a
documentor when useful. Required documentation stays in the same phase and PR;
[documentation coverage](references/documentation.md) defines the handoff.

Completion requires the observable outcome, integrated behavior, passing required
checks, accurate required documentation and conclusive independent verification.
Required UAT must pass. A process exit, summary assertion, checkbox or existing
file is not proof. Bug repairs need reproduction and regression evidence.

Evidence names the tested revision and actual commands/results. Material content
changes invalidate prior verification. Final publication readiness needs applicable
authorization, current verification and configured nonempty local checks. Default
draft progress pushes may precede completion; describe their unfinished scope
honestly. Observe required remote checks
after creating/updating the PR; pending or failed checks prevent declaring it
ready. Published, verified and merged are distinct facts. Never claim delivery
from an open PR or replace failed publication with a local merge. The coordinator
automatically merges the verified PR/MR through the forge unless the user opts
out, then confirms the remote merged state and revision. Follow
[phase-ship](commands/phase-ship.md) for both standalone and phase delivery.
The Python runtime publishes GitHub PRs only; the coordinator performs the merge
and uses the forge's supported tools for MRs. Missing credentials, unavailable
remotes, failed checks or required human reviews are concrete blockers: preserve
the branch and report them without bypassing repository protections or claiming
delivery. Do not ask again merely because delivery reached an internal step.

## Worktrees, recovery and cleanup

Every tracked mutation uses an assigned immediate-child worktree under the primary
checkout's ignored `.worktrees/`. Create siblings from the verified primary root;
never nest one under a linked checkout. The primary allows inspection, fetch and
verified fast-forward synchronization, not tracked edits or commits.
Follow [worktree](commands/worktree.md).

Require clean committed inputs at runtime boundaries. Serialize shared Git
operations and protect runtime state with its common-directory lock. Worktrees
isolate Git changes, not ports, databases or arbitrary external writes; declare
exclusive resources and respect host permissions.

Do not blindly restart an interrupted worker. Inspect its process, worktree,
commits and result before reconciliation. Preserve incomplete and unmerged work.
Status is read-only; the coordinator explicitly syncs the derived STATE view.
Local checkpoints are operational data; durable summaries and reports ship with
the phase. Old attempts require their compatible original runtime.

Remove only identified clean merged worktrees when cleanup is authorized. Verify
absolute targets stay within the intended worktree root. Preserve dirty, unmerged,
ignored or unrelated data. Uncertain cleanup is a report, not a forced deletion.

## Hooks and validation

Hooks are optional advisory notices: they warn and return success. They neither
grant permission nor create a sandbox, and lexical path detection has limits.

Run checks appropriate to changed behavior and required project commands. Runtime
changes need real Git/process workflow tests; hook changes need their Bash suites.
Report actual outcomes, failures and skips. Checks that repeat implementation
wording do not establish behavior. [Config](../.planning/config.yaml) owns command values and
worker routes; [runtime documentation](runtime/README.md) owns the CLI interface.

## Complete template use

Read full templates, including examples, counterexamples, consumer descriptions
and lifecycle instructions. Do not shorten them or substitute a compact variant
without an assignment calling for it. Use the artifact block to write project
records; instructional examples are not real project decisions.

The [template adaptation](references/template-adaptation.md) defines local runtime, host and
authority differences; [third-party notices](THIRD-PARTY-NOTICES.md) identify
upstream sources and adaptation history. Complete agent methods and their pinned external supporting sources
supply guidance, not installed slash commands. Use actual local procedures and
the runtime contract for execution.
Project records belong to `.planning/`; reusable rules, templates and tooling
belong to `.ai/`.
