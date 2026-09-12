# Execute a phase

Read [RULES](../RULES.md) and verify the assigned integration worktree. Inputs
must be committed, the tree clean, relevant decisions resolved and execution
authorized. Follow [phase-prepare](phase-prepare.md) for incomplete instructions.

```text
python .ai/runtime/phase.py check 01-authentication
python .ai/runtime/phase.py run 01-authentication
```

The runtime starts a fresh coder or documentor for each ready component in its
own immediate-child worktree. Independent components can overlap; ownership and
exclusive resources serialize conflicting assignments. A dependent component
starts after its own prerequisites are integrated and checked on the phase
branch. Unrelated earlier-wave work is not a barrier.

Workers commit their changes and SUMMARY. The coordinator audits scope, actual
commits and required checks before integration. A blocked or invalid result
remains visible and its checkout is preserved. Status distinguishes worker exit,
integration, verification and publication.

After integration, use [phase-verify](phase-verify.md), correct evidenced gaps
within authorized scope and run applicable UAT. Continue through already-authorized
steps rather than asking at each boundary. A real new decision still requires
resolution before its dependent work. For interruption, use
[phase-resume](phase-resume.md), not a blind second run.
