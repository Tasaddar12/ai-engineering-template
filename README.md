# Minimal AI project contracts

A small, Markdown-first draft for recording intent, planning changes, explaining
choices and describing the current project. Start at [AGENTS.md](AGENTS.md).

- [Rules of engagement](.ai/RULES.md)
- [One owner per fact](.ai/truth-map.md)
- [Paths and file IDs](.ai/config.yaml)
- [Now / Next / Blockers](.ai/state/STATE.md)
- [Workflows](.ai/workflows/README.md) and [command entry points](.ai/commands/README.md)
- [Research records](.ai/research/README.md)
- [Firm policies](.ai/policies/README.md) and [PASS/FAIL gates](.ai/gates/README.md)
- [Project context](.ai/state/PROJECT.md)
- [Eight agent roles](.ai/agents/README.md)
- [Current project specification](.ai/specs/SPEC-001-project-contracts.md)
- [Draft plan and delivery scope](.ai/plans/review/PLAN-001-minimal-ai-contracts.md)

The requested folder structure lives entirely under `.ai`. Templates are flat;
agent definitions and basic workflows are short Markdown documents. Policies own
requirements, gates check transitions, and research keeps evidence separate from decisions. Empty lifecycle
folders use `.gitkeep` so they survive a clone.

This branch contains documentation and configuration only. It has no application,
package installer, automatic agent dispatcher or installed Git/CI hooks. Hook checks
are manual conventions until a separately approved implementation adds enforcement.
