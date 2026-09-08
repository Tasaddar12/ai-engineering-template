# PLAN-001 manual coordination tools

This directory versions the tools and instructions still needed to finish this
plan. They support this repository's current manual development session. They
are not the workflow engine, an installed asset, or a substitute for its tests.

The [current user decision](single-stage-review-decision.md) requires one independent
review per remaining task, focused verification of fixes, then final combined
reviews and later plan refinements. The coordinator and briefs apply that manual
schedule without changing the toolkit's frozen runtime contracts. New candidate
manifests bind this decision; historical two-stage reviews remain unchanged.

Use [coordinator.py](coordinator.py) for the existing status, dispatch, candidate,
acceptance and failed-review checkpoints. It finds this checkout from its tracked
location and reads [dispatch records](dispatch/TASK-018-a1.json.txt) here. Run it
with the desired Windows development Python interpreter. Candidate validation
uses that interpreter; optional Python 3.11 and WSL lanes retain the documented
local interpreter bindings in the script. Those environments are disposable and
must be recreated separately on another machine. The tools still require manual
verification, completed owners, fresh independent reviews and policy checks.

For example, from the repository root:

```text
python .ai/plans/current/PLAN-001/evidence/coordination/coordinator.py status
```

A dispatch writes a tracked `dispatch/TASK-NNN-aN.json.txt` after creating the task
checkout. Commit that record before freezing the next review candidate. The text
suffix distinguishes manual diagnostics from schema-governed v1 artifacts; it
does not change the JSON bytes. Existing dispatches retain their original local
paths and Git identities as historical observations.

[count-native-invocations.py](count-native-invocations.py) reads an explicitly
supplied local session JSONL and writes only whitelisted invocation metadata to
an explicitly supplied output. It never copies prompts or conversation content.
Use `--help` for its arguments. This is conservative manual budget accounting,
not an implementation of the engine's runtime ledger.

[agent-brief.md](agent-brief.md), [reviewer-brief.md](reviewer-brief.md) and the
`next-*-dispatch.md` files are the current supplemental dispatch instructions.
Read only the selected task's briefing and explicit references. The tracked
task/spec/contracts and observed accepted dependencies remain authoritative.

The immutable [Git feasibility assessment](git-port-readiness.md.txt), its
[original probe](git-port-advisory/probe.py.txt), and the original
[Windows](git-port-advisory/windows-results.json.txt) and
[Linux](git-port-advisory/linux-results.json.txt) results preserve a planning
observation. Original filenames/links inside them describe their earlier local
execution. Do not run the saved probe against current worktrees or mistake it
for the actual TASK-007 implementation or acceptance tests.

[local-material-audit.md](local-material-audit.md) explains what was retained,
what is disposable, and which existing tasks own the actual product behavior.
Update these tracked tools and instructions directly; do not create another
canonical copy under `.ai/local`. Local runtimes, caches and throwaway fixtures
remain ignored. Required source, tests, build logic and reusable guidance belong
in their declared project paths and must survive a clean checkout/install.
