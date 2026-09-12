# Phase status

Read-only: do not edit records, commit, create a worktree or start workers.

```text
python .ai/runtime/phase.py status
python .ai/runtime/phase.py status 01-authentication
python .ai/runtime/phase.py status 01-authentication --remote
```

Combine observed runtime/PR facts with CONTEXT, summaries and verification.
Report what is ready, running, integrated, blocked, verified or published, the
revision that evidence covers, and the next action. Do not infer live processes
from an old STATE entry or claim delivery because a PR exists. Without --remote,
publication details reflect saved observations; --remote reads current PR/check
state without changing local records. Pending or failed required remote checks
mean the published PR is not yet ready.

Show relevant acceptance/documentation gaps and pending decisions. Keep the
response focused on changes or action needed. The coordinator can separately
run `python .ai/runtime/phase.py sync` in its assigned clean worktree to update
the derived STATE view; status itself remains read-only.
