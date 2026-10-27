# Workflow features and evidence

The workflow combines copied upstream methods with explicit user authority, isolated execution and a Python record runtime. Only Claude and Codex adapters are supported. Read [the runtime interface](../engineer/bin/README.md) for actual argv and result shapes.

| Feature | Use | Evidence / limit |
|---------|-----|------------------|
| Adaptive discussion | Capture choices and alternatives | CONTEXT owns decisions; DISCUSSION-LOG preserves answers |
| Bounded planning | Complete templates and exact ownership | Dependencies/files/resources form actual groups |
| Implementation authority | User instructs execution of named phase | Actual instruction in CONTEXT; readiness is insufficient |
| Mandatory isolation | Open/adopt isolated workflow session | Root/branch/base guards; no opt-out |
| TDD | Assigned TDD plans/tasks | Actual RED and GREEN evidence plus ancestry |
| Frozen verification | Capture revision and join every result | Current receipts and v4 digest; no invented evidence |
| Human acceptance | Runnable actions, fixtures and reply format | Actual final human acceptance |
| Canonical security tracking | Planned checklist and distinct unplanned trackers | Semantic dedup, provider BODY anchors and independent audit |
| Draft delivery | First authorized push opens draft | Keep scope/evidence current; merge requires instruction |
| Durable continuation | Handoff exact working context | Revisions, dirty paths, decisions and pending gates |
| Exact cleanup | Fresh preview and token approval | Revalidate integration and ownership before deletion |
| Planning repair | Review findings and current digest | Guarded structural operations preserve narrative/scope |

## Specialized entries

The retained catalog includes security and validation review, UAT audit, specification, code review/fixes, UI specification/review, added tests, fast execution and bounded quick batches. Read the corresponding command and workflow before using one; an entry name alone does not prove its checks or provider integrations ran.

## Currentness

A passing result is tied to covered source and inputs. Reuse evidence only when command/configuration/inputs and history remain valid. Source changes require affected rechecks; unchanged valid receipts should not be duplicated needlessly. Human judgment remains separate.

## Ownership

Structured planning changes use engineer_run query. Narrative stays in its owning artifact. PROJECT Key Decisions owns consequential decisions; an ADR stores optional rationale. See [truth map](../engineer/truth-map.md) and [artifact guide](ARTIFACT-GUIDE.md).
