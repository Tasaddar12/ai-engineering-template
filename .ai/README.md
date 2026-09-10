---
tier: contract
authority: human
id: AI-README
title: How .ai/ works
---

# `.ai/`

The working memory of this project: intent, contracts, plans, state, history.
[Agents](agents/README.md) define role scopes and [commands](commands/README.md)
own detailed procedures. [Workflows](workflows/README.md) compose those steps;
[policies](policies/README.md) and [gates](gates/README.md) define requirements
and pass/fail transitions. Project records and templates also live here.

**Agents: read [RULES.md](RULES.md) first.** It answers the question that
matters most — what you are allowed to change, and what to do when a document
contradicts reality. The short version: fix the document, record why, keep
going within the user-approved scope. The [approval policy](policies/approval.md)
requires a report and templated decision summary before unapproved action.

## Layout

```
.ai/
├── RULES.md            Rules of engagement. Mutability tiers, amendment protocol.
├── truth-map.md        Which file owns which fact. One owner per fact, always.
├── config.yaml         Mode (light/standard), paths, id formats.
├── specs/              What "correct" means. SPEC-{nnn}-{slug}.md
├── decisions/          Why we chose an approach. ADR-{nnnn}-{slug}.md
│   ├── amendments/     Why a contract changed. AMD-{nnn}-{slug}.md
│   ├── retired/        Superseded ADRs, with their rationale intact.
│   └── meetings/       What was said, and when. Never a requirement.
├── plans/              How we get there — stage is the directory:
│   ├── intake/         Captured problems, not yet planned.
│   ├── backlog/        Written, not started.
│   ├── active/         In progress. Keep this small.
│   ├── blocked/        Waiting on a human decision.
│   ├── review/         Built, awaiting verification.
│   ├── done/2026-Q3/   Finished, partitioned by quarter.
│   └── abandoned/      Deliberately not doing. Kept, with a reason.
├── fixes/              Single defects. Short lifecycle, same idea:
│   ├── open/           Being diagnosed or fixed.
│   └── done/2026-Q3/   Fixed and proved by a check.
├── agents/             Detailed role prompts.
├── commands/           Authoritative command procedures.
├── workflows/          Initialize, planning, implementation, review, parallel execution.
├── policies/           Firm cross-cutting requirements.
├── gates/              Pass/fail transition checks.
├── hooks/              Optional, unregistered Bash examples.
├── research/           General research evidence.
├── state/
│   ├── PROJECT.md      Purpose, non-goals and human constraints.
│   ├── STATE.md        Now / next / blockers. Churns constantly.
│   ├── journal/        Append-only daily log.
│   └── orchestration/  One board per /orchestrate run; per-track research
│                       briefs and review logs live on the track branches.
└── templates/          Copy these to create new documents.
```

## The three ideas that make this work

**1. A plan's stage is its directory.** Moving work is a `git mv`, which an
agent cannot forget to do or misreport. There is deliberately no `status:`
field in plan frontmatter — a second copy of the truth is a future
contradiction.

**2. Documents are tiered by who may change them.** `intent` needs a human.
`contract` is amendable by any agent, provided it records why. `plan`, `status`
and `log` are the agent's to maintain. An agent that knows which tier it is
looking at never has to guess whether it has permission, which is what
produces both refusals and silent workarounds.

**3. Each document has one tense.** A spec says what *is* — present tense, no
history, no intentions, no "deprecated" and no "not yet implemented". An ADR
says why we chose something and what it replaced. A plan says what we intend
next, and carries the exact spec wording it will land once the code works. Mix
the tenses and a spec becomes something an agent has to interpret rather than
read; keep them apart and every spec is true at every commit. See
[RULES.md](RULES.md#what-each-document-is-for).

| Tier | Files | Agent may |
|---|---|---|
| `intent` | `state/PROJECT.md`, `RULES.md`, approval policy | Edit only under explicit human instruction |
| `contract` | Specs, ADRs and operating contracts | Follow the amendment protocol |
| `plan` | `plans/`, `fixes/` | Rewrite |
| `status` | `state/STATE.md`, `state/orchestration/ORCH-*.md` | Overwrite |
| `log` | `state/journal/`, `amendments/`, research briefs | Append |

## Daily use

| To | Run |
|---|---|
| Set up a fresh project | `/onboard` |
| See where everything stands | `/plan-status` |
| Record a problem without fixing it | `/defer <what>` |
| Turn meeting notes into decisions | `/harvest <path>` |
| Fix a single defect, with proof | `/fix <what's broken>` |
| Write a new plan | `/plan-new <what>` |
| Promote a captured problem | `/plan-new INTAKE-nnn` (or `/fix` if it is a bug) |
| Start work | `/plan-start <id>` |
| Park on a human decision | `/plan-block <id> <question>` |
| Hand off for verification | `/plan-review <id>` |
| Close it out | `/plan-done <id>` |
| Sweep finished plans into a quarter | `/plan-archive` |
| Correct a wrong spec | `/spec-amend <id> <what's wrong>` |
| Schedule several plans into parallel worktrees | `/orchestrate <ids>` |
| Build one of those tracks, in its worktree | `/orchestrate-track <run> <track>` |
| See where a multi-plan run stands | `/orchestrate-status` |
| Tear down a run's worktrees | `/orchestrate-clean` |

`/orchestrate` is the one command that is not a step in the single-plan
lifecycle. It works out which plans can be built in parallel and which have to
wait, then creates a git worktree per group; `/orchestrate-track` builds one of
those groups, in its own session — see
[docs/ORCHESTRATION.md](../docs/ORCHESTRATION.md). For one plan, `/plan-start` is the single-plan route. A worktree or PR is still
required when the user's instruction or project policy calls for it.

Slash-style names above identify the Markdown files in commands; they are not
registered tools in this checkout. The default dispatch is manual. There is no
build step or launcher. Optional [hooks](hooks/README.md) need Bash and a
compatible host; copying the files does not activate them.

## Scaling down

A consuming project can choose less ceremony for a small change. Set `mode: light`
in [config.yaml](config.yaml) and use `plans/active/` with acceptance criteria
written directly in the plan. The rules in `RULES.md` still apply — they are
what stops an agent from bending code around a stale note, and that failure
happens at every project size. Raise the mode later; it is purely additive.

`fixes/` is live in every mode, `light` included. It is the cheapest thing here:
one document, two directories, and a regression test. In `light` mode the
contract a fix conforms to is the plan's acceptance criteria rather than a spec.
