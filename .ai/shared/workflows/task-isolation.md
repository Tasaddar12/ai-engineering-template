# Task Isolation Reviewer

Runs before dispatch and after every graph rewrite. Inputs: plan/spec acceptance, tasks, repository path inventory, architecture/ADRs, interface/resource claims, estimates, prior graph and failed review evidence when applicable. Output: structured isolation report plus proposed graph patch. It cannot grant permissions or waive acceptance.

## Required checks

| ID | Check | Decision rule |
| --- | --- | --- |
| ISO-01 | Size | One observable outcome, normally 1–3 acceptance checks and at most 6 production files; exceptions need explicit bounded rationale |
| ISO-02 | Clarity | Clear input/output, acceptance command or verifiable evidence, exclusions and owner |
| ISO-03 | Scope | Explicit owned paths; no unspecified broad repository write permission |
| ISO-04 | File overlap | Unordered tasks must have disjoint normalized write paths, including tests/docs/generated files |
| ISO-05 | API/contracts | Shared interfaces have a prerequisite owner and frozen handoff before consumers |
| ISO-06 | Schema/data | Shared DB schema, migrations and data fixtures have named exclusive resource claims |
| ISO-07 | Hidden dependencies | Imports, runtime wiring, package exports, registry and build metadata modeled |
| ISO-08 | Sequencing | Edges are acyclic, all referenced nodes exist, prerequisites supply needed handoffs |
| ISO-09 | Coupling | A task cannot require simultaneous edits to another task's owned surface |
| ISO-10 | Split/merge | Split multi-outcome tasks; merge tiny same-owner tasks when no useful independent acceptance boundary |
| ISO-11 | Shared groundwork | Extract common model/schema/scaffold work before parallel consumers |
| ISO-12 | Coverage | Every plan criterion maps to live task(s), with an integration assertion for cross-task behavior |

Path patterns in v1 are exact files or directory prefixes ending `/`; arbitrary globs are excluded to keep overlap deterministic. Normalize separators, Unicode and case conservatively for Windows. Parent/child directory claims overlap. Read-only references do not create exclusive claims, but a concurrent writer forces sequencing. Semantic resource claims catch conflicts despite disjoint files. Dynamic runtime detection complements design review; a pass is not proof no conflict can occur.

Rewrite choices: split, merge, add prerequisite, sequence, replace. For conflicting same-surface work prefer a prerequisite contract or explicit dependency. A new graph must remap downstream dependencies and acceptance coverage and preserve supersession lineage. Graph review is performed on the complete post-rewrite graph, not just added nodes.

Only the coordinator applies patches. Re-run deterministic checks and a fresh isolation review; no task may implement from a merely proposed graph. Review reports retain task records' content digest and graph revision. The foundation's PLAN-001 report records the actual review performed in this session.
