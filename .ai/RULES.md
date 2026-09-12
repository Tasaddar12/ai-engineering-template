---
tier: intent
authority: human
title: Shared engineering rules
---

# Shared engineering rules

Every agent reads this core. Commands own procedures, roles own responsibilities,
and references supply operation-specific details. Use [truth-map](truth-map.md)
to find the owner rather than maintaining another copy of a rule.

## Session and authorization

This is a reusable template. Keep [PROJECT](PROJECT.md) unfilled until adoption.
Template maintenance creates only project records requested by the user.
Historical records remain history.

Read PROJECT, STATE, the selected phase and role. Verify the assigned checkout's
absolute root and branch before writes. Inspect relevant sources at that
revision; another worker's checkout is not an integrated dependency.

A report request authorizes inspection, not implementation. An implementation
request authorizes its stated scope and ordinary necessary steps. Record actual
human instructions; do not invent approval or repeatedly ask at internal stage
boundaries. A later instruction can change or cancel scope. Publication, merge
and destructive cleanup need authorization covering those actions. The phase
runtime publishes PRs and never merges them.

Authors commit completed standalone work and component changes with descriptive,
nonempty messages before returning. Component workers also commit their SUMMARY.
An explicit instruction not to commit wins. Read-only work needs no empty commit.
Reviewers do not edit or commit the checkout.

## Phase authority

PROJECT owns purpose and boundaries; REQUIREMENTS owns desired product outcomes.
Phase CONTEXT owns exact acceptance, decisions, open questions and execution
authorization. IMPLEMENT documents supply bounded instructions and reference
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

SPECs describe verified current behavior on the deliverable revision. Proposed
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
changes invalidate prior verification. Publication needs authorization, current
verification and configured nonempty local checks. Observe required remote checks
after creating/updating the PR; pending or failed checks prevent declaring it
ready. Published, verified and merged are distinct facts. Never claim delivery
from an open PR or replace failed publication with a local merge.

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
wording do not establish behavior. [Config](config.yaml) owns command values and
worker routes; [runtime documentation](runtime/README.md) owns the CLI interface.
