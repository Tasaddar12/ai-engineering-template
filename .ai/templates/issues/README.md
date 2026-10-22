# Issue templates

Use the template for the issue type. Read its purpose, downstream consumers,
examples, guidelines and completion instructions, then copy only its **File Template**
block into the reviewed issue body.

Use concrete facts and safe evidence. Use `N/A` with a reason only for fields that
do not apply, and `Unknown` or `Pending` with the missing dependency for unavailable
facts or checks. Review duplicates and publication authority under the
[Git workflow](../../references/git-workflow.md), then validate the reviewed body
with `issue.validate` before publication. Structural success checks format; it does
not establish safe disclosure, working links, actual behavior or human acceptance.

Preserve an existing issue's type from its original intent, labels and prior body.
Bugs discovered during UAT remain Bug reports; do not convert engineering work
into UAT without runnable human actions or classify by the word "acceptance" alone.
Review open and closed issues and related PR context for duplicates. Keep defects
within the current change's scope in that change. Publish a separately reviewed
body file without private TODO metadata, then report its saved URL after readback
or the exact blocker. Direct provider edits bypass the runtime validation gate.

| Type | Template | Validation variant |
|---|---|---|
| Bug | [Bug](bug.md) | `Bug` |
| Enhancement | [Enhancement](enhancement.md) | `Enhancement` |
| Decision required | [Decision required](decision-required.md) | `Decision required` |
| Security risk | [Security risk](security-risk.md) | `Security risk` |
| Consolidated security risks | [Consolidated security checklist](security-risk-consolidated.md) | `Security risk` |
| UAT | [UAT](uat.md) | `UAT` |
