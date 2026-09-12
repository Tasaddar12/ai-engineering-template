# Phase-based AI engineering

A reusable workflow for taking a project outcome through discussion, research,
parallel implementation, documentation and independent verification.
Start with [AGENTS.md](AGENTS.md).

A phase keeps decisions and evidence together while giving each coder a small,
explicit assignment. Independent components run in separate worktrees and
integrate into a phase branch. One verified phase normally produces one PR.
**The runtime publishes PRs; it never merges them.**

## What lives where

```text
.ai/
  PROJECT.md          Purpose, success and boundaries
  REQUIREMENTS.md     Desired outcomes and phase mapping
  ROADMAP.md          Phase goals, order and links
  STATE.md            Compact derived progress view
  RULES.md            Shared rules
  config.yaml         Worker routes, concurrency and real checks
  codebase/           Optional maps of existing code
  phases/NN-slug/
    NN-CONTEXT.md             Scope, decisions and authorization
    NN-RESEARCH.md            Findings when needed
    NN-VALIDATION.md          Checking strategy when needed
    NN-01-IMPLEMENT.md        One component's instructions
    NN-01-SUMMARY.md          Its committed result
    NN-02-IMPLEMENT.md        Another component
    NN-02-SUMMARY.md
    NN-VERIFICATION.md       Independent integrated assessment
    NN-UAT.md                Human acceptance when applicable
  specs/              Verified current behavior
  decisions/          Significant rationale
  agents/             Role responsibilities
  commands/           Phase procedures
  references/         Details loaded when needed
  templates/          Artifact examples
  runtime/            Dispatch, integration, recovery and publication
docs/                 Human-facing guides
```

Optional discussion logs and pause notes stay inside the phase. Folders do not
move to indicate status, and components have no separate record lifecycle.

## The working loop

| Step | Result |
|---|---|
| Receive and discuss | CONTEXT with observable acceptance and actual decisions |
| Research if needed | Relevant findings and source evidence |
| Prepare and check | Bounded component instructions, ownership and dependencies |
| Execute | Fresh coder/documentor per ready component |
| Integrate | Checked prerequisite code available to dependent components |
| Verify and correct | Independent evidence for behavior and documentation |
| Accept and publish | Required UAT results and an open verified PR |

The coordinator starts workers. File overlap and exclusive resources serialize
conflicting assignments; a genuine dependency waits for its own integrated result.
An unrelated slow component does not impose a wave barrier.

Documentation obligations travel with the change. Coders can update nearby
explanations, and documentors handle substantial SPECs and guides. Verification
checks the complete outcome rather than merely counting completed components.

## Getting started

1. Follow [onboard](.ai/commands/onboard.md). Keep this template's PROJECT
   unfilled until it is adopted into a real project.
2. Configure the project's actual checks and worker routes in
   [config.yaml](.ai/config.yaml); install the
   [runtime dependencies](.ai/runtime/README.md).
3. Create or reuse an [assigned worktree](.ai/commands/worktree.md), then follow
   [phase-new](.ai/commands/phase-new.md) through preparation and execution.

The [command catalog](.ai/commands/README.md) contains assistant procedures.
Those Markdown files do not register slash commands. The executable interface is
`python .ai/runtime/phase.py`; use its [runtime guide](.ai/runtime/README.md)
for configuration and syntax.

Read the [phase workflow guide](docs/PHASE-WORKFLOW.md) for project onboarding,
agent responsibilities, context handoffs, dependency waves, documentation timing,
conflict handling, recovery and the full annotated folder structure. Use
[onboarding prompts](docs/ONBOARDING-PROMPTS.md) for reusable starting requests,
and [fact ownership](.ai/truth-map.md) for consistency rules.
The [migration reference](docs/PHASE-MIGRATION.md) records this template redesign.

## Validation

Run the Python workflow tests with:

```text
python -m unittest discover -s tests -v
```

Optional advisory hooks have their own Bash suites under `.ai/hooks/`; see
[hook documentation](.ai/hooks/README.md). They warn about common accidents and
do not enforce permissions or provide a sandbox.

Checks use real temporary Git fixtures and simulated worker/forge boundaries
where appropriate. Report actual results and limits rather than assuming a
configured command has passed.
