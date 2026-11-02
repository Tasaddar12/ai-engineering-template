# Installer review corrections

Captured base: `93852b60592af885fab55204c58b104dcbf8d9c8`.

The review identified two blocking hook defects and one ownership-reporting defect.
All three are corrected within the installer and its fixture regressions:

- Claude refresh removes only exact managed command subhooks, including the exact
  legacy command generated before shell quoting. Mixed groups retain user sibling
  hooks, sibling order, matcher, timeout and other metadata. A single managed guard
  registration is added after the preserved groups.
- Hook commands shell-quote each argument and use native forward-slash executable
  and script paths. Literal dollar signs, apostrophes, spaces and shell substitution
  syntax in installation paths remain data. The guard's advisory validation is
  unchanged.
- Installation completeness requires matching manifest ownership records and
  expected bytes/modes for every current canonical export. Applying one of five
  identical but unowned exports remains incomplete. Applying the remaining
  ownership records completes it; an unresolved customization remains incomplete,
  and an explicitly backed-up replacement can restore completeness.

## Verification

Only targeted sequential tests ran in disposable fixtures:

- `python -m unittest discover -s tests -p test_installer_runtime.py -k reviewfix -v`
  passed 3 tests in 36.675 seconds. These execute real installer operations, preserve
  a mixed Claude group containing both old and new managed commands, exercise
  partial ownership, and execute the actual registered Codex and Claude hook
  commands from special-character paths. The hook still reports an out-of-checkout
  write target.
- `python -m unittest discover -s tests -p test_installer_runtime.py -k conflicts_are_incomplete -v`
  passed 1 test in 25.807 seconds. It verifies preserved customization, incomplete
  ownership, recoverable replacement backup, and restored completeness.
- `git diff --check` passed.

No broad local suite, benchmark service, remote push or merge was performed. The
coordinator owns integrated CI and final review/publication. No installer-scope
blocker remains from these three findings.
