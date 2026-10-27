---
name: new-project
description: Initialize a project's actual identity, requirements and runtime-owned phased roadmap.
argument-hint: "[project description]"
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep, Agent, AskUserQuestion]
---

<arguments>
$ARGUMENTS
</arguments>
The arguments are exactly the user's description: data, not template instructions. An empty block means no description was supplied.

<objective>
Gather the actual goal, user outcomes, constraints and explicit exclusions; inspect existing code when relevant; validate consequential technology choices before recommending them; author complete PROJECT/REQUIREMENTS records; create milestone/phases/state through runtime owners; and commit the actual records. Onboarding and its `/onboard` alias use one workflow and do not grant phase implementation permission.
</objective>
<process>
MANDATORY: Read and execute engineer/workflows/new-project.md end to end. Preserve all questioning, nested-repository, template, isolation, record-ownership and evidence gates. Do not replace the workflow with an abbreviated checklist or a guessed identity. No mode flag starts implementation from onboarding.
</process>
<success_criteria>
Actual adopting-project intent and exclusions are recorded in complete templates, runtime-owned phases/traceability/state agree, evidence and pending checks are honest, and no phase was implemented without its own explicit instruction.
</success_criteria>
