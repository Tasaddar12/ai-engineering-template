<!-- generated-by: doc-writer -->
# PR 125 installation documentation summary

The documentation replaces obsolete root entry points with the canonical
Engineer source layout and the pinned Python installation flow. README and
INSTALL distinguish authoring sources, installed host namespaces and
runtime-created adopting-project records. CONTRIBUTING names the current
Python and static checks. LEGACY-RETIREMENT identifies the preserved templates,
attribution and historical requirements without claiming deferred work complete.

The author inspected `bin/install_support.py`, `bin/install.py`, `bin/update.py`,
`bin/migrate.py`, `engineer/bin/engineer.py`, the runtime guide and project
initialization code. The documented CLI flags, preview/application distinction,
manifest location, update conflict handling, selected migration behavior and
rollback path follow those implementations.

Verification for this documentation slice is limited to source comparison,
owned-path diff review, `git diff --check` and Markdown link inspection. At the
docs-only base, four relocation destinations are owned by the coordinator:
the Git workflow, issue template, PR template and root third-party notices.
Their links require final integrated readback. Installer execution,
whole-suite validation, independent review and remote checks remain the
coordinator's integration work; this summary does not claim those have passed.
