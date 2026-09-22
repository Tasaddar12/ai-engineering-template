# Project planning and phased implementation

A reusable engineering workflow: complete instructional templates, a separate
`.planning/` project workspace, workflow procedures that orchestrate subagents,
and a Python runtime that owns every planning record. Start with
[AGENTS.md](AGENTS.md).

**The project identity stays blank until adoption.** Template maintenance records
are not an adopting project's roadmap or delivery history.

## Start here

| Need | Read |
|---|---|
| Understand the complete workflow | [Project and phase workflow](.ai/guides/PHASE-WORKFLOW.md) |
| See features, safeguards and limitations | [Workflow features](.ai/guides/WORKFLOW-FEATURES.md) |
| Select and fill a template correctly | [Template guide](.ai/guides/ARTIFACT-GUIDE.md) |
| Initialize a project from actual intent | [Onboarding](.ai/commands/onboard.md) |
| Turn a goal into a milestone and phases | [New milestone](.ai/commands/new-milestone.md) |
| Call the runtime, or extend it | [Runtime guide](.ai/runtime/README.md) and [template contract](.ai/runtime/TEMPLATE-CONTRACT.md) |

## How it is layered

```
command (.ai/commands/) ── the entry point; names a workflow, changes nothing
  └─ workflow (.ai/workflows/) ── the procedure: what to load, whom to spawn,
                                   what to ask, which runtime verbs to call
       ├─ runtime (.ai/runtime/phase.py) ── every planning-record read and write
       └─ agent (.ai/agents/) ── a bounded role, spawned with its own context
```

A workflow orchestrates; a runtime verb mutates. Phase numbering, the roadmap
checklist, the progress table, STATE.md's derived counters, todos, quick tasks and
milestones all belong to the runtime, so a workflow never edits those files by
hand. Skills under `.agents/skills/` mirror the commands one-for-one.

## What lives where

| Location | Contents | Travels with Git? |
|---|---|---|
| `.planning/` | Project intent, requirements, roadmap, state, phase plans, evidence, research, specs, todos, quick tasks and project execution settings | Yes |
| `.ai/` | Reusable rules, commands, workflows, agent roles, complete templates, supporting guidance, runtime and advisory hooks | Yes |
| `.agents/skills/` | Command skills mirroring `.ai/commands/`, plus focused engineering methods | Yes |
| `docs/` | Human-facing usage and architecture guides | Yes |

## From request to delivery

| Stage | Command | Useful output |
|---|---|---|
| Onboard | `/onboard` | Real intent, inspected baseline, scoped requirements, phased roadmap, configured checks |
| Add work | `/phase`, `/new-milestone` | A phase or milestone in the roadmap, numbered and directory-backed |
| Discuss | `/discuss-phase {N}` | `NN-CONTEXT.md`: the decisions downstream agents must not re-litigate |
| Plan | `/plan-phase {N}` | `NN-RESEARCH.md` where warranted, and `NN-MM-PLAN.md` checked goal-backward |
| Execute | `/execute-phase {N}` | Commits and `NN-MM-SUMMARY.md` per plan, reviewed by a fresh code-reviewer |
| Verify | `/verify-work {N}` | `NN-VERIFICATION.md`: what is actually true, with gaps closed or recorded |
| Ship | `/ship {N}` | A pull request, gated on passing verification and checks |
| Close | `/complete-milestone` | A MILESTONES.md entry recording what shipped |

`/progress` reports and recommends; `/next` decides and proceeds. `/quick` handles
a change too small for a phase. `/capture` parks an idea without derailing the
current work.

Plans execute in dependency waves. Plans in the same wave run concurrently in
fresh agent contexts; plans that declare overlapping files are separated into
later waves regardless of their declared wave.

## Template fidelity and execution

The retained templates keep their complete teaching guidance, examples,
counterexamples and consumer descriptions at stable filenames under
[`.ai/templates/`](.ai/templates/README.md). The
[agent methods](.ai/agents/README.md) connect research, planning, implementation
and independent review through the workflow procedures. Git records adaptations,
and source attribution stays in
[third-party notices](.ai/THIRD-PARTY-NOTICES.md).

The executable interface is `python .ai/runtime/phase.py query <verb>`. Its
[contract](.ai/runtime/TEMPLATE-CONTRACT.md) explains the runtime metadata used
alongside the complete templates. A command or agent method file supplies
instructions; its presence does not install commands, dispatchers or host
integrations. [Agent adaptation](.ai/references/agent-adaptation.md) defines the
local boundaries.

`.planning/config.yaml` configures the runtime: `commit_docs`, workflow flags,
per-agent model and effort overrides and the project's real
`verification.commands`.

## Install or update with an agent

Replace `[codex|claude]` with your host. Copy the appropriate prompt into the
project's agent session; both authorize workflow changes only.

### Update an already configured project

```text
Update this project's installed workflow from the latest main revision of
https://github.com/Tasaddar12/ai-engineering-template. Follow its install guide;
compare and reconcile upstream changes with our installed host layout. Preserve
project identity, planning/history, settings, checks and custom instructions. Do
not re-onboard or reset project records. Validate the updated workflow and project
checks, then follow this project's delivery rules.
```

### Install the workflow

```text
Install https://github.com/Tasaddar12/ai-engineering-template from its latest main
revision into this project for [codex|claude]. Follow its install guide, preserve
existing project files and settings, install dependencies and validate the host
setup. Follow the delivery rules and report the onboarding next step; do not
implement product work.
```

See the [install guide](.ai/commands/install.md) for prerequisites and bootstrap
steps. Re-running the installer does not overwrite conflicting workflow files:
updates require reconciliation. Use `--migrate-existing` only for the legacy
separate `.ai` layout described in that guide.

## Adopt the template

Start with the [download-and-run installer](.ai/commands/install.md) for a new
directory or an existing project. It preserves existing files and sets up the
Python runtime in `.codex-venv` or `.claude-venv`. Preview with `--dry-run`.

Select `--host codex` or `--host claude` to install commands, workflows, agents and
runtime under `.codex` or `.claude`, including rules and advisory hooks. Codex is
the default; `--no-hooks` skips hook registration. Codex uses a root AGENTS.md and
skills in `.agents/skills`; Claude uses a root CLAUDE.md and its native skills
directory. The installer leaves this repository's `docs/` out of the target. The
links below refer to the authoring checkout; installed instructions use host paths.

1. Run [`/onboard`](.ai/commands/onboard.md). Establish the project's actual
   identity and inspect its baseline before asserting readiness.
2. Configure the project's real checks in
   [`.planning/config.yaml`](.planning/config.yaml) under `verification.commands`,
   and install the runtime dependencies. Without them, every phase is verified by
   reading alone.
3. Take a phase through discuss → plan → execute → verify using the
   [commands](.ai/commands/README.md).
4. Keep required documentation and verification attached to that phase, and
   complete the user's authorized delivery boundary.

**Tracked work defaults to slice commit, push and a draft PR.**
[Ship](.ai/commands/ship.md) publishes after verification passes and required
checks are green; it does not merge, and it has no bypass for unverified work.
Explicit instructions such as local-only, draft-only or no-merge override the
default. Cleanup needs separate authorization.

## Validation

```text
python -m unittest discover -s tests -v
```

`tests/test_phase_runtime.py` drives the runtime as a subprocess against real
temporary Git repositories, so it exercises the contract the workflows depend on
rather than internals. Optional [advisory hooks](.ai/hooks/README.md) have
separate Bash suites; they warn and return success rather than enforce host
permissions.

[Fact ownership](.ai/truth-map.md) explains which record resolves each kind of
question.
