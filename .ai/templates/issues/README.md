# Issue templates

1. **Select the type.** Use the table below. If editing an existing issue, preserve
   its type from its original intent, labels and prior body. If UAT reveals a bug,
   use Bug. Use UAT only for runnable human actions.
2. **Prepare the body.** Read the selected template's teaching sections. Copy only
   its **File Template** block into the reviewed body file. Fill it with concrete
   facts and safe evidence; exclude private TODO metadata. If a field does not
   apply, use `N/A` with a reason. If a fact or check is unavailable, use `Unknown`
   or `Pending` with its missing dependency.
3. **Review identity and authority.** Follow the
   [Git workflow](../../references/git-workflow.md). Compare open and closed issues
   and related PRs for duplicates. Keep defects within the current change's scope
   in that change.
4. **Validate the reviewed file.** Run
   `phase_run query issue.validate --variant "Bug" --body-file PATH`; replace
   `Bug` with the exact variant below and `PATH` with the reviewed file. If
   validation fails, correct the body before publication. Verify disclosure,
   links, behavior and human acceptance separately. Apply this step before direct
   provider edits too.
5. **Publish and read back.** Publish the reviewed content under the Git workflow.
   Compare the saved body with that content, then report its URL. If publication
   or readback fails, report the exact blocker.

| Type | Template | Validation variant |
|---|---|---|
| Bug | [Bug](bug.md) | `Bug` |
| Enhancement | [Enhancement](enhancement.md) | `Enhancement` |
| Decision required | [Decision required](decision-required.md) | `Decision required` |
| Security risk | [Security risk](security-risk.md) | `Security risk` |
| Consolidated security risks | [Consolidated security checklist](security-risk-consolidated.md) | `Security risk` |
| UAT | [UAT](uat.md) | `UAT` |
