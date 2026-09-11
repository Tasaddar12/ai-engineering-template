# Onboarding starter prompts

Paste-ready prompts for the first message of a fresh agent session in the
adoption worktree (see [onboard](../.ai/commands/onboard.md)). Each names an
adoption scope so `/onboard-pr --scope full|rules-only|issue-sweep|docs-reconciliation`
applies the named procedure. Full adoption requires filled intent,
configuration and structure; narrow scopes check their own content plus
required repository verification and do not claim those gates.

If you are not sure, use **B**. If agents on this project are already refusing
to edit docs or bending code around stale specs, run **A** first — it finds the
cause, and the cause is often something the copy alone will not fix.

| | Prompt | Use when |
|---|---|---|
| A | [Diagnose first](#a--diagnose-first) | Agents are already misbehaving and you want to know why |
| B | [Full adoption](#b--full-adoption-in-flight-project) | Default. Real project, work in progress |
| C | [Greenfield](#c--greenfield) | New or nearly-empty repo |
| D | [Light mode](#d--light-mode) | Small or short-lived project |
| E | [Rules only](#e--rules-only-no-specs-no-plans) | You only want the refuse/contort behavior fixed |
| F | [Issue sweep](#f--issue-sweep-only) | You mainly want deferred work captured |
| G | [Docs reconciliation](#g--docs-reconciliation-only) | Lots of existing docs, contradicting each other |
| H | [Brief me](#h--brief-me-on-an-existing-setup) | `.ai/` is already set up; resuming |
| I | [Harvest meeting notes](#i--harvest-meeting-and-design-notes) | Piles of architecture/design meeting docs |

Each prompt assumes the template files are already copied and committed. None of
them should be run in your main checkout.

---

## A — Diagnose first

Finds out why agents behave the way they do before changing anything. Worth ten
minutes even if you are certain you want the full structure, because the answer
is frequently a two-line fix that has nothing to do with the template.

```
Before we adopt anything, diagnose why AI agents on this repo refuse to edit
documentation and specs, and why they tend to contort code to satisfy stale
requirements instead of correcting them.

Read .ai/RULES.md first so you know what the target state is. Then audit,
without changing anything:

1. Every agent definition in .ai/agents/ — do its tools match its intended
   scope? Compare documentation writers with read-only reviewers and code agents.
2. AGENTS.md, and any instruction file — quote every line that
   forbids or discourages changing documentation, specs, plans or requirements.
3. The host's hook settings — anything that blocks writes to md files or
   doc directories, and whether its denial message names what IS allowed.
4. Requirements that appear in more than one place. For the top few, list every
   file that states them. This is the cause I most expect to find.
5. Specs or docs that dictate implementation (a file, function or constant),
   so any refactor falsifies them.
6. Requirement documents layered with history and aspiration — "deprecated",
   "removed in v2", "not yet implemented", struck-through paragraphs, embedded
   changelogs. Quote them. An agent has to work out which sentences are still
   in force before it can start, and it sometimes gets that wrong.
7. Instructions anywhere that tell agents to preserve requirement history in
   place rather than deleting it. Those read as prudence and cause #6.

Report findings ranked by how likely each is to be the actual cause, with the
specific fix for each. Do not edit anything yet.
```

---

## B — Full adoption, in-flight project

The default. Expect a real conversation: it will interview you for intent and
ask for a decision on every requirement-bearing document it finds.

```
This worktree has just had the .ai/ orchestration structure
copied in. Onboard this project onto it.

Run /onboard and work through every step, including the retrofit steps —
adopting existing requirement documents rather than duplicating them, auditing
AGENTS.md and the existing agents for language that contradicts .ai/RULES.md,
classifying known problems into FIX/INTAKE, and capturing architectural
decisions that were made but never written down.

Read the repo thoroughly before you ask me anything, so your questions are
informed ones. Then:

- Interview me for .ai/state/PROJECT.md. Push hard on non-goals and hard
  constraints; do not fill them in by guessing.
- Show me the leave/retire recommendation and code areas to inspect for each doc and
  wait for my call before moving or deleting anything.
- Cluster the TODO/FIXME sweep by theme and show the list first. Apply RULES
  to distinguish confirmed code bugs (FIX) from unknowns and fragments (INTAKE).
- Review actual code in the areas we are about to work on, then hand the
  evidence to a documentation agent for self-contained SPECs under RULES.
  Keep the existing-doc inventory separate from evidence for SPEC claims.

Stop and ask whenever a judgment is mine to make. Prepare approved changes in
the assigned worktree and use `/onboard-pr` for the reviewed commit and delivery.
```

---

## C — Greenfield

For a new or nearly-empty repo. Skips the reconciliation work, spends the time
on intent instead.

```
This is a new project with the .ai/ structure just copied in.
Onboard it.

Run /onboard. There is little or no existing code, so skip the document
adoption and issue sweep, and spend the effort on:

- .ai/state/PROJECT.md — interview me properly. Ask about non-goals and hard
  constraints until they are specific enough to reject a plan.
- .ai/config.yaml — recommend a mode and say why. Fill in project name, summary
  and the real test/lint commands under verification.commands.
- Acceptance criteria in the first PLAN for what we are about to build;
  the documentor will derive SPECs from actual code after code review.
- A first plan in .ai/plans/backlog/, checked by plan-checker.

Then append .ai/templates/AGENTS.snippet.md to AGENTS.md, creating it if
absent. Prepare approved changes in the assigned worktree and use `/onboard-pr`
for the reviewed commit and delivery.
```

---

## D — Light mode

Small or short-lived work with compact planning and documentation.

```
Onboard this project onto the .ai/ structure in light mode.

Set mode: light in .ai/config.yaml, along with project name, summary, and the
real verification commands. Use RULES for light-mode planning and the
post-code-review documentation requirements.

Keep it minimal:
- Fill .ai/state/PROJECT.md from a short interview. Non-goals and hard
  constraints still matter; the rest can be brief.
- One plan in .ai/plans/active/ for the work in hand.
- Sweep obvious TODO/FIXME and known-broken things into a classified FIX/INTAKE
  inventory, clustered and shown to me before writing records.
- Append .ai/templates/AGENTS.snippet.md to AGENTS.md.

Skip the roadmap, skip retro-specs, skip anything the mode does not require.
Tell me if you think light mode is the wrong call for this repo. Prepare the
approved configuration in the assigned worktree and use `/onboard-pr` for
reviewed delivery.
```

---

## E — Rules only, no specs, no plans

For when you want the refuse/contort behavior fixed and nothing else. Leaves
`specs/`, `plans/` and the lifecycle unused until you want them.

```
Use `/onboard-pr --scope rules-only`. I want the document-mutability rules in effect, and
nothing else yet.

1. Append .ai/templates/AGENTS.snippet.md to AGENTS.md (create it if absent).
2. Audit AGENTS.md and .ai/agents/ for anything that now contradicts
   .ai/RULES.md and the role's intended scope — especially documentation-writer
   tools, read-only reviewers and code/documentation ownership. Show me each one with the proposed edit.
3. Fill in .ai/config.yaml: project name, summary, mode: light, and the real
   verification commands.
4. Leave .ai/specs/ and .ai/plans/ alone entirely.

Then tell me, in a few lines, what changes about how agents will behave on this
repo and what does not. Run the repository's required verification commands and
prepare approved records in the assigned worktree. Use `/onboard-pr --scope
rules-only` for reviewed delivery; required CI still gates delivery.
```

---

## F — Issue sweep only

When the thing you actually want is every deferred and current problem written
down where an agent will find it.

```
Use `/onboard-pr --scope issue-sweep` after capturing the project's known
problems in FIX/INTAKE records under .ai/RULES.md,
without adopting the rest of the structure yet.

Sweep for:
- TODO, FIXME, HACK, XXX comments in source
- skipped, commented-out, or currently failing tests — run the test suite and
  report what actually fails
- anything the README or docs describe as temporary, known broken, or "for now"
- commented-out code blocks that look like deferred work
- dependencies pinned with a note explaining why

Then ask me for the open tickets and bugs you cannot see.

Cluster by theme and severity before writing any files, and show me the list
first — I want a readable pile, not one file per TODO. Write one
record per confirmed root cause or meaningful fragment using the FIX/INTAKE
templates and RULES classification, and for trivia
that will never be scheduled, say so and write nothing.

Report which confirmed code bugs are ready for /fix and which INTAKE fragments
need investigation or /plan-new.

Finish with two lists — the three items most worth a plan, and the ones that
are same-day /fix candidates — and why. Do not fix anything; run required
repository checks, capture approved records in the assigned worktree and use
`/onboard-pr --scope issue-sweep` for reviewed delivery. Required CI still
gates delivery.
```

---

## G — Docs reconciliation only

For a project carrying a lot of documentation that disagrees with itself or
with the code.

```
Use `/onboard-pr --scope docs-reconciliation` to reconcile this project's
existing documentation against .ai/truth-map.md,
without adopting the rest of the structure yet.

1. Inventory every document that states a requirement, threshold, limit, or
   business rule — README, docs/, design notes, AGENTS.md, docstrings.
2. Build the ownership table: for each fact, which document should own it, and
   which files currently restate it. Duplicated facts are what force agents to
   contort code, so this table is the deliverable.
3. Flag every place a document contradicts the code as it is now, and say which
   side you believe is wrong and how you established it.
4. For each document, recommend leave in docs / retire and identify code areas
   for review. A documentation agent derives any SPEC from that reviewed code,
   following RULES; existing documents are not SPEC sources.

Show me all of that before changing a single file. Then make only the changes I
approve, collapsing duplicates into links to the owning document. Run required
repository checks, prepare these approved edits in the assigned worktree and
use `/onboard-pr --scope docs-reconciliation` for reviewed delivery. Required
CI still gates delivery.
```

---

## H — Brief me on an existing setup

For resuming on a project already onboarded, or picking up an adoption someone
else started.

```
Run /onboard. This project already has .ai/ set up, so brief me rather than
restructuring anything.

Read RULES.md, truth-map.md, config.yaml, state/PROJECT.md, STATE.md and the
latest journal entry, then the specs and the plans in active/, review/ and
blocked/, then skim intake/.

Report: what this project is, where it stands, what is next, what is blocked
and on whom, and anything in intake/ that looks urgent or overlaps active work.

Spot-check two or three spec criteria against the actual code and tell me
whether the record is still true. Capture anything you find that you are not
about to fix with /defer. Do not start implementing.
```

---

## I — Harvest meeting and design notes

For a project carrying months of architecture and design meeting documents.
Run it **after** B or G, on one area at a time — not across the whole pile.

```
We have a lot of meeting and design documents from sessions about large
architecture and design changes. Inventory them and harvest the ones covering
<area>.

First, without changing anything: find every meeting note, design doc, and
architecture write-up in this repo. List them with date, subject, and your read
on whether it looks decided, exploratory, or superseded by a later one.

Then, for the <area> ones only, run /harvest. Remember these are log tier —
what was said on a date, never a requirement — so:

- Separate "decided" from "discussed but not decided" and tell me when the
  wording doesn't make that clear rather than guessing. A rejected option reads
  exactly like a chosen one in prose.
- Write ADRs only for real decisions, with the rejected options in the
  Alternatives table.
- Flag scope, non-goal and constraint changes for my approval — do not edit
  .ai/state/PROJECT.md yourself.
- Do NOT write specs for architecture we decided on but have not built. Specs
  describe what is correct now; the migration goes in plans.
- Give me an explicit "decided but not built" list at the end. That gap is
  what I most need to see.
- Where two meetings disagree and neither explicitly revisits the other, ask
  me instead of taking the more recent one.

Move all of them under .ai/decisions/meetings/ with proper frontmatter, and
leave the out-of-area ones marked unharvested. Prepare moves in the assigned
worktree and use `/onboard-pr` for reviewed delivery.
```

## Writing your own

The prompts above are long on purpose. Four things earn their length:

- **Name the steps you want.** `/onboard` does a lot; saying which parts matter
  keeps the session focused on the ones you care about.
- **Say where to stop and ask.** Onboarding makes decisions that are yours —
  intent, what to retire, what to retro-spec. An agent told to ask will.
- **Demand the list before the files.** "Show me the clustered list first" is
  what stands between you and forty unreviewable intake files.
- **Use `/onboard-pr`.** It is the deliberate reviewed step that lands onboarding
  changes from the assigned worktree.
