# Issue 95 link repair summary

## Change

Updated the canonical T-SYNC-01 issue links in `docs/maintenance/issue87/SYNC-PLAN.md` and `docs/maintenance/issue87/SYNC-SUMMARY.md` to use `#user-content-t-sync-01`. The two existing documents otherwise retain their original bytes.

## Evidence and status

The coordinator reports that issue 95's saved body contains an explicit `<a name="t-sync-01"></a>` immediately before the unchanged T-SYNC-01 checklist entry. GitHub preserves this target as `user-content-t-sync-01`; following the saved canonical URLs and checking `document.querySelector(':target')` reached the intended target for all four risks. Issue 95 remains open pending final CI and merge. No issue closure is claimed.

## Verification

Static diff and whitespace inspection only. No local tests or configured checks were run. This link correction makes no behavioral or security enforcement claim.
