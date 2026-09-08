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
