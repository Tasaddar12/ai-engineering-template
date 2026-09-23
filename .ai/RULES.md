---
tier: intent
authority: human
title: Shared engineering rules
---

# Shared engineering rules

Every agent reads this core. Commands name procedures, workflows own those
procedures, agents own responsibilities, references supply operation-specific
detail, and repository skills supply reusable engineering methods. Use
[truth-map](truth-map.md) to find a fact's owner rather than maintaining another
copy of a rule.

## Layering

```
command (.ai/commands/) ── the entry point; names a workflow, changes nothing
  └─ workflow (.ai/workflows/) ── the procedure: what to load, whom to spawn,
                                   what to ask, which runtime verbs to call
       ├─ runtime (.ai/runtime/phase.py) ── every planning-record read and write
       └─ agent (.ai/agents/) ── a bounded role, spawned with its own context
```

A workflow orchestrates and a runtime verb mutates. A workflow that edits
ROADMAP.md, STATE.md or a phase directory by hand will drift from the runtime
that owns their structure: go through a verb. First-time creation of a record
from its template is the one exception.

Skills under `.agents/skills/` mirror the commands one-for-one, so a host that
discovers skills and a host that registers slash commands behave identically.

## Session and authorization

Preserve the project's established identity, requirements, decisions and history.
[PROJECT](../.planning/PROJECT.md) owns project context. Complete missing context
through [onboarding](commands/onboard.md) from the user's intent and inspected
source; do not treat workflow examples or upstream maintenance records as this
project's scope.

Read PROJECT, STATE, the selected phase and your role. Verify the repository root
and branch before writes. Inspect relevant sources at that revision.

A report request authorizes inspection, not implementation. An implementation
request authorizes its stated scope and the ordinary steps it implies. Record
actual human instructions; do not invent approval, and do not re-ask at internal
stage boundaries. A later instruction can change or cancel scope. For authorized
tracked changes, the default delivery boundary includes slice commits, pushes and
a pull request. This standing authorization applies unless the user narrows it
(no commit, local only, draft only, do not merge). It does not authorize
additional product scope or destructive cleanup. Read-only requests stay
read-only. Record the applicable default or explicit override in the phase's
CONTEXT.

### Commit and push workflow

1. **Finish one slice.** Run its applicable checks — preparation, code, tests,
   documentation or corrections.
2. **Commit immediately,** with a descriptive message. Agents include their SUMMARY.
3. **Push** when delivery is authorized.
4. **First push: open a draft PR for tracking.** Later pushes update that same PR.
5. **Repeat before starting the next slice or ending the turn.** Never batch
   completed slices into a later commit.
6. **Finish delivery** through [ship](commands/ship.md): verification passed,
   required checks green, then the user's merge instruction.

If a push or draft creation fails, report the blocker and preserve the commit.
Explicit no-commit, local-only or no-merge instructions override these defaults.
Read-only work needs no commit; reviewers do not edit or commit.

## Phase authority

**Every phase requires discussion with the user before planning or
implementation.** Phase creation, an implementation request and an existing PLAN
cannot substitute for that discussion. [discuss-phase](commands/discuss-phase.md)
writes `NN-CONTEXT.md` and `NN-DISCUSSION-LOG.md`, recording only actual
questions, options, evidence and replies. Unresolved choices must name the work
they block. Do not spawn implementation agents while a phase's decisions are
unrecorded. Discussion completion never grants implementation permission. The
log is audit-only; downstream agents read decisions in CONTEXT.

**NEVER start implementing a phase unless the user explicitly tells you to
implement that phase.** Creating, discussing, researching or planning a phase,
approving its design, passing readiness checks, and merging planning records do
not authorize implementation. Do not infer permission from a roadmap, a suggested
next action, an automatic continuation, or the default delivery workflow.

Record the user's explicit implementation instruction and the phase scope it
covers in CONTEXT before running [execute-phase](commands/execute-phase.md).
Without it, finish authorized planning and report that implementation awaits an
explicit instruction. Earlier explicit authorization stays valid for its stated
phases unless changed or withdrawn; do not ask again for the same permission.
Completing one phase never authorizes the next unless the instruction covers it.

PROJECT owns purpose and boundaries; REQUIREMENTS owns desired product outcomes;
ROADMAP owns the phase boundary. Phase CONTEXT owns acceptance, decisions, open
questions and execution authorization. PLAN documents supply bounded instructions
and reference that acceptance. Research, transcripts, agent results and status
views cannot authorize new scope.

Resolve changes to human intent before implementing dependent behavior. Record
the actual resolution in CONTEXT. Distinguish a choice within delegated discretion
from human approval. Questions block only dependent scope; continue independent
research or planned work. Never dispatch an assignment with a missing decision
disguised as an implementation detail.

Existing valid contracts govern unchanged behavior. Preserve approved outcomes;
never weaken acceptance or document missing behavior as complete. Substantive
scope changes need a recorded human decision. Routine adjustments within scope
need evidence and a recorded deviation.

Commit ready inputs before execution. An attempt uses its recorded input revision.
Reconcile changed inputs before a new attempt.

## Documents and conflicts

Current specifications under `.planning/specs/` describe verified behavior on the
deliverable revision. Phase `NN-SPEC.md` records desired behavior. Proposed
behavior stays in the phase until implemented. Guides explain actual use and
operation. Significant ADRs preserve rationale; supersede a decision with a new
ADR and links instead of rewriting its historical reasoning. Git and phase
records preserve ordinary change history; no separate journal is required.

### Retiring an entry

**Never strike an entry through, and never annotate one as "Closed", "Done" or
"Superseded" in place.** An item that no longer applies is removed from the
digest and recorded where that kind of fact is owned. Strikethrough is what an
agent reaches for when no retirement path exists; each of these is that path:

| Item | Retire it with | It lands in |
|---|---|---|
| Decision | already recorded when added; rotates out of the digest | PROJECT.md Key Decisions |
| Decision reversed | `state.add-decision` recording the replacement | PROJECT.md Key Decisions, as a new row |
| Blocker resolved | `state.clear-blocker "<match>"` | removed; git holds what it said |
| Requirement met | `requirements.set-status <id> Complete` | REQUIREMENTS.md Traceability |
| Scope deferred | `state.add-deferred <category> <item>` | STATE.md Deferred Items |
| Todo done | `todo.complete <name>` | `.planning/todos/completed/` |

`planning.validate` reports strikethroughs and in-place closure markers in any
planning record. It is warn-only: it never blocks a session on a cosmetic
finding, and `--strict` is for a caller that explicitly wants drift to fail.

### Deciding

Decisions that constrain future work belong in PROJECT.md's Key Decisions table,
written by `state.add-decision` as they are taken. A reversal is a new row
recording the replacement and what changed, not an edit to the old one.

**A technology choice is validated before it is proposed.** Before recommending a
library, runtime, service or integration, run the smallest thing that could fail
— install it and call the one API the project depends on, or make the integration
return one real response — and put what it actually printed in the decision's
rationale. Proposing a solution asserts it will work, and for anything that
executes, the only evidence for that is having executed it. A failed spike is
recorded as a finding rather than hidden: it is the cheapest possible version of
discovering the problem.

Decisions are taken while deciding, not while building. A choice that feels
consequential during execution means the phase was planned short of a decision it
needed: record a blocker and let planning decide it.

When sources disagree, identify both claims and inspect their evidence:

- Code violating valid required behavior needs a code correction.
- Documentation misstating established correct behavior needs a document correction.
- Authorized future behavior differing from current code is an approved transition.
- Conflicting human decisions need a recorded human resolution for dependent work.
- Duplicate fact owners need one authoritative owner and references elsewhere.

Research and tests provide evidence; neither alone changes user intent. Record
relevant findings in the affected phase. Unrelated discoveries go in its Deferred
section with evidence and the scope boundary, or become a todo through
[capture](commands/capture.md). A separately authorized change can become another
phase. Search before duplicating a finding. Deferring a required gap does not make
the original phase complete.

## Modular project rules

Read the [project rule catalog](rules/README.md) and the rule files applicable to
this assignment. Rules supplement project conventions; they do not replace skills,
approved specifications or actual user instructions. Use the
[rule template](templates/rule.md) when recording a new established convention.

## Orchestration and handoffs

The orchestrator owns routing, phase records and integration. It spawns agents
with fresh context for bounded work, and it does not do that work itself: a
workflow that reads files, edits code or runs tests while an agent is active
conflicts with the agent it dispatched.

Spawn agents by their exact name — `researcher`, `phase-preparer`,
`phase-checker`, `coder`, `verifier`, `code-reviewer`, `doc-writer`,
`doc-verifier`, `integration-checker`, `codebase-mapper`, `debugger`. Never
substitute a generic agent type; the project's own definitions carry the prompts
and tool permissions that make the result trustworthy. Resolve the model through
`phase_run query resolve-model <agent>` and the reasoning effort through
`phase_run query resolve-effort <agent>`, and pass both inline on the dispatch
call; agent definitions carry neither as frontmatter. A resolved `inherit` means
omit that argument and let the host choose.

Agents edit only the paths their plan declares, plus their own SUMMARY. They do
not spawn agents, switch branches, merge, publish or edit shared status.

Plan ownership uses exact repository-relative paths or directory prefixes ending
in `/`, without traversal, globs or whole-repository scope. Plans that declare
overlapping paths must not share an execution wave, whatever their declared wave
says. Genuine prerequisites define dependency edges; agree shared interfaces
before dispatch.

Give agents their assignment, the applicable constraints, the files their plan
names in `read_first`, and the dependency summaries they need — not every
transcript. Follow [worker handoff](references/worker-handoff.md).

## Issues found while working

Never stop an authorized run to ask about an issue. Never create todos. Route
each issue:

1. **In scope** — a defect, failing check or test, wrong plan assumption, or
   verification gap that blocks the phase goal or acceptance, inside the phase's
   files and decisions: fix it now. Dispatch the responsible `coder` or a
   `debugger` with `isolation="worktree"`, or plan gap closure. Record the
   deviation in the SUMMARY.
2. **Out of scope** — improvements, refactors, unrelated pre-existing bugs, new
   capability, flaky tests outside the phase, documentation debt: leave it in the
   plan SUMMARY's Deferred section (what, where, likely fix). List what is still
   open in the closing report.
3. **Needs a human** — changing a locked decision or acceptance; destructive or
   irreversible actions; unverified packages; credentials, access or spending:
   never guess. Mark only the dependent plan or step blocked, continue all
   independent work, and list each item with its options and a recommendation
   in the closing report.

For a choice inside the phase's locked decisions, acceptance and declared scope,
take the recommended option and record it:

```bash
phase_run query state.add-decision "<decision> (decided within delegated discretion)"
```

Do not call `todo.add`. Ask the user only the `/ship` merge question.

## Worktrees, integration and cleanup

**Every executor runs in its own worktree. This is not configurable.** Without
isolation, concurrent agents edit one working tree and interleave their commits
into one history, and a plan can no longer be attributed or reverted. Declaring
non-overlapping paths is a planning discipline, not an enforcement mechanism.

Resolve the model once per dispatch through
`phase_run query dispatch-isolation`, and branch only on the result:

- `harness-worktree` — the host creates and binds the checkout; pass its
  isolation argument on dispatch and run no git for setup.
- `orchestrator-worktree` — the runtime creates the checkout through
  `worktree.create`; every git operation is the runtime's.

There is no third value. No setting disables isolation, and a config that asks
for `none`, `null` or `false` is an error, not a fallback. When isolation cannot
be established — a git too old for worktrees, a worktree root that is not
ignored — the verb **fails and execution stops** with the cause. It never
degrades to a shared checkout.

**Enforcement is not prose.** [worktree-guard.sh](hooks/worktree-guard.sh)
refuses (exit 2) an `Agent`/`Task` dispatch of a write-capable subagent —
`coder`, `doc-writer`, `debugger` — that arrives without `isolation="worktree"`,
and warns on any edit or write from a checkout that is not a linked worktree.
The instruction in the workflow tells you to isolate; the hook is what makes
skipping it fail. A read-only agent has nothing to isolate and is not gated.

A wrong base is caught where it happens, not predicted beforehand: under
`harness-worktree` each executor's spawn-time branch check compares its real
base against the revision the orchestrator captured and halts on a mismatch.

The orchestrator owns the worktree lifecycle, and each model carries the one
guard it needs. Under `harness-worktree` the executor verifies its branch and
base at spawn through
[worktree-branch-check](references/worktree-branch-check.md) and halts with
`exit 42` on a mismatch; it never repairs a checkout it did not create. Under
`orchestrator-worktree` the runtime already set the base, so the executor is
pinned to its root instead — see
[worktree-path-safety](references/worktree-path-safety.md). Follow
[worktree-recovery-policy](references/worktree-recovery-policy.md) when a run
does not go cleanly.

Integrate every isolated wave through `worktree.merge-wave` before running
checks or review — both judge the merged tree, not one the work has not landed
in. A merge into a protected branch is refused. A branch that deletes a path its
plan did not declare in `files_deleted` is blocked, because a deletion
authorization is never inferred from a general scope declaration. A rename
counts: moving a file away removes its old path, so the source needs the same
authority as any other removal. Conflicts abort with the worktree preserved.

Cleanup requires merge evidence from the repository, not a manifest's claim:
`worktree.cleanup-wave` removes a checkout only when git agrees its branch is an
ancestor of HEAD, preserves everything else with a reason, and reports it.
Preserve unmerged, dirty and blocked worktrees. `--force` discards work and is
the user's decision, never the orchestrator's.

Worktree isolation does not isolate databases, ports, accounts or caches, and
ignored data is not automatically disposable. Declare shared resources before
running plans in parallel. Read-only reporting never needs a checkout.

## Review, documentation and completion

Before dispatching implementation, obtain an independent phase-checker assessment
when the phase has multiple plans, changes a shared interface, migrates persisted
data, or changes authentication, authorization or another security boundary.
Correct blocking findings before dispatch. Obtain independent verification for
implemented outcomes through [verify-work](commands/verify-work.md). Every phase
that changes source requires a separate fresh code-reviewer before completion;
a coder's self-check and a verifier reading a review method do not replace that
assignment. Additional review follows actual risk; there is no fixed count.
Correct findings within authorized scope and repeat the affected checks. Broaden
review when changed behavior invalidates prior evidence. Keep findings visible and
distinguish editorial details from defects.

Coders may update tests, comments and nearby explanations while their
understanding is fresh. For required documentation, assign a doc-writer when
creating a specification or guide, changing an operational sequence, or explaining
behavior across components. A command or option-name correction alone does not
require a separate doc-writer. Give the doc-writer exact document paths and the
implementation evidence for each changed claim. These triggers do not authorize
documentation outside the approved scope. Required documentation stays in the same
phase and PR; [documentation coverage](references/documentation.md) defines the
handoff.

Completion requires the observable outcome, integrated behavior, passing required
checks, accurate required documentation and conclusive independent verification.
A process exit, a summary assertion, a ticked checkbox or an existing file is not
proof. Bug repairs need reproduction and regression evidence.

Evidence names the tested revision and the actual commands and results. Material
content changes invalidate prior verification: a verification report whose
recorded revision is behind HEAD is stale, and re-verification is required rather
than optional. Publication readiness needs applicable authorization, current
verification and configured non-empty project checks. Observe required remote
checks after creating or updating the PR; pending or failed checks prevent
declaring it ready. Published, verified and merged are distinct facts. Never claim
delivery from an open PR. Follow [ship](commands/ship.md); it publishes and does
not merge. Missing credentials, unavailable remotes, failed checks and required
human reviews are concrete blockers: preserve the branch and report them without
bypassing repository protections or claiming delivery.

## Interruption and recovery

An agent that times out, exhausts its context or turn limit, or returns blocked
does not end the authorized phase and does not require another user prompt.
Inspect what it committed, what it left dirty and what it reported, then assign
only the remaining work to a fresh bounded agent. Preserve incomplete work, reuse
valid completed results, and keep independent ready plans moving.

A plan whose agent reported "complete" with no SUMMARY.md, or with no commits,
did not complete. Treat it as blocked and say so rather than ticking it.

The lowest-numbered phase whose plan files outnumber its summary files has
unfinished execution. [progress](commands/progress.md) and [next](commands/next.md)
check this before routing, and resume it ahead of new work — an advanced STATE.md
position is exactly when work gets silently dropped.

Resolve failures within authorized scope; stop dependent work only for a concrete
blocker requiring unavailable access, an external change or a new user decision.
Honor explicit user pauses and delivery limits. STATE.md's counters are derived
from ROADMAP.md on every write, so they cannot be corrected by editing them —
correct the roadmap.

## Hooks and validation

Hooks are optional advisory notices: they warn and return success. They neither
grant permission nor create a sandbox, and lexical path detection has limits.

Run checks appropriate to the changed behavior plus the project's required
commands. Runtime changes need real Git and subprocess tests; hook changes need
their Bash suites. Report actual outcomes, failures and skips. A check that
restates the implementation's wording does not establish behavior.
[Config](../.planning/config.yaml) owns command values and the model and effort
overrides; [runtime documentation](runtime/README.md) owns the verb interface.

## Complete template use

Read full templates, including examples, counterexamples, consumer descriptions
and lifecycle instructions. Do not shorten them or substitute a compact variant
without an assignment calling for it. Use the artifact block to write project
records; instructional examples are not real project decisions.

[Runtime behavior](references/template-adaptation.md) defines local runtime, host
and authority differences; [third-party notices](THIRD-PARTY-NOTICES.md) identify
upstream sources and adaptation history. A named agent method is not proof that
the host registered a slash command or agent type.

Project records belong to `.planning/`; reusable rules, workflows, templates and
tooling belong to `.ai/`.
