# Bounded correction dispatch

Use the exact registered `targeted-fixer` for a narrow deterministic repair when its role fits; otherwise use the assigned final role. Read `agents/targeted-fixer.md` before dispatch. The [execute-phase workflow](../workflows/execute-phase.md) owns procedure.

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

## Host dispatch and isolation

Read [the targeted-fixer role](../../agents/targeted-fixer.md), [branch identity](worktree-branch-check.md) and [path safety](worktree-path-safety.md). Resolve `engineer_run query resolve-model targeted-fixer --raw` and `engineer_run query resolve-effort targeted-fixer --raw` immediately before dispatch; pass concrete values inline and omit inherited fields.

Read `engineer_run query dispatch-isolation --raw`, adding `--plan PLAN_ID` when the actual caller supplies a plan identity. Use the configured supported strategy: orchestrator-worktree creates and records the isolated checkout through `worktree.create` before assignment; harness-worktree uses the host's actual `isolation="worktree"` mechanism and records its returned identity before mutation. Neither strategy permits writes in the shared caller checkout. Do not emit harness isolation on an orchestrator-worktree call. Include the exact root, branch, base, finding origin, required property, diagnosis, owned paths, exclusions, check order, complete summary path and result destination.

On Claude use the exact `subagent_type="targeted-fixer"`; on Codex use its registered targeted-fixer definition and native model/effort fields. Do not invent generic fallback agents. The originating debugger/reviewer supplies cited evidence, not a mutable ownership transfer or independent approval. Wait for complete committed repair and confirmed stop before integration. Require fresh independent review and verification on the integrated result, then return to the active caller rather than starting a second shipping session.
