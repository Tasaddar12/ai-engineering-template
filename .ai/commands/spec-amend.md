---
description: Correct a spec or ADR that turns out to be wrong, with a recorded amendment
argument-hint: <spec-id> <what's wrong with it>
---

Arguments: **$ARGUMENTS** — the first token is the spec or ADR id; everything
after it describes what is wrong with it. If no id was given, work out which
document is at fault and confirm it before amending.

Read and follow [RULES](../RULES.md). Assign this procedure to a documentation
agent after the code-review handoff.

The documentation agent works in an assigned worktree and completes the reviewed
PR lifecycle; use [worktree lifecycle](worktree.md).

This is the mechanism that keeps stale documents from forcing bad code. Using
it is normal and expected — a project whose specs are never amended is a
project whose specs are being ignored.

1. **Read the document** and establish which side is actually wrong.
   - Is the document stale, or is the code buggy? **A bug in the code does not
     license amending the spec to match the bug.** If the code is wrong, stop
     here and run `/fix` instead — that is the route for code that fails to do
     what the record already says it should.
   - Does the correction request a change to human intent? Check the PLAN's
     recorded human resolutions under
     [Intent and PLAN approval](../RULES.md#intent-and-plan-approval).
     Investigate and report any unresolved request before implementation.
2. **Write the record first.** Copy `.ai/templates/AMENDMENT.md` to
   `.ai/decisions/amendments/AMD-{nnn}-{slug}.md`, using a coordinator-issued
   AMD id block. Fill in all four sections: what the document said, what is
   actually true, why they diverged, what you changed it to.
3. **Rewrite the document so it states the new truth — and only that.**
   - **Replace the wording; never annotate it.** Do not add "was previously",
     "deprecated", "no longer applies", "removed in v2", strikethrough, or a
     commented-out copy of the old criterion. You just wrote the amendment
     record; that is what carries the history, and duplicating it into the spec
     gives the same fact two owners. A spec has to read as a true statement
     about the software today, with nothing else in it.
   - **If the requirement is gone, delete it** — the criterion, the section, or
     the whole spec file. A spec that governs nothing will be read as a
     requirement by the next agent. Deleting loses nothing: the record you just
     wrote says what it said and why it went, and git has every version.
   - **Keep it in the shape that survives** — acceptance criteria and
     invariants, not implementation detail. If the original was falsified by a
     refactor because it named a file or a constant, reword it so the next
     refactor does not falsify it again.
   - **On an ADR, do not rewrite the reasoning.** An ADR is a dated record and
     is allowed to be about the past. Correcting a factual error in it is an
     amendment; changing the decision is a *new* ADR that names this one in
     `supersedes:`, plus `status: superseded` and `superseded_by:` here. That
     status flip needs no amendment record — the new ADR is the record.
4. **Link the affected document from the AMD.** For an ADR, add the amendment
   ID to its links. A SPEC may retain or add optional traceability links in
   frontmatter, while its body stays self-contained and independent of records.
5. **Follow the change downstream.** Other specs, plans, docs, or tests that
   depended on the old wording. Check `.ai/truth-map.md` — if the same fact was
   restated elsewhere, collapse the copies into links now.
6. Land the spec, amendment and any related ADR in the final documentation
   batch after the applicable readiness or implementation handoff. Full tracks
   use the same code PR; standalone documentation tracks use their own reviewed
   documentation PR with merge, synchronization and cleanup. Commit each
   assigned PLAN documentation step under [PLAN records and commits](../RULES.md#plan-records-and-commits).
7. Append a journal entry, and clear the matching line from **Known drift** in
   `.ai/state/STATE.md` if there is one.

Report: the amendment id, what moved, and what else you had to update. Three
sentences per section in the record is plenty — it exists so a human can audit
why the contract moved, not to slow you down.
