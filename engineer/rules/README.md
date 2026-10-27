# Modular rules

Place reusable scoped rules alongside the workflow's agents, references and templates. Read [shared rules](../RULES.md) first; a module cannot weaken authority, isolation, verification, human acceptance or publication gates.

1. Identify one invariant, exact affected paths/operations and owning authority.
2. Read the complete [rule template](../templates/rule.md).
3. State required inputs, actions, outputs, conditions, exceptions and stop gates.
4. Include concrete compliant/violating examples and behavioral evidence.
5. Link the consuming workflow/role; do not create a second owner for the same fact.
6. Follow [Git workflow](../references/git-workflow.md) for commit, issue and PR changes.

Current project-specific policy belongs in the adopting project's approved records or instructions. Reusable template maintenance does not fill project identity or create project execution records without a request.

## Rule catalog and assignment

| Field | Required content |
|---|---|
| Rule ID / file | Stable identity and exact module path. |
| Scope | Exact paths, operations, roles and trigger conditions. |
| Authority | User/project/shared requirement the rule implements. |
| Required reading | Complete named prerequisites and fact owners. |
| Actions / outputs | Concrete obligations and expected evidence. |
| Exceptions / stop | Explicit authorized exceptions and real dependent blockers. |
| Consumers | Workflows/roles that load and enforce the module. |

The coordinator loads the catalog and shared RULES, selects modules by the actual assignment and supplies those exact paths to each worker. Workers read applicable modules before acting and name any missing required module. A missing rule is an explicit input gap, never permission to invent its text or silently ignore its intended obligation. Continue independent scope while requesting the missing owner/path.

When modules conflict, compare actual instruction authority, scope and approved intent. Record the exact incompatible clauses and affected task; resolve through the owning coordinator/user when needed before dependent writes. A local module cannot weaken shared authority, isolation, acceptance or publication. Repair the owning module and affected consumers once the conflict is resolved; do not maintain two contradictory copies or use the more convenient clause without evidence.
