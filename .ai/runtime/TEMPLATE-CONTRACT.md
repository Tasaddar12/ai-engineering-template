# Full phase templates and the local runtime

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

Good authorization quotes or faithfully records the user's explicit instruction
to implement this phase and its boundary. Keep `approval: pending` for creation,
discussion, research, preparation or design approval alone. Bad authorization
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
Phase records, STATE, PROJECT, REQUIREMENTS, ROADMAP, RULES and config are coordinator-owned.
Every committed deletion must name its exact path in files_deleted, even when a
directory prefix or files_modified otherwise grants ownership.
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
No JSON configuration template is supplied; upstream JSON examples do not
configure this Python runtime.

Local process/checkpoint data remains in the Git common directory under
`ai/phases/`. It is operational data, separate from project records. Checkpoint
keys include the `.planning` phase path.

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

## Native TDD feature plans

A `type: tdd` plan uses a feature-shaped output. Keep its `<feature>` block with
`<name>`, `<files>`, `<behavior>` and `<implementation>`, plus objective, context,
verification, success criteria and output. It does not need artificial `<tasks>`
or an execution_context section; the feature block supplies the task contract.
Add the same local ownership, requirement, acceptance, documentation, argv-check,
autonomy and wave metadata as other plans, and the Documentation handoff section.

The feature block names one behavior small enough for a complete RED/GREEN cycle:

```xml
<feature>
  <name>[One observable behavior]</name>
  <files>[Exact implementation and test paths]</files>
  <behavior>
    [Inputs, expected outputs, boundary cases and the assertion that fails before repair]
  </behavior>
  <implementation>
    [Implementation approach after the failing behavioral check is established]
  </implementation>
</feature>
```

Keep this inside the complete PLAN with the metadata and surrounding sections
listed above. Choose TDD when the behavior has a clear test oracle; a fixture or
infrastructure problem must be diagnosed before it can count as a behavioral RED.

The worker writes and commits a named behavioral test first, runs it and records
why the failure is the expected assertion (RED), then implements and commits the
passing behavior (GREEN). Refactor only to remove duplication introduced by the
change, simplify changed control flow, or satisfy an applicable project convention
in the assigned code. Preserve acceptance behavior and owned paths; do not add
features or clean up unrelated code. After refactoring, rerun the named behavioral
test and affected component checks; record the commands and results in TDD Evidence.
If no listed purpose applies, record `Refactor: not required` in TDD Evidence. A startup
error, fixture failure, zero discovered tests or unrelated assertion is not RED.
Add `## TDD Evidence` to the complete SUMMARY with the command, target test,
expected/actual assertion, exit codes, RED/GREEN commit IDs and refactor outcome.

The Python runtime accepts this structure, requires the evidence section, audits
all commits and reruns final GREEN checks. The independent verifier judges the
RED evidence and intended outcome. This runtime does not implement the imported
Node tool's pre-GREEN evidence verdict or config-driven commit-pattern gate;
those examples remain reference methods, not claims about automatic enforcement.

## Explicitly selected summary variants

The complete `summary.md` is the supplied executable output; compact, minimal,
standard and complex variant templates are not retained. A separately authorized
alternative does not waive integration evidence. Preserve applicable authoring
sections and every named section required by this runtime: Accomplishments,
Task Commits, Files Created/Modified, Decisions Made, Deviations from Plan,
Issues Encountered, User Setup Required, Next Phase Readiness and Checks.
Also include status, requirements-completed, acceptance and documentation metadata.
A combined Decisions & Deviations heading can remain, but it does not substitute
for the separately reviewable named evidence. TDD plans also add TDD Evidence.
Do not replace the complete default with a shorter variant without an explicit
assignment choice; use additional sections, not deleted source guidance.

## Independent component code review

Before integrating a code component, the runner dispatches a fresh code-reviewer
on its committed revision in a separate read-only worktree. The author continues
to run component checks but cannot supply its own independent review. Reviewers
receive the exact base/head, changed paths and a saved diff, including deletions.

The external report preserves the code-reviewer structure and adds exact
`revision` and `diff_base` fields. `findings.critical` and `findings.warning` are
nonnegative integer counts. Summary, Critical Issues and Warnings sections are
required; write `None` for empty findings. Set `status: issues_found` when either
critical or warning findings exist. Integration requires `status: clean` or
`status: issues_found` with `findings.critical: 0`, a successful supervisor receipt and an unchanged
review checkout. `skipped` never satisfies this gate. Reuse is bound to the exact
revision, base and report hash. Findings return to a bounded coder correction,
followed by fresh review. The final phase verifier assesses integrated outcomes
and includes the saved component review evidence.

Set `execution.max_tasks_per_component` to a positive integer to enforce a task
count; null leaves the numeric count uncapped. Native TDD PLANs require exactly
one feature. Set PLAN `review_depth: deep` for security boundaries, concurrency,
shared mutable state or cross-component contracts; otherwise set `review_depth: standard`.
Classify demonstrated defects, unmet acceptance and concrete security/data-loss
risks as critical. Classify advisory robustness improvements without those defects
as warning. Do not downgrade defects to permit integration.

Before verification, commit VERIFICATION frontmatter `warning_dispositions` as a
list of mappings with `component`, `revision` (reviewed commit), `finding` (WR-NN),
`disposition` (`accepted` or `deferred`) and nonempty `reason`. Include exactly one
matching item per advisory warning in the retained component/resolution reports.
Set `status: gaps_found` when creating this record before verification; only a
completed independent verifier can replace it with `status: passed`. The runner
supplies these decisions and reports to the verifier and preserves the decisions
in its output. The verifier must report demonstrated defects as gaps regardless
of the coordinator disposition. Missing decisions block verification.

Retry failed review execution with `resume PHASE --workers-stopped` after process
and checkout inspection. Corrected worker commits must descend from the reviewed
revision and retain the same base and PLAN; preserve prior reports in `review_history`.
Use `verify PHASE --workers-stopped` to capture missing historical reviews. If
that review finds critical defects, integrate a correction component and repeat
the command to capture `review_resolution` against the corrected integrated
revision. The reviewer must name each original critical finding and its resolution
evidence. Retain the original report; source changes invalidate resolution evidence.
