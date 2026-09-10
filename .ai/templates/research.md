---
tier: log
authority: agent
id: RES-{{ nnn }}
question: {{ bounded_question }}
links: []
title: {{ title }}
---
> Log: preserve evidence; append corrections.

# {{ title }}

## Question and scope

What decision needs evidence and the authorized investigation boundary.

## Where the change lands

Relevant files, call paths, surrounding patterns and existing test commands.

## Findings and sources

Sources actually inspected, supported findings and explicit uncertainty.

## Contradictions

| Document / claim | Observed evidence | Uncertainty / next decision |
| --- | --- | --- |
| {{ reference }} | {{ observed }} | {{ uncertainty }} |

## Risks and deferred findings

Link intake for out-of-scope problems. Research identifies contradictions;
the authorized implementor resolves them with the relevant code in view.

## Handoff

What the planner or implementor needs, including targeted checks and limits.
A recommendation is not a requirement or authority.

<!-- RES-{nnn}-{slug}.md. Completed research is evidence, not a contract.
Append a correction rather than silently replacing its premise. -->
