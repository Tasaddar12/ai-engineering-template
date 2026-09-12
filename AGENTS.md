# Agent entry point

This repository is a reusable engineering workflow template. Keep the adopting
project's identity unfilled until onboarding. Create project-specific records
for template maintenance only when the user requests them.

Read [.ai/RULES.md](.ai/RULES.md), [PROJECT](.ai/PROJECT.md),
[STATE](.ai/STATE.md), the selected phase and your [role](.ai/agents/README.md).
Load the selected [command](.ai/commands/README.md) and applicable references.
[Truth map](.ai/truth-map.md) locates each fact's owner.

[Repository skills](docs/AGENT-SKILLS.md) supply focused engineering methods.
Load matching skills and those named in the component's Read first section from
the assigned checkout; do not read every skill body.

Report when asked to report; implement the scope already authorized. Do not ask
again for an approval already supplied. Record consequential decisions in phase
context. When code and documents disagree, establish which side is wrong with
evidence and preserve approved outcomes.

All tracked changes and commits use an assigned immediate-child worktree under
the primary checkout's ignored `.worktrees/`. Verify the absolute root and branch
before writes; follow [worktree](.ai/commands/worktree.md). The primary checkout is
read-only for tracked changes and commits.

Commit completed standalone work and each component's changes and summary with
a nonempty descriptive message before returning. An explicit instruction not to
commit wins. Read-only work needs no empty commit.

The coordinator starts workers; role files do not install a dispatcher. Workers
follow their assigned paths and return evidence. Phase paths stay stable, and
required documentation remains attached to its phase.

Start at [onboard](.ai/commands/onboard.md) and
[phase-status](.ai/commands/phase-status.md). Use
[phase-verify](.ai/commands/phase-verify.md) before publication. Publishing a PR
does not mean delivery: **the runtime never merges**. Preserve unmerged work
and follow the user's explicit delivery boundary.
