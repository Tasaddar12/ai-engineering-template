# Independent prewrite matrix proposal

Scout: `gpt-6-luna/high`; input `e87f49debbd64daf25157da0b693d328ad3dd531`. The coordinator condensed the returned static proposal. The initial scout ran no tests; its rows do not establish implementation correctness or live-host support. Independent RED review added N2. Test-only 1414979 and corrected 38b7b1c establish the initial installed-boundary RED; their source-denial failures and passing note controls are recorded separately in IMPLEMENTATION-SUMMARY. Other matrix families remain unrun until implementation.

| ID | Refusal or preservation case | Legitimate control / evidence |
|---|---|---|
| N1 | Untracked create/update under `.planning/scratchpads/**`, even without session identity: advisory; no creation | Preserve current `.ai/hooks/worktree-guard.test.sh:120` and `tests/test_install.py:722` behavior |
| N2 | Plain unlinked create/update under the resolved OS temporary directory, outside every Git repository: allow without identity or preparation | Independent RED review CR-01; both installed host pipelines mutate the disposable note and preserve exact worktree/preparation state. No extension guessing, linked/cross-repository, rename/delete/mixed exemption. |
| S1 | Source write in primary: cancel original operation; select/create at most one verified destination and provide exact continuation | Fresh destination root/branch/base check, read and rebuilt mutation |
| S2 | Missing exclusive actor/unit identity: no guessed/newest session | Explicit verified unit mapping takes precedence; Codex parent session ID is not exclusive |
| S3 | Conflicting repository/session/unit mapping or multiple plausible units: cancel | One exact verified mapping reuses only its unit |
| M1 | Mixed note/source patch: cancel entire operation | Note-only untracked create/update remains advisory |
| M2 | Tracked path under scratchpad namespace: source-sensitive | Untracked ordinary scratchpad remains advisory |
| M3 | Delete/rename/move from or to notes, including mixed operations: source-sensitive | Create/update-only note control; no extension exemption |
| P1 | Relative, absolute, nested-cwd, Windows separator and traversal forms resolve consistently | Verified linked destination; no silent argument retargeting |
| P2 | Symlink/junction/nested-repository paths cannot gain a note exemption or cross-unit permission | Plain unlinked note path; platform-specific real link fixtures |
| D1 | Preserve primary tracked/staged/untracked/ignored bytes and index exactly during preparation | Clean primary can prepare at captured committed base; no fetch/stash/reset/clean/copy |
| D2 | Pending edit depends on dirty primary source or ignored content: do not copy/replay it | Surface dependency; fresh destination reads before rebuilding |
| B1 | Repeated old-root requests remain cancelled; creation/notice is not handoff proof | At most one destination per verified identity; independently verified destination continuation |
| B2 | Concurrent same-identity first calls serialize/reuse; different identities never alias | Timeout after uncertain creation inspects registration/journal before another create |
| V1 | Existing checkout or intended-root marker with old cwd does not authorize source write | Supported host/coordinator transition plus actual Git proof and fresh reads |
| V2 | Changed cwd/repository/branch/base/target or stale binding invalidates earlier proof | Exact current binding and source target must still match |
| I1 | Malformed/missing path/tool/identity, creation failure and internal deadline produce truthful refusal/unsupported outcome | Recognized read/note controls remain noncreating; outer hook failures/timeouts may fail open |
| H1 | Native Codex/Claude payload and exact synchronous denial envelope through installed aggregate pipeline | Adapter fixtures are not trusted live cancellation/context-switch proof |
| R1 | Read-only/nonmutation tool causes no creation/handoff | Source mutation triggers its applicable source policy |

## Required evidence layers

- Classification/helper fixtures, native hook entrypoint cases and installed Codex/Claude aggregate registrations.
- Disposable real-Git session creation/reuse, ambiguity/drift, concurrent and uncertain-create recovery, dirty/index preservation.
- Test-only failing revision before source repair, then the same focused cases pass with legitimate controls.
- Live supported-host cancellation, transition, permission/root binding, fresh read and destination mutation require separate evidence before advertising end-to-end automatic entry.

## Source and contract receipts

- Existing parser/advisory controls: `.ai/hooks/worktree-guard.sh:147-175,195-262`; its Bash suite `:103-164`.
- Session reuse/create: `.ai/runtime/lib/worktrees.py:747-832`; `tests/test_session_delivery.py:85-120`.
- Installed registration/launch: `.ai/install.py:430-468`; `tests/test_install.py:664-735`.
- Frozen research: [RESEARCH](RESEARCH.md); human scope: [CONTEXT](CONTEXT.md).
- Current official common input: [Codex](https://learn.chatgpt.com/docs/hooks#common-input-fields), [Claude](https://code.claude.com/docs/en/hooks#common-input-fields). Codex subagents share parent `session_id`; no documented pretool actor ID. Claude documents `agent_id`.
- Cancellation: [Codex](https://learn.chatgpt.com/docs/hooks#pretooluse), [Claude](https://code.claude.com/docs/en/hooks#pretooluse-decision-control). Use synchronous `hookSpecificOutput` with `permissionDecision: deny`, or exit2/stderr. Do not use unsupported pretool stop fields.

Outer hook failures/timeouts, cloud orchestration, existing exec sessions, opaque shell/external writers and installed-version uncertainty limit enforcement. The matrix is a proposal; the independent plan checker and source reviewer own their respective verdicts.
