# Review result

Subject: {{ plan_or_report_link }}

Reviewed revision: {{ commit_or_draft_revision }}

Verdict: {{ PASS_or_CHANGES_REQUIRED }}

## Findings

| Location | Issue and impact | Required change |
| --- | --- | --- |
| {{ location }} | {{ issue }} | {{ remedy }} |

For PASS, write None instead of an empty table. Put all findings in this one report.

## Evidence and limits

What was inspected, what checks actually ran, and what remains unknown.

## Next decision

The exact repair, acceptance or delivery decision. A review does not grant authority.
