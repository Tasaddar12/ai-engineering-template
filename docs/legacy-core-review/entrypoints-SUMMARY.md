# Legacy entrypoints retirement summary

Status: complete (owned entrypoint slice; integration and independent verification remain coordinator-owned).

## Identity and scope

- Checkout: `D:/Codex Projects/ai-engineering-template/.worktrees/legacy-entrypoints-201128194`
- Branch: `phase-legacy-entrypoints`
- Input revision: `734ecc2cb80e1b72041f0e823802530ce3ed8541`
- Owned paths: `agents/`, `commands/`, `skills/` and this summary.
- Sole whole-file deletion: `agents/debug-session-manager.md`.
- Authority: reviewed A01-A14 findings; V-22/30/53/74/75/113/136-139/148/149; C-05/11/21/28; R-AG-041/120/134/227/230/233/326/331/332. PR 127 retention boundaries preserved.

## Changes

Retired the session-manager advertisement, fixer-owned worktree creation/recovery/merge/cleanup and isolation opt-out, research cache/provider/confidence seams, MemPalace dispatch/indexing, broken-windows recording, calibrated scope estimates, global learning injection and subrepo commit-hash extraction. The fixer verifies the coordinator-supplied checkout, branch and revision before writing; its parse/apply/report methods remain byte-for-byte unchanged. Its rollback, syntax/verification strategy and Windows reparse-point prohibition remain.

Research now asks bounded questions through available documentation/MCP/WebSearch/WebFetch tools and records direct provenance with static confidence tiers. Package-legitimacy requirements remain. The debugger retains its offline knowledge-base method, and plan checking retains ordinary task/file/context budgets.

Commands and their exact skill copies no longer advertise retired external review lanes, discussion overlays, intel modes, update sync/reapply routes, workstreams, convergence, ADR ingestion or the retired reviews CLI flag. The next command routes to the existing next workflow. Onboarding uses mapping and project initialization. Milestone completion uses the retained milestone entry template in its appropriate MILESTONES.md role. Planner review-feedback context remains supported without advertising the removed CLI route.

Removed imports of retired bootstrap helpers and inlined repository/role/relevant-skill reading. Removed standalone stdout overflow unwrapping. Host-qualified imports, run-resolver, response-language, UI-brand and retained reference families remain.

## Verification

- Initial `Get-Location` and Git root/branch/HEAD checks matched the assigned checkout and input revision.
- Python static scan: all 42 command/skill pairs are byte-identical.
- Python static scan: no owned Markdown callers remain for the retired features/helpers enumerated in this assignment, including the session manager, research seams, MemPalace, smart-zone estimator, overflow protocol, reviewer lanes, workstreams and isolation opt-out.
- Python document smoke check: all 50 changed surviving documents preserve baseline structural-tag balance and code-fence parity.
- Python preservation check: fixer parse/apply/report steps unchanged against input revision; rollback, three-tier verification and reparse-point guard retained; research package-legitimacy method retained.
- `git diff --check`: passed after removing an extra terminal blank line in update command/skill.
- One initial preservation-check invocation encountered Windows cp1252 decoding; rerun with explicit UTF-8 passed. This was the check harness, not a source failure.

## Remaining / deferred

Workflow, runtime, references/template retirement and their integration checks belong to the other assigned slices. Repository-wide link/verb checks and fresh independent verification must run after integration. General Node/Python semantic and installer migrations remain outside this retirement-only scope. No adopting-project planning records were created or modified. No push, publication, merge or branch changes were performed.

## Threat flags

None identified in the inspected Markdown entrypoint retirement scope; no new executable, network, authentication or storage surface was introduced.
