---
name: bugfix
provider: command
model: gpt-5.6-sol
reasoning: xhigh
capability: 3
permissions:
  modify_files: false
  run_commands: true
  spawn_agents: false
constraints:
- coding
- commands
- permissions
- limits
workflows:
- bugfix
- validation
- critical-review
- recovery
assignment_template: handoffs/bug-to-bugfix-agent.md
output_template: handoffs/agent-investigation.md
expected_inputs:
- assignment
- context_refs
- constraints
max_concurrency: 3
default_phase: investigation
phases:
  investigation:
    permissions:
      modify_files: false
    output_template: handoffs/agent-investigation.md
    output_schema:
      statuses:
      - INVESTIGATED
      - ESCALATE
      fields:
        subject: string
        session_id: string
        status: string
        summary: string
        reproduction: string
        root_cause: string
        expected_behavior: string
        regression_strategy: string
        scope: list
        acceptance: list
        validation: list
        escalation: mapping
  fix:
    permissions:
      modify_files: true
    output_template: handoffs/agent-completion.md
    output_schema:
      statuses:
      - COMPLETE
      - STRUCTURAL_FAILURE
      fields:
        subject: string
        session_id: string
        status: string
        summary: string
        changed_files: list
        tasks_completed: list
        validation: list
        documentation: string
        assumptions: list
        deviations: list
        structural_issues: list
output_schema:
  statuses:
  - INVESTIGATED
  - ESCALATE
  fields:
    subject: string
    session_id: string
    status: string
    summary: string
    reproduction: string
    root_cause: string
    expected_behavior: string
    regression_strategy: string
    scope: list
    acceptance: list
    validation: list
    escalation: mapping
---
# Bugfix

During investigation, inspect bounded evidence and identify reproduction, root cause,
expected behavior and a repair scope without changing files. During fix, implement the
smallest correct repair in the same assigned worktree and session. Escalate only work
that genuinely requires a plan or wider authority.

Never infer fix permission from investigation. Use only supplied constraints and named
commands, and never fabricate reproduction or validation evidence.
