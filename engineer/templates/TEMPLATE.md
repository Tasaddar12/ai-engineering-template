# Complete template use

Read the entire template before authoring an artifact, including guidance, examples, producer and consumer notes. Preserve every required section and frontmatter field; use an explicit None / not applicable with a reason when a section has no content. Do not replace a complete template with a compact variant or a summary of its requirements.

## Authoring sequence

1. Identify the artifact in [the registry](README.md) and read its complete template.
2. Read the producing workflow and each consuming schema or parser.
3. Separate runtime-owned structures from authored narrative. Use `engineer_run query` for runtime-owned changes; write narrative only in its owning artifact.
4. Fill concrete paths, identifiers, statuses, commands and evidence. Remove instructional placeholders from current records.
5. Check required keys, matching phase/plan identity and producer-consumer consistency. Record checks actually run; pending evidence stays pending.
6. Return the artifact, revision, limitations and first continuation step to the coordinator.

## Connect a template to the Python runtime

| Concern | Template author | Runtime owner | Boundary |
|---------|-----------------|---------------|----------|
| Identity and metadata | Declare required keys and enum values | Parse and validate current records | Do not infer missing current metadata from prose |
| Project data | Explain purpose and examples | Initialize and update owned structures | Keep adopting identity blank in reusable templates |
| PLAN | Preserve acceptance, documentation, checks argv and issue_refs | Validate identity, dependencies and ownership | Deletion paths are explicit, never implied |
| Configuration | Document defaults and effect | Read YAML and supply supported defaults | Do not invent tests or silent success defaults |
| Waves | Explain declared planning labels | Form groups from dependencies and overlap | Labels do not exempt shared ownership |
| Source versus current records | Keep placeholders in templates | Reject unresolved placeholders in current records | Do not mistake examples for actual evidence |
| Checkpoints | Preserve answer/resume fields | Route only authorized automation | Never infer human acceptance |
| Verification | Preserve revision, coverage and v4 digest | Fingerprint and validate receipts | Missing evidence remains a gap |
| Completion | Preserve goal and handoff fields | Reconcile authorized bookkeeping | Completion does not authorize the next phase |
| Publication | Preserve exact PR evidence | Coordinator publishes after gates | Merge requires the user's instruction |
| Optional artifacts | Explain applicability | Validate only when produced/required | Optional rationale does not own decisions |
| Recovery | Preserve completed, remaining and dirty paths | Session/handoff state | Confirm worker stop before reassigning paths |

## Handoff checklist

- Exact input and output revisions, repository, branch and owned paths.
- Completed outcomes and committed changes; distinguish partial or dirty work.
- Remaining work, missing inputs, failed gates and uncertain process state.
- Exact checks with observed outcomes; label not run or not configured honestly.
- First bounded continuation and its owner; preserve pending human decisions.

| Weak handoff | Useful handoff |
|--------------|----------------|
| Everything done | Commit SHA, exact outcomes, evidence and remaining items |
| Tests fine | Tested SHA, exact argv, exit status and evidence path |
| Continue later | First dependent step, preconditions and owner |
| Need approval | Exact unresolved choice, alternatives, impact and authorization source |
| Updated docs | Paths, changed contract and consumer checks |

Reusable instructions belong in `engineer/`; adopting-project records belong in `.planning/`. See [runtime integrity](../references/template-contract.md#planning-record-integrity).
