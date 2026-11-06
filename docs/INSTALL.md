<!-- generated-by: doc-writer -->
# Install, update and migrate Engineer

The `bin/` tools export a pinned local Git revision into a selected Claude or
Codex installation layout. They do not fetch a source repository implicitly.
Use Git and Python 3.11 or newer; no third-party Python packages are required. The POSIX
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
the chosen target, host, revision, findings, file actions and conflict resolutions.
`--dry-run` previews without applying the export. `--plan` writes the complete
transaction to the explicitly named JSON file.

Use `--host claude` for Claude. For a global installation, select the intended home
root with `--target` and replace `--local` with `--global`; for example,
`--target "$HOME" --host codex --global`. Global scope affects the chosen home
namespace, instruction entry and skills directory. Do not choose it when the
intended scope is one project.

Global runtime execution honors `CODEX_HOME` and `CLAUDE_CONFIG_DIR`. Updating a
global installation requires `.codex` for Codex or `.claude` for Claude as its
namespace directory name; a different parent home directory is supported.
Update discovery and installer previews for custom namespace names stop with
`unsupported-global-namespace`, preserving that directory.

The installer supports both hosts with explicit scope; there is no implicit
host, revision or target selection. `--no-hooks` omits the installer's advisory
hook registration. `--skip-deps` is a compatibility flag: the current runtime
uses only the Python standard library. Installer and runtime entry points
suppress Python bytecode caches so execution does not add machine-specific cache
data to the installation.

## Apply the exact plan

After reviewing `install-plan.json`, compute its current file hash and apply it:

```sh
PLAN_HASH="$(python -I -c 'import hashlib,pathlib,sys; print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())' install-plan.json)"
python -I bin/install.py --apply install-plan.json \
  --source "$SOURCE" --target "$TARGET" --reviewed-plan-sha256 "$PLAN_HASH"
```

The hash identifies the exact plan file bytes; it is not the plan's internal
snapshot token. If the plan is changed during reconciliation, review it again
and compute the hash from the final file. Application regenerates the export
from the captured revision and rejects source-exporter drift, stale target
content or changed ownership metadata.

New schema 2 plans store `source` and `target` as `.` logical roots, including
plans written with `--plan`. Supply the actual source checkout and target again
with `--source` and `--target` when applying. A fresh-install plan can be applied
to a different explicitly chosen empty target when its recorded contents match;
the pinned revision, exporter digests and installation identity checks still
apply. Direct installation with the initial explicit source and target remains
available without a saved plan.

Codex skills are installed under `<target>/.agents/skills/<skill>/SKILL.md`,
including supporting files in each skill directory. For `--local`, `<target>` is
the project root; for `--global`, select your home directory so skills live in
`$HOME/.agents/skills`. This follows the
[official Codex skill locations](https://developers.openai.com/codex/build-skills).
Codex runtime, commands, agent definitions and configuration remain under
`<target>/.codex/`. Claude keeps its exports, including skills, under
`<target>/.claude/`.

Publication templates are authored only under the source repository's `.github/`
directory. A local installation for either host exports the eight issue forms
from `.github/ISSUE_TEMPLATE/` (Bug, Enhancement, Feature request, Docs issue,
Chore, Decision required, Security risk and UAT), their authoring guide, and the
`.github/PULL_REQUEST_TEMPLATE/enhancement.md`, `feature.md` and `fix.md` bodies
to the same paths in the target project.
The repository itself uses these templates too. A global installation keeps
these assets under `<target>/.codex/.github/` or `<target>/.claude/.github/`
for its runtime; it does not create a home-level `.github/` directory. Install
locally in a consumer repository to make its templates available on GitHub.
Template files participate in the same ownership, customization-conflict,
backup and rollback handling as other managed exports.

For PR creation on GitHub, select a separate body with the `template` query
parameter: `template=enhancement.md`, `template=feature.md` or `template=fix.md`.
These files provide task-specific Goal, Changes and Verification prompts and
retain the common required fields. Each includes full authoring guidance.
GitHub does not add an automatic PR type picker. Runtime `pr.open` accepts
`--template enhancement`, `--template feature` or `--template fix` to validate
the supplied body against that template; existing invocations select enhancement
when the option is omitted. The installer exports only these three PR bodies
and does not create a default PR template. Feature request is the dedicated issue
form for a new capability;
Enhancement retains the existing request shape for improving a capability.

The ownership manifest is
`<target>/<namespace>/engineer-install/manifest.json`. New schema 2 manifests
record `source = "."`, `source_kind = "git-snapshot"`, the pinned revision, host,
scope, owned-file digests and an installation ID. The matching ID is stored in
`engineer-install/identity.json`. Local scope adds a managed block to
the project's root `AGENTS.md` or `CLAUDE.md`; global scope uses the namespace's
instruction entry. Existing instructions outside the managed block remain.
Codex discovers `.agents/skills` automatically; the installer no longer adds
`[[skills.config]]` entries for generated skills. Its managed configuration block
still registers the advisory hook unless `--no-hooks` is selected. Claude
discovers its native `.claude/skills` directory and retains its host settings,
including the same optional hook. The hook locates the active project
at invocation time, including when a session starts in a subdirectory, and uses
`python` from `PATH`. Backups and transaction journals live under the same
`engineer-install/` directory.

Local role, workflow, command and managed-entry references start at the project
root, using `.codex/` or `.claude/` without the install machine's directory or a
worktree name. Generated runtime shell paths resolve the active Git root when
invoked, including from a nested directory. Global references resolve the active
host home when used through
`${CODEX_HOME:-$HOME/.codex}` or `${CLAUDE_CONFIG_DIR:-$HOME/.claude}`. Newly
written plans, manifests and transaction journals use logical roots and relative
file entries without recording the source checkout's or target's location.

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

Inside a Git checkout, an installed runtime rejects an `ENGINEER_ROOT` value
that conflicts with the active checkout before root-sensitive reads or writes.
Correct or clear a stale value before continuing. Source-checkout runtimes and
explicit-root operation outside Git retain their existing behavior.

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

Review the complete plan, compute its file SHA-256 as above, and apply it with
the explicit source and target:

```sh
python -I bin/update.py --apply update-plan.json \
  --source "$SOURCE" --target "$TARGET" --reviewed-plan-sha256 "$PLAN_HASH"
```

Update previews are not applied merely by generating them. For schema 2
installations, the runtime's `query update.changes` also requires an explicit
`--source` checkout and `--ref`; `update-context` provides no remembered
executable source checkout path.

An owned file modified locally is a conflict rather than an automatic overwrite.
Preserve it or reconcile it explicitly; a selected conflict requires the reviewed
`backup-and-replace` resolution. Use repeated `--select` options to limit
application to exact target-relative paths. Unselected work can leave an
installation incomplete. Unmanaged additions, retired owned paths and project
planning records are preserved. Revalidate after updating.

Updates to this layout preserve previously installed
`engineer/templates/issue.md`, `engineer/templates/pull-request.md` and
`engineer/references/git-workflow.md` as retired owned paths. Current publication
validation reads the `.github/` templates. Remove confirmed legacy leftovers
separately within the authorized cleanup scope.
Previously installed default PR templates are likewise preserved as retired
owned paths; the current installer does not export or recreate them.

For an older Codex installation, unchanged owned files in `.codex/skills` are
exported to `.agents/skills`; the old files remain preserved. The updated managed
configuration block removes the installer's old `[[skills.config]]` entries.
User configuration outside that block remains intact. A legacy counterpart whose
bytes differ from both its ownership digest and the new export becomes a conflict
on its `.agents/skills` destination, with `legacy_skill_path` and
`legacy_skill_before` identifying the original.
Preserving that conflict leaves the new export unapplied and the installation
incomplete. Reconcile the customization into the active skill location before
using it, or explicitly select `backup-and-replace` to install the pinned
canonical version. That resolution backs up the legacy bytes and keeps the
original file. Once the new path is owned, later updates use its ownership record
rather than treating the preserved old copy as a fresh conflict.

Additional legacy skill files, such as custom skills or supporting assets, report
`codex-skill-migration-required` and block ordinary update application. Preview
and apply the reviewed migration mapping below to carry them into `.agents/skills`.

A relocated Claude hook is retired only when its exact command is proven by a
digest-linked snapshot of the previously owned settings. Uncertain ownership
produces `legacy-hook-ownership-unresolved` and blocks application; reconcile the
ownership evidence before retrying. Other hooks in the same group are preserved.

## Migrate a legacy installation

For a project with a legacy separate `.ai` tree, host `runtime/` layout or
Codex `.codex/skills` directory, preview the mapping:

```sh
python -I bin/migrate.py --source "$SOURCE" --ref "$PIN" \
  --target "$TARGET" --host codex --local --plan migration-plan.json
```

Inspect each old path, destination, conflict and backup-only entry. For Codex,
`.ai/skills` and `.codex/skills` map to `.agents/skills`; Claude's `.ai/skills`
continues to map to `.claude/skills`. Existing canonical exports receive
backup-only legacy entries, while additional custom skills and assets receive
copy entries or conflicts when the destination exists. Customized canonical
counterparts still require the conflict reconciliation described above; migration
does not silently activate the stock version. Original files remain in place,
and selected mappings preserve their original bytes in transaction backups.

Global migrations report `global-migration-reference` and refuse application
when legacy namespace references occur in shell, Python, JSON, TOML or YAML files; reconcile
those references for each file's consumer before applying. Markdown and text
references are rewritten to portable host-home references.

Review the final plan and compute its file SHA-256. Apply only explicitly
selected target-relative destination paths:

```sh
python -I bin/migrate.py --apply migration-plan.json \
  --source "$SOURCE" --target "$TARGET" --reviewed-plan-sha256 "$PLAN_HASH" \
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

Replace `TRANSACTION_ID` with the actual returned directory. Keep
`engineer-install/identity.json` with the installation when moving the complete
project. Schema 2 journals use `target = "."`; rollback checks their host and
installation ID against that marker, then validates backup digests and current
file state before restoring files. This permits rollback after relocation and
refuses a backup copied from another installation. If files have changed since
application, preserve the evidence and reconcile the reported drift rather than
overwriting later work.

Legacy schema 1 journals retain their original target binding. Existing backup
bytes are preserved, including historical path data; the portable metadata
format applies to newly written records.
