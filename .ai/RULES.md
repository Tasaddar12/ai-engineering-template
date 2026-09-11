---
tier: intent
authority: human
id: RULES
title: Rules of engagement for AI agents
---

# Rules of Engagement

Every agent reads and follows this file before acting. Shared project and
workflow rules live here. Agent files own their specific instructions and
commands own their procedures; both reference this file for shared rules.

## Session and authorization

This repository is a reusable template. Do not create project-specific PLANs,
SPECs, ADRs, AMDs or journal entries for template maintenance unless the user
requests them. Keep the adopting project's identity and intent unfilled until
onboarding. Existing historical records remain history.

Read PROJECT, STATE, the selected record and role, and verify the absolute
checkout root and branch before writes. Work in the assigned checkout; do not
read or edit sibling worktrees as a substitute for the assigned Git revision.
The post-PLAN defect auditor may inspect explicitly assigned preserved trees.

Report when asked to report; implement when authorized to implement. An explicit
instruction authorizes its exact scope and ordinary necessary steps. Do not
ask again for an approval already supplied. Publication, merge and destructive
cleanup require authorization covering those actions. A later human instruction
can change or cancel earlier scope.

Always commit task changes with a nonempty descriptive message before the final
response. An explicit instruction not to commit wins. Read-only work needs no
empty commit. Commit every implementation and documentation step in a PLAN
separately as it completes; do not accumulate several steps into a phase commit.

## The Prime Rule

Human intent governs the proposed target. Preserve approved outcomes and
establish which side is wrong when code and documents disagree.

## Intent and PLAN approval

PROJECT owns human intent: purpose, success, non-goals, hard constraints and
out-of-bounds actions. A PLAN cannot approve, override or automatically change
intent, including when the intended change is inside its own target.

Every PLAN explicitly declares whether it requests intent changes in its
Execution contract. Each request states the proposed change, a decision
(pending, approved or rejected), and the actual human resolution. Resolve every
requested change with a human before any implementation of that PLAN starts.
Approval without a recorded human resolution is insufficient. A rejected
request requires a revised proposal or cancellation, not an implementation
workaround. Existing explicit human approval can be recorded without asking again.
Any newly discovered intent conflict pauses that PLAN until resolved; other
unblocked PLANs continue.

Planning can propose future non-intent contract changes and explain conflicts
with existing contracts. It does not authorize execution by itself. Once
implementation is authorized and intent decisions are resolved, preserve the
PLAN's intended outcome. Existing contracts govern behavior left unchanged.

Do not invent a requirement or silently choose between unresolved human
decisions. Do not bend code around stale documentation or weaken a valid
target to excuse a bug. Investigate whether code or documentation is wrong
using observed behavior and tests, then assign the correction to its owner.

Concrete critical breakage (data loss, a security failure, corruption, broken
build/startup or loss of a core capability) requires a FIX or supporting PLAN,
ordered by dependency under an ORCH when appropriate. Preserve the original
target and continue independent work. Supporting work never evades a human
rejection or cancellation.

## What each document is for

Three document types carry almost all the weight, and keeping them apart is
what stops the record from becoming an archaeology exercise.

| Document | Tense | Holds |
|---|---|---|
| `specs/SPEC-*.md` | **present** | What correct behavior *is*, right now |
| `decisions/ADR-*.md` | past | Why we chose this, and what it replaced |
| `plans/**/PLAN-*.md` | future | What we intend to build next |

A SPEC is based only on verified actual code and observed behavior. Documents
may guide investigation but cannot establish a SPEC claim. A SPEC contains no
references to other documents, including ADR/PLAN/AMD IDs or frontmatter links.
Amendments, decisions and PLANs may link inward to a SPEC. Use general module
areas, symbols and behavioral checks instead of fragile line references/counts.

**A spec describes the system as it is.** Read cold, with nothing else open, it
must be a true statement about the software today. That has one strict
consequence:

> A spec never records its own history. No "removed in v2", no "deprecated",
> no "no longer applies", no "not yet implemented", no "was previously 300ms",
> no strikethrough, no commented-out criteria, no `TODO`.

When a requirement changes, **rewrite the spec so it states the new requirement
and nothing else.** When a requirement goes away, **delete it** — the
criterion, the section, or the whole spec file. Nothing is lost by deleting it:
the amendment record says what the spec used to say and why it moved, the ADR
says why the decision changed, and git holds every previous version. Leaving
the old wording behind as an annotation is how a spec turns into something an
agent has to interpret instead of read — and an agent interpreting a spec is an
agent guessing.

**A spec never describes behavior that does not exist yet.** A spec asserting
the target state makes every verification fail, which teaches everyone to
ignore the verifier. Unbuilt behavior lives in the plan that will build it,
under its **Contract changes** section — the exact wording the spec will carry
on the merged/deliverable revision. The documentor lands that wording after
both code reviews in the final documentation batch.

**An ADR is the opposite of a spec** — a dated record, and allowed to be about
the past. That is why superseding an ADR means writing a new one that points at
it, never rewriting the old one, and why only an ADR with `status: accepted` is
authority.

**A PLAN carries an intended future outcome; once execution is authorized,
implementation and verification must preserve it.**

---

## Mutability tiers

Every project record under `.ai/` declares a tier in its frontmatter.
Executable files and agent/command entry points are not project records. The tier tells you
what you may do without asking.

| Tier | What it holds | Examples | You may |
|---|---|---|---|
| `intent` | Why this project exists; hard constraints; non-goals | `state/PROJECT.md`, this file | Human authority. Explicit human resolution is required for any requested intent change before PLAN implementation. |
| `contract` | What "correct" means right now | `specs/SPEC-*.md`, `decisions/ADR-*.md` | Documentation agents amend with verified evidence and a recorded amendment. |
| `plan` | How we intend to get there | `plans/**/PLAN-*.md`, `fixes/**/FIX-*.md` | Assigned planning/documentation agents revise PLANs; implementors may create FIX/INTAKE records. |
| `status` | Where things stand | `state/STATE.md` | The assigned coordinator updates the present. |
| `log` | What happened | `state/journal/*.md`, `decisions/amendments/*.md` | **Append only.** Never edit or delete past entries. |

Frontmatter on every `.ai/` document:

```yaml
---
tier: contract          # intent | contract | plan | status | log
authority: agent        # human | agent  — who has final say
id: ADR-0004
title: Short human-readable title
links: [PLAN-011]
---
```

Two things deliberately absent from plan frontmatter: a `status:` field and a
`stage:` field. **A plan's stage is its directory.** Duplicating it in
frontmatter creates a second version of the truth that will eventually
disagree with the first. The same holds for a fix.

---

## Plans move the contract with them

A plan is not only a to-do list. Most plans change what "correct" means, and a
plan that changes behavior without moving the contract leaves the specs
describing software that no longer exists.

So every plan declares, up front, in its **Contract changes** section:

- **Specs it creates** — with the acceptance criteria drafted in the plan, in
  present tense, ready to land verbatim.
- **Specs it amends** — the criterion that moves, and its replacement wording.
  Also drafted in the plan, not written into `specs/` ahead of the code.
- **Decisions it needs** — a new ADR when the plan embodies reasoning that
  outlives it; an existing ADR it *confirms*, cited by id; or an existing ADR
  it **supersedes**.

That section is what the plan-checker reviews and what closing the plan is
graded against. A plan that changes behavior and lists nothing there is either
mislabelled or has not been thought through.

**Superseding an ADR** takes a new ADR that names the old one in its
`supersedes:` frontmatter. On the old ADR, set `status: superseded` and
`superseded_by:` — that is the one edit to a `contract`-tier file that needs no
amendment record, because the new ADR *is* the record. Never rewrite the old
ADR's Context, Decision or Alternatives; its whole value is being an accurate
account of what was decided at the time.

## PLAN records and commits

A PLAN contains its goal, acceptance, unchanged governing behavior, dependencies,
owned paths, proposed contract changes, risks and an Execution contract.
The contract is a JSON block with intent_changes, ordered steps and
completed_intake. An empty intent_changes list explicitly requests no intent change.
completed_intake lists existing captures the implementation is expected to resolve;
a name in that list alone is not proof of completion.

Each step has a unique stable id, a title and phase build or document. Define
independently verifiable slices and include documentation steps for expected
documentation edits. Runtime reads this explicit contract at the initial Git
revision; it does not infer steps from prose or let later notes weaken the target.
Resolve dependencies and human intent before dispatch.

Commit each PLAN step separately, immediately after its work and checks. Runtime
build/document workers make those commits in their assigned branch and use:
`PLAN-Step: <original-plan-path>#<step-id>` as a commit trailer. Each trailer
corresponds to exactly one ordered step in the assigned phase. Empty commits,
a batch standing in for multiple steps, or research/FIX/INTAKE-only commits
standing in for implementation are not completion. Additional evidence-only
commits are allowed. Permission failure preserves the work for recovery;
it never authorizes bypassing host permissions.

PLAN content is written by planning/documentation agents. Implementors do not
rewrite the target, contract, steps or acceptance; they report discoveries.
The documentor updates PLAN notes and final documentation after code review.
The coordinator performs directory moves without rewriting content.

## Roles

Each [agent file](agents/README.md) owns that agent's scope, duties, inputs,
methods and reporting requirements. Every agent reads and follows this file
for shared rules. Its assignment may narrow its role's scope.

The roles are instructions, not an installed dispatcher or permission system.
Use [Review and documentation](#review-and-documentation) for the shared
handoff and documentation-ownership requirements.

## The amendment protocol

The assigned documentor uses this after code review when changing a
`contract`-tier file: a spec or an ADR.

1. Write the amendment record first: copy `templates/AMENDMENT.md` to
   `decisions/amendments/AMD-<nnn>-<slug>.md`. It captures four things — what
   the document said, what is actually true, why they diverged, and what you
   changed it to.
2. Rewrite the spec so it states the new truth and nothing else — replace the
   wording, never annotate it, and delete the criterion outright if the
   requirement is gone. On an ADR, correct a factual error only; changing the
   decision is a new ADR, not an edit.
3. Keep the affected document reference in the AMD. An ADR may link back to
   the amendment; a SPEC never contains document references.
4. Include both files in the documentation commit in the same PR as the code
   change. Implementation and documentation commits may be separate while the
   track is under review.

The record exists so a human can audit *why* the contract moved, not to slow
you down. It is three sentences, not an essay. **An amendment is never a
failure**; it is the system working. A project whose specs never get amended is
a project whose specs are being ignored.

For a PLAN with human intent resolved, this protocol records the transition
after code review two. Future contract wording stays in the PLAN during
implementation; unresolved intent requests follow the approval rule above.

Amendments are `log` tier — append only. If a later amendment supersedes an
earlier one, write a new record that says so.

**An amendment records the change, so the spec does not have to.** Rewrite the
spec to state the new truth cleanly and leave no trace of the old wording in
it. If you find yourself wanting to annotate the spec so a reader can tell
what changed, that is the amendment's job and it is already done.

---

## Bug fixes

Not every change needs a plan. A **bug fix** is a change that makes the code do
what the record already says it should, and the line is exactly that:

> A fix restores conformance with the contract. A plan changes what
> conformance means.

If existing requirements, the approved target or demonstrable code invariants
establish a defect, that is a fix even when a SPEC is silent. Nothing in `contract` tier moves, so
there is no spec to amend, no ADR to write, and no reason to spend the whole
plan lifecycle on it.

Every confirmed code bug gets a FIX, at every severity and scope. Unknowns,
documentation discrepancies, ideas, concepts and other fragments get INTAKE.
Never label an unconfirmed suspicion a code bug.

A fix gets a short record at `fixes/open/FIX-{nnn}-{slug}.md` from
`templates/FIX.md`, and a two-stage lifecycle of the same kind as a plan — the
stage is the directory: `fixes/open/` while it is being worked,
`fixes/done/<period>/` once it holds. [`/fix`](../.ai/commands/fix.md) runs
the whole loop.

Four things go in the record: the symptom, the root cause, the change, and the
check that fails before and passes after. **A fix is not done without that
check** — a fix with no regression test is a fix with a scheduled recurrence.
And the record exists because a defect nobody wrote down is a defect that gets
reintroduced by the next agent, who has no way to know it was ever considered.

Three things look like fixes and need care. **FIX items are code-only:**

- **The spec is silent on the case.** Capture the contract decision as its own
  INTAKE. If existing acceptance or a demonstrable code invariant establishes a defect,
  record that separately as a FIX; otherwise do not invent correctness in a fix.
- **The spec or documentation is wrong.** Capture an INTAKE for the correction.
  It becomes planned documentation/contract work later, not a code FIX.
- **The fix needs an ADR, a spec rewrite, or more than a handful of files.**
  Promote it with `/plan-new` and link the fix record from the plan. A fix that
  grows into a plan is normal and expected; a plan disguised as a fix skips the
  checker and the verifier, which is the failure this route can produce.

Do not use a fix to sneak a behavior change past review, and do not open a plan
for a one-line defect the requirements already condemn. Make the smallest
cause-directed change, without unrelated refactoring. If reproduction fails,
record uncertainty rather than guessing. Manual-only verification is a
disclosed weakness, not an automated pass.

Standalone/manual fixes use one commit per FIX with source, regression check
and proof. Runtime correction workers return proof and leave scoped changes
for the coordinator's audited correction commit. Workers can create new
FIX/INTAKE records within their assigned ranges; documentors/coordinators
update existing record content and lifecycle according to role ownership.

---

## Meeting notes and design documents are not contracts

A meeting note, a design doc, a whiteboard write-up, an email thread: all `log`
tier. They record what was said on a date. **Nothing in them is authoritative,
including sentences that begin "we will".**

Never implement from one. A note where three options were debated is a debate,
not a specification, and the wording in the room does not distinguish a
decision from a strong opinion. Two specific failures:

- **Reading discussion as a requirement.** The rejected option is written down
  in the same prose as the chosen one.
- **Reading a decision as reality.** A meeting decided to move to a new
  architecture; the code is still the old one. The note describes neither the
  present nor a lie — it describes an intention. An agent that treats it as
  current will "fix" working code to match something nobody has built.

Accepted ADRs record decisions. Meeting notes alone never authorize intent or
scope changes. A PLAN may propose intent changes, but each request needs an
explicit human resolution before implementation, including changes inside the
PLAN target. An agent that finds an unbuilt idea raises the gap as INTAKE or a
PLAN proposal.

Turning notes into contracts is what [`/harvest`](../.ai/commands/harvest.md)
does. A note carries `harvested:` in its frontmatter so you can tell whether
its contents are in effect yet.

## Precedence when documents disagree

1. **Human intent** governs purpose, constraints and authorized scope. A PLAN
   cannot override it; requested changes follow Intent and PLAN approval.
2. **Working, tested code** is evidence of present behavior, not a veto over an
   approved future target. First confirm the code is right: a bug does not
   authorize rewriting a valid requirement to excuse it.
3. **The authorized PLAN target** governs declared future changes after human
   intent requests are resolved. Exact future wording remains in the PLAN
   until code review and documentation are complete.
4. **Existing contracts** govern unchanged behavior. Check accepted ADRs and
   amendment history when establishing which contract is current.
5. **Meeting and Research notes** are evidence, never requirements. A note
   cannot override intent, an approved target or a verified contract.

If two documents at the same tier disagree and you cannot tell which is
correct, that is a `truth-map.md` violation — two files own the same fact. Fix
the ownership, not just the wording, after preserving the PLAN's
target. See [truth-map.md](truth-map.md).

---

## Writing specs that survive

Most spec churn is self-inflicted, caused by specs that describe an
implementation instead of a requirement. A spec that names a file, a function,
or a constant is falsified by the next refactor.

Write **acceptance criteria and invariants**, not instructions:

| Don't | Do |
|---|---|
| "Use a 300ms debounce in `useSearch.ts`" | "Typing quickly issues at most one request per burst" |
| "Store the token in `localStorage`" | "A returning user is still signed in; the token is never readable by third-party script" |
| "Add a `retry_count` column" | "A failed job is retried at most 3 times, and its attempt count survives a restart" |

The second cause of churn is specs that narrate their own history. Same table,
different failure:

| Don't | Do |
|---|---|
| "Sessions last 30 days (was 7 days before ADR-0012)" | "A session lasts 30 days" |
| "~~Passwords must be 8 characters~~ **Deprecated — see below**" | Delete the line. Write the current rule once. |
| "Export to CSV. *(XML export removed in v3.)*" | "Export produces CSV." |
| "Rate limiting — not yet implemented" | Delete it. It belongs in the plan that will build it. |
| "Retries: 3 (TODO: confirm with ops)" | Put it under **Open questions**, or leave it out. |

Two tests, and a spec has to pass both:

1. *Could this stay true through a rewrite of the module?* If not, it belongs in
   a plan or an ADR.
2. *Is every sentence in it true of the software right now?* If not, either the
   code is wrong or the spec is — resolve it, do not annotate it.

---

## Review and documentation

All product documentation work happens after both code reviews. This includes
SPECs, ADRs, AMDs, PLAN delivery notes, guides, comments and docstrings.
Only documentation agents modify SPECs, ADRs, AMDs and other product
documentation. Code agents do not mix documentation
cleanup into implementation. Functional directives embedded in comments
(e.g. compiler pragmas) remain executable configuration, not editorial prose.

A completed track runs two fresh code reviews, with at most one immediate code
correction between them. The second runs even if the first approves. After the
code handoff, the documentation agent completes the documentation steps. Two
documentation reviews follow, with at most one documentation correction between
them. No third review, repeated immediate fix pass or late scribe refresh.
Interrupted sessions do not reset attempt counts.

Research notes may be written before implementation and may be read by
implementors and reviewers. Planning documents are preparation; PLAN delivery
notes and product documentation use the post-code-review handoff.

Documentation agents receive Research notes, implementation reports, code-review
findings and proof. They verify actual behavior, then update SPECs, ADRs, AMDs,
PLANs and other documents. They preserve the intended outcome instead of
documenting incomplete code as accepted. They prefer general script areas,
symbols and behavior over unstable source line numbers and counts.

Late comments/docstrings may touch explicitly declared source_documentation_paths.
They must preserve executable behavior. Runtime checks Python AST equivalence
after removing docstrings; other languages need an explicit project-supplied
equivalence command. Missing equivalence support parks that edit rather than
allowing unchecked source changes after code review.

Record substantive problems and minor editorial findings accurately.
Spelling, stale line references, approximate item counts, layout and similar
details never make otherwise adequate SPEC coverage incomplete and never block
closeout. A number that defines actual behavior (such as a retry limit) is a
functional claim, not an editorial count.

## Definition of done

PLAN-Done validates and delivers already complete work. It does not repair code,
rewrite documentation, weaken a target or start another review.

Its substantive rejection reasons are:
1. Actual required code is missing.
2. Actual required functionality is missing or broken.
3. The overall implementation is not documented accurately in SPECs.

On rejection, leave lifecycle records in place and report the missing behavior
or coverage, evidence, and concrete next actions. Confirmed code defects go to
FIX; substantial missing work can need a supporting PLAN. Documentation agents
address missing SPEC coverage. Preserve the original target. Spinning off a
FIX or PLAN does not make an incomplete original implementation mergeable.

Small documentation corrections never block. A fully implemented result with
adequate SPEC coverage may retain editorial or unrelated INTAKE/FIX follow-ups.
Preserve the actual review verdict; delivery does not turn findings into approval.
All modes use actual-code SPEC coverage at closeout, including light mode.

Validate the entire closing set before making lifecycle changes. Then move the
completed PLAN and only evidenced, resolved INTAKE items to plans/done/<period>,
commit those mechanical moves, and complete authorized clean delivery.
Unverified/unrelated captures stay open. The coordinator records the resulting
present and history after delivery; PLAN-Done does not perform content repairs.

Execution prerequisites remain necessary: authorization, conclusive evidence,
passing required checks, valid worker results, clean Git state and a working
forge. Missing evidence is not a pass. These are operational delivery conditions,
not additional editorial standards. A failed required check or operational
failure preserves work and reports recovery actions.

## Problems you find but are not going to fix

Scope discipline says don't fix what the current change isn't about. That is
correct, and it is not permission to let the finding evaporate. **A problem
mentioned only in a session summary is lost**, and the next agent will
rediscover it and quietly work around it — which is the failure at the top of
this file, arriving by a slower route.

So: capture, don't fix, and don't merely mention. Use `/defer`. Confirmed code
defects go directly to `fixes/open/FIX-{nnn}-{slug}.md`, at every severity and
even when out of scope. Documentation and contract corrections each get their
own `plans/intake/INTAKE-{nnn}-{slug}.md`; other unplanned work also uses INTAKE.
Use the corresponding template. FIX work proceeds through `/fix`; INTAKE work
is triaged through `/plan-archive` and `/plan-new`.

Documentation agents resolve in-scope documentation contradictions and
ownership duplicates after code review. Other agents hand off the evidence;
they do not interrupt code work to edit documentation. Unrelated fragments are
captured as INTAKE for later documentation work.

Search existing records before creating a duplicate. Repeated root causes
reuse the record with new evidence. Omission from a later review is not proof
of correction. Only evidenced resolved INTAKE items move to done/<period>;
unrelated or unverified captures stay open. Abandoned means deliberately
rejected by a human scope decision, not successfully delivered.

## Autonomous review and fix

Residual missing code/functionality or absent overall SPEC coverage prevents
merge. Capture its FIX/INTAKE evidence and identify supporting work; do not
use severity downgrades or a permissive residual-policy override to close it.

After other PLAN work completes, a fresh read-only audit examines open code
FIXes, previous proof and actual integrated or explicitly preserved trees.
A parked defect and work waiting on it do not prevent examining that defect;
other unfinished project PLANs do. Include open reports from earlier runs.
Current done/abandoned record lifecycle overrides stale receipt copies.
The audit does not close unproved records, repair code, or restart the original
review loop. Documentation fragments remain INTAKE for planned documentation work.

## When you are genuinely blocked

An unresolved human intent request blocks that PLAN before implementation,
even when it falls inside the proposed target. An existing document's old
non-intent wording alone does not create a human decision. Concrete critical
breakage follows the supporting FIX/PLAN procedure. Never use supporting work
to evade a later explicit human rejection or cancellation.

When a genuinely missing human decision blocks the work:

1. Move the plan to `plans/blocked/`.
2. Have the planning/documentation agent add a `## Blocked` section to it: the question, the options you see, and
   your recommendation.
3. Record it under blockers in `state/STATE.md`.
4. **Do every part of the task that does not depend on the answer**, then
   report what you finished and what is waiting.

Do not sit idle on a missing decision: do every independent part of the task
and report what is waiting. Do not silently pick an answer to an unresolved
intent-tier question or override an explicit later human instruction.

## Single owner

Each fact has one owner, indexed by truth-map. Other documents link to that
owner instead of copying rules or thresholds. Add an ownership entry before
introducing a new fact category. Resolve conflicting owners, not just wording.

Shared project and workflow rules belong in this file. Each agent's specific
instructions belong in its agent file, which references this file. Commands
own their operating procedures. Templates hold fields and example record
shapes; guides provide navigation, examples and tool interfaces.
Self-contained SPECs are the exception to outbound links: they state their own
verified behavior without citing another document.

## Scheduling and IDs

A track is one worktree/branch/PR containing sequential PLANs. Waves display
dependency depth only. Run every unblocked track as soon as its own prerequisites,
capacity and resources permit; wait only for blocked tracks and their dependents.
A ready dependent need not wait for unrelated earlier-wave work.

Shared source, SPECs or ADRs are contention; genuine build/verification
prerequisites are dependencies. Group overlapping owners or serialize them.
Declare dependency evidence and confidence. Do not silently break a cycle;
propose a corrected dependency or PLAN boundary. Exclude vague work without
usable steps/acceptance and explain why. Recheck ready PLANs against landed
prerequisites before allocation.

lifecycle.max_active is guidance. Report excess concurrency without rejecting
work or requesting permission merely because the suggested count is exceeded.
orchestration.max_parallel_tracks limits actual runtime capacity.

Reserve 20 IDs of each type (FIX, INTAKE, SPEC, ADR, AMD) for every track at
dispatch, before branching. Exclude templates/examples when finding existing
IDs. Previously issued blocks are never reused. Workers create records only
within their reserved ranges; the coordinator allocates structured findings
without colliding with worker-created records.

The normal process estimate is tracks x 6 through tracks x 8: one build,
two code reviewers, one documentation worker, two documentation reviewers,
and up to one correction of each kind. Three tracks therefore use 18–24
workers, plus scheduling and any later defect audit. Separate manual research
sessions or exceptional recovery change the estimate and must be disclosed.

## Runtime worker protocol

The explicit JSON execution snapshot uses protocol_version 2. PLANs contain
their own Execution contract; runtime reads it at plan_source_sha. Old schedules
must be reconciled with their compatible runtime/receipts, not silently upgraded
or restarted with cleared review counts. Configuration is not parsed from YAML.

The worker follows this file and its assigned role. Assignment supplies phase,
worktree/branch, original PLANs, steps, scopes, research paths, reserved IDs,
checks and documentation handoff. Run only the assigned phase: no nested agents,
branch changes, merge/rebase, publication or sibling-worktree writes.
Build/document workers commit each assigned step; fix/docs-fix workers leave
their scoped edits for the coordinator's audited correction commit. Reviewers
do not edit or commit. Host permissions must support the selected Git operations.

Use argv commands and the supplied result schema. Return complete or blocked
with actual evidence, implementation_complete, documentation_complete,
spec_coverage, resolved_intake and findings. Code reviews assess implementation;
documentation reviews assess overall SPEC coverage. Each coverage entry names
the PLAN, an existing SPEC path and code evidence. Each resolved INTAKE entry
names a declared capture and evidence of its actual completion.

Findings use stable keys, kind, severity, general path/area, evidence and impact:
missing_code, missing_functionality, missing_spec_coverage, editorial or unrelated.
Do not classify a code bug as editorial. Use approved only with no findings,
changes_requested with findings, and cannot_review for insufficient evidence.
Do not use a false completeness flag for spelling/count/line-reference issues.

Ownership uses exact paths or directory prefixes ending in /. No traversal,
globs or whole-repository scope. code_paths and documentation_paths are
disjoint subsets of owned_paths. Prose document extensions are .md, .markdown,
.rst and .adoc. Executable configuration remains code regardless of directory.
research_paths name separate owned notes; source_documentation_paths name
explicit code files with behavior-equivalence verification.

Shared STATE, journal, run boards and receipts are coordinator-owned.
Workers may create new FIX/INTAKE reports; the coordinator audits reserved IDs
and preserves them in the queue. It also creates reports from structured
review findings and retains valid evidence even if a phase fails its edit audit.

## Delivery, recovery and cleanup

Require a clean synchronized target checkout and ignored worktree root.
Allocate new tracks at the verified target revision containing their dependencies.
Declare exclusive ports/databases/caches/accounts and distinct environment
settings. Worktrees do not isolate external services or arbitrary writes;
host permissions provide the sandbox. Permission failure never authorizes bypass.

Require nonempty local checks and named GitHub checks. Missing, skipped,
failed or inconclusive required checks are not success; optional checks do not
gate delivery. GitHub formal changes-requested reviews remain a forge gate.
Require strict up-to-date branch protection enforced for administrators.
Runtime uses merge commits, not administrator bypass, squash/rebase or merge queues.

Only the coordinator publishes and merges. Serialize target integration and
delivery: refresh target, integrate it into the track, run checks on that tree,
push, verify required GitHub checks, and merge the exact checked head.
A target advance needs fresh integration validation. Conflicts, PR/auth/network
failures or invalid results park affected work; independent tracks continue.
Do not replace failed PR delivery with a local merge.

After merge, synchronize the target and verify ancestry and the tested merge
tree before releasing dependents or cleaning up. Mechanical lifecycle moves
alone do not count as delivered while the PR remains unmerged.

Remove only exact clean merged worktrees and branches. Preserve unmerged,
dirty, ignored, unrelated or advanced work. Ambiguous cleanup is a dry-run.
Forced deletion requires explicit authorization for the identified loss.
Automatically remove only declared, initially absent, ignored disposable
directories without tracked files or redirected paths. Keep scratch/cache
output in run-owned temporary space. Abandonment preserves files and releases
reservations; it never satisfies dependencies or claims a merge.

Keep atomic receipts and an OS lock for the Git common directory. An interrupted
writer is not automatically replayed. Reconcile inspected HEAD, process and
result before retrying. Retry resumes a clean checkpoint; reconcile can consume
a completed step-commit result without repeating its worker. Never reset
review/fix counts. Lost merge responses resume verification/cleanup, not reviews.

## Hooks and validation

Hooks are optional advisory notices. They warn, return success and never issue
permission decisions. No registration is supplied. File tools warn on outside
paths/direct Git metadata; shell inspection is best-effort and recognizes
standard stream devices. Missing repository context is quiet. Lexical checks,
shell quoting, symlinks and junctions limit detection; hooks are not a sandbox.

Run the Python integration suite for runtime changes and the Bash regression
suite before and after hook changes. Use real temporary Git fixtures and
simulated forge/model responses for repository tests. Report actual command
results, skips and failures. No test outcome is inferred from a checklist.

## Configuration and onboarding

Configuration owns project values, paths, ID formats, suggested concurrency,
runtime capacity, worker routes and verification commands. Light mode reduces
planning ceremony; standard uses the full record lifecycle; full adds phase
planning and named acceptance checks. Quality and SPEC coverage at delivery
remain the same. Documentation uses its configured lightweight worker route
without a code-model fallback.

Fresh onboarding inspects code before asking questions, then obtains human
intent, mode and actual verification commands. Existing documentation is an
inventory to investigate, not a SPEC source. Propose leave/retire decisions and
obtain authorization before moves/deletions. Documentation agents write
self-contained SPECs only after inspecting/reviewing actual code in relevant
areas. Greenfield projects have no SPEC claims until code exists.

Cluster confirmed bugs into FIX records and other fragments into INTAKE. Show
the clustered adoption inventory before writing it. Capture only human-confirmed
historical decisions. Seed remaining work, initialize current state and add the
AGENTS entry point. A returning session briefs itself without restructuring.

Harvest only relevant meeting areas, oldest first, preserving original text and
recording harvested date/produced IDs. Distinguish decisions already built,
decisions awaiting work, debate, current-behavior claims and intent requests.
Later notes win only when they explicitly revisit the decision; otherwise ask.
Documentation agents record confirmed decisions; unbuilt work becomes INTAKE/PLAN.
