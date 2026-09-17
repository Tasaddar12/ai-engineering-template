# Third-party notices

The complete adapted agents in `.ai/agents/` derive from [open-gsd/gsd-core](https://github.com/open-gsd/gsd-core/blob/4713ffba761a069bbd79e4833b4bea4e14848388/agents), revision `4713ffba761a069bbd79e4833b4bea4e14848388`. No compact agents are used.

The retained project templates derive from the same MIT-licensed project at
revision `c0b2a05d2f310adc0a1f35fd71fbc9f28f4e4977`; their original adaptation
history is preserved in [upstream Git history](https://github.com/Tasaddar12/ai-engineering-template/commits/main/).
Supporting methods are adapted and bundled in `.ai/references/methods/` or in
their consuming role sections; the table below locates each method.
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
| [researcher: Documentation lookup](agents/researcher.md#documentation-lookup) | `research-documentation-lookup.md` |
| [researcher: Research philosophy](agents/researcher.md#research-philosophy) | `research-philosophy.md` |
| [researcher: Research verification protocol](agents/researcher.md#research-verification-protocol) | `research-verification-protocol.md` |
| [methods/security-asvs-levels.md](references/methods/security-asvs-levels.md) | `security-asvs-levels.md` |
| [methods/tdd.md](references/methods/tdd.md) | `tdd.md` |
| [methods/thinking-models-debug.md](references/methods/thinking-models-debug.md) | `thinking-models-debug.md` |
| [methods/thinking-models-execution.md](references/methods/thinking-models-execution.md) | `thinking-models-execution.md` |
| [methods/thinking-models-planning.md](references/methods/thinking-models-planning.md) | `thinking-models-planning.md` |
| [researcher: Research decision models](agents/researcher.md#research-decision-models) | `thinking-models-research.md` |
| [methods/thinking-models-verification.md](references/methods/thinking-models-verification.md) | `thinking-models-verification.md` |
| [researcher: Untrusted-Input Boundary](agents/researcher.md#untrusted-input-boundary) | `untrusted-input-boundary.md` |
| [methods/verification-overrides.md](references/methods/verification-overrides.md) | `verification-overrides.md` |
| [methods/verifier-evidence-gate.md](references/methods/verifier-evidence-gate.md) | `verifier-evidence-gate.md` |
| [methods/verifier-phase-gates.md](references/methods/verifier-phase-gates.md) | `verifier-phase-gates.md` |
| [methods/verifier-wiring-patterns.md](references/methods/verifier-wiring-patterns.md) | `verifier-wiring-patterns.md` |
| [methods/verify-command-path-resolvability.md](references/methods/verify-command-path-resolvability.md) | `verify-command-path-resolvability.md` |
| [methods/verify-mvp-mode.md](references/methods/verify-mvp-mode.md) | `verify-mvp-mode.md` |

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
