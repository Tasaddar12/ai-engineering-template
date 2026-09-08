# Record templates

These files are immutable masters. Copy the needed template, fill it, and store the result in the selected namespace:

| Template | Filled record location |
| --- | --- |
| `PLAN.md`, `SPEC.md` | `.codex/plans/current/<plan-id>/` |
| `TASK.md` | `.codex/plans/current/<plan-id>/tasks/current/` or plan-local evidence for a JSON task |
| `REVIEW.md` | `.codex/plans/current/<plan-id>/reviews/` |
| `HANDOFF.md`, `EVIDENCE.md` | `.codex/plans/current/<plan-id>/evidence/` |
| `DECISION.md` | `.codex/decisions/` |
| `RESEARCH.md` | `.codex/research/` |

Do not edit the master under `.codex/templates/`. Claude installations replace the namespace in this guide with `.claude/` during installation.
