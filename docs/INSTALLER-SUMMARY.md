# Installer and runtime launcher validation

Base revision: `8e7b56b3cec9563a0361d317f0836f05f0f6c770` (PR 129 integrated into PR 125).

The current installer originally refused the complete workflow source because ten
JSON scope adapters still used JavaScript. The export translator now recognizes
those exact array readers, base selectors and argument encoders, preserves their
validation, and emits Python equivalents. Unknown runtime JavaScript remains a
blocking export finding.

Installed shell bootstraps quote paths as POSIX shell data and translate the
central resolver include to its installed location. The runtime shim converts its
computed script path with `cygpath` when Git Bash is present, fixing the reproduced
Windows App Execution Alias failure on `/tmp` paths. Native POSIX behavior retains
the original path.

Windows exports compare modes that Windows `chmod` can produce. An unchanged,
fully owned installation returns a no-op without rewriting assets, provenance,
transaction journals or the lock file. Unresolved customization conflicts make
previews incomplete; application preserves those files unless an exact reviewed
backup-and-replace resolution selects them.

The empty `skills/SKILL/` authoring stub is excluded. Source maintenance `scripts/`
are also excluded because they depend on the authoring checkout's Git history and
`PLANNED-UPDATES.md`; installed runtime commands and installer entry points remain
available under the selected host namespace.

## Evidence

- `python -m unittest discover -s tests -p test_installer_runtime.py -v`:
  8 tests passed in 123.381 seconds before the final maintenance-script packaging
  exclusion.
- `python -m unittest discover -s tests -p test_installer_runtime.py -k clean_installs -v`:
  the affected four host/scope installs and reruns passed after excluding source
  maintenance scripts (1 test in 57.333 seconds).
- The fixtures install the complete canonical source for Codex and Claude, both
  locally and globally; execute the installed Python runtime; parse Codex agent
  TOML and skill configuration; preserve existing instructions, settings, hooks and
  planning; verify identical bytes and modification times on reruns; exercise
  conflicts, explicit replacement backups, pinned updates, rollback and stale
  preview/token refusal; and execute Git Bash with literal special-character paths.
- The initial Git Bash fixture reproduced the Windows `/tmp` failure. After the
  shim repair, its targeted rerun passed (1 test in 10.767 seconds).
- The strengthened unknown-JavaScript test exercises the actual installer CLI
  against an unsupported Git source, confirms `export-blocked`, and confirms no
  target is created; its targeted rerun passed (1 test in 4.653 seconds).
- `git diff --check`: passed.

The tests validate generated native host configuration, not a launched interactive
Codex or Claude session. The final integrated repository and CI checks remain the
coordinator's responsibility. No Docker service or benchmark worktree was changed.
