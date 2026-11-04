<!-- generated-by: doc-writer -->
# Install, update and migrate Engineer

The `bin/` tools export a pinned local Git revision into a selected Claude or
Codex namespace. They do not fetch a source repository implicitly. Use Git and
Python 3.11 or newer; no third-party Python packages are required. The POSIX
launcher and shell workflow examples require a POSIX shell. Use Git Bash on
Windows, or call the Python runtime directly.

## Preview a fresh installation

From the source checkout, choose an actual target project and host:

```sh
SOURCE="$(pwd)"
PIN="$(git rev-parse HEAD)"
TARGET="../your-project"
python -I bin/install.py --source "$SOURCE" --ref "$PIN" \
  --target "$TARGET" --host codex --local --dry-run --plan install-plan.json
```

`--ref` is resolved to an immutable commit. Only committed source at that revision
is exported; uncommitted source edits are not part of the installation. Review
the plan's target, host, revision, findings, file actions and conflict resolutions.
`--dry-run` previews without applying the export. `--plan` writes the complete
transaction to the explicitly named JSON file.

Use `--host claude` for Claude. For a global installation, select the intended home
root with `--target` and replace `--local` with `--global`; for example,
`--target "$HOME" --host codex --global`. Global scope affects the chosen home
namespace and its instruction entry. Do not choose it when the intended scope is
one project.

The installer supports both hosts with explicit scope; there is no implicit
host, revision or target selection. `--no-hooks` omits the installer's advisory
hook registration. `--skip-deps` is a compatibility flag: the current runtime
uses only the Python standard library.

## Apply the exact plan

After reviewing `install-plan.json`, compute its current file hash and apply it:

```sh
PLAN_HASH="$(python -I -c 'import hashlib,pathlib,sys; print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())' install-plan.json)"
python -I bin/install.py --apply install-plan.json \
  --reviewed-plan-sha256 "$PLAN_HASH"
```

The hash identifies the exact plan file bytes; it is not the plan's internal
snapshot token. If the plan is changed during reconciliation, review it again
and compute the hash from the final file. Application regenerates the export
from the captured revision and rejects source-exporter drift, stale target
content or changed ownership metadata.

The exported assets live under `<target>/.codex/` or `<target>/.claude/`.
The ownership manifest is
`<target>/<namespace>/engineer-install/manifest.json`, with the source, pinned
revision, host, scope and owned-file digests. Local scope adds a managed block to
the project's root `AGENTS.md` or `CLAUDE.md`; global scope uses the namespace's
instruction entry. Existing instructions outside the managed block remain.
Generated skills are placed under the selected namespace. Codex configuration
uses paths such as `skills/onboard/SKILL.md`, resolved from `.codex/config.toml`'s
directory; Claude discovers its native skills directory. Host settings add the
advisory hook unless `--no-hooks` is selected. The hook locates the active project
at invocation time, including when a session starts in a subdirectory, and uses
`python` from `PATH`. Backups and transaction journals live under the same
`engineer-install/` directory.

Local role, workflow, command and managed-entry references start at the project
root, using `.codex/` or `.claude/` without the install machine's directory or a
worktree name. Global references resolve the active host home when used through
`${CODEX_HOME:-$HOME/.codex}` or `${CLAUDE_CONFIG_DIR:-$HOME/.claude}`. Transaction
plans and journals retain concrete source and target identities for review,
drift checks and recovery; those records do not define runtime instruction paths.

Each Codex agent has a small `.codex/agents/<role>.toml` wrapper with its required
name and description, `model = "gpt-6.1-sol"` and
`model_reasoning_effort = "high"`. Its `developer_instructions` tells the agent to
read and follow the complete installed `.codex/agents/<role>.md` counterpart
before working, and to stop and report if that file is unavailable. The full
method remains in Markdown. This is an instruction to read a file, rather than a
native TOML include; Codex reads its own counterpart, while Claude retains its
separate `.claude/agents/` files. For example, a local executor wrapper contains:

```toml
developer_instructions = "Read and follow the complete role at .codex/agents/executor.md before acting. Read its local workflow and referenced shared rules; the assignment bounds your scope. Phase implementation requires the user's explicit instruction to implement that phase. If that file cannot be read, stop and report the missing counterpart."
```

The path has no quotation marks inside the instruction text. The outer quotation
marks delimit the TOML string.

The retired `guides/` and `maintenance/` directories are excluded from exports,
including their `engineer/` and namespace-root variants, even when selecting an
older source pin. They are absent from the current template. Existing retired
files or user additions are preserved by the update transaction; remove confirmed
legacy leftovers separately within the authorized cleanup scope.

## Validate the installation

For a local Codex install, run from the target project's Git checkout:

```sh
cd "$TARGET"
python -I .codex/engineer/bin/engineer.py query runtime-identity --pick packageName --raw
python -I .codex/engineer/bin/engineer.py query update-context --config-dir .codex --runtime codex
python -I .codex/engineer/bin/engineer.py query help
```

The identity must be `engineer-runtime`. Check the context result's resolved
installation, pinned revision, host, target and completeness, and inspect the
manifest and generated host configuration. For Claude, use `.claude` and
`--runtime claude`. For global scope, use the selected home target. Where a POSIX
shell is available, also exercise the sibling `engineer_run` launcher:

```sh
sh .codex/engineer/bin/engineer_run query runtime-identity --pick packageName --raw
```

Return to the source checkout and rerun the preview with the same source,
revision, target, host and scope; unchanged
managed exports should be reported as unchanged. Installation does not onboard
the project or run its product checks. Restart or refresh the host as needed to
load its configuration, then use `/onboard` or `/new-project` with the actual
project intent. The runtime creates `.planning/` project records through
`project.init`; configure the project's real verification commands there.

## Update an existing installation

Fetch source updates explicitly with Git, inspect them and select the revision.
Then preview against the existing installation:

```sh
python -I bin/update.py --source "$SOURCE" --ref "$PIN" \
  --target "$TARGET" --host codex --local --plan update-plan.json
```

Review the complete plan, compute its file SHA-256 as above, and run
`python -I bin/update.py --apply update-plan.json --reviewed-plan-sha256 "$PLAN_HASH"`.
Update previews are not applied merely by generating them.

An owned file modified locally is a conflict rather than an automatic overwrite.
Preserve it or reconcile it explicitly; a selected conflict requires the reviewed
`backup-and-replace` resolution. Use repeated `--select` options to limit
application to exact target-relative paths. Unselected work can leave an
installation incomplete. Unmanaged additions, retired owned paths and project
planning records are preserved. Revalidate after updating.

## Migrate a legacy installation

For a project with a legacy separate `.ai` tree or host `runtime/` layout,
preview the mapping:

```sh
python -I bin/migrate.py --source "$SOURCE" --ref "$PIN" \
  --target "$TARGET" --host codex --local --plan migration-plan.json
```

Inspect each old path, destination, conflict and backup-only entry. Global
migrations report `global-migration-reference` and refuse application when legacy
namespace references occur in shell, Python, JSON, TOML or YAML files; reconcile
those references for each file's consumer before applying. Markdown and text
references are rewritten to portable host-home references.

Review the final plan and compute its file SHA-256. Apply only explicitly
selected target-relative destination paths:

```sh
python -I bin/migrate.py --apply migration-plan.json \
  --reviewed-plan-sha256 "$PLAN_HASH" \
  --select .codex/engineer/bin/engineer.py
```

The single selection above illustrates the syntax; select the full reviewed set
needed for the intended migration. Migration preserves original legacy files and
records original bytes in recoverable backups for selected mappings. It does not
silently delete the old tree or project history. Cleanup of an adopting project's
legacy content requires its own scoped authorization and evidence that useful
customizations were preserved. The removed authoring layout remains available
in Git history.

`bin/install.py --migrate-existing` previews the same migration operation;
`bin/install.py --update` previews an update. Use their explicit plan/application
flow rather than assuming those options immediately apply changes.

## Recover a transaction

Keep the returned backup path. To roll back that exact transaction:

```sh
python -I bin/update.py --target "$TARGET" --host codex \
  --rollback "$TARGET/.codex/engineer-install/backups/TRANSACTION_ID"
```

Replace `TRANSACTION_ID` with the actual returned directory. Rollback validates
the target, journal, backup digests and current file state before restoring
files. If files have changed since application, preserve the evidence and
reconcile the reported drift rather than overwriting later work.
