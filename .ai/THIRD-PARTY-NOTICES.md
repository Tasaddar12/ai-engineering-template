# Third-party notices

The complete adapted agents in `.ai/agents/` derive from [open-gsd/gsd-core](https://github.com/open-gsd/gsd-core/blob/4713ffba761a069bbd79e4833b4bea4e14848388/agents), revision `4713ffba761a069bbd79e4833b4bea4e14848388`. No compact agents are used.

The retained project templates derive from the same MIT-licensed project at
revision `c0b2a05d2f310adc0a1f35fd71fbc9f28f4e4977`; their original adaptation
history is preserved in [upstream Git history](https://github.com/Tasaddar12/ai-engineering-template/commits/main/).
Supporting methods are adapted and bundled in `.ai/references/methods/`;
the table below locates each method. Roles link to these reference files.
They were downloaded from the pinned sources below before adaptation. The local
copies replace external required reading and SDK commands; these provenance URLs
are historical records, not instructions for agents to fetch during assignments.

The supporting method files preserve useful source techniques and examples while
adapting ownership, authorization, task forms, evidence and commands to the local
Python workflow. Unsupported automatic approvals, state mutations, helper tools
and optional services are replaced by explicit local procedures or capability
limits. Installation carries the local documents into either host namespace.

`thinking-models-*.md` also carries the source's attribution to the
[mattnowdev/thinking-partner model catalog](https://github.com/mattnowdev/thinking-partner).
This is attribution, not an additional runtime dependency.

## Worktree isolation provenance

The worktree isolation references derive from
[open-gsd/gsd-core](https://github.com/open-gsd/gsd-core) at revision
`b956bb7`, which is **later** than the `4713ffba` revision the agents and
methods above are pinned to. The worktree work in that project moved
substantially after `4713ffba` — the persisted isolation resolution, orphan
reaping and the Windows path-pin hardening all postdate it — so these files
record their own, newer revision rather than claiming the older pin.

| Bundled local reference | Upstream relative path |
|---|---|
| [references/worktree-branch-check.md](references/worktree-branch-check.md) | `gsd-core/references/worktree-branch-check.md` |
| [references/worktree-path-safety.md](references/worktree-path-safety.md) | `gsd-core/references/worktree-path-safety.md` |
| [references/worktree-recovery-policy.md](references/worktree-recovery-policy.md) | `gsd-core/workflows/execute-phase/steps/worktree-recovery-policy.md` |

The two guard blocks are adapted closely, because they are portable shell with
no upstream tooling dependency: the branch namespaces are respelled for the
branches this runtime and Claude Code actually create, the issue references are
dropped, and the sentinel file is renamed. The recovery policy is upstream
policy prose with its merge-evidence rule extended to name this project's
`worktree.cleanup-wave` behavior.

`.ai/runtime/lib/worktrees.py` is **not** a copy. Upstream implements this as
TypeScript (`src/worktree-safety.cts` and neighbours) behind a Node tool shim;
this project's runtime is Python behind `phase.py`. The module reimplements the
subset this project needs — isolation resolution, fork-base checking, worktree
creation, wave merge with a deletion guard, conservative cleanup, orphan reaping
and health — and keeps upstream's contracts: isolation is a negotiated
capability that fails closed, the orchestrator owns the worktree lifecycle, a
deletion authorization is never inferred from a general scope declaration, and
metadata pruning never removes a checkout that still exists.

It departs from upstream on one point deliberately. Upstream treats isolation as
a preference: `workflow.use_worktrees: false` disables it, and several
conditions (a diverged fork base, a submodule in scope, an unresolvable
capability) degrade to sequential execution. This project requires isolation, so
that setting does not exist here, `none` is not a mode, and those conditions
either raise or warn instead of degrading. The enforcement upstream places in
`hooks/gsd-agent-isolation-guard.js` is served here by
[hooks/worktree-guard.sh](hooks/worktree-guard.sh), which is an independent
implementation reading the dispatch payload rather than a persisted sentinel.

## Bundled method provenance

All entries below originate at revision `4713ffba761a069bbd79e4833b4bea4e14848388`
in the upstream repository's `gsd-core/references/` directory. The table maps
each adapted method's current local location to its original upstream path.
The content is adapted, not an exact source mirror.

| Bundled local method | Upstream relative path |
|---|---|
| [methods/verification-patterns.md](references/methods/verification-patterns.md) | `verification-patterns.md` |
| [methods/checkpoints.md](references/methods/checkpoints.md) | `checkpoints.md` |
| [methods/common-bug-patterns.md](references/methods/common-bug-patterns.md) | `common-bug-patterns.md` |
| [methods/context-budget.md](references/methods/context-budget.md) | `context-budget.md` |
| [methods/debugger-bug-taxonomy.md](references/methods/debugger-bug-taxonomy.md) | `debugger-bug-taxonomy.md` |
| [methods/debugger-fix-acceptance.md](references/methods/debugger-fix-acceptance.md) | `debugger-fix-acceptance.md` |
| [methods/debugger-philosophy.md](references/methods/debugger-philosophy.md) | `debugger-philosophy.md` |
| [methods/debugger-prevention.md](references/methods/debugger-prevention.md) | `debugger-prevention.md` |
| [methods/debugger-rca-branching.md](references/methods/debugger-rca-branching.md) | `debugger-rca-branching.md` |
| [methods/debugger-repro-hardening.md](references/methods/debugger-repro-hardening.md) | `debugger-repro-hardening.md` |
| [methods/debugger-sbfl.md](references/methods/debugger-sbfl.md) | `debugger-sbfl.md` |
| [methods/debugger-semantic-recall.md](references/methods/debugger-semantic-recall.md) | `debugger-semantic-recall.md` |
| [methods/debugger-techniques.md](references/methods/debugger-techniques.md) | `debugger-techniques.md` |
| [methods/execute-mvp-tdd.md](references/methods/execute-mvp-tdd.md) | `execute-mvp-tdd.md` |
| [methods/executor-examples.md](references/methods/executor-examples.md) | `executor-examples.md` |
| [methods/failing-direction.md](references/methods/failing-direction.md) | `failing-direction.md` |
| [methods/few-shot-examples/plan-checker.md](references/methods/few-shot-examples/plan-checker.md) | `few-shot-examples/plan-checker.md` |
| [methods/few-shot-examples/verifier.md](references/methods/few-shot-examples/verifier.md) | `few-shot-examples/verifier.md` |
| [methods/gates.md](references/methods/gates.md) | `gates.md` |
| [methods/honest-verifier.md](references/methods/honest-verifier.md) | `honest-verifier.md` |
| [methods/ios-scaffold.md](references/methods/ios-scaffold.md) | `ios-scaffold.md` |
| [methods/nyquist-compliance.md](references/methods/nyquist-compliance.md) | `nyquist-compliance.md` |
| [methods/plan-checker-examples.md](references/methods/plan-checker-examples.md) | `plan-checker-examples.md` |
| [methods/planner-antipatterns.md](references/methods/planner-antipatterns.md) | `planner-antipatterns.md` |
| [methods/planner-chunked.md](references/methods/planner-chunked.md) | `planner-chunked.md` |
| [methods/planner-coupling.md](references/methods/planner-coupling.md) | `planner-coupling.md` |
| [methods/planner-gap-closure.md](references/methods/planner-gap-closure.md) | `planner-gap-closure.md` |
| [methods/planner-guidance.md](references/methods/planner-guidance.md) | `planner-guidance.md` |
| [methods/planner-interface-context.md](references/methods/planner-interface-context.md) | `planner-interface-context.md` |
| [methods/planner-load-graph-context.md](references/methods/planner-load-graph-context.md) | `planner-load-graph-context.md` |
| [methods/planner-preconditions.md](references/methods/planner-preconditions.md) | `planner-preconditions.md` |
| [methods/planner-quick-batch.md](references/methods/planner-quick-batch.md) | `planner-quick-batch.md` |
| [methods/planner-reversibility.md](references/methods/planner-reversibility.md) | `planner-reversibility.md` |
| [methods/planner-reviews.md](references/methods/planner-reviews.md) | `planner-reviews.md` |
| [methods/planner-revision.md](references/methods/planner-revision.md) | `planner-revision.md` |
| [methods/planner-source-audit.md](references/methods/planner-source-audit.md) | `planner-source-audit.md` |
| [methods/planner-verify-command-grounding.md](references/methods/planner-verify-command-grounding.md) | `planner-verify-command-grounding.md` |
| [methods/research-documentation-lookup.md](references/methods/research-documentation-lookup.md) | `research-documentation-lookup.md` |
| [methods/research-philosophy.md](references/methods/research-philosophy.md) | `research-philosophy.md` |
| [methods/research-verification-protocol.md](references/methods/research-verification-protocol.md) | `research-verification-protocol.md` |
| [methods/security-asvs-levels.md](references/methods/security-asvs-levels.md) | `security-asvs-levels.md` |
| [methods/tdd.md](references/methods/tdd.md) | `tdd.md` |
| [methods/thinking-models-debug.md](references/methods/thinking-models-debug.md) | `thinking-models-debug.md` |
| [methods/thinking-models-execution.md](references/methods/thinking-models-execution.md) | `thinking-models-execution.md` |
| [methods/thinking-models-planning.md](references/methods/thinking-models-planning.md) | `thinking-models-planning.md` |
| [methods/thinking-models-research.md](references/methods/thinking-models-research.md) | `thinking-models-research.md` |
| [methods/thinking-models-verification.md](references/methods/thinking-models-verification.md) | `thinking-models-verification.md` |
| [methods/untrusted-input-boundary.md](references/methods/untrusted-input-boundary.md) | `untrusted-input-boundary.md` |
| [methods/verification-overrides.md](references/methods/verification-overrides.md) | `verification-overrides.md` |
| [methods/verifier-evidence-gate.md](references/methods/verifier-evidence-gate.md) | `verifier-evidence-gate.md` |
| [methods/verifier-phase-gates.md](references/methods/verifier-phase-gates.md) | `verifier-phase-gates.md` |
| [methods/verifier-wiring-patterns.md](references/methods/verifier-wiring-patterns.md) | `verifier-wiring-patterns.md` |
| [methods/verify-command-path-resolvability.md](references/methods/verify-command-path-resolvability.md) | `verify-command-path-resolvability.md` |
| [methods/verify-mvp-mode.md](references/methods/verify-mvp-mode.md) | `verify-mvp-mode.md` |

[templates/milestone.md](templates/milestone.md) derives from
`gsd-core/templates/milestone.md` at revision
`4713ffba761a069bbd79e4833b4bea4e14848388`. Its File Template, structure block,
guidelines and example are the upstream text, reduced to the fields this
project's runtime and complete-milestone workflow actually produce: the task
count and language-specific line count are dropped, the Git range is respelled
for local phase-scoped commit subjects, and the file header matches what
`milestone.complete` writes. The upstream `templates/milestone-archive.md` is
not copied — it describes per-milestone archive files under
`.planning/milestones/`, and this project writes long-form
`{version}-SUMMARY.md` files there from a skeleton the milestone-summary
workflow owns instead.

The PROJECT evolution guidance was reconciled against the source
`gsd-core/workflows/transition.md` and `complete-milestone.md` at template revision
`c0b2a05d2f310adc0a1f35fd71fbc9f28f4e4977`. Its relevant checklist remains in the
local project template; unsupported source lifecycle commands are not copied.
The STATE template's inherited `src/state-md-schema.cts` was inspected at that
same revision; local authoring/sync instructions now describe the actual Python
runtime rather than relying on the external generator. Checkpoint and evidence
methods shared with older templates use the bundled adapted method revision above.

MIT License

Copyright (c) 2026 Open GSD

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
