---
tier: contract
authority: human
id: TRUTH-MAP
title: Which file owns which fact
---

# Truth Map

Every fact in this project has **exactly one owner**. Other documents may link
to it. Explanations and examples link to their governing owner; they do not
introduce a competing requirement or an independent copy to maintain.

Duplicated facts are the single largest cause of AI agents producing bad work.
When the same requirement appears in four files, no change can satisfy all
four, so the agent either refuses or contorts the implementation until every
copy is technically satisfied. Neither is what you wanted.

## Ownership

| Fact | Owned by | Everyone else |
|---|---|---|
| Why this project exists; non-goals | `state/PROJECT.md` | Link to it |
| Hard constraints (compliance, budget, platform) | `state/PROJECT.md` | Link to it |
| What "correct behavior" means **now** | `specs/SPEC-*.md` | Link by spec id |
| Behavior we intend but have not built | the **Contract changes** section of the plan that will build it | Never a spec |
| Why we chose an approach | `decisions/ADR-*.md` | Link by ADR id |
| What a superseded decision was | the **superseded** ADR, left intact | Never rewrite it |
| What was *said* in a meeting | `decisions/meetings/MEET-*.md` | Link — never treat as a requirement |
| Why a contract changed, and what it said before | `decisions/amendments/AMD-*.md` | Link by AMD id — **never annotate the spec** |
| How we plan to build something | `plans/**/PLAN-*.md` | Link by plan id |
| A defect, its root cause, and the check that catches it | `fixes/**/FIX-*.md` | Link by fix id |
| What stage a plan or fix is at | **its directory** | Never restate |
| Why a multi-plan run was sequenced that way | `state/orchestration/ORCH-*.md` | Link by run id |
| What one agent found out about the code before building | `state/orchestration/<run>/<track>/RESEARCH-*.md` | Link — never a requirement |
| What each review round of a track found | `state/orchestration/<run>/<track>/REVIEW-LOG.md` | Link by round — the reviewer never reads it |
| What is happening right now | `state/STATE.md` | Link to it |
| What happened on a given day | `state/journal/YYYY-MM-DD.md` | Link to it |
| How the code actually works | **the code** | Describe, never duplicate |
| How to use the product | `docs/` | Link to it |
| Which instructions to read first | `AGENTS.md` at repo root | Link to it |
| Mutability and amendment protocols | `RULES.md` | Link to the relevant section |
| User action/publication authority | root `AGENTS.md` and the user's instruction | Record the actual grant in the selected PLAN/FIX when applicable |
| Record maintenance and current specifications | `RULES.md` | Link to the relevant section |
| Track ownership and handoff | `commands/orchestrate-track.md` | Roles apply their narrower scope within that assignment |
| Role scope and role-specific reports | `agents/<role>.md` | Select a role rather than inventing permissions |
| Detailed steps for an operation | `commands/<command>.md` | Indexes link the procedures for common tasks |
| Track review scope and evidence exclusions | `agents/track-reviewer.md` | The track coordinator supplies the permitted packet |
| Paths, ID formats and configured options | `config.yaml` | Read values from it |
| General investigation evidence | `research/RES-*.md` | Link; never treat a brief as authority |
| Whether a PR merged or a branch exists | Git and the forge | Record the observed revision and URL |
| Reusable record shape | `templates/` | Copy and complete the appropriate template; reports follow their role or command |

Note the split inside the decision block: a meeting note owns *what was said on
a date*, an ADR owns *what we decided*. They are different facts, and
conflating them is how a debate about three options becomes a requirement. A
meeting note is evidence for an ADR, never a substitute for one — see
[`/harvest`](commands/harvest.md).

The orchestration board is `status` tier; research and review logs are `log`. All
sit *below* every contract in [the precedence order](RULES.md#precedence-when-documents-disagree).
A research brief records what one agent believed about the code on one day —
like a meeting note, it is evidence and never a requirement. An implementor
that finds the brief wrong trusts the code and says so.

Note also the three rows that exist to keep history out of the specs. **The
past is owned elsewhere**: what a spec used to say belongs to its amendment, why
a decision changed belongs to the ADR that superseded it, and a defect's story
belongs to its fix record. A spec that carries any of it has taken over a fact
it does not own — which is why "deprecated", "removed in v2" and "not yet
implemented" are truth-map violations and not merely untidy. See
[RULES.md](RULES.md#what-each-document-is-for).

## Rules for authors, human and agent

1. **Link, don't copy.** Write "satisfies SPEC-004" rather than restating
   SPEC-004's criteria. A reader who needs the detail can follow the link; a
   copy will drift.
2. **Numbers and rules live once.** Any threshold, limit, timeout, or business
   rule appears in exactly one document. If you need it in a second place,
   reference it.
3. **Specify observable behavior and link its verification.** Keep incidental
   implementation mechanics in code; use a test or document check as evidence.
4. **Found a duplicate?** Delete the copy, replace it with a link, and note it
   in the journal. This belongs to approved record reconciliation. A report-only request
   reports the duplicate instead of editing it.

## Adding a new kind of fact

If you need to record something with no owner in the table above, add a row
first, then write the document. If a fact does not fit the table at all, that
is a signal to ask rather than to invent a new file.
