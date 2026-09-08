# Repository AI records

Tell Codex or ChatGPT to **read `.ai/AGENTS.md` before working**. Codex does not automatically discover this hidden instruction file when launched at the repository root. Claude Code reads `.claude/CLAUDE.md` when that provider entry file is installed.

The paths here describe this toolkit's existing development records. Fresh OpenAI installations use `.codex/` and explicitly read `.codex/AGENTS.md`; fresh Claude installations use `.claude/`. The source `.ai/` records and immutable history are retained, and none of them are copied into an installation. Canonical product guides under `docs/` use `.codex/` as their installed path; resolve those paths to `.ai/` when applying a role to this source repository.

`project/agent-models.json` contains both provider maps. This repository retains the user's Sol/xhigh implementation override and Astra/xhigh reviews; fresh installations default routine development to Terra/high or Sonnet/high. Automatic provider bindings remain unconfigured. Manual development invocations record their observed native tool configuration and its limits in task and review evidence. Graph r4 isolation approval is recorded separately in the selected plan.

`STATE.json` is the registry entry point. Read it first, select the current role from `../docs/agents/README.md`, then load only that role guide, the selected plan and task, explicit references, and accepted dependency handoffs. Do not load the whole agent folder or archived history by default. The reusable installed product payload is canonical under `docs/agents/`, `docs/templates/`, `docs/workflows/`, and `docs/defaults/`.

```text
.ai/
  AGENTS.md
  STATE.json
  framework.json
  ROADMAP.md
  decisions/                 shared project decisions
  research/                  shared sourced research
  project/                   shared project policy
  shared/                    architecture and reusable workflow rules
  plans/
    current/PLAN-NNN/
      plan.json  plan.md  spec.json  spec.md  graph.json
      tasks/{current,completed,archived}/
      commands/  reviews/  evidence/  history/
    completed/
    archived/
```

Plan IDs are unique across the project. Task, command, review, and evidence IDs are local to a plan bundle, so two current plans may each own `TASK-001` and `test.TASK-001`. References to those local records include the plan ID. Current, completed, and archived directories provide clear navigation, while status fields remain explicit.

The flat bootstrap tools are functional:

```text
python src/install.py TARGET --assistant codex
python src/ai.py --project TARGET plan create PLAN-001 --title "Title"
python src/ai.py --project TARGET task create PLAN-001 TASK-002 --title "Title" --objective "Objective"
python src/validate_foundation.py --project TARGET
```

They install one self-contained provider namespace, create draft plan/task bundles, and validate local structure. They do not execute tasks, invoke agents, approve reviews, publish changes, or mark plans completed. A reviewed task may follow the documented manual current-to-completed move; whole-plan and archive relocation remain reserved for the planned logical-reference transition service.

Use `--assistant claude` for Claude; `--assistant chatgpt` aliases `codex`. Existing `.ai/` records remain supported by the CLI and validator, but the installer does not migrate or duplicate them.

Linked Git worktrees exist under `.worktrees/` only while needed. Remove each clean merged worktree through Git, retain failed or unmerged work by branch/commit, and remove the empty `.worktrees/` directory after cleanup.
