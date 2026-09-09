# Lifecycle and durable knowledge

| Location | Required record state | Meaning |
| --- | --- | --- |
| `plans/current/` | plan is not completed; `archived: false` | Draft, isolation, active, blocked, review, or delivery work |
| `plans/completed/` | `status: completed`; `archived: false` | All completion gates and observed merge evidence passed |
| `plans/archived/` | `archived: true` | Retained history excluded from default context |
| `tasks/current/` | task is not completed; `archived: false` | Backlog through accepted, blocked, or superseded work |
| `tasks/completed/` | `status: completed`; `archived: false` | Task completion was observed with its plan |
| `tasks/archived/` | `archived: true` | Retained task history excluded from the live graph |

Location supplies navigation and scope; status supplies the exact workflow state. The bootstrap reserves these lifecycle directories but does not implement movement. TASK-009 must make relocation, `.ai/STATE.json`, logical references, and status or archival changes one transaction before TASK-030 may expose archive behavior. Completed and archived are distinct: completed is a gate result, while archived is a retention/context choice.

Plan and task identity is qualified. A record reference uses the plan ID plus its local task, command, review, or evidence ID. IDs are unique within that plan, and separate current plans may reuse `TASK-001` safely. Shared decisions and research retain project-wide IDs.

A fresh agent reads project state, selects one current plan, resolves one task in that bundle, and loads only explicit references and accepted dependency handoffs. Archived history is never default context. A historical manifest resolves each stored relative path beneath that manifest's own immutable snapshot root and verifies the recorded content hash; it never rewrites old paths or old review bytes. Missing processes become unknown or interrupted, not successful; missing unpushed code is reported as unavailable.
