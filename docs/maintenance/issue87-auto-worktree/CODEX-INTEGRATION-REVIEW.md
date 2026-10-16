## Integration check

**Static wiring is present at HEAD `54c41fbc06a376d8cbebb92d745536558bf0a615`. Runtime and end-to-end behavior remain unverified.** The checkout is clean, and `git diff --check` reported no issues.

The installer maps the tracked launcher asset to `.codex/codex-worktree.py`, exports the adjacent runtime, and registers three synchronous Codex guards: `PreToolUse` with matcher `*`, plus `SessionStart` and `UserPromptSubmit`, each with a 30-second timeout. Update and migration planners both consume the same installer payload. The generated adapters route to `launcher_main` and `hook_main`.

The launcher statically connects phase/quick selection, existing-session reuse, captured-base validation, `open_session(..., sync=False)`, destination and installation checks, hook trust checks, and effective-policy comparison before building native argv. That argv sets the destination with `--cd`, enables hooks, and passes a prompt as one argument after `--`; it contains no sandbox or approval override. Hook decisions classify supported tool operations and validate roots, while lifecycle events preserve primary-checkout note handling.

The six workflow consumers—quick, discuss-phase, plan-phase, execute-phase, verify-work, and ship—point to the canonical startup protocol. It describes a **new Codex run**, not movement of an active conversation. Claude’s native entry path remains separate.

The destructive-guard fixture fix selects the two intended shell handlers by command identity, asserts exactly one of each, then applies the existing matcher. The retained installed tracer remains present and unmodified. These are source observations, not test results.

| Acceptance | Static status |
|---|---|
| CW-01, CW-02 | Wired; runtime behavior unverified |
| CW-03 | Install, update, and migration wiring present; export tests not run |
| CW-04 | Policy and trust checks present; effective-feature behavior unresolved |
| CW-05 | **Blocked/unverified**: native shell and patch denial proof was not run |
| CW-06 | Documentation points to the canonical protocol; runtime claims unverified |

The plan records all local Python, import, export, test, and validator checks as **NOT_RUN** after the reported execution denial. Native/generated hook or launcher execution and manual CI rerouting were also out of scope. The `--enable hooks` invocation combined with preserved `features.hooks=false` remains an explicit open question. Original live AW acceptance and issue98 threat evidence remain unresolved.
