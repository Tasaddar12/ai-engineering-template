# PLAN-001 / TASK-038 attempt a1 implementation handoff

## Candidate identity

| Field | Value |
| --- | --- |
| Attempt | `TASK-038-a1` |
| Branch | `ai/PLAN-001/TASK-038/a1` |
| Logical worktree | `TASK-038-a1` |
| Dispatch/base commit | `a72ffa7fcca3b47205af93f746d240dc9717d296` |
| Candidate commit | The Git commit containing this handoff; its exact OID is reported after commit because a commit cannot embed its own object ID. |
| Approved graph | `PLAN-001-r4`, revision 4 |
| Structural task digest | `c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e` |
| Accepted prerequisite | TASK-004 accepted candidate and handoff, already integrated into the dispatch base |

The candidate changes exactly the three TASK-038-owned paths:

- `src/config.py`
- `tests/unit/config/test_config.py`
- `.ai/plans/current/PLAN-001/evidence/implementation/TASK-038.md`

No schema, task, graph, shared contract, policy, project state, provider-native setting, command
record, or other task-owned source was changed.

## Behavior and acceptance mapping

### TASK-038-AC1

- `load_installation_record(root, *, namespace=None) -> InstallationRecord` discovers exactly one
  tracked `.codex`, `.claude`, or source `.ai` installation. Native provider directories without a
  framework record do not count as installations. Installation, schema, policy, and model files are
  read through checked non-link paths.
- `load_project_settings(root: Path, installation: InstallationRecord) -> ProjectSettings` is the
  frozen service-contract signature. It verifies that the supplied immutable installation equals
  the tracked record, loads the accepted TASK-004 `ContractRegistry`, validates the actual v1 wire
  artifacts, and returns detached frozen values.
- Compatibility requires v1 `schema_version`/`schema_compatibility`; `upgrade_pending` blocks use.
  Installed ownership and manifest paths stay inside the selected provider namespace, source
  foundation uses `.ai`, required policy/model files are project-owned, and framework/project roots
  cannot overlap.
- The model decoder validates provider-specific effort fields, role and policy-profile references,
  consistent ranks for one model ID, namespace/active-provider compatibility, and the invariant that
  `review_high` outranks `implementation` for both configured catalogs and policy ranks.
- Configuration precedence is explicit in `ProjectSettings.resolve_run`: built-in conservative
  defaults, complete project policy, then a run-local restriction. A hydrated `saved` `RunSettings`
  value wins unchanged on resume and cannot be combined with new overrides.
- `RunSettings.to_payload()` and `decode_run_settings(payload)` define an exact closed portable
  encoding for content-addressed persistence without inventing a v1 artifact kind. The decoder
  rejects missing, extra, and invalid fields. `ProjectSettings.effective_policy(...)` applies the
  same resolved snapshot to a detached `ProjectPolicy`; `ProjectPolicy.to_wire()` returns the
  schema-valid effective policy bytes a persistence owner can place behind `workflow-run.policy_ref`.

### TASK-038-AC2

- Unknown top-level/nested wire fields are rejected by `ContractRegistry`. Semantic decoding also
  rejects unknown action names, duplicate/aliased names, unsafe portable paths, ambiguous managed
  namespaces, cross-provider parameter wiring, unresolved model/profile references, mismatched
  configured bindings, and invalid external grants.
- Sensitive actions cannot be classified as autonomous. Run overrides may only reduce numeric
  limits or strengthen sandboxing; they cannot broaden the project policy.
- A policy profile with `configured: false` has no automatic binding even when its schema fields
  retain installer-populated provider/model hints. `ProjectSettings.configured_model(...)` returns
  `None` in that case. `AgentModels.model_for_role(...)` separately exposes the catalog
  recommendation. Provider-native configuration is never read or promoted to verified automatic
  configuration.
- All collections are tuples of frozen values; path/action/provider text is normalized and caller
  mappings are detached. The implementation does not read the process environment, acquire
  credentials, dispatch agents, authorize an action, or mutate policy/configuration files.

## Public interfaces and downstream notes

The bounded public surface is:

- `InstallationRecord`, `ProjectPolicy`, `PolicyModelProfile`, `AgentModels`,
  `ProviderModelProfile`, `ProjectSettings`, `RunOverrides`, and `RunSettings` immutable values;
- `load_installation_record`, `decode_installation_record`, `load_project_settings`, and
  `decode_run_settings` decoders;
- `ProjectSettings.configured_model`, `ProjectSettings.model_for_role`, and
  `ProjectSettings.resolve_run` lookups/resolution, plus `ProjectSettings.effective_policy` and
  `ProjectPolicy.to_wire` for a detached effective policy snapshot;
- `ProjectPolicy.action_requirement` returns `autonomous`, `approval`, or `denied` classification;
  it does not consume a grant or authorize an effect.

TASK-009/034 own persistence and runtime wiring. For resume, they must keep `workflow-run.policy_ref`
pointing to the immutable schema-valid effective policy snapshot, store the closed `RunSettings`
payload through the existing content-addressed `state-event.payload_ref`/evidence mechanism, hydrate
it with `decode_run_settings`, and pass it as `saved`. This task performs none of that IO. The v1
workflow-run schema has no direct `max_parallel`, `max_review_cycles`, or `required_sandbox` field,
so no such field was invented. Approved ephemeral environment bindings remain separate and are not
part of the saved payload.

TASK-006 continues to consume the accepted typed command definition from TASK-002. TASK-038 does not
decode or normalize command `argv`; whitespace, tabs, and newlines in schema-valid fixed arguments
therefore remain under the command contract owner. TASK-017/020 can use `configured_model` to reject
absent or insufficient gate bindings, and TASK-016 can use the normalized refs/model lookups without
reading native settings.

## Actual validation evidence

Working directory: `D:/Codex Projects/ai-engineering-template/.worktrees/TASK-038-a1`.
Interpreter: `D:/Codex Projects/ai-engineering-template/.ai/local/full-plan-venv/Scripts/python.exe`.

| Command | Observed result |
| --- | --- |
| `-m unittest discover -s tests/unit/config/ -p test_*.py` | Exit 0; 27 tests; `OK`. Exact declared task command with the coordinator interpreter. |
| `-m py_compile src/config.py tests/unit/config/test_config.py` | Exit 0. |
| `git diff --check` | Exit 0 after the final source, test, and handoff edits. |

The 27 tests include successful installed/source loads, immutable normalized values, configured and
unconfigured model behavior, native-provider-setting isolation, read-only bytes, run precedence and
saved payload round trips. Failure cases cover unknown fields/actions/profiles, sensitive autonomous
actions, invalid grants, capability ordering, provider parameter crossing, mismatched configured
models, namespace ambiguity, compatibility/upgrade status, unsafe/overlapping paths, stale
installation identity, broader run overrides, sandbox weakening, malformed saved payloads, and
resume combined with new overrides.

## Assumptions, deviations, risks, and reviewer guidance

- The runtime compatibility key is the installation's `schema_compatibility`; framework versions
  must be semantic version strings but are not forced to one exact patch release.
- The action vocabulary is intentionally closed to the documented v1 policy actions. A new policy
  action needs an owned compatibility change rather than silent acceptance.
- An unconfigured policy model's provider/model fields are retained as normalized hints, but only
  `configured_model` is authoritative for automatic dispatch. Manual native invocation evidence is
  separate evidence and cannot change this result.
- RunSettings is an exact non-record payload, not a new schema-backed artifact. Persistence owners
  must hash/store/hydrate it through existing references and preserve the effective policy snapshot.
- There are no scope deviations, source-contract changes, new dependencies, skipped required checks,
  credentials, remote calls, policy changes, or concrete prerequisite blockers. The missing direct
  run fields are handled through existing policy/payload references as directed by the coordinator.
- Reviewers should independently mutate copied provider-native settings, project records, run
  payloads, and caller mappings; confirm no automatic binding or file mutation occurs; verify link,
  traversal, namespace, compatibility, action, profile, capability, and override failures; and bind
  both reviews to the exact committed candidate.

Implementation provenance: the coordinator dispatched this attempt with the standing OpenAI
`gpt-5.6-sol` / `xhigh` selection. This records coordinator-observed native tool configuration only.
No provider-returned effective model ID, effort value, provider invocation UUID, production adapter,
or credential was exposed or claimed.
