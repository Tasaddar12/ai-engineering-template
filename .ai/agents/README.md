# Agent responsibilities and handoffs

Read [RULES](../RULES.md) and the selected role in full. Assignments narrow
ownership. These are complete methods with local adapters. Installation also
provides native host agent definitions; these do not create new runtime commands.
The [adaptation](../references/agent-adaptation.md) defines actual host execution,
source examples and result contracts.

| Role | Dispatched by | Input → result → consumer |
|---|---|---|
| [Coordinator](coordinator.md) | All phase procedures | User intent and evidence → scoped assignments, integration and authorized delivery |
| [Codebase mapper](codebase-mapper.md) | onboard, plan-phase | Assigned focus and revision → committed source map → researcher/preparer |
| [Researcher](researcher.md) | plan-phase, new-milestone, onboard | Bounded technical questions → committed evidence and unresolved choices → orchestrator/preparer |
| [Phase preparer](phase-preparer.md) | plan-phase, quick, verify-work | CONTEXT, research and source → committed bounded PLANs → independent checker |
| [Phase checker](phase-checker.md) | plan-phase, quick | Prepared plans and source → read-only readiness findings → orchestrator/preparer |
| [Coder](coder.md) | execute-phase, quick | One implementation PLAN → committed changes, checks and SUMMARY → orchestrator integration |
| [Doc writer](doc-writer.md) | execute-phase | Owned docs and integrated implementation, or claim failures in fix mode → committed docs/SUMMARY → independent verification |
| [Doc verifier](doc-verifier.md) | verify-work | Exact doc paths and integrated revision → read-only claim results → verifier → writer or coder correction |
| [Integration checker](integration-checker.md) | verify-work | Expected cross-phase connections → read-only wiring and flow evidence → verifier |
| [Code reviewer](code-reviewer.md) | execute-phase, verify-work, ship | Exact changed files, base and revision → read-only classified findings → orchestrator/coder |
| [Debugger](debugger.md) | next, verify-work | Reproduction and assigned failure → diagnosis and regression/fix proposal → orchestrator/coder |
| [Verifier](verifier.md) | verify-work | Integrated acceptance, source and specialist evidence → independent VERIFICATION report → orchestrator correction or publication |

The orchestrator selects the useful responsibilities; a small change need not run
every specialist. The documentation route reads doc-writer directly. The verifier
loads doc-verifier for documentation obligations and integration-checker for
connections.

A fresh code-reviewer separately assesses the changed source before a phase
closes; the verifier cannot substitute for that dispatch, and a coder's
self-check is not a review. Agents never spawn each other — the orchestrator owns
every handoff.

Reviewers return complete results to the orchestrator, which routes false
documentation claims to the writer's fix mode and code defects to an owned coder
assignment, integrates the committed repairs, then asks for current independent
evidence. Required docs and their corrections stay in the same phase. The
[notices](../THIRD-PARTY-NOTICES.md) preserve the license and attribution.

## Dispatching an agent

Spawn by the exact role name above. Resolve the model from the runtime and pass
it inline:

```bash
phase_run query resolve-model <agent> --raw
```

A resolved `inherit` means the project configured no override — omit the model
argument and let the host choose. Pass `model` only when a concrete model came
back. `phase_run query resolve-agent <agent>` returns the same value alongside
the role's declared tools, disallowed tools, turn limit and skills.

**Markdown agent definitions carry no `model:` frontmatter.** Claude no longer
reads a model from there, so it is supplied on the dispatch call instead. Set a
per-agent override in `.planning/config.yaml`:

```yaml
agents:
  coder:
    model: opus
```

## Native host definitions

Codex installation adds one `.toml` file per role beside its complete Markdown
method in `.codex/agents/`. Each defines `name`, `description`, `model` and
`developer_instructions` pointing at the role file; the installer relocates that
path to `.codex/agents/<role>.md`. **Codex's TOML `model` is Codex's own
configuration surface** and is unrelated to the inline injection above.

Claude installation copies the full Markdown agents to `.claude/agents/`.

| Roles | Codex model |
|---|---|
| coordinator, researcher, phase-preparer, coder, debugger | `gpt-5.6-terra` |
| codebase-mapper, phase-checker, doc-writer, doc-verifier, integration-checker, code-reviewer, verifier | `gpt-5.6-luna` |

Edit the installed TOML `model` to customise a Codex role; the host must support
the chosen model. These files do not change the current orchestrator
conversation's model, and they do not start agents on their own.

Formats: [Codex custom agents](https://learn.chatgpt.com/docs/agent-configuration/subagents)
and [Claude Code subagents](https://code.claude.com/docs/en/sub-agents).

See [supporting methods](../references/methods/README.md) for the local reference
catalog and method boundaries.
