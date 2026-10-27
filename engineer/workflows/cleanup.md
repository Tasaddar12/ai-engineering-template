<!-- workflow: cleanup; produces: exact cleanup outcomes -->
<purpose>
Preview integrated owned worktrees and branches, obtain approval for the exact captured snapshot, then apply only that approved list. This workflow does not archive planning records.
</purpose>
<required_reading>
@~/.claude/engineer/RULES.md
@~/.claude/engineer/references/cleanup.md
@~/.claude/engineer/references/git-workflow.md
</required_reading>
<process>
<step name="resolve_and_preview">
Read and execute `engineer/workflows/_runtime-launcher.snippet.sh`. Resolve the repository root and use its configured owner evidence; do not infer ownership from a branch's spelling. Run `engineer_run query cleanup.preview`. Keep the returned `approval_token`, complete `entries` list, and `count` together. Each entry binds an exact path, branch, and captured head. Show every entry, including the full absolute path, branch, head and integration evidence. State explicitly that preview is read-only. A zero-count preview ends here.

Do not substitute a fresh preview after obtaining approval. A changed preview is a different snapshot and needs its own exact approval.
</step>
<step name="exact_human_approval">
Ask the user to approve the displayed snapshot with the exact phrase `Approve exact cleanup snapshot <approval_token>`. Name all proposed deletions in the same visible approval item. Keep the original reply and token. A generic yes, stale token, approval of another list, or silence does not authorize deletion. The approval token is evidence tied to a specific preview; never manufacture or edit it. If the user approves only a subset, obtain a preview/token for that exact subset through the supported preview interface before any apply; if no such interface exists, stop with the requested subset preserved.
</step>
<step name="apply_and_report">
After an explicit reply approving that exact snapshot, run `engineer_run query cleanup.apply --approval-token "${APPROVAL_TOKEN}" --confirm`. The runtime revalidates exact ownership, worktree cleanliness, captured HEAD, and ancestor/integration evidence before each deletion. Do not add a force option or replace the operation with direct filesystem or Git branch deletion. Preserve changed, unowned, dirty, unmerged or unverifiable entries.

Report removed, preserved and failed entries separately, with their reasons and the original snapshot token. A partial failure does not authorize retrying a new list under the old approval. Do not create a planning bookkeeping commit for cleanup. Phase and quick record retirement belongs to `clean-planning` and milestone completion.
</step>
</process>
<success_criteria>
Preview changed nothing; approval names the exact snapshot; the guarded apply alone performed deletions; every removed, preserved and failed entry is accounted for. There is no approval override.
</success_criteria>
