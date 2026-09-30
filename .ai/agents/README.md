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
| [Scout](scout.md) | Every non-scout role | Narrow read-only question and revision → cited evidence → assigning role |
| [Verifier](verifier.md) | verify-work | Integrated acceptance, source and specialist evidence → independent VERIFICATION report → orchestrator correction or publication |

The orchestrator selects the useful responsibilities; a small change need not run
every specialist. The documentation route reads doc-writer directly. The verifier
loads doc-verifier for documentation obligations and integration-checker for
connections.

A fresh code-reviewer separately assesses the changed source before a phase
closes; the verifier cannot substitute for that dispatch, and a coder's
self-check is not a review. Worker roles may spawn only `scout` children for
the assigned evidence task. Scouts never spawn children; the orchestrator owns
worker lifecycle, integration, shared records and publication.

Reviewers return complete results to the orchestrator, which routes false
documentation claims to the writer's fix mode and code defects to an owned coder
assignment, integrates the committed repairs, then asks for current independent
evidence. Required docs and their corrections stay in the same phase. The
[notices](../THIRD-PARTY-NOTICES.md) preserve the license and attribution.

## Dispatching an agent

Spawn by the exact role name above. Resolve the model and the effort from the
runtime and pass both inline:

```bash
python .ai/runtime/phase.py query resolve-model <role> --host codex
python .ai/runtime/phase.py query resolve-effort <role> --host codex
python .ai/runtime/phase.py query resolve-agent <role> --host codex
python .ai/runtime/phase.py query resolve-model <role> --host claude
python .ai/runtime/phase.py query resolve-effort <role> --host claude
python .ai/runtime/phase.py query resolve-agent <role> --host claude
```

Use these explicit `--host` forms while working from the source `.ai` tree.
An installed `.codex` runtime infers Codex from its namespace; an installed
`.claude` runtime infers Claude. For example, run
`python .codex/runtime/phase.py query resolve-model <role>` or
`python .claude/runtime/phase.py query resolve-model <role>` from the project
root. The installed runtime accepts `--host` only when it matches its namespace.

A resolved `inherit` means the selected host supplies no explicit value — omit
that argument and let the host choose. The two resolve independently, so a role can
carry an effort and no model, or the reverse. `resolve-agent` returns both
alongside the role's declared tools, disallowed tools and skills.

Worker Markdown definitions carry no `model:` or `effort:` frontmatter; the
`scout` role is the exception and declares `model: haiku` for direct Claude
dispatch. Codex worker model and effort come from native TOML definitions.
Claude worker overrides come from `.planning/config.yaml`; set one there:

```yaml
agents:
  coder:
    model: opus
    effort: xhigh
```

Claude worker model values are host aliases (`opus`, `sonnet`, `haiku`,
`fable`), not full API ids. Codex worker values are read from each role's native
TOML. Effort accepts `low`, `medium`, `high`, `xhigh`, `max` or `inherit`;
unsupported values fail resolution.

**No role caps its turns.** `maxTurns` is deliberately absent: the agents that
used to carry it are the long ones — execution, review, documentation,
verification — and a turn ceiling ends them mid-slice with committed work and no
SUMMARY.md, which reads downstream as a blocked agent rather than a truncated
one. Context, not turns, is what actually bounds an agent here, and
`handoff.context_percent` already bounds that with a handoff that preserves the
work.

## Native host definitions

Codex installation adds one `.toml` file per role beside its complete Markdown
method in `.codex/agents/`. Each defines `name`, `description`, `model`,
`model_reasoning_effort` and `developer_instructions` pointing at the role file;
the installer relocates that path to `.codex/agents/<role>.md`. **Codex's TOML
`model` and `model_reasoning_effort` are Codex's own configuration surface** and
are unrelated to the inline injection above.

Claude installation copies the full Markdown agents to `.claude/agents/`.

| Roles | Codex model | Codex effort |
|---|---|---|
| coordinator, researcher, phase-preparer, coder | `gpt-6.1-sol` | `high` |
| debugger, code-reviewer, verifier, phase-checker | `gpt-6.1-sol` | `high` |
| codebase-mapper, doc-writer | `gpt-6-luna` | `high` |
| doc-verifier, integration-checker | `gpt-6-luna` | `medium` |
| scout | `gpt-6-luna` | `high` |

`scout` is the read-only evidence role. Codex resolves it to
`gpt-6-luna`/`high`; Claude resolves it to `haiku` with effort `inherit` (omit
the effort argument). These values are fixed and ignore `.planning/config.yaml`.
Read [scout dispatch](../references/scout-dispatch.md) for its assignment,
result, waiting and fallback procedure.

Edit the installed TOML `model` or `model_reasoning_effort` to customise a Codex
role; the host must support the chosen model and effort. These files do not
change the current orchestrator conversation's model, and they do not start
agents on their own.

Formats: [Codex custom agents](https://learn.chatgpt.com/docs/agent-configuration/subagents)
and [Claude Code subagents](https://code.claude.com/docs/en/sub-agents).

See [supporting methods](../references/methods/README.md) for the local reference
catalog and method boundaries.
