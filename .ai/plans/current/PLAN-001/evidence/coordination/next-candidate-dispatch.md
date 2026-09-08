# TASK-019 coordination reminders

Own candidates.py, reviews_candidates test leaf and TASK-019 handoff. Consume
accepted001 values and004 contracts only; do not add undeclared imports of Git,
workflow or orchestration services. Read the exact candidate v1 schema, including
task_id=None for a plan candidate and both full Git object ID widths. Algorithm
inputs/output may be immutable values or schema-shaped frozen artifacts; downstream
owners can translate them into their own predeclared port DTOs without changing
v1 fields or requiring a reverse dependency.

Deterministically bind exact base/head, binary diff bytes, graph revision and
required graph/spec/ADR/contract/handoff context, validation bytes, policy/model
inputs and checklist version. Hash actual supplied immutable bytes and document
where upstream verified Git/content observations enter; do not claim a pure hash
operation inspected Git. Validate the emitted v1 record. Input ordering and
duplicate/alias handling must be explicit rather than accidentally depending on
mapping insertion order or local file enumeration.

Avoid self-referential hashes: validation happens before final candidate creation,
and fingerprint excludes itself. A task candidate and a plan integration candidate
use the same schema with the appropriate task identity. Recompute/verify a
candidate against current material inputs and reject every changed component;
missing evidence, stale hashes or caller mutation cannot be interpreted as a match.
Preserve raw content bytes where that is the contract, including line endings.

Test deterministic repeated construction, defensive input freezing, each material
input independently changed, malformed/full-width OIDs, missing/aliased references,
task versus plan identity, registry validation and no self-reference. Keep review
gate policy, actual Git/command execution, context discovery and storage outside
this algorithm owner. Return concrete prerequisite gaps instead of editing others.

## Open review question: applicable context roles

The current owner-final CandidateContext constructor requires nonempty ADR and
handoff collections unconditionally. Independently reconcile this with a first
dependency-free task and a plan having no ADRs. The approved graph's TASK-001
has no dependencies, and its accepted v1 candidate is valid without dependency
handoff material. The candidate schema requires nonempty aggregate context_refs,
not a fabricated artifact in every role. Determine whether the constructor can
represent all required review cases while rejecting genuinely missing applicable
context. Prove a concrete typed case using actual task/plan inputs and cite the
frozen requirements; do not invent placeholder handoffs or impose an unowned
context-discovery service. This is a coordinator question for fresh R1/R2, not a
review verdict or permission to change another task's source.
