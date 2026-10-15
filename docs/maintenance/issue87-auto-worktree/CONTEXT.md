# Issue 87: automatic worktree handoff

## Authority and scope

The actual human request delivered through Jarvis was: “AI Workflows often ignore needing a worktree... different hook to force it to open a worktree when it tries to write or edit anything and its not currently in one... Look into it and get another PR if we dont have something open for it already.” The coordinator owns duplicate checking and publication. This maintenance record does not fill the adoption skeleton or establish an adopting project's phases.

## Decisions

- Investigate the current host hook contract and prepare a separate draft implementation for a matching gap; never merge.
- Preserve PR 86's preference for scratchpad warnings. Distinguish task notes from source edits; do not restore a repeated hard-halt retry loop.
- Preserve uncommitted changes and prevent writes to the old checkout from continuing after a claimed handoff.
- Keep the six existing drafts separate and frozen. Work 73/74, live infrastructure, tool installation and real cleanup are out of scope.

## Claude's Discretion

- Researcher may choose the bounded evidence and recommend an implementation and test boundary. Recommendations are technical findings, not additional human decisions.
- Researcher owns only this CONTEXT.md and RESEARCH.md. No production edits, test execution, provider writes, publication or merge.

## Deferred Ideas

- Work 73/74, unrelated drafts, live infrastructure, tool installs and real cleanup.

## Coordinator technical scope decisions

- The human clarified: "Well yeah we changed this earlier but that was for different reasons. This time we actually move the agent itself". Acceptance requires movement of the same existing agent/session, subsequent tools using the destination by default, and cancellation followed by fresh reconstruction of the pending edit. Checkout preparation, shell `cd`, path rewriting, cancellation alone and replacement children do not satisfy this outcome.
- Subsequent parent steering explicitly authorizes implementing a supported target-host route with capability gating. Current executor limitations must be distinguished from reusable-template host support. Official Claude documentation supports instruction-driven native `EnterWorktree` creation after synchronous cancellation. Replan for that conditional Claude route; do not release the earlier preparation-only plan.
- Gate Claude routing on actual native tool/schema availability, eligible role and policy, and the trusted creation hook. Preserve native approval requirements for existing outside paths; never disguise reuse as new creation to avoid approval. Verify native context binding before fresh destination reads and a rebuilt mutation. Preserve or fully account for staged, unstaged, untracked and ignored data.
- Codex currently lacks an authenticated same-thread host controller in this template. State that precise unsupported integration boundary; cancellation or a prepared checkout does not implement automatic movement. No universal enforcement or live-host success claim may be inferred from a simulated contract test. Live native smoke remains a distinct evidence requirement.
- These are bounded implementation choices under the user's existing authorization. The six original draft heads remain frozen, all PRs remain unmerged, and issue 87 stays open.
- Official pre-edit linkage evidence: `CLAUDE_CODE_SESSION_ID` is documented in Bash/PowerShell tool and hook subprocesses; `${CLAUDE_SESSION_ID}` is skill-content substitution, not a shell variable. No agent-ID environment variable was established. A known-unit workflow request can be provisional with repository, nonce and available session correlation; actual native hook identity must be compared and conflicts refused. CLI identity arguments are correlation claims, not authentication. Do not invent a main-agent ID or use request/journal success as movement proof. See [environment variables](https://code.claude.com/docs/en/env-vars), [skill substitutions](https://code.claude.com/docs/en/skills#available-string-substitutions) and [WorktreeCreate fields](https://code.claude.com/docs/en/hooks#worktreecreate-input). This is a bounded implementation clarification of the approved request/bootstrap contract.

- To implement the user's source-versus-task-note distinction without guessing from file extensions, ordinary external temporary artifacts are limited to plain unlinked create/update paths under the resolved OS temporary directory and outside every Git repository. No identity or preparation is needed there. This is a bounded technical choice under delegated implementation discretion, not an additional human approval.
- Mixed, rename/delete, linked/reparse/hardlinked, cross-repository and ambiguous paths receive source/unsupported handling. Non-temp external locations are not a note exemption.
- Independent RED review required the corresponding both-host control before production; corrected test-only38b7b1c retains genuine source refusal failures and passing ordinary-note controls. PLAN/MATRIX alignment and independent bounded recheck precede source release.

## Coordinator dependency reconciliation for Task 4

The user authorized preserving existing prior work through distinct adjustments
and stacked drafts. Coordinator therefore selects frozen PR93 (47593a3d3f71739bd146a6c2c3590798d7c73c2e),
already on frozen PR92 (d8f2c8bd0c4dca0f82a7fc8a95e4f0abb8bcd2b6), as PR97's
dependency. After current code-05 review corrections integrate and this plan is
independently checked, use a local non-rewriting merge into97 and the bounded
native/planning runtime/installer union in STACK-PLAN. This is routine dependency
reconciliation within existing delegated authority, not a new human approval.
Preserve both frozen parent heads and PR89/91/94/88; no PR is merged. Change the
actual PR97 base only after checked integration; never import the original-six
umbrella/prototype into97 or copy independent PR91/94 policy into its own diff.
After final97, test/review a separate disposable local original-six composition
without publishing it. Existing maintenance acceptance and live-native uncertainty
remain; a real planning-preservation integration failure must be repaired, not
deferred. Native exit stays essential preservation, with no second cleanup project.
