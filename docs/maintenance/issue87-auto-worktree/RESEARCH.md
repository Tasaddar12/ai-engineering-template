# Issue 87: host capability research

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- Investigate the current host hook contract and prepare a separate draft implementation for a matching gap; never merge.
- Preserve PR 86's preference for scratchpad warnings. Distinguish task notes from source edits; do not restore a repeated hard-halt retry loop.
- Preserve uncommitted changes and prevent writes to the old checkout from continuing after a claimed handoff.
- Keep the six existing drafts separate and frozen. Work 73/74, live infrastructure, tool installation and real cleanup are out of scope.

### Claude's Discretion

- Researcher may choose the bounded evidence and recommend an implementation and test boundary. Recommendations are technical findings, not additional human decisions.
- Researcher owns only this CONTEXT.md and RESEARCH.md. No production edits, test execution, provider writes, publication or merge.

### Deferred Ideas (OUT OF SCOPE)

- Work 73/74, unrelated drafts, live infrastructure, tool installs and real cleanup.
</user_constraints>

## Evidence boundary

Research date: 2026-10-15. Repository inspected at `77b5668f2003bea60127d87e8785469286abafb3`. Coverage: complete for the documented capability decision; live-host behavior remains unverified. No production files changed and no tests, installs, provider writes or real worktree cleanup ran.

Local inspection came first. Neither CLI was available through the current PowerShell command search. The Codex package data directory was visible, but package/runtime enumeration returned access denied. The coordinator confirmed that no trustworthy installed executable, runtime source path or version was observed and directed no broader protected-directory inspection. Thus this report does **not** certify an installed Codex or Claude version. The official pages below are unversioned current documentation retrieved on the research date, not evidence of the installed release. No local source was available to cross-check their implementation.

## Host capability table

| Surface | Pending input and cancellation | Session/worktree binding | Confidence |
|---|---|---|---|
| Codex local hooks | Pretool rewriting is documented: allow plus replacement input; shell/patch require a command string. Explicit denial or exit 2 prevents a supported call. | Hook commands inherit session cwd. A pretool response does not document a session-rebinding operation. | MEDIUM, official contract only [CITED: https://learn.chatgpt.com/docs/hooks#pretooluse] |
| Claude Code hooks | Replacement input replaces the entire argument object; preserve unchanged fields. Denial cancels the pending call. | WorktreeCreate supplies a checkout path when a host worktree operation invokes it. It is not itself the trigger for an arbitrary edit. | MEDIUM [CITED: https://code.claude.com/docs/en/hooks#pretooluse-decision-control] [CITED: https://code.claude.com/docs/en/hooks#worktreecreate] |
| Claude Code native tool | A separate worktree entry operation creates and switches, or enters an existing path. | Paths outside the standard Claude worktree directory require host approval since v2.1.206; pinned agents have additional target restrictions. | MEDIUM; minimum changes documented, installed version unknown [CITED: https://code.claude.com/docs/en/tools-reference] |
| Codex desktop native Handoff | Moves a chat between Local and Worktree and handles the Git transfer. | Host-owned operation, distinct from rewriting a file tool. | MEDIUM [CITED: https://learn.chatgpt.com/docs/environments/git-worktrees#working-between-local-and-worktree] |
| Available Codex app tool metadata | Creation attaches a worktree but leaves the caller in its existing checkout; handoff moves another thread and cannot move its caller. | This session cannot treat creation/attachment as self-handoff. | HIGH for exposed tool contract; not a CLI API claim [VERIFIED: current create_worktree/handoff_thread tool descriptions] |

Additional Codex limits: unsupported pretool stop fields, hook errors or malformed output can allow the pending call to continue. Existing exec-session input is not rechecked; some specialized tools opt out. Local shell hooks are unsupported with cloud orchestration even when execution is local. These documented exceptions rule out a universal enforcement claim. [CITED: https://learn.chatgpt.com/docs/hooks#tool-coverage] [CITED: https://learn.chatgpt.com/docs/hooks#managed-hooks-from-requirementstoml]

Claude's environment persistence facility is available only to specified lifecycle events, not pretool hooks. Worktree creation through a shell command bypasses WorktreeCreate. Therefore neither should be presented as a pretool session-switch API. [CITED: https://code.claude.com/docs/en/hooks#persist-environment-variables] [CITED: https://code.claude.com/docs/en/hooks#worktreecreate]

## Repository evidence

- The current guard selects file mutations, warns on primary-checkout or cross-checkout targets, and succeeds. Its tool selector is quoted below; this is existing behavior, not a proposed replacement. [VERIFIED: .ai/hooks/worktree-guard.sh:147-175,195-262]

  DATA_C9A72F10_START
  `Write|Edit|MultiEdit|NotebookEdit|apply_patch`
  DATA_C9A72F10_END

- Installer registration covers both hosts; Claude alone registers the existing location hook, whose creation branch uses the caller's committed HEAD and returns a registered existing destination when found. It does not register a workflow session. [VERIFIED: .ai/install.py:430-468; .ai/hooks/worktree-location.sh:91-112]
- Runtime session opening reuses an open matching kind/label and otherwise creates a named branch and checkout. It returns the checkout; it does not change a host session's cwd. These returned field names are present in the source: [VERIFIED: .ai/runtime/lib/worktrees.py:747-832]

  DATA_B34E17C8_START
  `worktree`, `branch`, `base`, `reused`, `synced`
  DATA_B34E17C8_END

- The documented caller must run subsequent commands in the returned checkout. Runtime creation and explicit caller transition are already separate steps. [VERIFIED: .ai/references/worktree-sessions.md:68-102]
- Default session opening calls base synchronization. Synchronization can fetch and fast-forward the primary base; auto-prewrite code cannot claim it merely creates an isolated checkout without considering that side effect. [VERIFIED: .ai/runtime/lib/worktrees.py:785-796; .ai/runtime/lib/delivery.py:352-396]

## Recommendation and unsafe alternatives

**Research conclusion:** use a source-sensitive prewrite handoff guard plus an explicit host/coordinator transition. Do not describe a hook-only path rewrite as opening the active session in a worktree. This is a design inference from the contracts above, not a claim that a live host transition was exercised.

The pretool response can modify arguments, but does not document replacing an edit with a different tool invocation or atomically rebinding cwd, permissions, repository context and the pending call. Changing the hook subprocess's directory changes that subprocess only. Creating a checkout, printing its path, adding context, or recording an intended root cannot establish that the next shell, read and write tools use it. Native entry/Handoff is the appropriate host operation; re-read the destination before constructing the edit again.

Use a bounded transition: detect the first source mutation; select an unambiguous existing unit of work or create one with an explicit committed base and no implicit primary sync; cancel the pending source mutation with a concise handoff instruction; enter/bind through the supported host/coordinator; verify real checkout, branch and base; re-read and regenerate the mutation there. The old checkout remains in a pending-handoff state until this proof exists. Repeated old-root mutations must never be allowed merely because creation succeeded or a notice was shown once. Workflow continuation must perform the handoff, not resubmit the blocked call in a retry loop. If that host cannot provide the transition, report the unsupported dependent scope instead of claiming completion.

Keep the advisory guard intact as a separate concern. Preserve task-note/scratchpad warnings and read-only behavior. A planning record intended for delivery is repository content; a filename ending in Markdown does not by itself identify disposable notes. An explicit, narrow task-note policy is needed, with mixed note/source operations treated as source operations.

Do not rewrite absolute primary paths into another checkout blindly: a read may have observed uncommitted content absent from the destination, and a multi-path patch may rename or delete files across roots. Merely choosing a worktree by the current branch, transcript text or arbitrary newest session can target another unit's work. Existing uncommitted tracked, staged, untracked and ignored files must stay intact; never auto-stash, reset, clean or bulk-copy them. If the requested change depends on dirty source, cancel and surface that dependency for coordinator handling. A note exception must not permit source deletion/rename or traversal through symlinks, junctions or nested repositories.

Do not attempt general shell-command parsing as part of this slice. Shell writes, existing exec sessions and external writers prevent the proposed hook from guaranteeing every filesystem mutation. Hard filesystem isolation would require a separately scoped host permission boundary.

## Candidate bounded implementation and validation

1. Add a separate host-aware prewrite component and its installer registration. Reuse repository session selection/creation with explicit identity and base. Preserve the existing advisory script byte-for-byte. Give source, note-only, read-only, unknown-input and mixed mutations explicit outcomes.
2. Persist a minimal handoff state keyed by session and repository; create once, verify before reuse, keep old-root source writes cancelled, and emit one actionable transition instruction. Require explicit confirmation from Git in the selected root, not an intended-root marker. Serialize concurrent first writes. On offline operation use an explicitly captured local commit; on timeout or uncertain creation outcome inspect existing session/Git registration before another creation. Never fall back to the primary checkout. Do not make an unavailable native session switch look successful. The coordinator must specify and implement the actual transition before advertising automatic entry.
3. Extend the existing hook Bash and installed-launcher fixture suites, plus disposable real-Git session tests. Cover clean primary creation, matching reuse, distinct/ambiguous units, read-only and note-only no creation, mixed patches, relative/absolute Windows paths, rename/delete targets, malformed input, stale destinations, offline operation, timeout after creation, concurrent first writes, creation failure and repeated attempts. Assert primary tracked/staged/untracked bytes and index state survive; no extra checkout appears on retries; no old-root edit executes after claimed handoff.
4. Add adapter-contract fixtures for each host's precise input replacement and cancellation shape, but label these as fixtures. A live supported-host smoke check must separately prove cancellation, native cwd/binding transition, permissions, fresh destination read and successful destination mutation before claiming end-to-end automatic behavior.

No tests ran in this research assignment. The scout identified existing hook/installer coverage and session reuse coverage; new implementation needs the missing behavioral cases above. Do not substitute a string-match test for a live host transition.

## Project Constraints (from AGENTS.md)

- Keep adoption records unfilled; use this separate maintenance record.
- Verify assigned root, branch and base; write only the two assigned documents.
- Source implementations require isolated workers and independent review/verification. The coordinator owns dispatch, integration, shared planning records and publication.
- Commit only the assigned slice, preserve unrelated work, and never merge without human authorization.
- Runtime owns planning-record mutations. No invented phase or manual shared-state updates.

## Environment Availability

PowerShell and Git were observed. Ripgrep was unavailable; native PowerShell reads were used. No new dependency is recommended. Installed Codex/Claude versions and trusted runtime code remain unavailable; official contracts are the fallback. Live host verification is a remaining delivery requirement, not an installation instruction.

## Unknowns and limits

- Exact installed releases, hook enablement, and local versus cloud orchestration mode were not established. Minimum safe compatibility cannot be inferred from current docs alone.
- No documented pretool API was found for an atomic same-session move and replay. This is a documentation boundary, not proof that no private host capability exists.
- A complete unattended transition must be demonstrated in the supported host; the repository's shell/installer fixtures cannot establish it. Source gating plus a handoff instruction is an honest partial result if native transition remains unavailable.
- The source/task-note policy and dirty-source dependency handling must be explicit implementation acceptance. They cannot be decided by extension guessing.
