<!-- generated-by: doc-writer -->
# Legacy layout retirement

The authoring repository now has one canonical Engineer source tree in
`agents/`, `commands/`, `engineer/`, `hooks/`, `bin/`, `scripts/` and `skills/`.
The old checked-in `.ai/` implementation and `.planning/` adoption skeleton are
removed. This prevents a source checkout from appearing to contain an active
installed workflow and an initialized customer project.

## Preserved material

The issue, pull-request and ADR templates move from the old tree to
`engineer/templates/`. The canonical Git workflow moves to
`engineer/references/git-workflow.md`. Third-party attribution moves to the root
`THIRD-PARTY-NOTICES.md`.

The removed PROJECT, REQUIREMENTS, ROADMAP and STATE records contained unfilled
adoption placeholders, not this repository's approved project identity. Removed
quick-task records recorded earlier template maintenance. Those records and the
old implementation remain available in Git history; no adopting project's
existing records are deleted by the installer.

[PLANNED-UPDATES.md](../PLANNED-UPDATES.md) preserves the historical requirements,
decisions and reconciliation rows. Its baseline is `9443672`, and its instructions
explain reading an exact historical path with `git show`. The integration of
PR 129 into PR 125 does not assert that all later proposed overhaul work has been
implemented or verified. The deferred workflow and documentation rewrites from
PRs 130–163 remain outside this integration; PR 129's history identifies its
selectively included follow-up changes.

## Test ownership

Dedicated tests for the removed runtime, installer and old prose contracts are
retired with that implementation; the exact module removals are recorded in the
Git change. Current Python runtime tests, including `test_engineer_runtime.py`
and `test_engineer_cli.py`, and the current installer/source-tool suites exercise
the retained layout. A removed legacy assertion is not evidence that its old
behavior has been independently verified in the new implementation. Validation
reports must identify the actual tested revision, commands and outcomes.

## Adoption remains explicit

Install through [the current installer](INSTALL.md). A host namespace and its
ownership manifest identify a pinned installation. After installation,
`/onboard`, `/new-project` or the runtime's `project.init` operation creates an
adopting project's actual `.planning/` records. Preserve that project's identity,
requirements, history, settings and custom instructions during future updates.

Repository cleanup and project migration are separate operations. The migrator
preserves legacy originals and backups; it does not use this authoring cleanup as
permission to remove an adopting project's legacy files.
