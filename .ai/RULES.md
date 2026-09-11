---
tier: intent
authority: human
id: RULES
title: Rules of engagement for AI agents
---

# Rules of Engagement

Every agent working in this repository reads this file before touching anything
else. It defines what may change, who may change it, and — most importantly —
what to do when the written record and reality disagree.

---

## The Prime Rule

**Every PLAN, including a draft or unapproved PLAN, always has authority to
define and require changes to any SPEC, ADR, AMD, amendment, or other project
document within its declared target.** A conflict, whether enumerated in the
PLAN or discovered later as a consequence of its target, never blocks creating,
refining, reviewing, approving, or implementing a PLAN on that ground. Preserve
behavior outside the PLAN's declared target.

Documents here are versioned, not sacred. When you find that a spec, plan, or
doc is wrong, stale, incomplete, or incompatible with the change you are
making:

1. **Preserve the PLAN's declared target wording.** During the working branch,
   the current spec may intentionally lag that target until the final
   documentation batch.
2. **The documentor fixes and records every document transition required by
   the PLAN's target, including consequences discovered later, after
   code review two**, in the same PR. This is a delivery obligation, not a
   precondition to implementation.
3. **Continue the work without a silent workaround.** Preserve the PLAN's
   original outcome and continue independent work while the documentation
   transition is recorded.

Three specific failures this rule exists to prevent:

- **Silent workaround.** Contorting an implementation so a stale requirement is
  technically satisfied. This is how bugs get manufactured. If a requirement is
  wrong, it is wrong — say so and change it.
- **Refusal.** Declining to make a change because a document describes the old
  behavior. Check the tier table below: nearly everything here is yours to
  amend. A document describing the past is not an instruction to preserve it.
- **Divergence.** Changing the code and leaving the document behind. The next
  agent inherits a contradiction and no way to tell which side is true.

If you are unsure whether a document is stale or you are wrong, **the answer is
never to guess quietly.** State the contradiction plainly, preserve the PLAN's
target, and record the document transition. Ask only when a new intent outside
the target or an explicit later human instruction requires a decision; a
document conflict does not create repeat approval.

### PLAN authority and the critical-functionality exception

The PLAN's authority over its target documents is unconditional. A draft or
otherwise unapproved PLAN does not itself authorize execution, launch work, or
external action; lifecycle scheduling and permission to execute remain separate
from whether the PLAN can define its target contracts. A later direct human
instruction that explicitly changes or cancels the work governs that scope; a
document conflict does not create another approval loop.

The only reason to prevent an implementation step once work is authorized to
execute is concrete evidence that the PLAN itself would break critical project
functionality. Examples include data loss, a security failure, unrecoverable
corruption, an inability to build or start, or loss of a core user-visible
capability. A stale, contradictory, incomplete, or otherwise mismatched
document is not critical breakage.

When a PLAN step is unsafe on that evidence, do not abandon the PLAN or change
its intended outcome. Scope one or more supporting PLANs under a new or
existing ORCH, order them by dependency, and implement those supporting PLANs
before the unsafe step. Record the evidence and dependency in the ORCH; keep
unrelated work moving. Required verification, review, and delivery conditions
still apply to every PLAN.

---

## What each document is for

Three document types carry almost all the weight, and keeping them apart is
what stops the record from becoming an archaeology exercise.

| Document | Tense | Holds |
|---|---|---|
| `specs/SPEC-*.md` | **present** | What correct behavior *is*, right now |
| `decisions/ADR-*.md` | past | Why we chose this, and what it replaced |
| `plans/**/PLAN-*.md` | future | What we intend to build next |

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

Every file under `.ai/` declares a tier in its frontmatter. The tier tells you
what you may do without asking.

| Tier | What it holds | Examples | You may |
|---|---|---|---|
| `intent` | Why this project exists; hard constraints; non-goals | `state/PROJECT.md`, this file | Human authority. Stop and ask before changing intent outside a PLAN target. Every PLAN authorizes the necessary document transitions within its declared target; only the critical-functionality exception above can prevent implementation. |
| `contract` | What "correct" means right now | `specs/SPEC-*.md`, `decisions/ADR-*.md` | **Amend freely, with a recorded amendment.** See protocol below. |
| `plan` | How we intend to get there | `plans/**/PLAN-*.md`, `fixes/**/FIX-*.md` | **Rewrite freely.** Plans are disposable. |
| `status` | Where things stand | `state/STATE.md` | **Overwrite freely.** Expected to churn every session. |
| `log` | What happened | `state/journal/*.md`, `decisions/amendments/*.md` | **Append only.** Never edit or delete past entries. |

Frontmatter on every `.ai/` document:

```yaml
---
tier: contract          # intent | contract | plan | status | log
authority: agent        # human | agent  — who has final say
id: SPEC-004
title: Short human-readable title
links: [ADR-0002, PLAN-011]
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

---

## The amendment protocol

Use this whenever you change a `contract`-tier file: a spec, or an ADR.

1. Write the amendment record first: copy `templates/AMENDMENT.md` to
   `decisions/amendments/AMD-<nnn>-<slug>.md`. It captures four things — what
   the document said, what is actually true, why they diverged, and what you
   changed it to.
2. Rewrite the spec so it states the new truth and nothing else — replace the
   wording, never annotate it, and delete the criterion outright if the
   requirement is gone. On an ADR, correct a factual error only; changing the
   decision is a new ADR, not an edit.
3. Add the amendment id to the affected document's `links:`.
4. Include both files in the documentation commit in the same PR as the code
   change. Implementation and documentation commits may be separate while the
   track is under review.

The record exists so a human can audit *why* the contract moved, not to slow
you down. It is three sentences, not an essay. **An amendment is never a
failure**; it is the system working. A project whose specs never get amended is
a project whose specs are being ignored.

For a PLAN, this protocol records the transition after code review two and does
not block implementation. The PLAN's declared target remains the authority
while the working branch is in flight.

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

If the specs, ADRs and intent already describe the behavior you want and the
code simply does not do it, that is a fix. Nothing in `contract` tier moves, so
there is no spec to amend, no ADR to write, and no reason to spend the whole
plan lifecycle on it.

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
  INTAKE. If an existing acceptance criterion establishes a code defect, record
  that separately as a FIX; otherwise do not invent correctness in a fix.
- **The spec or documentation is wrong.** Capture an INTAKE for the correction.
  It becomes planned documentation/contract work later, not a code FIX.
- **The fix needs an ADR, a spec rewrite, or more than a handful of files.**
  Promote it with `/plan-new` and link the fix record from the plan. A fix that
  grows into a plan is normal and expected; a plan disguised as a fix skips the
  checker and the verifier, which is the failure this route can produce.

Do not use a fix to sneak a behavior change past review, and do not open a plan
for a one-line defect the specs already condemn. Both waste the distinction.

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

Decisions become real by landing in `decisions/ADR-*.md`. Constraints and scope
changes become real by landing in `state/PROJECT.md`, which takes a human.
Until then, an agent that finds a note describing something that ought to be
true should **raise the gap, not act on it**.

Turning notes into contracts is what [`/harvest`](../.ai/commands/harvest.md)
does. A note carries `harvested:` in its frontmatter so you can tell whether
its contents are in effect yet.

## Precedence when documents disagree

Reality first, then the declared target contract, then human intent for
behavior the PLAN does not change:

1. **Working, tested code** is evidence of present behavior, not a veto over a
   PLAN's declared future target. Documents follow reality for behavior already
   delivered — but only after you have *confirmed* the code is right; a bug in
   the code does not license amending the spec to match the bug. Existing code
   cannot veto a PLAN's target.
2. **A PLAN's Contract changes section governs its explicitly
   declared target changes, even when it conflicts with any existing spec, ADR,
   amendment, or other document.** A PLAN may always require a change to any
   contract. Its exact future wording remains in the PLAN until implementation
   and the documentation batch land; the conflict is recorded as a document
   transition after code review two and is never an implementation veto.
3. **`state/PROJECT.md`** and the more recent accepted `contract` govern
   behavior and constraints the PLAN does not change. Check
   amendment and ADR history before assuming a spec is current.
4. **A meeting note beats nothing.** It is evidence, and it loses to every
   tier above it. A note that contradicts a spec means someone needs to
   harvest it, not that the spec is wrong.

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

## Definition of done

A task is done when **the software satisfies the PLAN's intended outcome**
and the updated specs truthfully describe the delivered behavior.

Verification checks observed behavior against the PLAN's target and the
truthful updated specs. Never weaken or rewrite the PLAN's target to excuse
missing or incorrect implementation. If implementation is incomplete or
incorrect, fix it or use the critical-functionality procedure above; preserve
the target.

Before calling anything done:

- The specs it touches describe what the code now actually does — in present
  tense, with no annotation about what they used to say.
- Everything the plan listed under **Contract changes** has landed: specs
  written or amended, ADRs written, superseded ADRs marked.
- Any contract change has an amendment record.
- A fix has a check that fails before it and passes after.
- `state/STATE.md` reflects the new present.
- A journal entry exists for the session.

These are required verification and delivery conditions for completion. They
are not preconditions to implementing a PLAN, and a document
mismatch by itself is never evidence of critical breakage.

---

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

Outside autonomous review, two things are **always in scope** and get fixed
rather than captured, because leaving them is what corrupts everyone's future
work. A PLAN's promised contract/documentation changes are the explicit
exception: preserve them until the final documentation batch:

- a document that contradicts reality → amend it, with a record
- the same fact restated in two documents → collapse it into a link

### Autonomous review and fix

The autonomous review workflow takes precedence over the incidental amendment
and always-in-scope rules above. The original PLAN's promised documentation
and contracts still land with its implementation. Document and contract
transitions necessary to the PLAN's target, including consequences
discovered in review, remain in that PLAN's final documentation batch. Only
unrelated or independently proposed documentation and contract review findings
become separate INTAKE items for later; do not expand the review fix pass to
edit documentation.

Run at most **two reviews**, with one immediate code-fix pass after the first.
At the second failure, or for other residual defects, retain code FIX reports
and documentation/contract INTAKE reports for after all other PLANs complete.
No third review, repeated permission request or severity downgrade ends the
loop. Preserve the actual verdict and proof. A track with findings may be
`ready_with_followups` when required checks pass; it is not an approved review.
Required check failures, incomplete work and `cannot_review` park that track
while independent PLANs continue. Completed work runs exactly two cold code
reviews and exactly two cold documentation reviews. At most one code correction
occurs between code reviews, and at most one documentation correction occurs
between documentation reviews. Resume does not reset counts, and no scribe or
verifier review follows documentation review two. See [the runtime](runtime/README.md)
for enforced delivery conditions and post-PLAN queue handoff.

And if what you found is severe — data loss, a security hole, a broken build —
capture it *and* say so plainly. Filing an urgent problem is not the same as
handling it; say which one you did.

## When you are genuinely blocked

Blocked means only that a genuinely missing human decision is required and was
not supplied by the PLAN. A conflict with an existing intent or
other document is not such a question. An explicit later human instruction or
cancellation is honored as given and does not create supporting PLANs to evade
it. Concrete evidence of critical breakage follows the supporting-PLAN/ORCH
procedure above and is not an automatic human-decision wait.

When a genuinely missing human decision blocks the work:

1. Move the plan to `plans/blocked/`.
2. Add a `## Blocked` section to it: the question, the options you see, and
   your recommendation.
3. Record it under blockers in `state/STATE.md`.
4. **Do every part of the task that does not depend on the answer**, then
   report what you finished and what is waiting.

Do not sit idle on a missing decision: do every independent part of the task
and report what is waiting. Do not silently pick an answer to an unresolved
intent-tier question or override an explicit later human instruction.
