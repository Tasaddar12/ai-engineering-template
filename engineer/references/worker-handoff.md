# Worker assignment and continuation

The coordinator owns dispatch, lifecycle, integration, shared records and publication. A worker owns only its assigned source or read-only evidence packet. Read [parallel status](parallel-status.md), [worktree sessions](worktree-sessions.md) and the consuming workflow before dispatch.

## Assignment pre-flight

Capture the exact repository root, branch and full input SHA. Resolve the exact role from `agents/README.md` and model/effort through `engineer_run query resolve-model ROLE --raw` and `resolve-effort ROLE --raw`; omit inherited settings. Give the worker required paths and complete templates, one bounded outcome, exact write ownership, exclusions, check argv and output destination. A worker verifies identity before any edit.

```text
Role: exact registered role
Outcome: one bounded result
Repository: absolute assigned checkout
Branch: assigned branch
Input revision: full SHA
Read first: exact paths and complete templates
Own: exact paths; explicit deletions and shared resources
Exclude: shared records, other workers and publication
Checks: exact argv lists, or none/not run with authority
Output: required artifact or cited packet, commit and result fields
```

 A timeout is not evidence that a worker stopped.

## Completion contracts

| Worker kind | Completion requires | Does not do |
|-------------|---------------------|-------------|
| Source-changing executor/fixer/writer | Owned commits and required SUMMARY or explicitly assigned maintenance result | Push, integrate, update shared state or publish |
| Coordinator | Join results, reconcile gates and owned records, integrate and publish when authorized | Reassign a live worker's paths |

The consuming workflow owns exact completion markers and regexes. A presentation heading alone is not completion evidence. Inspect artifact content, commit ancestry, scope and remaining items. Preserve the upstream distinction between sentinel-match, artifact+query and structured-return; do not invent a single generic completion parser.

## Partial return

```text
Status: partial | blocked
Repository / branch: actual identity
Revision: base SHA; head SHA
Completed: committed outcomes and exact paths
Remaining: unfinished obligations and first next action
Dirty paths: exact paths or none
Checks: exact commands, observed outcomes, evidence paths
Blockers: exact missing fact/decision/capability and dependent scope
Process state: stopped | running | unknown
Next owner: coordinator or assigned continuation
```

Do not label required uncommitted work complete. Preserve a dirty diff and explain it; never discard it to simplify the handoff. If user ordering defers checks, record pending checks and continue authorized source work.

## Durable handoff

Use `engineer_run query handoff.limits` for measured thresholds. Write durable context with `handoff.write ID --reason TEXT --completed TEXT --remaining TEXT --next TEXT`, adding phase/plan/agent/role/blockers/notes when applicable. `handoff.read ID` restores its record and continuation text; `handoff.consume ID` is called only after the continuation has actually been adopted. The hook at `../../hooks/context-handoff.sh` is advisory; it does not grant authority or prove persistence succeeded.

Preserve exact goals, approved decisions, source identities, base/head revisions, completed commits, dirty paths, pending gates, user test ordering, live process identity and the first bounded continuation. A short synopsis that drops any of these is not a faithful handoff.

## Confirmed stop and reassignment

1. Request worker stop through the actual host lifecycle API.
2. Wait for a terminal result or positive stopped confirmation. A wait timeout or lack of output is insufficient.
3. Record the last known head, dirty paths and process state.
4. Only then inspect/integrate or assign a new writer to those paths.
5. If stop cannot be confirmed, preserve ownership and continue independent work. Do not perform overlapping repair.

## Resume

Read the durable handoff, assigned role, current source artifacts and existing user authorization. Verify repository/branch/head and check for drift from the captured revision. Preserve completed valid work; reconcile changed inputs before using receipts or plans. Resume the exact first remaining action, then report deviations and updated evidence. Use [progress](../../commands/progress.md) for a report or [next](../../commands/next.md) when authorized to advance; installation follows [install](../../commands/install.md).
