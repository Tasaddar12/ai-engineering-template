# Installed workflow layout

This canonical source document shows `.ai/` paths. Installation renders the same records and links inside the one selected namespace.

```text
.ai/
  AGENTS.md  README.md  STATE.json  framework.json  requirements.txt
  agents/                         role index and individual guides
  templates/                      reusable blank record documents
  workflows/                      focused operating procedures
  project/policy.json
  decisions/index.json
  research/
  framework/{manifest.json,schemas/v1/}
  tools/{ai.py,validate_foundation.py}
  plans/
    current/PLAN-NNN/
      plan.json  plan.md  spec.json  spec.md  graph.json
      tasks/{current,completed,archived}/
      commands/  reviews/  evidence/  history/
    completed/
    archived/
  local/                          ignored host-local state; created only when needed
```

Plan IDs are unique across the project. Task, command, review, handoff, and evidence IDs are local to a plan; references to them include the plan ID. Plan specifications, graphs, tasks, commands, reviews, evidence, and history remain inside their bundle. Policy, decisions, research, agent guides, templates, workflows, schemas, and tools are namespace-wide.

The bootstrap commits `.gitkeep` markers for required empty record directories so the layout survives a Git archive or fresh checkout. It does not create `.worktrees/` or `local/`; create those only while local work needs them. It reserves completed and archived directories but does not relocate records or grant completion.
