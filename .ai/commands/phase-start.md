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

Workers commit each completed meaningful slice immediately and commit their
SUMMARY. The coordinator audits scope, actual
commits and required checks before integration. A blocked or invalid result
remains visible and its checkout is preserved. Status distinguishes worker exit,
integration, verification and publication.

After integration, use [phase-verify](phase-verify.md), correct evidenced gaps
within authorized scope and run applicable UAT. Continue through already-authorized
steps rather than asking at each boundary. A real new decision still requires
resolution before its dependent work. For interruption, use
[phase-resume](phase-resume.md), not a blind second run.

## Execution guidance

The [coder](../agents/coder.md) method explains task execution, deviations,
checkpoints and result writing. Documentation components use the
[documentor](../agents/documentor.md) and its full [doc-writer](../agents/doc-writer.md)
method to author claims against integrated evidence. Use the selected role with
[local adaptation](../references/template-adaptation.md), the assigned PLAN, and the
full [summary template](../templates/summary.md). Preserve task completion evidence,
actual changes, decisions, dependency effects, issues and remaining work. Add
[runtime result fields](../runtime/TEMPLATE-CONTRACT.md); a blocked task cannot
be reported as a completed requirement.

An uncertain failure can require the [debugger](../agents/debugger.md). The worker
returns its evidence and blocked boundary; the coordinator assigns the focused
investigation and routes its result to the responsible coder or documentor.
Workers do not dispatch more agents. Required documentation follows its code
dependencies, then enters independent document verification during phase-verify.
