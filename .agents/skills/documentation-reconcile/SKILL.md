---
name: documentation-reconcile
description: Audit and update guides or SPECs after a change, during onboarding, or when claims conflict. Check exact claims against source and current intent, then correct the responsible document or report the code defect.
---

# Reconcile documentation with evidence

Use the assigned role, [fact owners](../../../.ai/truth-map.md) and
[documentation coverage](../../../.ai/references/documentation.md).
This method does not give a documentor permission to change source behavior.

## Turn prose into checkable claims

Identify affected guidance from the change: behavior, public interfaces,
configuration, installation, operations and significant architectural choices.
Inspect exact paths, commands/options, functions, dependencies, endpoints and
runtime claims rather than searching for a few matching words.

For each important discrepancy, retain the document location, claimed behavior,
implementation/intent evidence, revision or configuration context, impact and
proposed correction. First check whether the documents describe different
versions, modes or scopes; not every difference is a contradiction.

For example, a guide saying verification starts during execution requires
checking the actual dispatch path. A verifier role file or executable existing
on disk does not prove when that process runs.

## Correct the responsible side

Apply the [conflict rules](../../../.ai/RULES.md#documents-and-conflicts):
a valid unmet requirement needs a code correction; stale guidance about correct
behavior needs a document correction; an authorized future transition remains
future scope until implemented. Conflicting human decisions go to the coordinator
for resolution of dependent work.

Keep intent in PROJECT/REQUIREMENTS, exact phase decisions in CONTEXT, current
behavior in SPECs, and usage in guides. Link to the owner instead of copying its
contract into several documents. Preserve significant ADR rationale and history.

## Complete the actual handoff

Check each required document on the component assigned to cover it. Inspect code,
callers and meaningful checks at the deliverable revision. Evaluate executable
examples even when labeled examples: inspect their effects before running them,
and use safe checks or isolated fixtures appropriate to the assignment.

Report updated and verified, verified unchanged, not applicable with a reason,
or unresolved coverage in the assigned SUMMARY. For a read-only audit, return
findings in the caller's requested format without writing records. A required
missing document or unsupported claim remains a gap; a label cannot remove the
obligation.

For documentation that follows another component, use its integrated code and
summary. Coders should hand off changed interfaces, configuration, behavior and
proof rather than claim coverage for a guide a later documentor has not written.
Return code defects and decisions outside your scope with evidence.
