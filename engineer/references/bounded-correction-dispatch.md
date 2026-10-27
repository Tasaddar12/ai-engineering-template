# Bounded correction dispatch

Use the exact registered `code-fixer` for a narrow deterministic repair when its role fits; otherwise use the assigned final role. Read `agents/code-fixer.md` before dispatch. The [execute-phase workflow](../workflows/execute-phase.md) owns procedure.

## Required correction packet

- Exact repository, branch, input revision and current artifact digest.
- Stable finding IDs, severity, authority and required_property.
- Cited evidence showing the property fails; distinguish demonstrated failure from preference.
- Exact owned output paths and forbidden paths; declared deletions/resources.
- Smallest affected source/contract reading set and complete consuming template.
- Required affected check argv, reusable passing evidence and pending human decisions.
- Expected return artifact, commit requirement and first continuation.

## Procedure

1. Freeze the producer output before review. Wait for its confirmed stop.
2. Join all assigned reviewer results and classify duplicate or conflicting findings by evidence and authority.
3. Assign only the specific corrections; do not send the worker to rediscover the repository.
4. The worker satisfies the required property through the smallest sufficient repair. A fix_hint illustrates an option and is not authority.
5. Record a disposition for every stable ID: fixed with evidence, unsupported with explanation, or blocked by an exact decision/input.
6. Rerun affected checks after all writers stop; reuse only unchanged valid receipt inputs.
7. Continue correction until resolved or specifically blocked. No fixed review count permits unresolved failures, and no identical failed attempt is repeated without a changed hypothesis/input.

## Conflict route

If a finding contradicts approved scope or a locked decision, preserve the decision, cite both sources and return the specific conflict to the coordinator. Continue nonconflicting corrections. Do not weaken acceptance, silently defer work or invent approval to close the review.
