# Current PLAN-001 implementation briefing

This is manual development coordination of the complete 39-task offline MVP. It is
session guidance, not product code, and must not be copied into the runtime payload.

Use only your dispatched task worktree and declared task write scope. Read its
.ai/AGENTS.md, README/STATE, task, selected spec, relevant explicit references,
docs/agents/implementer.md, frozen service contracts, and accepted dependency
handoffs. The approved graph is r4; do not modify structural graph/task fields or
shared contracts. Report a concrete prerequisite gap to the coordinator rather
than repairing another task's module or inventing alternate public semantics.

Implementation model/effort selected by standing user preference: gpt-5.6-sol,
xhigh. Record coordinator-observed native tool configuration honestly; separate
this from provider-returned observations. No actual production provider adapter is
configured or required in this deterministic fake agent/hosting MVP.

Keep source as explicit flat src/*.py modules, typed immutable request/results with
shared values/errors and Protocol boundaries. Do not create a package wrapper,
central registry, exports, or shared fixture outside the declared scope. Interface
owners should check required downstream service semantics before freezing fields.
Service-specific DTOs may refine the frozen signatures but must not invent fields
in the serialized v1 schemas. Existing linked evidence supports effort provenance;
see .ai/plans/current/PLAN-001/evidence/effort-provenance-clarification.md.

Production-facing methods should consume their actual typed port contracts, not
parallel dict-only APIs. Treat mutable caller inputs as untrusted, validate identity
and expected generation/revision, preserve explicit ambiguous/cancelled states,
and do not interpret missing evidence as success. Derive behavior from the task
and accepted contracts rather than implementing every adjacent component.

Use argument arrays and shell=False; no remote calls, credentials, publication,
force cleanup, reset, or changes to project-owned/native configuration. Default
fresh installation roots are .codex (OpenAI) or .claude; this repository retains .ai.
Reusable material remains in docs/agents, docs/templates, docs/workflows/defaults.

Validate the exact declared test command with the coordinator venv:
D:/Codex Projects/ai-engineering-template/.ai/local/full-plan-venv/Scripts/python.exe.
Tests must import this worktree's src rather than the editable venv's root src.
Meaningful acceptance and failure-case tests are required, with a nonzero observed
count. Avoid repeating unrelated suites after focused checks pass without a reason.
Parent tests/unit and tests/e2e have no __init__.py; do not create unowned parent
files. Task leaf discovery is authoritative until TASK-037 owns aggregate wiring.

Record changed paths, exact base/commit identity, actual commands/results,
acceptance mapping, public signatures/dependency notes, assumptions and risks in
only the declared implementation handoff path. Historical/review/evidence bytes
are exact via .ai/.gitattributes. Preserve existing history.

Commit a clean candidate, verify Git state, and send FINAL only when all edits have
stopped. Do not send an early ready message and then keep editing. Coordinator
will merge current integration metadata, run declared validation independently,
freeze a candidate and obtain one independent Astra/xhigh task review under the
[user's single-stage decision](single-stage-review-decision.md). Scoped fixes get
current validation and focused independent verification, with a new exact-candidate
report. Do not self-approve or merge. Final combined reviews follow implementation.

## Local persistence port reminder for TASK-002 and TASK-009

Read .ai/shared/state/persistence.md and service-contracts.md together. Events
are typed transaction values carrying EntityId; the state-event v1 schema has no
plan_id field. Project initialization before any plan must remain representable.
Do not require a plan-qualified RecordRef for each journal event or invent a plan
for zero-plan initialization. StateStore journals events internally and returns
EvidenceRefs; plan-owned record lookup remains qualified. This is the previously
reviewed zero-plan advisory, not an extra wire-schema field.

Projection updates must express lifecycle relocation old/new logical locations,
reference updates and manifest effects in one generation. Allocate operation ID
once, deduplicate after restart, and preserve expected generation. Concrete
state implementation owns its OS-backed Git-common-directory lock and isolated
staging/CAS checkpoint; the interface-only task must leave these behaviors
representable without doing IO itself. Read actual downstream task acceptance
before freezing mandatory fields.

For TASK-002 command DTOs, inspect the actual command-definition.schema.json
and command-evidence.schema.json names/fields. cwd_rule includes project,
worktree and control; cwd_relative must represent the selected root itself
(e.g. '.') without weakening ScopePath's distinct scope-claim rules. Keep local
bindings separate from portable evidence. Command definitions are typed values
in CommandRequest per the frozen service contract; do not force every internal
project setup command into a fabricated plan solely to build the request.

## Payload text and command arguments

Preserve fixed argv values byte-for-byte through configuration, requests, and
execution. Evidence may apply its documented secret redactions, while retaining
all other argument contents. Arguments can legitimately contain newlines, tabs,
or significant surrounding whitespace. Metadata-label validators must not be reused
for arbitrary payload text. Apply actual schema item constraints and executable
safety constraints separately; never silently strip or rewrite an argument. TASK002
R1 confirmed a concrete instance of this defect; future TASK006/018
consumers must use the finally accepted port implementation and prove preservation.

## Minimum-version validation runtimes

Project-local Python3.11.16 with declared jsonschema4.26.0 is available on both hosts:
Windows ROOT/.ai/local/full-plan-py311-venv/Scripts/python.exe;
Linux /mnt/d/Codex Projects/ai-engineering-template/.ai/local/full-plan-linux-py311-venv/bin/python.
Use Linux through WSL Ubuntu-24.04 --exec and exact candidate cwd. Use these for
meaningful minimum-version checks or final packaging; do not repeat unrelated
suites after they pass. Existing Python3.12 environments remain the declared
coordinator test default. No remote CI execution is implied by local WSL testing.

## Required project material

Current user instruction: every required runtime helper, regression test and reusable
usage instruction must be versioned in its task-owned source, tests or canonical
docs. A private helper invoked by product code is part of the runtime closure.
No required behavior may depend on ignored .ai/local, a session script, an editable
root install or an untracked fixture. Keep local material only for disposable
execution/cache; give new helper files a concrete purpose and reuse existing tools.
Report useful local discoveries and their tracked disposition in the task handoff.
See the tracked coordination README and local-material-audit.md for this plan's
manual tools; those are not installed product dependencies.
