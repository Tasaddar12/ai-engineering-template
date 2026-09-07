# Record templates

These files are immutable masters. Copy the needed template, fill it, and store the result in the selected namespace:

| Template | Filled record location |
| --- | --- |
| `PLAN.md`, `SPEC.md` | `.ai/plans/current/<plan-id>/` |
| `TASK.md` | `.ai/plans/current/<plan-id>/tasks/current/` or plan-local evidence for a JSON task |
| `REVIEW.md` | `.ai/plans/current/<plan-id>/reviews/` |
| `HANDOFF.md`, `EVIDENCE.md` | `.ai/plans/current/<plan-id>/evidence/` |
| `DECISION.md` | `.ai/decisions/` |
| `RESEARCH.md` | `.ai/research/` |

Do not edit the master under `.ai/templates/`. Claude installations replace the namespace in this guide with `.claude/` during installation.
