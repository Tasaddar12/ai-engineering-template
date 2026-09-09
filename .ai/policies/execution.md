# Execution and delivery policy

## Requirements

1. Stay inside the fixed assigned worktree and branch. Never modify another checkout.
   The orchestrator owns live state and delivery coordination. The pr-agent performs
   Git writes only under the exact user-authorized assignment; other workers do not.
2. Perform only the approved scope. Report scope expansion or an accepted contract
   change before acting; apply the approval and record policies.
3. Run agreed validation at the end. Record the actual command/check, subject revision,
   result and limits. Missing, failed, denied, stale or unrun checks cannot pass.
4. Review the full relevant proposal or implementation diff. An implementor cannot
   supply their own independent review. Changed content invalidates affected reviews
   and gate results.
5. Every commit needs a nonempty descriptive message. Push only to the approved
   destination and verify that the remote branch tip matches the local commit.
6. Creating a PR or merging requires authority for that action. Never force-push or
   treat a push as merge approval.
7. After an authorized merge, verify the hosting result and synchronize the target.
   Only after the worktree-only assignment ends may the orchestrator use its integration
   checkout for authorized synchronization and retirement.
8. Remove only the clean, stopped, exact owned worktree and its local branch after
   proving its tip has no unmerged work. An advanced or uncertain branch stays intact.

## Evidence

Use the relevant gate before advancing. A FAIL holds that transition; it does not
automatically create a global blocker. Record the reason and the next bounded action.
Manual policies and gates are not executable Git hooks or automated enforcement.
