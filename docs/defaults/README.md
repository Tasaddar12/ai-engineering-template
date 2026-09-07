# AI workflow records

Start with [the focused workflow](workflows/START.md), then select one role from the [agent index](agents/README.md). Read only the chosen role guide, `.ai/STATE.json`, one selected plan and task, and their explicit references. Do not load every guide or archived history.

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

Plans are complete bundles under `.ai/plans/current/PLAN-NNN/`. Plan IDs are project-unique. Task, command, review, handoff, and evidence IDs are local to their plan and references include the plan ID. The bootstrap reserves completed and archived directories but does not move records or grant completion.

Create and inspect records:

```text
python .ai/tools/ai.py --project . plan create PLAN-100 --title "Title"
python .ai/tools/ai.py --project . task create PLAN-100 TASK-002 --title "Title" --objective "Objective" --depends-on TASK-001
python .ai/tools/ai.py --project . plan list
```

Install the validator dependency and validate the selected namespace:

```text
python -m pip install -r .ai/requirements.txt
python .ai/tools/validate_foundation.py --project .
```

The tools create and validate records. They do not execute tasks, invoke agents, approve reviews, publish changes, relocate lifecycle bundles, or mark work complete. Create `.worktrees/` only when an active linked Git worktree is needed, and remove the empty directory after Git removes the last worktree.

Before implementation or independent review, a project owner must configure the applicable entries in `.ai/project/policy.json`: set `provider`, `model_id`, `capability_rank`, and `configured` from the actual available invocation. Record actual provider/model provenance in each handoff or review. Keep unavailable values null and `configured: false`; pause the affected gate when the required implementation or higher-capability review profile cannot be verified.
