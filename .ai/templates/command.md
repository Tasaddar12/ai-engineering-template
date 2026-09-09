---
tier: contract
authority: agent
description: {{ when_to_use }}
argument_hint: {{ required_inputs }}
---
> Contract: select the linked procedure within existing user authority.

# {{ command_name }}

Use when: {{ trigger }}.

Inputs: {{ required_inputs }}.

Follow [{{ workflow_name }}]({{ workflow_link }}). The workflow owns the
steps; RULES links the owning authority policy.

Return: {{ report_template_and_handoff }}.

<!-- {command}.md. Keep aliases thin; do not duplicate workflow steps.
This is a Markdown entry point, not an installed executable command. -->
