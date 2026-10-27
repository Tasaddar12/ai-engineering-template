# Asking for workflow work

Use natural language or the named command. The agent follows the matching workflow and honors authority already supplied. A slash prefix is not required for a request such as "let's discuss phase 01".

| Request | Meaning and boundary |
|---------|----------------------|
| Set up this project | Onboard identity, requirements and roadmap |
| Where are we? | Report progress and one next action |
| Let's discuss phase 01 | Ask adaptive questions and record decisions |
| Plan phase 01 | Produce complete bounded plans and evidence |
| Implement phase 01 | Explicit execution authority for that phase and stated scope |
| Verify phase 01 | Inspect goal completion, checks and human acceptance |
| Ship phase 01 | Publish verified work; merge still requires instruction |
| Merge this PR | Merge specified verified PR after current provider gates |
| Make this small fix | Use a bounded ad hoc workflow for one coherent outcome |
| Capture this idea | Create a requested todo without derailing current work |
| Clean up these resources | Preview exact owned resources; fresh deletion approval required |

## Give useful scope

State the outcome, affected phase/task, required behavior and material constraints. Include exact source/issue links and user ordering such as "create every draft PR before running checks". Existing authorization persists across turns for its covered scope; a follow-up status question steers the active task rather than automatically cancelling it.

## Decisions and missing input

The agent prepares a concrete reviewable result before requesting a genuinely missing decision. It records the actual answer and blocks only dependent work, continuing independent authorized work. Silence, mode flags and suggested options do not supply approval. Secure credentials go through masked/provider entry, never conversation text.

## Reports

Expect exact outcomes, current revision, evidence actually observed, pending checks/acceptance and remaining work. Not run, not configured, failed and unverifiable are distinct. A file or PR existing does not prove its acceptance passed.

## Handoffs

A continuation preserves base/head, completed commits, remaining scope, dirty paths, pending human decisions, process state and first bounded next action. Ask for /progress to report or /next to advance within existing authority. A completed phase alone never authorizes implementing the next.

Read [phase workflow](PHASE-WORKFLOW.md), [phase authority](../engineer/RULES.md#phase-authority) and [worker handoff](../engineer/references/worker-handoff.md).
