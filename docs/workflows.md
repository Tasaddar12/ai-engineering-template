# Streamlined workflows

| Entry | Steps | Outputs |
| --- | --- | --- |
| Project init/adopt | Inspect target, preflight paths, seed missing configuration | STATE, models, constraints, roles/templates |
| Research | Define question, collect dated evidence, preserve uncertainties | Research Markdown, optional ADR |
| Plan create/implement | Plan/tasks, decomposition, checked feature DAG, schedule batches | Plan/tasks/features, decomposition handoff, run journal |
| Feature (internal) | Worktree, implementation, validation, critical review, repair, PR | Assignment/completion/review handoffs, validation evidence, PR body |
| Bug fix | Investigation/root cause, fix worktree, regression/fix, validation, critical review, PR | Bug and focused handoffs; substantial changes become plan |
| Recovery (internal) | Diagnose structure, revise/supersede, decompose, resume | Reasoned recovery handoff, lineage/revised graph |
| Merge/cleanup | Observe merge, complete artifacts, update index, remove eligible tree | Git observation, completion handoff, preserved history |

Decomposition groups tasks by coherent ownership, bounded effort and shared interfaces; it splits oversized work, merges tiny tasks, adds prerequisites and revises dependencies. Exact task coverage and both DAGs must pass before launch. Shared path roots or schema/API resources cannot be used by concurrent batches.

Each implementation receives its role, feature/tasks, allowed/prohibited paths, explicit context references, dependency handoffs, acceptance criteria, validation commands and constraints. It inspects code first, tests meaningful behavior and documents changes. Repairs reuse its session and structured issue artifact. One reviewer receives the full updated diff, acceptance criteria, completion handoff and actual validation. Verdict: PASS or CHANGES_REQUIRED; categories: correctness, security, documentation. Each issue states location, explanation, required change and validation. Preserve every iteration.

Ordinary defects stay in the repair loop. Wrong boundaries, prerequisite gaps, conflicts, substantial expansion or recurring structural failures invoke recovery. Preserve branches/evidence, validate replacement lineage and dependencies, then redecompose. Budgets prevent endless loops; exhausted or nonrecoverable work stays visibly blocked.

Managed checkouts live under `.worktrees/`. Persist branch/worktree intent before dispatch; check actual branch/head on resume. Cleanup requires a registered clean managed tree with no active owner plus merge confirmation or explicit supersession/abandonment; retain branch/audit reason. Preserve unknown, locked, dirty, escaped or ambiguous worktrees. Age is never evidence. Dependencies require code on the base, not just review approval.
