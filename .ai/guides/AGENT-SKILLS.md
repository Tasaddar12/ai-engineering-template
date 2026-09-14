# Repository agent skills

These skills give agents reusable methods for recurring engineering work. They
live with the template, so adopting projects and fresh worker checkouts receive
the same guidance.

## Pick the method that fits the assignment

| Skill | When it helps | What it contributes | Result goes to |
|---|---|---|---|
| [codebase-recon](../../.agents/skills/codebase-recon/SKILL.md) | Onboarding or entering unfamiliar code | Trace the affected flow, owners, boundaries and existing checks | Assigned codebase map or concise findings |
| [bounded-research](../../.agents/skills/bounded-research/SKILL.md) | A technical question prevents a sound decision | Check relevant versions, primary evidence, alternatives and uncertainty | Phase RESEARCH or the requested research result |
| [phase-decomposition](../../.agents/skills/phase-decomposition/SKILL.md) | Defining project phases or preparing a substantial phase | Connect outcomes to components, interfaces, dependencies, checks and docs | ROADMAP, CONTEXT and PLAN as appropriate |
| [hypothesis-debugging](../../.agents/skills/hypothesis-debugging/SKILL.md) | A bug, intermittent failure or failing check needs explanation | Use discriminating experiments and retain eliminated hypotheses | Research findings and the assigned repair summary |
| [regression-design](../../.agents/skills/regression-design/SKILL.md) | A repair or behavior change needs convincing checks | Choose an observable oracle that catches the defect and plausible wrong fixes | Assigned tests and actual check evidence |
| [documentation-reconcile](../../.agents/skills/documentation-reconcile/SKILL.md) | Guides or SPECs need updating, or sources disagree | Verify exact claims and identify whether code, documentation or intent needs attention | Assigned documents and coverage in SUMMARY |
| [outcome-verification](../../.agents/skills/outcome-verification/SKILL.md) | Independent phase verification or PR review | Trace acceptance through real producers, consumers and observable results | VERIFICATION or the requested review report |
| [context-handoff](../../.agents/skills/context-handoff/SKILL.md) | Dispatch, a blocked result or interruption would otherwise lose context | Preserve source links, decisions, revision-specific evidence and the next action | PLAN, SUMMARY or an optional pause note |

Select only useful skills. A small repair might need hypothesis debugging and a
regression check; it does not need the entire catalog or a research document.
A documentation-only assignment usually needs reconciliation, not a new phase
decomposition.

## Discovery and use

Codex discovers repository skills in `.agents/skills` from its working directory
through the repository root. It first sees skill names, descriptions and paths;
the selected skill's body is loaded when needed. Each entry is a `SKILL.md` with
a small YAML header containing its name and description. Repository skills need
no personal installation. See the [official skill documentation](https://learn.chatgpt.com/docs/build-skills).

[Installation](../commands/install.md) puts complete skills directly in
`.agents/skills` for Codex and `.claude/skills` for Claude. Each host discovers the
full method there; there are no generated wrappers. All required files travel
with Git. See [Claude skill discovery](https://code.claude.com/docs/en/skills).

For a worker whose method matters to the result, the coordinator lists the
repository-relative skill path in the full PLAN's **read-first/context inputs**,
with a short reason. For example:

```markdown
## Read first

- .agents/skills/hypothesis-debugging/SKILL.md — distinguish the competing
  explanations before changing the retry behavior.
- .agents/skills/regression-design/SKILL.md — retain the original failure and
  check that the repair prevents it.
- The affected source paths, current contract and relevant dependency summary.
```

A worker reads those paths in its own assigned checkout. Commit required skills
before dispatch. Each fresh worker receives its recorded assigned base revision,
including changes already integrated when it starts. Do not rely on a
coordinator's global installation, an uncommitted working copy, or the worker
inheriting the conversation.

Skills are not included in the runtime's phase-input fingerprint, so they are
not frozen to the phase's initial revision. Treat a material change to a required
method as an assignment change: the coordinator reviews affected scope and
reconciles active work before further dispatch. A running worker keeps its
original instructions and checkout; a later worker can receive a newer copy.

Native discovery helps selection; an explicit path also works for another host
that can read Markdown but does not discover repository skills itself. If names
collide with personal or plugin skills, the assignment's exact repository path
identifies the intended instructions. The host adapter must allow the worker to
read its assigned checkout. The phase runtime already supplies that checkout
and the component's instructions; no separate skill registration is needed.

An ordinary request can make the selection explicit:

> Use the repository's hypothesis-debugging skill to investigate this failure,
> then its regression-design skill for the authorized repair's checks.

This does not install a command or start a separate agent.

## How skills fit the workflow

| Layer | Owns | How skills relate |
|---|---|---|
| [RULES](../RULES.md) | Authority, boundaries and required evidence | Methods operate within these rules |
| [Roles](../agents/README.md) | Responsibility and read/write scope | Any assigned role can use a relevant method |
| [Commands](../commands/README.md) | Workflow procedures | A procedure can select a method for a step |
| [References](../references/worker-handoff.md) | Artifact and runtime handoff details | Skills use the existing inputs and result destinations |
| [Phase records](../../.planning/phases/README.md) | Decisions, assignments and durable evidence | Skills place their results in the assigned record |
| [Runtime](../runtime/README.md) | Worker dispatch, integration and recovery | The coordinator starts workers; a skill does not dispatch them |

During onboarding, reconnaissance identifies the real code and checks.
During preparation, bounded research resolves a technical uncertainty and
decomposition turns agreed scope into useful components. The coordinator records
required methods in Read first. Coders use debugging or regression design when
needed; documentors reconcile claims against the integrated behavior. The
independent verifier traces the complete outcome. Handoff guidance keeps the
next worker's context small and specific.

These are methods within the authorized workflow. Full phase-local PLAN
artifacts carry the assignments; selecting a skill
does not itself introduce another lifecycle or approval gate. Do not copy a
skill's method into every component or load every skill body for every worker.

## Folder structure

```text
.agents/
  skills/
    codebase-recon/
      SKILL.md                 Trace relevant existing code and checks
    bounded-research/
      SKILL.md                 Resolve a bounded technical question
    phase-decomposition/
      SKILL.md                 Prepare phase/component boundaries
    hypothesis-debugging/
      SKILL.md                 Find causes through discriminating experiments
    regression-design/
      SKILL.md                 Design checks that expose incorrect behavior
    documentation-reconcile/
      SKILL.md                 Reconcile claims with evidence and intent
    outcome-verification/
      SKILL.md                 Verify the complete observable outcome
    context-handoff/
      SKILL.md                 Preserve the minimum useful continuation context
.ai/guides/
  AGENT-SKILLS.md               This catalog and usage guide
```

Each skill currently needs just one Markdown file. Supporting examples or scripts
belong beside a skill only when they solve a demonstrated recurring need. There
is no separate registry or per-skill tracking file.

## Methods and supporting guidance

The local skills apply focused engineering methods within our phase workflow.
The [template guide](ARTIFACT-GUIDE.md) and [agent catalog](../agents/README.md)
connect them to the complete selected role methods. Local host mappings live in
[agent adaptation](../references/agent-adaptation.md), and attribution lives in
[third-party notices](../THIRD-PARTY-NOTICES.md).

| Supporting method | Useful idea | Application here |
|---|---|---|
| [Skill discovery](#discovery-and-use) and [worker handoff](../references/worker-handoff.md) | Give fresh agents a dependable route to applicable guidance | Use repository discovery and explicit read-first paths; load selected bodies and keep required core/role reading |
| [Researcher](../agents/researcher.md) | Check exact evidence and distinguish unknown from incompatible | Answer the phase's actual technical decision |
| [Phase preparer](../agents/phase-preparer.md) and [phase checker](../agents/phase-checker.md) | Make dependencies, interfaces and executable checks concrete | Prepare bounded phase-local PLAN components using detailed task guidance |
| [Debugger](../agents/debugger.md) and [regression design](../../.agents/skills/regression-design/SKILL.md) | Test explanations and retain a representative failure | Debug within the assignment and design meaningful regression evidence |
| [Document verifier](../agents/doc-verifier.md) and [documentation reconciliation](../../.agents/skills/documentation-reconcile/SKILL.md) | Audit concrete claims and trace their evidence | Apply our fact owners and intent rules; correct the responsible side |
| [Verifier](../agents/verifier.md) and [integration checker](../agents/integration-checker.md) | Existing artifacts are weaker evidence than connected behavior | Trace acceptance to actual execution and distinguish a defect from missing proof |
| [Context handoff](../../.agents/skills/context-handoff/SKILL.md) | Bound each worker's input and retain useful continuation evidence | Use source links and existing summaries without model-specific budget thresholds |

## Keep the skills useful

Maintain engineering methods in the skill, workflow policy in RULES, procedures
in commands, and record mechanics in references. Link to those owners when the
method needs them. Describe concrete selection triggers and observable results;
remove guidance that merely repeats what an agent already knows.

After a skill changes, check its metadata and local links, verify native discovery
when packaging changes, and try it on a representative assignment. A clean parse
proves discovery, not that an agent selected the right method or produced a
correct result. Review the actual output and fix demonstrated weaknesses.

## Full templates, focused methods and later expansion

| Need | Source to load | Result destination |
|---|---|---|
| Author a planning/result artifact | Complete relevant `.ai/templates/` file, including its good/bad examples and consumers | The destination named by the template under `.planning/` |
| Connect an artifact to Python execution | `.ai/runtime/TEMPLATE-CONTRACT.md` | Additive metadata in the same phase artifact |
| Apply a recurring engineering method | Matching `.agents/skills/<name>/SKILL.md` | Assigned map, research, plan, source, summary or report |
| Apply a specialist agent method | `.ai/agents/README.md`, selected full role and `.ai/references/agent-adaptation.md` | Existing assigned record or external review result; respect role boundaries |

The selected specialist roles run through the existing procedures. The coordinator
assigns mapping, research, preparation and independent preparation checking; the
runtime routes code, documentation and phase verification. Documentation writing
uses doc-writer, followed by independent doc-verifier evidence during phase-verify.
Integration checking and code review feed the same assessment when relevant.
The coordinator assigns corrections and repeats affected independent checks.
These role methods do not add command names or install another dispatcher.

When a method is required, put its exact repository path in the full PLAN's
`<read_first>` or context inputs, with the reason it matters. Read it from the
assigned committed checkout. Preserve template guidance rather than replacing
its task-level actions and verification with a generic skill name.
