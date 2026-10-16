# Documentation summary: Issue 87 native worktree entry

**Result:** Updated the four assigned documentation paths against the integrated
Task 1-2 implementation at `06b1b25d0454d42eee04a767522f8a419229a7e5`.

## Coverage

| Required path | Coverage |
|---|---|
| `.ai/hooks/README.md` | **Updated and verified.** Documents the blocking source-prewrite hook alongside advisory hooks, cancellation without precreation, the conditional same-caller native gates, the fresh pinned-base `wf-entry-` callback, existing-path approval, ordinary dispatch reuse, narrow note allowances and unchanged advisory warnings. Installer exports and actual hook/runtime behavior were inspected. |
| `.ai/references/worktree-sessions.md` | **Updated and verified.** Adds the conditional six-workflow Claude entry route and exact implemented `prewrite.request`, `prewrite.begin` and `prewrite.confirm` verbs; preserves normal session behavior and explains new versus existing mode, native completion/default checks, fresh reads and later-turn defaults. |
| `.ai/runtime/README.md` | **Updated and verified.** Adds the actual prewrite verb interfaces and their boundaries, including Git-only confirmation with `host_binding_verified: false`, correlation claims versus authentication, and the precise Codex integration limitation. |
| `.ai/RULES.md` — Hooks and validation section | **Updated and verified.** Reconciles advisory and blocking hooks, conditional native entry, note exceptions, approval boundary, SIMULATED fixtures and live-host evidence. All other RULES sections remain unchanged. |

Source claims were checked against `.ai/references/same-agent-worktree.md`,
`.ai/install.py`, `.ai/runtime/lib/prewrite.py`,
`.ai/hooks/source-prewrite.sh`, `.ai/hooks/worktree-location.sh` and the
`quick`, `discuss-phase`, `plan-phase`, `execute-phase`, `verify-work` and
`ship` workflow entry sections. Linked local targets were checked against the
repository. No implementation paths were changed.

## Validation and remaining evidence

- `git diff --check` — passed on the owned documentation diff; all local link
  targets introduced or referenced by these sections exist.
- Deterministic source and integration suite results are reported from the
  integrated source receipt; they were not rerun for this documentation-only
  task: native contract 9 passed; prewrite 23 passed with 1 Windows symlink
  privilege skip; installer 41 passed with 1 such skip; installer update 66
  passed with 4 documented skips; session delivery 60 passed; agent sources 16
  passed; workflow links 4 passed; migration suite 18 passed. Bash source,
  location and advisory suites reported 12, 25 and 60 passed respectively.
- Native host behavior in those fixtures is **SIMULATED**. A live eligible
  Claude host transition, default-context change and later-turn behavior remain
  **unverified here**; no live host support evidence is claimed by these docs.

## Deferred

None within this documentation assignment. Live native smoke remains a separate
acceptance gap owned by integration and verification.

## Follow-up documentation review

DOC-01 found that the Hooks README claim “There is no Python hook adapter” was
incorrect. The registered entrypoint is the shell script
`.ai/hooks/source-prewrite.sh`, which invokes
`.ai/runtime/lib/prewrite.py hook --host <host>`; the Python adapter's `main`
dispatches the `hook` action to `source_decision`. The README now distinguishes
the shell hook entrypoint from its Python decision adapter and preserves the
nearby installed-host hook folder and launcher guidance. No other document or
source path changed in this follow-up. The independent review's live-host
conditions remain unverified as already recorded above.
