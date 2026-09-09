# Git inspection safety

All Git subprocesses pass through the central command runner. For inspections that can
produce patch content, configured conversion and external diff programs are outside the
trusted primitive and must never execute.

The runner unconditionally inserts `--no-ext-diff` and `--no-textconv` immediately
after the subcommand in every allowed `git diff` and `git log` invocation after policy
validation. It never infers suppression from later tokens: those tokens may be option
values or path operands after `--`. This applies equally to configured program names
and explicitly allowed absolute Git executables. The normalized semantic argv,
including these suppressions, is retained in command results and evidence.

Inherited `GIT_*` settings are removed for every accepted Git executable form, and
protected configuration values disable repository hooks, filesystem monitors,
credential helpers, pagers, and global external diff commands. Caller-provided Git
global options, context overrides, `--ext-diff`, and `--textconv` remain forbidden, so
later arguments or configuration cannot opt helpers back in.

Verbose `git status` forms also produce diff content, but that command does not support
the suppression options. They are rejected before process creation, including bundled
short options and unambiguous long-option abbreviations. Option scanning stops at the
literal `--`, so names such as `-v` remain valid path operands. Non-verbose status
inspection remains available.
