---
description: Run one orchestration track through build, two code reviews, documentation, two documentation reviews and delivery.
argument-hint: <run-id> <track-id>
---

Build track **$2** of run **$1**. Read and follow [RULES](../RULES.md).
The coordinator schedules, records, publishes and merges runtime work.
Build/document workers commit each assigned PLAN step; the coordinator commits
correction passes and lifecycle moves. A track never merges another track or
edits shared state.

## Track scope

Read `.ai/config.yaml` and `.ai/RULES.md`. Establish the absolute worktree,
branch, base SHA, run manifest, reserved IDs, owned paths, code paths,
documentation paths, Research-note paths, source-documentation paths and
exclusive resources before dispatching any worker. Check the original PLAN's
Execution contract and human-intent resolutions under RULES.
Never read or write a sibling worktree. Runtime phase attempts and receipts are
durable and authoritative; never infer or reset counts from commit subjects.

## Linear phases

1. **Build.** Fresh research and code implementation run in the assigned
   worktree. It may write an assigned Research note and create new FIX/INTAKE
   records within its reserved ranges. The build worker may write source/tests and
   perform its own source self-review. It must not edit PLAN content, specs,
   ADRs, amendments, documentation, comments/docstrings, STATE, journal,
   receipts or review records. An incomplete or inconclusive build parks.

2. **PR when there is a diff.** For a code diff, the coordinator prepares and
   opens the PR before review. A documentation-only track runs both code
   reviews first and opens its PR only after the documentation batch creates a
   diff. A documentation-only track whose branch still has no net diff from its
   base after the document phase stops with a recorded no-change outcome,
   preserves the checkout, and does not create an empty commit or PR or proceed
   to documentation reviews or delivery. Code-only tracks may already have a
   valid code diff/PR and may continue without documentation edits. PR/push
   failure parks the track.

3. **Code review one.** A fresh `track-reviewer` receives the PLAN, current
   contracts, Research notes, source and filtered diff. It reviews code quality
   and correctness, never documentation quality or prior code-review verdicts.
   It independently verifies the Research notes' claims.

4. **Optional code correction.** If review one has actionable code findings,
   one fresh fixer may correct them in code scope and provide real regression
   proof. Documentation/contract findings become INTAKE and do not return to
   the code fixer. If review one is approved or has zero eligible code fixes,
   continue to review two; never jump to completion.

5. **Code review two (mandatory).** A second fresh cold code reviewer runs
   whenever prior phases are complete and conclusive, including after an
   approved first review or a zero-fix triage. Review count is persisted in
   receipts. A second failure preserves `changes requested`. Use
   [Definition of done](../RULES.md#definition-of-done) to distinguish missing
   code/functionality from unrelated follow-ups. Inconclusive or
   incomplete work parks.

6. **Consolidated documentation.** After code review two, the lightweight
   documentation worker uses `orchestration.documentation.model` (default
   `gpt-5.6-luna`) through the separate `documentation_worker_command`; there
   is no code-model fallback. It lands every original PLAN promise within
   explicit documentation paths, including promised specs, amendments and ADR
   decisions, and returns overall SPEC coverage. It receives Research notes,
   implementation reports, both code reviews and findings. It may update owned
   PLAN delivery notes and assigned source comments/docstrings with verified
   behavior equivalence. It writes no executable behavior, tests, YAML/JSON
   or coordinator records.

7. **Documentation review one.** A fresh
   `track-documentation-reviewer` checks every original promise, including an
   empty documentation scope, links/anchors and documentation claims using
   code only as evidence. It never performs code review. `changes requested`
   permits the single supplied-findings documentation correction; unrelated or
   out-of-scope corrections become INTAKE. Missing original promises are
   assessed under [Definition of done](../RULES.md#definition-of-done);
   editorial details do not make overall SPEC coverage incomplete.

8. **Optional documentation correction.** A fresh documentation worker may
   correct only actionable findings from documentation review one and missing
   original promises. No new decisions, executable behavior changes or unrelated
   cleanup. Assigned comments/docstrings use the source-documentation check.
   Runtime coordinator owns the commit and receipt.

9. **Documentation review two (mandatory).** A second fresh documentation-only
   reviewer runs whenever review one and any correction are complete and
   conclusive, including when review one was approved or had zero findings. It
   reports overall SPEC coverage through `documentation_complete`, using
   RULES to distinguish substantive gaps from editorial findings. No
   third documentation review, scribe refresh or late content edit occurs.

10. **Final checks and delivery.** The coordinator audits the final integrated
    head, required commands, owned paths, PR state, review SHAs, phase receipts,
    and implementation/SPEC completeness. It validates the whole closing set,
    then moves completed PLAN and evidenced resolved INTAKE records to done.
    It writes terminal state and pushes a ready
    or ready-with-followups result. Failed checks, missing evidence, dirty
    read-only phases, PR failure or unresolved human decisions park the track.

Both review ceilings are exactly two: code `max_rounds: 2` and documentation
`max_review_rounds: 2`. At most one correction occurs between each pair. Resume
reconciles process, result, Git state and receipts without resetting counts.
Only coordinator-generated evidence and lifecycle moves may follow the final
review. The coordinator owns shared STATE, journal, PLAN moves, FIX/INTAKE
record updates, receipts, correction/lifecycle commits and publication in runtime mode.

The terminal report names the state, plans built, review verdicts, promises
landed, IDs used, checks and actual failures. Never report an approval for an
inconclusive phase or call residual findings approved.
