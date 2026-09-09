# Workflows

Workflows own steps; [commands](../commands/README.md) select operations.
[Policies](../policies/README.md) own requirements and [gates](../gates/README.md)
check readiness to advance.

| Workflow | Lead / handoff | Result |
| --- | --- | --- |
| [Initialize](initialize.md) | orchestrator | Project context, live state and initial record scaffold. |
| [Report](report.md) | orchestrator, with bug-reviewer for bugs | Intake and next decision. |
| [Research](research.md) | researcher to orchestrator | Sources, findings, uncertainty and recommendation. |
| [Planning](planning.md) | planner to orchestrator | Bounded proposal and user decision. |
| [Implementation](implementation.md) | implementor, tester, orchestrator | Changes, specs and final test evidence. |
| [Review](review.md) | reviewer to orchestrator | One verdict with actionable findings. |
| [Parallel execution](parallel-execution.md) | orchestrator with assigned workers | Independent results, combined validation and review. |
| [Deliver](deliver.md) | pr-agent under orchestrator coordination | The approved Git action and observed outcome. |

Use only the operations needed for the request. These are manual procedures and role
handoffs; defining them does not launch agents or authorize product work.
