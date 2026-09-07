# Repository AI records

Tell Codex or ChatGPT to **read `.ai/AGENTS.md` before working**. Codex does not automatically discover this hidden instruction file when launched at the repository root. Claude Code reads `.claude/CLAUDE.md` when that provider entry file is installed.

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
python src/install.py TARGET --assistant claude|chatgpt
python src/ai.py --project TARGET plan create PLAN-001 --title "Title"
python src/ai.py --project TARGET task create PLAN-001 TASK-002 --title "Title" --objective "Objective"
python src/validate_foundation.py --project TARGET
```

They install one self-contained provider namespace, create draft plan/task bundles, and validate local structure. They do not execute tasks, invoke agents, approve reviews, publish changes, or mark plans completed. A reviewed task may follow the documented manual current-to-completed move; whole-plan and archive relocation remain reserved for the planned logical-reference transition service.

Linked Git worktrees exist under `.worktrees/` only while needed. Remove each clean merged worktree through Git, retain failed or unmerged work by branch/commit, and remove the empty `.worktrees/` directory after cleanup.
