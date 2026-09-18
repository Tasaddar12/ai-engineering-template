# Project planning and parallel implementation

A reusable engineering workflow with complete instructional templates, a separate
`.planning/` project workspace, and a Python runtime for bounded parallel workers.
Start with [AGENTS.md](AGENTS.md).

**The project identity stays blank until adoption.** Template maintenance records
are not an adopting project's roadmap or delivery history.

## Start here

| Need | Read |
|---|---|
| Understand the complete workflow | [Project and phase workflow](.ai/guides/PHASE-WORKFLOW.md) |
| See features, safeguards and limitations | [Workflow features](.ai/guides/WORKFLOW-FEATURES.md) |
| Select and fill a template correctly | [Template guide](.ai/guides/ARTIFACT-GUIDE.md) |
| Give an agent a starting request | [Onboarding prompts](.ai/commands/onboard.md) |
| Turn one or several goals into phases | [Goal planning](.ai/commands/goal-plan.md) |
| Configure and run workers | [Runtime guide](.ai/runtime/README.md) and [template contract](.ai/runtime/TEMPLATE-CONTRACT.md) |
| Select a focused engineering method | [Repository skills](.ai/guides/AGENT-SKILLS.md) |
| Understand the proposed next-stage entry workflows | [Workflow direction](docs/WORKFLOW-DIRECTION.md) |

## What lives where

| Location | Contents | Travels with Git? |
|---|---|---|
| `.planning/` | Project intent, requirements, roadmap, state, phase plans, evidence, research, current specs, decisions and project execution settings | Yes, for committed records |
| `.ai/` | Reusable rules, local procedures and roles, complete templates, supporting guidance, runtime and advisory hooks | Yes |
| `.agents/skills/` | Focused engineering methods selected for each assignment | Yes |
| `docs/` | Human-facing usage, feature and architecture guides | Yes |
| Primary checkout's `.worktrees/` | Assigned integration and worker checkouts | No; ignored local working directories |
| Git common directory's `ai/phases/` | Runtime lock, process records, attempts, prompts and local logs | No; machine-local operational evidence |

## From request to delivery

| Stage | Useful output |
|---|---|
| Onboard | Real intent, inspected baseline, meaningful checks and worker configuration |
| Define and discuss | Observable phase acceptance, boundaries, decisions and authorization |
| Research when needed | Evidence that resolves implementation uncertainty |
| Plan and check | Detailed `NN-CC-PLAN.md` assignments with task actions, checks, dependencies and ownership |
| Execute and integrate | Fresh bounded workers; committed, audited results become available to dependents |
| Verify and accept | Independent outcome assessment, corrected gaps, required human observations |
| Publish and deliver | Push each completed slice to a PR/MR; automatically merge after verification and required checks unless the user opts out |

The coordinator starts workers. Independent components run concurrently; shared
files, exclusive resources and genuine prerequisites constrain scheduling. A
slow unrelated component does not block every later component behind a wave.

## Template fidelity and execution

The retained templates keep their complete teaching guidance, examples,
counterexamples and consumer descriptions at stable filenames under
[`.ai/templates/`](.ai/templates/README.md). Selected full
[agent methods](.ai/agents/README.md) connect research, preparation, implementation
and independent review through the existing procedures. Git records adaptations.
Source attribution and revision history remain in
[third-party notices](.ai/THIRD-PARTY-NOTICES.md).

The executable interface remains `python .ai/runtime/phase.py`. Its
[additive contract](.ai/runtime/TEMPLATE-CONTRACT.md) explains the runtime metadata
used alongside the complete templates. Agent method files supply instructions;
their presence does not install commands, dispatchers or host integrations.
[Agent adaptation](.ai/references/agent-adaptation.md) defines the local boundaries.

`.planning/config.yaml` configures this runtime. Upstream configuration examples
are not silently translated into Python runtime settings.

## Install or update with an agent

Replace `[codex|claude]` with your host. Copy the appropriate prompt into the
project's agent session; both authorize workflow changes only.

### Update an already configured project

```text
Update this project's installed workflow from the latest main revision of
https://github.com/Tasaddar12/ai-engineering-template. Follow its install guide
in an assigned worktree; compare and reconcile upstream changes with our installed
host layout. Preserve project identity, planning/history, settings, worker routes,
checks and custom instructions. Do not re-onboard or reset project records.
Validate the updated workflow and project checks, then open a PR; do not merge.
```

### Install the workflow

```text
Install https://github.com/Tasaddar12/ai-engineering-template from its latest main
revision into this project for [codex|claude]. Follow its install guide in an
assigned worktree, preserve existing project files/settings, install dependencies
and validate the host setup. Open a PR; do not merge. Report the onboarding next
step; do not implement product work.
```

See the [install guide](.ai/commands/install.md) for prerequisites and bootstrap
steps. Re-running the installer does not overwrite conflicting workflow files:
updates require reconciliation. Use `--migrate-existing` only for the legacy
separate `.ai` layout described in that guide.

## Adopt the template

Start with the [download-and-run installer](.ai/commands/install.md) for a new directory
or an existing project. It preserves existing files and sets up the Python
runtime in `.codex-venv` or `.claude-venv`. Preview with `--dry-run`; then finish onboarding below.
Select `--host codex` or `--host claude` to install commands, agents and runtime under
`.codex` or `.claude`, including rules and advisory hooks. Complete skills live
in each host's discovery directory. A fresh installation has no separate `.ai` directory. Codex is the default;
`--no-hooks` skips new hook registrations. Existing project settings are preserved.
Installed instructions describe the destination project, and existing planning
records remain authoritative. Existing `.ai` + `.planning` projects can use
`--migrate-existing` to rebuild the selected host layout while preserving project
history, custom material and verified original-file backups. Preview the migration
with `--dry-run` in an assigned worktree.
The installer leaves this repository's `docs/` directory out of the target.
Installed procedures live in the selected host's `commands` directory, role
methods in `agents`, and supporting guides in `guides`. Codex uses root AGENTS.md
and complete skills in `.agents/skills`; Claude uses root CLAUDE.md and its native
skills directory. Committed files propagate to new Git worktrees. The links below
refer to the template authoring checkout; installed instructions use host paths.

1. Follow [onboard](.ai/commands/onboard.md) in an assigned worktree. Establish the
   actual project's identity and inspect its baseline before asserting readiness.
2. Configure real worker routes and checks in
   [`.planning/config.yaml`](.planning/config.yaml). Install the runtime dependencies.
3. Select a coherent phase and follow the [local procedures](.ai/commands/README.md)
   to discuss, research, plan, check and execute it.
4. Keep required documentation and verification attached to that phase. Complete
   the user's authorized delivery boundary and preserve unfinished work.

**Tracked work defaults to worktree, slice commit, push, PR/MR and automatic merge.**
The coordinator carries out [delivery](.ai/commands/phase-ship.md) after final
verification and required checks; the Python publisher only publishes GitHub PRs.
Explicit instructions such as local-only, draft-only or no-merge override the
default. Cleanup needs separate authorization. An open draft is progress visibility.

## Validation

```text
python -m unittest discover -s tests -v
```

Runtime tests use real temporary Git repositories and processes with deterministic
workers and simulated external boundaries. They establish specific runtime
behavior, not the quality of every live agent assignment. Optional
[advisory hooks](.ai/hooks/README.md) have separate Bash suites; they warn and
return success rather than enforce host permissions.

[Fact ownership](.ai/truth-map.md) explains which record resolves each kind of question.
