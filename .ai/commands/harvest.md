---
description: Turn a meeting or design document into ADRs, intent changes and intake items
argument-hint: <path to the document, or a directory of them>
---

Harvest: **$ARGUMENTS**

Meeting and design documents are `log` tier — a record of what was said on a
date, never a contract. Harvesting extracts the parts that *are* contracts and
leaves the rest as history. Until a note is harvested, nothing in it is in
effect, no matter how it is phrased.

## 1. Read it, and place it

Read the whole document. If it is not already under
`.ai/decisions/meetings/`, `git mv` it there as
`MEET-YYYY-MM-DD-{slug}.md` and add the frontmatter from
`.ai/templates/MEETING.md` — keep the original text intact below it. Use the
date the meeting happened, not today.

If a directory was given, list what you found and harvest **oldest first**, so
later notes can supersede earlier ones rather than the reverse.

## 2. Sort every claim in it

For each substantive item, decide which of these it is — and when a note mixes
"we decided" with "we should probably", the wording in the room is not
reliable. Ask if you cannot tell.

- **Decided, and reflected in the code already** → an ADR in
  `.ai/decisions/`, `status: accepted`. Say in **Context** which meeting it
  came from.
- **Decided, but not built yet** → an ADR *plus* work in `.ai/plans/intake/`
  or the roadmap. See the trap in step 4 — this is the case that goes wrong.
- **Discussed, not decided** → stays in the note. Fold the options and the
  arguments into the relevant ADR's **Alternatives considered** table, since
  that is exactly what that table wants and meetings are where it comes from.
- **A change to scope, non-goals, constraints or priorities** → `intent` tier.
  Draft the wording, show the user, and **do not edit
  `.ai/intent/PROJECT.md` without their explicit approval.**
- **A statement of current behavior** → check it against the code. If it holds
  and matters, it may become a spec. If it does not hold, it is stale
  discussion, not a requirement — say so.
- **Follow-up work** → an `INTAKE-{nnn}` per real item, clustered.
- **Anything else** → leave it in the note.

## 3. Reconcile against what already exists

Before writing anything:

- Does an ADR already cover this? Then either the note adds alternatives to it,
  or it supersedes it — write a new ADR with the old id in `supersedes:`, then
  set `status: superseded` and `superseded_by:` on the old one and change
  nothing else in it. Never rewrite a past ADR's Context, Decision or
  Alternatives; its value is being an accurate account of what was decided at
  the time. That status flip needs no amendment record — the new ADR is the
  record.
- Do two meetings disagree? Later wins **only** if it explicitly revisits the
  same question; otherwise this is a real ambiguity and a question for the
  user. Do not silently pick the more recent one.
- Does the note contradict a live spec? Follow the amendment protocol in
  `.ai/RULES.md` — with the note as the evidence, not as the authority.
- Does it contradict `.ai/intent/PROJECT.md`? Stop and ask. Intent outranks
  every meeting.

## 4. The trap: decisions that aren't built yet

A meeting decides on a new architecture; the code is still the old one. Record
the decision as an ADR, and **do not write specs asserting the new behavior**.
Specs describe what correct means *now*; a spec describing the target state
makes every verification fail and teaches everyone to ignore the verifier. Do
not annotate the existing specs either — no "superseded by ADR-0012", no "being
replaced". They still describe the software, and that is all they are for.

The migration lives in plans. The ADR says where you are going; the specs say
where you are; the plans get you from one to the other, carrying the new spec
wording in their **Contract changes** section until the code catches up. If you
want the target behavior written down as criteria, that section is where it
goes — drafted, in present tense, ready to land with the code.

Say plainly in your report which decisions are recorded-but-unbuilt, because
that gap is invisible otherwise and it is where the worst surprises live.

## 5. Close the loop

Set `harvested: YYYY-MM-DD` in the note's frontmatter and list every id it
produced in `produced:`. That is what stops the note being mined twice, and
what tells the next reader whether its contents are in effect yet.

Append a journal entry. Add a `.ai/truth-map.md` row if the note introduced a
kind of fact with no owner.

## Report

- Documents harvested, and where they now live
- ADRs written, one line each
- Intent changes **proposed** — flagged clearly as needing the user's approval
- Intake items created
- **Decided but not built** — the gap list
- Contradictions found: between meetings, against specs, against intent
- Anything you could not classify, and the question you need answered

Harvest only the documents covering the area about to be worked on. Mining
years of meeting notes in one pass produces a pile of ADRs nobody has verified,
which is the same problem as retro-specifying a whole codebase.
