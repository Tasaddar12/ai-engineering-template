---
name: codebase-recon
description: Map unfamiliar code before onboarding or a cross-cutting change. Trace real entry points, data flow, ownership, test seams, and documentation instead of reading the whole repository.
---

# Codebase reconnaissance

Work within the assigned role and [shared rules](../../../.ai/RULES.md).
Produce the smallest source map that lets the next worker act correctly.

## Trace the relevant behavior

Start from the requested user action, command, job or failure. Find its entry
point, follow calls to the state or external boundary, then follow the result
back to its consumer. Inspect callers as well as definitions: an exported
function may never participate in the actual flow.

Use repository searches to locate candidates, then read the relevant source.
Directory names, architecture diagrams and search hits are leads, not evidence
that a layer runs. For each important boundary, identify:

| Question | Evidence to locate |
|---|---|
| What starts this behavior? | Registered route, command, event handler or job |
| Where is state read or changed? | Actual storage client, transaction or service call |
| Where are errors and access decisions handled? | Executed checks and their callers |
| What proves the flow works? | Relevant assertions, fixtures and integration checks |

Inspect manifests, lockfiles and configured commands before proposing test
invocations. Reuse commands that work at the assigned revision and directory.
Distinguish implementation from mocks, disabled routes and unfinished stubs.

For an adoption or migration, also identify relevant state outside Git:
stored data, environment configuration, scheduled jobs, generated artifacts or
installed integrations. Report what was inspected and what remains unknown;
a source search cannot prove external state is absent.

## Leave a useful map

Return a compact flow with source locations, the revision, ownership boundaries,
available checks, relevant guides and unresolved questions. Separate observed
current behavior from the requested change. Save an assigned codebase map only
when later work would otherwise repeat this investigation; avoid a file-by-file
inventory or a second architecture contract.

Use the [truth map](../../../.ai/truth-map.md) to link existing fact owners.
Hand proposed scope or document corrections to the coordinator rather than
silently converting observations into requirements.
