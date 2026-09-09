# Agent assignment

Agent: {{ role }}

Plan and task IDs, or bounded FIX: {{ references }}

Authority: {{ user_decision_reference }}

Worktree and branch: {{ fixed_worktree_and_branch }}

Allowed files and owned specs: {{ exact_scope }}

Prerequisites: {{ completed_dependencies }}

Expected output and return location: {{ report_contract }}

Validation scope: {{ agreed_checks_or_none }}

Return findings to the orchestrator; do not change shared state or widen the assignment.
