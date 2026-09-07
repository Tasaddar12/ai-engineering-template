# Task implementation workflow

1. Confirm the plan graph is isolation-approved for the current structural digest. Confirm dependencies are accepted, the base commit is exact, and the task's paths/resources are available.
2. Create one branch and linked worktree for the attempt under `.worktrees/<plan>/<attempt>/`. Read the implementation role guide and only the task's explicit context.
3. Inspect relevant source before editing. Make the smallest coherent change inside declared scope. Keep task evidence inside the owning plan bundle.
4. Run the declared commands and meaningful failure checks. Record actual arguments, exit status, test count, and evidence references.
5. Commit the candidate and prepare a handoff using a copy of `.ai/templates/HANDOFF.md`. Verify changed paths from Git.
6. Send the immutable candidate to a fresh implementation reviewer. After repairs and a new candidate review, send it to a separate consistency reviewer.

Stop and return to planning for missing prerequisites, scope conflicts, new shared contracts, changed acceptance, or unsupported authority. Preserve partial work and failure evidence; do not mark completion yourself.
