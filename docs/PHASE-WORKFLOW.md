# Working through a phase

Start with [AGENTS](../AGENTS.md), [shared rules](../engineer/RULES.md), project identity and current state. The [truth map](../engineer/truth-map.md) identifies each fact's owner. A command selects a workflow; the workflow supplies the procedure and invokes the Python runtime for structured records.

## Choose the entry

| User intent | Entry | Result |
|-------------|-------|--------|
| Initialize an adopting project | /onboard | PROJECT, REQUIREMENTS and phased ROADMAP |
| See current position | /progress | Evidence report and one recommended next action |
| Advance authorized work | /next | Detect state and proceed within authority |
| Add or adjust phase scope | /phase | Runtime-owned roadmap change |
| Clarify a phase | /discuss-phase N | CONTEXT plus incremental DISCUSSION-LOG |
| Plan approved scope | /plan-phase N | Research, validation architecture and complete PLANs |
| Implement authorized phase | /execute-phase N | Owned commits and complete SUMMARYs |
| Confirm phase goal | /verify-work N | Frozen evidence, report and required UAT |
| Publish verified phase | /ship N | Current draft/ready tracking; merge only on instruction |
| Close shipped milestone | /complete-milestone | Audited shipped record and exact archive |

## Discussion

Discussion clarifies choices within the roadmap boundary. Record each answer incrementally in DISCUSSION-LOG and approved decisions in CONTEXT. Validate a technology choice with an actual check before recommending it; label pending validation honestly if user ordering defers checks. Discussion does not grant execution authority or expand scope.

## Planning

Read the complete PLAN template, approved decisions and current source. Plans name exact modified/deleted paths, resources, dependencies, acceptance, documentation, argv checks and canonical issue references. Wave labels describe intended order; actual groups honor dependencies and overlap. Prefer a thin real end-to-end slice with declared producer contracts. Research cannot silently add or defer scope.

## Implementation authority

The user must explicitly instruct implementation of the phase. Record the actual instruction and covered scope in CONTEXT. Planning readiness, design approval or completion of the previous phase is insufficient. Honor already supplied authority without asking again.

## Isolated execution

The coordinator creates/adopts an isolated session, verifies its path/branch/base and assigns bounded workers. Workers verify identity, read required inputs, commit completed slices and return complete summaries. The coordinator waits for positive stop before integration or overlapping fixes. A timeout does not prove exit. Shared state updates and publication belong to the coordinator.

## Verification

After writers stop and integration finishes, capture one clean revision. Required configured checks and independent read-only specialists inspect that freeze. Join every result before accepting evidence or making corrections. Reuse receipts only when commands/configuration/inputs and ancestry remain valid. Preserve observed failures, missing evidence and required human judgment.

Source presence is not behavior proof. Human UAT needs concrete entry points, fixtures and actions, actual responses and final explicit acceptance. A resolving gap plan and matching SUMMARY may set resolved_by/resolved_at without fabricating acceptance. The final report retains v4 covered digest and currentness evidence.

## Publication and continuation

Open a draft on the first authorized push and update it after each slice. Ready/ship require current passed verification, canonical issue/threat reconciliation and independent issue-link audit. Merge only when instructed. Completing this phase does not authorize the next phase. Preserve remaining work in its owning artifact or durable handoff; do not create todos unless the user requests capture.

Read [requests](REQUESTS.md) for natural-language entry points and [artifact guide](ARTIFACT-GUIDE.md) for record ownership. Exact procedures remain in [workflows](../engineer/workflows/).
