# Verify and correct a phase

Read [RULES](../RULES.md), CONTEXT, component summaries, current contracts and
the actual integrated code. Use the assigned clean integration worktree.

```text
python .ai/runtime/phase.py verify 01-authentication
```

For assigned TDD plans, first complete the coordinator's
[end-of-phase TDD review](../references/methods/tdd.md#end-of-phase-tdd-review-checkpoint):
triage per-plan RED/GREEN/REFACTOR evidence and gate violations automatically.
Every row MUST produce a next action: sufficient required evidence MUST auto-pass
without a human prompt and proceed immediately to independent verification;
missing required evidence MUST trigger a bounded automated reproduction or
correction, followed by the affected checks. Preserve original history and never
invent retrospective RED evidence. Preserve explicit test deferrals as missing
evidence. This coordinator review is not a user survey, a permission request or
a stopping point; it does not replace independent verification and is not
automatically performed by the runner. Only an actually assigned human-only
acceptance check follows UAT; template checkpoint wording does not create one.

The runtime dispatches the independent [verifier](../agents/verifier.md). It
checks phase acceptance, component connections, regressions and documentation at
the assigned revision. The host saves the report externally while the checkout
stays unchanged; the coordinator audits, stores and commits VERIFICATION.

Component code reviews are required before integration and retained in the final
verification report. They do not replace assessment of integrated behavior.
Dispatch a separate specialist when existing evidence leaves any of these questions unresolved:

- Assign [doc-verifier](../agents/doc-verifier.md) when a required documentation claim lacks source evidence or conflicts with observed behavior.
- Assign [integration-checker](../agents/integration-checker.md) when a required cross-component flow lacks end-to-end evidence or its wiring evidence conflicts.
- Assign [code-reviewer](../agents/code-reviewer.md) when a source-defect finding lacks an independent verdict on the current revision or integration changes invalidate its prior review.

These assignments supplement the required component reviews; do not skip a
component review because no additional question is unresolved. They are specialist
assignments within phase-verify, not extra runtime routes or commands.
The verifier incorporates their evidence at the same assigned revision and remains
responsible for a conclusive phase assessment. A reviewer does not edit its target
or spawn more reviewers; missing specialist evidence is returned to the coordinator.

The coordinator routes document findings to a documentor using doc-writer, source
findings to a coder, and uncertain causes to a debugger before repair. Each repair
keeps the finding, evidence and affected acceptance attached to the phase. After
integration, repeat the affected specialist assessment and independent phase
verification at the new revision. An author cannot close its own independent
review solely by asserting that a correction was made.

Verifier attempts also retain their worktree, process identity and result path.
An interrupted verifier must stop before its result is reused. If no usable report
for the current source remains, inspect the saved attempt and allow a fresh one:

```text
python .ai/runtime/phase.py verify 01-authentication --workers-stopped
```

The flag asserts an inspected, stopped attempt; it does not stop a live process.
For an interrupted phase-verifier process, use `verify PHASE --workers-stopped`.
For a failed or interrupted component code-reviewer before integration, use
`resume PHASE --workers-stopped` after inspecting its process, worktree and report.
For missing review receipts on an already-integrated component, use
`verify PHASE --workers-stopped`. Follow [phase-resume](phase-resume.md) for
correction commits and historical finding resolution; do not replay implementation
to recover a failed review process.

Keep missing behavior, documentation or evidence as gaps. Correct bounded
findings within authorized scope; obtain a real decision if the target must
change. Preserve finding history, revise affected instructions and reconcile any
existing attempt before further execution. After confirming prior workers have
stopped, retain completed instructions and add bounded corrective components:

```text
python .ai/runtime/phase.py run 01-authentication --replan --workers-stopped
```

The flags assert a reconciled attempt; they do not stop workers or authorize scope.
Rerun affected checks and independent verification on the resulting revision.

A summary assertion or successful process is not a pass. For required human-only
checks not yet performed, set VERIFICATION frontmatter `status: human_needed` and
list each pending check under Human Verification Required; use [phase-uat](phase-uat.md).
If demonstrated gaps also exist, set `status: gaps_found` and retain the pending
human checks. Required missing evidence prevents
final readiness and merge. Draft progress pushes follow
[phase-ship](phase-ship.md); the runtime publisher still requires verification.
Additional review follows the risks and changes; there is no fixed
limit that strands known repairable work.

After recording each report, the coordinator MUST immediately dispatch its
required correction, obtain current independent verification, or proceed to
[phase-ship](phase-ship.md) when all required evidence passes. A report with gaps
MUST NOT end the execution loop while an authorized correction is possible.
Continue independent work before escalating a concrete unavailable dependency;
honor the user's actual pauses and delivery boundary.

## Full verification artifact

Use the complete [verification report](../templates/verification-report.md) and
[verifier method](../agents/verifier.md) with the
[local adapter](../references/agent-adaptation.md). Trace observable truths, real
artifacts and critical connections, with requirement coverage, regression evidence,
anti-pattern findings and human-only checks. Add the assigned revision and
[runtime result metadata](../runtime/TEMPLATE-CONTRACT.md). Do not substitute
a short verdict for the full report or equate a string match with working behavior.
