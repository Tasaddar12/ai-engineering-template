---
tier: contract
authority: human
id: TRUTH-MAP
title: Which file owns which fact
links: [RULES]
---

# Truth Map

Use [RULES: Single owner](RULES.md#single-owner) for shared ownership policy.
This index locates project facts and instruction owners.

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
| What one agent found out about the code before building | `research/*.md` | Link — never a requirement |
| What each review round of a track found | Runtime phase receipts under the Git common directory; manual `state/orchestration/<run>/<track>/REVIEW-LOG.md` | Runtime receipts are authoritative in runtime mode; the manual log is authoritative only for manual runs |
| What is happening right now | `state/STATE.md` | Link to it |
| What happened on a given day | `state/journal/YYYY-MM-DD.md` | Link to it |
| How the code actually works | **the code** | Describe, never duplicate |
| How to use the product | `docs/` | Link to it |
| Shared project/workflow rules | `RULES.md` | Link to it |
| An agent's scope, duties, methods and report | `agents/<role>.md` | Link to the agent |
| A command's operating procedure | `commands/<command>.md` | Link to the command |
| Tool values, paths and routes | `config.yaml` | Link to the setting |

Note the split inside the decision block: a meeting note owns *what was said on
a date*, an ADR owns *what we decided*. They are different facts, and
conflating them is how a debate about three options becomes a requirement. A
meeting note is evidence for an ADR, never a substitute for one — see
[`/harvest`](../.ai/commands/harvest.md).

The two orchestration rows are `status` and `log` tier respectively, and both
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

## Adding a new kind of fact

Use [RULES: Single owner](RULES.md#single-owner), then add its owner to the
table above. SPEC self-containment is defined in
[What each document is for](RULES.md#what-each-document-is-for).
