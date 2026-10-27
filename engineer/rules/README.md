# Modular rules

Place reusable scoped rules alongside the workflow's agents, references and templates. Read [shared rules](../RULES.md) first; a module cannot weaken authority, isolation, verification, human acceptance or publication gates.

1. Identify one invariant, exact affected paths/operations and owning authority.
2. Read the complete [rule template](../templates/rule.md).
3. State required inputs, actions, outputs, conditions, exceptions and stop gates.
4. Include concrete compliant/violating examples and behavioral evidence.
5. Link the consuming workflow/role; do not create a second owner for the same fact.
6. Follow [Git workflow](../references/git-workflow.md) for commit, issue and PR changes.

Current project-specific policy belongs in the adopting project's approved records or instructions. Reusable template maintenance does not fill project identity or create project execution records without a request.
