# Agent responsibilities and handoffs

Read [RULES](../RULES.md) and the selected role in full. Assignments narrow
ownership. These are complete methods with local adapters. Installation also
provides native host agent definitions; these do not create new runtime commands.
The [adaptation](../references/agent-adaptation.md)
defines actual host execution, source examples and result contracts.

| Role | Existing workflow | Input → result → consumer |
|---|---|---|
| [Coordinator](coordinator.md) | All phase procedures | User intent and evidence → scoped assignments, integration and authorized delivery |
| [Codebase mapper](codebase-mapper.md) | onboard, phase-research | Assigned focus and revision → committed source map → researcher/preparer |
| [Researcher](researcher.md) | phase-research | Bounded technical questions → committed evidence and unresolved choices → coordinator/preparer |
| [Phase preparer](phase-preparer.md) | phase-prepare | CONTEXT, research and source → committed bounded PLANs/VALIDATION → independent checker |
| [Phase checker](phase-checker.md) | phase-prepare | Prepared plans and source → read-only readiness findings → coordinator/preparer |
| [Coder](coder.md) | phase-start | One implementation PLAN → committed changes, checks and SUMMARY → coordinator integration |
| [Doc writer](doc-writer.md) | phase-start | Owned docs and integrated implementation, or claim failures in fix mode → committed docs/SUMMARY → independent verification |
| [Doc verifier](doc-verifier.md) | phase-verify | Exact doc paths and integrated revision → read-only claim results → phase verifier/coordinator → writer or coder correction |
| [Integration checker](integration-checker.md) | phase-verify | Expected component/phase connections → read-only wiring and flow evidence → phase verifier/coordinator |
| [Code reviewer](code-reviewer.md) | phase-verify, phase-ship | Exact changed files/base and revision → read-only classified findings → coordinator/coder |
| [Debugger](debugger.md) | phase-resume, phase-verify | Reproduction and assigned failure → diagnosis and regression/fix proposal → coordinator/coder |
| [Verifier](verifier.md) | phase-verify | Integrated acceptance, source and specialist evidence → full independent external report → coordinator correction or publication |

The coordinator selects useful responsibilities; a small change need not run
every specialist. The Python runtime launches code, documentation and verifier
routes from [config](../../.planning/config.yaml). The documentation route reads doc-writer directly. The independent verifier
loads doc-verifier for documentation obligations and integration-checker for
connections, using code-reviewer when relevant. The coordinator can assign fresh
specialists separately through available host capabilities when risk warrants;
workers never spawn each other. Existing procedures own every handoff.

Reviewers return complete results for host capture outside the checkout. The
coordinator returns false documentation claims to the writer's fix mode and code
defects to an owned coder assignment, integrates committed repairs, then asks for
current independent evidence. Required docs and their corrections stay in the
same phase. See the [documentation loop](../references/agent-adaptation.md#documentation-handoff).

Eleven complete, non-compact source agents are adapted here. Coordinator remains
the local scheduling role; documentation assignments read doc-writer directly. Optional
upstream agents for dedicated UI/DOM, security, AI/eval, domain-specific research,
profiling, knowledge-store curation and milestone services are not installed.
Their useful general checks remain in the selected full methods. Bundled local
supporting methods do not register those omitted agents or workflows.

[notices](../THIRD-PARTY-NOTICES.md) preserve the license and attribution.

## Native host models

Codex installation adds one `.toml` file per role beside its complete Markdown
method in `.codex/agents/`. Each defines `name`, `description`, `model` and
`developer_instructions` that tell the agent to read the direct role file in the
assigned checkout. The installer relocates that path to `.codex/agents/<role>.md`.
Claude installation copies the full Markdown agents to `.claude/agents/`, including
the explicit `model` in each file's YAML frontmatter. Legacy `.ai` migration adds
missing defaults to known Claude roles with simple frontmatter, preserving custom
models and instructions. Unusual frontmatter is preserved and reported for manual
model reconciliation.

| Roles | Codex model | Claude model |
|---|---|---|
| coordinator, researcher, phase-preparer, coder, debugger | `gpt-5.6-terra` | `sonnet` |
| codebase-mapper, phase-checker, doc-writer, doc-verifier, integration-checker, code-reviewer, verifier | `gpt-5.6-luna` | `sonnet` |

These are native agent defaults. Edit the installed TOML `model` for Codex or
Markdown `model` for Claude to customize a role; the host must support the chosen
model. The Codex role's Markdown `model` field is Claude metadata: Codex takes its
model from TOML. These files do not change the current coordinator conversation's
model or automatically start workers.

The Python runtime's separate CLI processes still use the routes in
[config](../../.planning/config.yaml). Codex routes pass their explicit `--model`;
the Claude adapter uses the configured Claude CLI model. Native agent model fields
apply when the host selects that native agent, not when a generic CLI session
only reads a role file. Customize runtime routes separately when needed.

Formats: [Codex custom agents](https://learn.chatgpt.com/docs/agent-configuration/subagents)
and [Claude Code subagents](https://code.claude.com/docs/en/sub-agents).
