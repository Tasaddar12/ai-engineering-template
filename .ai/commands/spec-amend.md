---
description: Correct a spec or ADR that turns out to be wrong, with a recorded amendment
argument-hint: <spec-id> <what's wrong with it>
---

Arguments: **$ARGUMENTS** — the first token is the spec or ADR id; everything
after it describes what is wrong with it. If no id was given, work out which
document is at fault and confirm it before amending.

This is the mechanism that keeps stale documents from forcing bad code. Using
it is normal and expected — a project whose specs are never amended is a
project whose specs are being ignored.

1. **Read the document** and establish which side is actually wrong.
   - Is the document stale, or is the code buggy? **A bug in the code does not
     license amending the spec to match the bug.** If the code is wrong, stop
     here and run `/fix` instead — that is the route for code that fails to do
     what the record already says it should.
   - Does the correction violate anything in `.ai/state/PROJECT.md`? Hard
     constraints and non-goals outrank any spec. If it does, this is a blocker
     for a human, not an amendment.
2. **Write the record first.** Copy `.ai/templates/AMENDMENT.md` to
   `.ai/decisions/amendments/AMD-{nnn}-{slug}.md`, numbering after the highest
   existing. Fill in all four sections: what the document said, what is
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
4. **Add the amendment id** to the document's `links:` frontmatter.
5. **Follow the change downstream.** Other specs, plans, docs, or tests that
   depended on the old wording. Check `.ai/truth-map.md` — if the same fact was
   restated elsewhere, collapse the copies into links now.
6. **Commit together** with the related code change, if there is one. One
   commit, one coherent story.
7. Append a journal entry, and clear the matching line from **Known drift** in
   `.ai/state/STATE.md` if there is one.

Report: the amendment id, what moved, and what else you had to update. Three
sentences per section in the record is plenty — it exists so a human can audit
why the contract moved, not to slow you down.
