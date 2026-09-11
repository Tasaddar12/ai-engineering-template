<!--
Append this to the project's root AGENTS.md. Do not replace an existing
AGENTS.md with it.

This snippet is the single most important piece of wiring in the template. An
agent that never reads .ai/RULES.md falls straight back to the default
behavior the structure exists to prevent: refusing to touch documentation, or
bending code around a stale spec. Everything below is deliberately short so it
survives in a crowded AGENTS.md.
-->

## Working in this repository

Project intent, specs, plans, and state live in [`.ai/`](.ai/). Read
and follow [`.ai/RULES.md`](.ai/RULES.md) for shared rules, your
[agent file](.ai/agents/README.md) for agent-specific instructions, and
[`.ai/state/STATE.md`](.ai/state/STATE.md) to see where things stand.

**Documents here are versioned, not sacred.** When a spec, plan, or doc
contradicts reality:

1. Work out which side is wrong — a bug in the code does not license amending
   the spec to match the bug.
2. If the document is wrong, pass the evidence to the documentation agent.
   After code review, it corrects the document and records why in an amendment
   under `.ai/decisions/amendments/` for SPEC/ADR changes.
3. Continue the work.

**Never** contort an implementation so a stale requirement is technically
satisfied, and never refuse a change because a document describes the old
behavior. Silent workarounds are the only forbidden move.

**Each document has one tense.** A spec says what *is*. An ADR says why we
chose something and what it replaced. A plan says what we intend next. Use
[RULES](.ai/RULES.md#what-each-document-is-for) when choosing the record.

So a spec carries **no history and no intentions** — never "deprecated",
"removed in v2", "no longer applies", "was previously", "not yet implemented",
`TODO`, or strikethrough. When a requirement changes, rewrite the line to state
the new one. When it goes away, delete it — the criterion, the section, or the
file. The amendment record holds what it said and why it moved, the ADR holds
why the decision changed, and git holds every version. Behavior that is decided
but unbuilt lives in the plan that will build it. Every PLAN records whether it
requests changes to human intent. Put each
request and the human resolution in its Execution contract, following
[Intent and PLAN approval](.ai/RULES.md#intent-and-plan-approval), before
implementation. Draft future non-intent contract wording in the PLAN. Existing
specs govern unchanged behavior; specs become truthful for the
merged/deliverable revision in the documentation batch, not at every
intermediate code commit.

Where to find each kind of change and its governing rule:

| Path | Tier | Change procedure |
|---|---|---|
| `.ai/state/PROJECT.md` | `intent` | Record the human decision under [intent approval](.ai/RULES.md#intent-and-plan-approval) |
| `.ai/specs/**`, `.ai/decisions/**` | `contract` | Documentation agent applies the [amendment protocol](.ai/RULES.md#the-amendment-protocol) |
| `.ai/plans/**`, `.ai/fixes/**` | `plan` | Use the selected [agent's scope](.ai/agents/README.md) and lifecycle command |
| `.ai/state/STATE.md` | `status` | Coordinator records the current work |
| `.ai/state/journal/**`, `.ai/decisions/amendments/**` | `log` | Append only |
| `.ai/decisions/meetings/**` | `log` | Append only — **never a requirement** |

**Plans move the contract with them.** A plan declares up front, under
**Contract changes**, which specs it creates, amends or retires — with the
wording drafted — and which ADR it needs, cites or supersedes. Use that section
during the code-to-documentation handoff. PLAN-Done then
validates the completed implementation and overall SPEC coverage under
[Definition of done](.ai/RULES.md#definition-of-done). Superseding an ADR means a
new ADR naming the old one, plus `status: superseded` on the old one; only `status: accepted` is
authority.

**A single defect is a fix, not a plan.** A fix restores conformance with the
contract; a plan changes what conformance means. Run `/fix` — it records the
symptom, cause, change and the check that fails before and passes after, in
`.ai/fixes/`. No regression test, no fix.

**Meeting notes and design docs are not contracts.** They record what was said
on a date, where a rejected option reads exactly like a chosen one, and a
decision to rebuild something reads exactly like a description of what exists.
Never implement from one. Decisions become real in `.ai/decisions/`, scope
changes in `.ai/state/PROJECT.md` — until then, raise the gap rather than acting on it.
`/harvest` converts notes into contracts.

A plan's or fix's stage is the directory it sits in — move it with `git mv`,
and never add a `status:` field. Every fact has exactly one owning document; see
[`.ai/truth-map.md`](.ai/truth-map.md). Link to facts, never restate them.

**Found a problem that isn't this task?** Don't fix it, and don't just mention
it — a finding that lives only in a session summary is lost. Capture it with
`/defer`: confirmed code bugs go to `.ai/fixes/open/` as FIX items; documentation
and contract corrections get separate INTAKE items in `.ai/plans/intake/`.
Autonomous review follows [RULES](.ai/RULES.md#autonomous-review-and-fix):
the review sequence, retained findings and incomplete-work handling.

Run `/plan-status` to see where the project stands, `/onboard` to get briefed.
Commit each PLAN step using
[PLAN records and commits](.ai/RULES.md#plan-records-and-commits).
Pass implementation reports, Research notes and review evidence to the
documentation agent for SPEC/ADR/AMD/PLAN updates after code review.
