# Full GSD templates and the local runtime

Read the complete upstream template before authoring or reviewing its output.
The template's File Template is the output skeleton; examples and teaching
sections remain in the source template. Keep all applicable output sections.
This contract adds local execution evidence; it does not replace upstream guidance.

| Artifact | Producer | Consumer | Local additions |
|---|---|---|---|
| NN-CONTEXT.md | Discussion coordinator; `new` seeds the full context skeleton | Researcher, preparer, checker, runtime | YAML phase number, approval, depends_on, uat; Acceptance and Authorization sections |
| NN-CC-PLAN.md | Phase preparer | Checker, scheduler, assigned worker | kind, resources, acceptance, documentation, checks; Documentation handoff section |
| NN-CC-SUMMARY.md | Assigned worker | Integrator, downstream workers, verifier | acceptance, documentation; Checks section with actual evidence |
| NN-VERIFICATION.md | Independent verifier | Coordinator and publication gate | revision; Acceptance, Integration, Documentation, Findings sections; runtime source and check receipts |
| NN-UAT.md | Coordinator recording actual human observations | Returning sessions and publication gate | revision, source_fingerprint, cases, history; source keeps upstream's list of summaries |

## Author a context

Use `.ai/templates/context.md` in full. `new` copies its first File Template,
substitutes phase/name/date, and adds pending authorization and acceptance.
Fill Phase Boundary, decision categories, canonical references, code insights,
specific ideas and deferred ideas according to its instructions. Do not infer
human approval from a template status label. Add this frontmatter:

```yaml
phase: "01"
approval: pending  # approved only when actual authorization is recorded below
depends_on: []     # delivered phase directory names, e.g. 02-foundation
uat: false
```

Append `## Acceptance` with observable outcomes such as
`- [ ] AUTH-01: A signed-out visitor cannot retrieve another user's profile.`
Append `## Authorization` with the actual user instruction and its scope/date.
Keep unresolved choices in `## Open Questions`; dispatch only decided scope.
Acceptance IDs may be requirement IDs or finer phase criteria with their own IDs.

Good authorization names the user's request and its boundary. Bad authorization
says "approved because the plan looks ready." A checker cannot grant permission.

## Author an executable plan

Use `.ai/templates/phase-prompt.md` without shortening its instructions or removing
its task-level action, verification, done, context or success sections. The file
name is phase-local `01-01-PLAN.md`; no separate work-item lifecycle is introduced.
Use the upstream `phase: 01-name`, quoted `plan: "01"`, `type: execute|tdd`,
`files_modified`, `files_deleted`, `requirements`, `depends_on` and XML wrappers.
Add the following to its existing YAML frontmatter, never a second YAML header:

```yaml
kind: code  # or documentation; omitted means code
resources: []  # exclusive ports, databases or other shared mutable resources
acceptance: [AUTH-01]  # defaults to requirements only when the IDs are identical
documentation: [docs/authentication.md]  # exact paths this component completes
checks:
  - [python, -m, unittest, tests.test_authentication]
```

`files_modified` grants exact paths or directory prefixes ending in `/`.
`files_deleted` grants exact files only. A path belongs in one of these fields,
not both. Declarations use Git's exact case/spelling; traversal and globs fail.
Phase records, STATE, PROJECT, REQUIREMENTS, RULES and config are coordinator-owned.
The worker automatically owns its assigned SUMMARY. `requirements` stays nonempty;
`acceptance` covers the phase's identified outcomes. Add `## Documentation` after
the upstream output explaining the assigned documentation or dependent handoff.

Good checks exercise the observable outcome (including a denied request).
Bad checks only assert a file exists when the acceptance concerns access control.
The runtime executes argv lists without a shell. Keep explanatory verification
prose and commands in the upstream task and verification sections too.

`depends_on` drives readiness after integration and checks. `wave` is descriptive;
it does not impose a global scheduling barrier. Overlapping paths/resources
serialize even when `coupling_justified` explains an upstream same-wave coupling.
That upstream advisory exemption cannot override this runtime's isolation gate.
`must_haves` and `user_setup` remain available to the checker and verifier.

The process scheduler dispatches autonomous plans. Non-autonomous/checkpoint plans
remain valid planning artifacts but cannot be launched by `run`. The coordinator
must handle their checkpoint with the human, record the decision in CONTEXT, and
prepare an autonomous continuation; never delete a checkpoint to make a gate pass.
An unresolved external `user_setup` prerequisite is likewise a readiness blocker.

## Produce and validate results

Use the complete `.ai/templates/summary.md` File Template. Keep performance,
accomplishments, task commits, files, decisions, deviations, issues, setup and next
phase readiness. Preserve `requirements-completed`, coverage and other upstream
metadata. Add `acceptance`, `documentation` and `## Checks` naming actual commands,
results, failures/skips and tested revision. `status: complete` is already part of
the upstream template; use `blocked` when incomplete and explain why.

Good evidence names the scenario, command, observed result and revision. Bad
evidence repeats "all requirements satisfied" without demonstrating behavior.
The runtime audits every commit's ownership, clean ancestry, non-summary changes,
coverage and required document existence, then reruns the declared checks.
The independent verifier still establishes whether claims match real behavior.

Use `.ai/templates/verification-report.md` in full. Add the exact assigned
`revision` and the Acceptance, Integration, Documentation and Findings sections.
The runner appends its own source fingerprint/check evidence and attests the
committed report; upstream covered_files/covered_digest remain separate upstream
metadata and cannot substitute for this runtime's attestation. Never invent an
upstream digest or claim it was calculated by an unrun tool.

UAT keeps upstream Current Test, Tests, Summary and Gaps sections, phase identity,
summary source list and timestamps. Runtime case receipts keep every observation,
and previous sessions retain their source and cases. `fail` in the CLI displays
as upstream `issue`. A skipped or blocked case remains unresolved; every required
case needs an actual passing human observation. Source changes invalidate evidence.

## Storage and migration boundary

Project data lives in `.planning/`; reusable instructions, templates and tooling
live in `.ai/`. `.planning/config.yaml` is this Python runtime's execution config.
The complete upstream `.ai/templates/config.json` is an optional upstream template,
not an equivalent config file consumed by this Python runtime.

Local process/checkpoint data remains in the Git common directory under
`ai/phases/`. It is operational data, not a project record in `.ai/`. New checkpoint
keys include the `.planning` phase path. Status fails visibly on legacy `.ai`
project records, legacy IMPLEMENT files and a matching old-path checkpoint rather
than silently reporting no work. Inspect/finish old attempts at their compatible
original revision. Archive inspected checkpoints explicitly before starting a new
attempt; this release does not convert live or historical attempts automatically.

Migration checklist:

1. Inspect old workers, worktrees, commits and checkpoints with their original runtime.
2. Preserve incomplete/unmerged output and establish that writers stopped.
3. Move durable records to `.planning` in an assigned worktree.
4. Reconcile each IMPLEMENT to the full phase-prompt File Template and PLAN name.
5. Commit inputs, configure real checks, run readiness and an independent review.
6. Begin a new attempt; retain old evidence without treating it as current verification.

## Phase numbering boundary

The full upstream roadmap retains decimal insertion examples and instructions.
This Python allocator currently creates and accepts integer phase identifiers
only (NN-slug). Decimal insertion is an upstream method pending a future command
expansion; it is not silently rounded, ignored, or advertised as executable here.
Keep the example guidance in the template. Use an explicitly authorized next
integer phase with recorded dependency decisions for this runtime, or retain the
decimal proposal as a planning artifact until compatible tooling is provided.

`sync` updates only a dedicated Runtime Status section in the full STATE artifact.
Project reference, current position, metrics, accumulated context, deferred items
and session continuity remain coordinator-authored and are never discarded by sync.
