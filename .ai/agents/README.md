# Agent responsibilities and handoffs

Read [RULES](../RULES.md) and the selected role in full. Assignments narrow
ownership. These are complete methods with local adapters, not registered agent
types or new commands. The [adaptation](../references/agent-adaptation.md)
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
the local scheduling role; documentor remains the runtime entry adapter. Optional
upstream agents for dedicated UI/DOM, security, AI/eval, domain-specific research,
profiling, knowledge-store curation and milestone services are not installed.
Their useful general checks remain in the selected full methods. Pinned external
supporting references do not register those omitted agents or workflows.

[Provenance](PROVENANCE.json) preserves source hashes and reversible adaptations;
[notices](../THIRD-PARTY-NOTICES.md) preserve the license and attribution.
