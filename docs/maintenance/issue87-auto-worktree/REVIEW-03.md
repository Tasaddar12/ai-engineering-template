---
revision: 9f762c305572004e76f44f8572566b02bc04b234
diff_base: 47593a3d3f71739bd146a6c2c3590798d7c73c2e
reviewed: 2026-10-16T00:52:18Z
status: issues_found
---

# Joined native/planning review

Independent repository code-reviewer (`gpt-6.1-sol/high`) reviewed 25 source,
consumer, installer and test paths across the frozen PR93..PR97 own boundary.
It ran no tests, changed no files and created no children. The exact input was
clean. Earlier CR-01/02/03 and DOC-01 corrections remain present.

## CR-STACK-01: BLOCKER - migration fixture assumes the old hook inventory

`tests/test_install_migration.py:358-359` selects the first non-Agent PreToolUse
matcher. The joined inventory places destructive-git-guard.py first, so this
selects the shell matcher rather than source-prewrite.sh's editing matcher.
The editing-group assertion at line391 consequently fails (expected1, actual0).
After correcting this selector, the canonical complete command counter still
cannot match the migrated counter at lines403-410: its old four-script filter
excludes destructive-git-guard.py and planning-integrity.sh.

Repair only this fixture and its summary. Select the actual source-prewrite.sh
handler identity and derive migrated identities from the complete canonical
managed inventory. Preserve event/matcher/command/commandWindows comparisons,
editing order, both advisory registrations, user-hook preservation and legacy
path absence. Run the affected method and complete migration suite.

Root independently reproduced this exact failure: 1 test /4.025s, exit1,
assertion1!=0, no setup/import error. Ubuntu CI38831468504 reproduced the same
sole failure:746 tests/271.014s,15 skips. Windows was cancelled after the known
failure; this run supplies RED evidence only, never a GREEN receipt.

## Production assessment

No additional demonstrated production correctness/security defect was found.
One exact registered native-adapter set governs Workspace selection,
snapshot/warning bypass and structured native OSError conversion. Registration
is validated before the exception; ordinary success/error planning warnings
remain. Installer union, native ticket/provider/session route, classification,
six workflow consumers and changed tests were traced. Advisory guard and
.planning have empty own-boundary diffs. Live host movement remains unverified.
