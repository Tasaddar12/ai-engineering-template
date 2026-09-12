# Verify and correct a phase

Read [RULES](../RULES.md), CONTEXT, component summaries, current contracts and
the actual integrated code. Use the assigned clean integration worktree.

```text
python .ai/runtime/phase.py verify 01-authentication
```

The runtime dispatches the independent [verifier](../agents/verifier.md). It
checks phase acceptance, component connections, regressions and documentation at
the assigned revision. It writes an external report while leaving the checkout
unchanged; the coordinator audits, stores and commits VERIFICATION.

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

A summary assertion or successful process is not a pass. Report human-only checks
as pending and use [phase-uat](phase-uat.md). Required missing evidence prevents
publication. Additional review follows the risks and changes; there is no fixed
limit that strands known repairable work.
