# Python installer, updater and migration

The supported installation interface is implemented in Python. It requires
Python 3.11+ and Git. The source checkout provides `bin/install.py`,
`bin/update.py` and `bin/migrate.py`; an installed copy of the migration tool is
available at `.HOST/bin/migrate.py`, where `HOST` is `codex` or `claude`.

## Install

From a source checkout, install into a new or existing target and select the host:

```bash
python -I bin/install.py --target ./my-project --host codex
```

Use `--host claude` for Claude Code. The installer installs the selected workflow
files and runtime; it does not create a virtual environment. The runtime launcher
uses an existing host-specific environment (such as `.codex-venv` or
`.claude-venv`) or project `.venv` when available, then falls back to system
Python. `--dry-run` previews the operation. Existing conflicting files are
reported for reconciliation; installation does not overwrite them silently.

## Update

Updates use an immutable source revision and a reviewed transaction plan. The
installed `update.py` first produces a preview; inspect the complete changes and
file actions before applying. Apply the exact plan with its SHA-256 digest:

```bash
python -I .codex/bin/update.py --apply UPDATE_PLAN.json \
  --reviewed-plan-sha256 REVIEWED_PLAN_SHA256
```

By default, the updater applies non-conflicting entries and preserves customized
conflicts. It reports `complete: false` if required entries remain preserved.
Pass one or more `--select TARGET_RELATIVE_PATH` options to apply only selected
paths. `--select-all` selects every reviewed path, including conflicts, and
requires each selected conflict to have a reviewed `backup-and-replace`
resolution. The SHA-256 must identify the exact reviewed plan bytes. The updater
checks source and target state again before writing, records a recoverable
backup, and rolls back a failed transaction.

## Migrate an existing separate `.ai` layout

Migration is a two-step, reviewed operation. Preview from a source checkout:

```bash
python -I bin/migrate.py --source SOURCE_REPOSITORY --ref PIN \
  --target PROJECT_ROOT --host codex --local --plan MIGRATION_PLAN.json
```

Inspect the plan and its conflicts. Apply it by explicitly selecting the reviewed
entries:

```bash
python -I bin/migrate.py --apply MIGRATION_PLAN.json \
  --reviewed-plan-sha256 REVIEWED_PLAN_SHA256 --select-all
```

Alternatively, use repeatable `--select TARGET_RELATIVE_PATH` arguments to choose
specific plan paths. `--select-all` includes every entry, including legacy copies
and backups; unresolved conflicts still stop apply unless the reviewed plan
resolves them with `backup-and-replace`. Migration apply always requires an
explicit selection.

`install.py --migrate-existing` invokes migration preview only. It does not apply
the plan; save it with `--plan` if needed and use `migrate.py --apply` separately.
The migration keeps original `.ai` files. Legacy runtime and hook trees are
copied under `.HOST/legacy/` so sibling imports continue to work, while the new
runtime remains under `.HOST/engineer/bin/lib/`. Legacy bytes that cannot be
decoded as UTF-8 are copied without text transformation. The migration manifest
records original sources; later pinned updates can proceed while those originals
remain unchanged. Modified or newly added legacy sources require a fresh
migration preview.

Migration is not a deletion or cleanup operation: retain the source `.ai` tree
and review the generated plan, backups and resulting manifest as part of the
change record.
