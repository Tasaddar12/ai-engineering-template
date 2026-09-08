# AI workflow records

Start with [the focused workflow](workflows/START.md), then select one role from the [agent index](agents/README.md). Read only the chosen role guide, `.codex/STATE.json`, one selected plan and task, and their explicit references. Do not load every guide or archived history.

| Current stage | Read next |
| --- | --- |
| Empty install or plan design | [Planning](workflows/PLANNING.md) |
| Context selection | [Context](workflows/CONTEXT.md) |
| One approved task | [Implementation](workflows/IMPLEMENTATION.md) |
| Candidate checks | [Review](workflows/REVIEW.md) |
| Failure or structural discovery | [Recovery](workflows/RECOVERY.md) |
| Integration, delivery, retention | [Completion](workflows/COMPLETION.md) |
| Changing or uncertain facts | [Research](workflows/RESEARCH.md) |
| Path and ownership questions | [Layout](workflows/LAYOUT.md) |
| Agent models, effort, and overrides | [Models](workflows/MODELS.md) |

Plans are complete bundles under `.codex/plans/current/PLAN-NNN/`. Plan IDs are project-unique. Task, command, review, handoff, and evidence IDs are local to their plan and references include the plan ID. The bootstrap reserves completed and archived directories but does not move records or grant completion.

Create and inspect records:

```text
python .codex/tools/ai.py --project . plan create PLAN-100 --title "Title"
python .codex/tools/ai.py --project . task create PLAN-100 TASK-002 --title "Title" --objective "Objective" --depends-on TASK-001
python .codex/tools/ai.py --project . plan list
```

Install the validator dependency and validate the selected namespace:

```text
python -m pip install -r .codex/requirements.txt
python .codex/tools/validate_foundation.py --project .
```

The tools create and validate records. They do not execute tasks, invoke agents, approve reviews, publish changes, relocate lifecycle bundles, or mark work complete. Create `.worktrees/` only when an active linked Git worktree is needed, and remove the empty directory after Git removes the last worktree.

Every role has editable defaults for both providers in `.codex/project/agent-models.json`. Fresh installation selects the provider and prefills the gate profiles in `.codex/project/policy.json`, keeping `configured: false` until the model and effort are verified in the actual host. Before implementation or independent review, reconcile the applicable policy profile with that invocation and record actual provider/model/effort provenance in the handoff or review. Retain unavailable recommendations as defaults, keep the affected policy profile unconfigured, and pause that gate. See the [model selection guide](workflows/MODELS.md) for overrides and escalation.
