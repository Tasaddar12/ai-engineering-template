# Agent model defaults

Every role has an explicit default for both OpenAI and Anthropic in `.codex/project/agent-models.json`. The installer copies `docs/defaults/AGENT_MODELS.json` to that project-owned file and selects `active_provider` for the requested assistant. Both provider maps remain available. These are editable workflow defaults; the bootstrap does not dispatch agents, register native subagents, or change the model of an ordinary ChatGPT conversation.

## Default profiles

Verified against official documentation on 2026-09-07. Role assignments are this toolkit's recommendations, not provider benchmarks.

| Profile | OpenAI model / reasoning effort | Anthropic model / effort |
| --- | --- | --- |
| `research` | `gpt-5.6-luna` / medium | `claude-haiku-4-5-20251001` / omitted |
| `operations` | `gpt-5.6-terra` / medium | `claude-sonnet-5` / medium |
| `implementation` | `gpt-5.6-terra` / high | `claude-sonnet-5` / high |
| `implementation_escalated` | `gpt-5.6-sol` / xhigh | `claude-opus-5` / high |
| `planning` | `gpt-6-astra` / xhigh | `claude-opus-5` / high |
| `review_high` | `gpt-6-astra` / xhigh | `claude-opus-5` / high |
| `recovery` | `gpt-6-astra` / xhigh | `claude-opus-5` / high |
| `review_escalated` | Keep Astra; no higher default is declared | `claude-fable-5-1` / high |

OpenAI identifies [Astra](https://developers.openai.com/api/docs/models/gpt-6-astra) as its strongest model and [Terra](https://developers.openai.com/api/docs/models/gpt-5.6-terra) as balancing capability and cost. [Luna](https://developers.openai.com/api/docs/models/gpt-5.6-luna) is suited to inexpensive bounded collection and summarization; [Sol](https://developers.openai.com/api/docs/models/gpt-5.6-sol) is the development escalation.

Anthropic's [model comparison](https://platform.claude.com/docs/en/models/overview) supports using Haiku for inexpensive work, Sonnet for routine development, and Opus for more demanding reasoning. [Fable 5.1](https://platform.claude.com/docs/en/models/fable-5-1/overview) is reserved here for escalated review or cases where Opus is insufficient.

Effort controls remain provider-specific. OpenAI `reasoning_effort` maps to the host's reasoning setting (or `reasoning.effort` in the Responses API). Anthropic `effort` maps to the supported host setting (or `output_config.effort` in the API). Null means omit the parameter; Haiku does not support the effort control. Do not send OpenAI parameters to Claude or assume equal effort names imply equal compute. See [Claude effort](https://platform.claude.com/docs/en/build-with-claude/effort).

## Every role

Use the named profile under `providers[active_provider].profiles`. Each `roles[role]` entry has independent OpenAI and Anthropic profile selections, so either provider can be overridden without changing the other.

| Role | Default profile for both providers |
| --- | --- |
| [coordinator](../agents/coordinator.md) | `planning` |
| [context-curator](../agents/context-curator.md) | `research` |
| [repository-analyst](../agents/repository-analyst.md) | `operations` |
| [researcher](../agents/researcher.md) | `research` |
| [evidence-reviewer](../agents/evidence-reviewer.md) | `review_high` |
| [requirements-author](../agents/requirements-author.md) | `planning` |
| [architecture-author](../agents/architecture-author.md) | `planning` |
| [planner](../agents/planner.md) | `planning` |
| [task-isolation-reviewer](../agents/task-isolation-reviewer.md) | `review_high` |
| [git-worktree-operator](../agents/git-worktree-operator.md) | `operations` |
| [implementer](../agents/implementer.md) | `implementation` |
| [validation-agent](../agents/validation-agent.md) | `operations` |
| [security-reviewer](../agents/security-reviewer.md) | `review_high` |
| [implementation-reviewer](../agents/implementation-reviewer.md) | `review_high` |
| [consistency-reviewer](../agents/consistency-reviewer.md) | `review_high` |
| [integrator](../agents/integrator.md) | `implementation` |
| [plan-integration-reviewer](../agents/plan-integration-reviewer.md) | `review_high` |
| [recovery-replanner](../agents/recovery-replanner.md) | `recovery` |
| [documentation-author](../agents/documentation-author.md) | `research` |
| [adoption-upgrade](../agents/adoption-upgrade.md) | `implementation` |
| [delivery-agent](../agents/delivery-agent.md) | `operations` |
| [archive-agent](../agents/archive-agent.md) | `operations` |

The aliases in the [agent index](../agents/README.md) inherit the model of their canonical role. Validation agents run commands and report facts; accepting a candidate belongs to the independent review roles.

## Applying and overriding defaults

1. Read only the active role's mapping and selected provider profile. Explicit user choices override defaults. For example, a requested Sol/xhigh correction uses `implementation_escalated`; it does not silently replace every future development default.
2. Verify that the actual host/account offers the model, effort, required tools, and context. The published model catalog is not proof of account access. Use exact IDs when supported; ordinary ChatGPT users select an available model manually.
3. New installations prefill the four gate profiles in `project/policy.json` from `policy_profile_map`, with `configured: false`. Before a gate, reconcile the policy provider, model ID, and rank with the actual invocation, then set `configured: true` only after verification. Defaults are recommendations; policy records the verified gate configuration. Repeat installation preserves edits to both files and does not resynchronize them.
4. Record actual model and effort in the handoff/review evidence. Never substitute the configured expectation for observed provenance. Explicit user overrides must also be reflected in the applicable gate profile before that gate is accepted.

The numeric capability ranks are this project's ordered model tiers within each provider, not cross-provider benchmark scores. Research is rank 1; routine development is rank 2; Sol and Opus are rank 3; Astra and Fable are rank 4. Assign one consistent rank to each model. A higher effort on the same model does not raise its rank.

## Escalation and cost control

Keep research bounded to the selected question, retrieve primary sources, and hand consequential claims to the evidence reviewer. Escalate uncertain synthesis instead of allowing inexpensive research output to establish architecture or acceptance.

Escalate implementation to `implementation_escalated` after repeated substantive failures or a demonstrated reasoning gap. Reduce the task's context and check its scope before retrying. Record why the escalation is needed.

Review must remain independent and use a rank strictly above the model that actually implemented the candidate. If Claude implementation escalates to Opus, change the affected reviewer mappings and the `review_high` policy profile to `review_escalated` (Fable) before review. Sol implementation can keep Astra review. If implementation reaches the highest verified tier and no higher review model is available, stop that gate for an explicit policy decision; do not inflate ranks or silently downgrade the review.

A missing model does not authorize a different provider or additional paid access. Reconfigure to an available model only within existing authority, keep the gate's required separation, and record the change. Recheck model IDs and availability when upgrading the toolkit; retain existing project choices until deliberately updated.
