<!-- generated-by: doc-writer -->
# Engineer workflow template

Engineer provides reusable agent methods, commands, workflows and complete
instructional templates, backed by a Python runtime for project planning and
execution records. It supports Claude and Codex installations.

## Install into a project

Use Python 3.11 or newer and Git. The runtime and installer use only the Python
standard library; the shell launcher and shell workflow examples require a POSIX
shell, such as Git Bash on Windows.

Clone this source repository, select the revision to install, and preview an
explicit target and host:

```sh
git clone https://github.com/Tasaddar12/ai-engineering-template.git
cd ai-engineering-template
SOURCE="$(pwd)"
PIN="$(git rev-parse HEAD)"
TARGET="/absolute/path/to/your/project"
python -I bin/install.py --source "$SOURCE" --ref "$PIN" \
  --target "$TARGET" --host codex --local --dry-run --plan install-plan.json
```

Review the plan, then apply that exact plan with its SHA-256. The
[install guide](docs/INSTALL.md) gives the commands, Claude and global options,
validation, update, migration and rollback procedures.

Installation exports the selected host namespace (`.codex/` or `.claude/`),
integrates managed host settings and an instruction entry, and records ownership
in `engineer-install/manifest.json` inside that namespace. Merely copying this
checkout into a project does not register its commands or roles.

After installation, use `/onboard` or `/new-project` to establish the adopting
project's real identity, requirements and roadmap. Configure its actual
verification commands before relying on workflow verification. Project records
are created in `.planning/`; this source repository does not supply a fake
adopting project or completed execution history.

## Use the runtime

From the source checkout, inspect the runtime without installing a host:

```sh
python -I engineer/bin/engineer.py query runtime-identity --pick packageName --raw
python -I engineer/bin/engineer.py query help
```

The identity command prints `engineer-runtime`. In an installed Codex project,
the corresponding entry is `.codex/engineer/bin/engineer.py`; Claude uses
`.claude/engineer/bin/engineer.py`. The POSIX `engineer_run` launcher sits beside
the Python entry. See the [runtime guide](engineer/bin/README.md).

`/phase`, `/discuss-phase`, `/plan-phase`, `/execute-phase`, `/verify-work` and
`/ship` cover the main delivery flow. `/quick` handles a bounded change;
`/capture` saves an idea. A command selects its workflow; the workflow directs
agents and calls runtime operations. Implementation and merge still require the
user's applicable authorization.

## Source layout

| Path | Purpose |
|---|---|
| `agents/` | Full agent methods and role catalog |
| `commands/` | Command entry points and command catalog |
| `engineer/workflows/` | Orchestration procedures |
| `engineer/references/` | Supporting methods and contracts |
| `engineer/templates/` | Complete artifact templates |
| `engineer/bin/` | Python runtime and POSIX launcher |
| `hooks/` | Host advisory hooks |
| `bin/` | Pinned installer, updater, migrator and export helpers |
| `skills/` | Source command skills |
| `scripts/` | Source migration and validation tools |
| `tests/` | Current runtime, installer and source-tool regressions |

For maintenance, start with [AGENTS.md](AGENTS.md) and
[CONTRIBUTING.md](CONTRIBUTING.md). Historical overhaul requirements remain in
[PLANNED-UPDATES.md](PLANNED-UPDATES.md); they do not assert that every proposed
feature has been implemented. Git history preserves the removed duplicate layout
and earlier maintenance records.

## Update an installation

`bin/update.py` previews changes from an explicit local source and revision.
Apply the exact reviewed transaction with its file hash. Existing project records,
unmanaged files and instructions outside managed blocks are preserved; modified
owned files are reported as conflicts for reconciliation. Use `bin/migrate.py`
for a legacy installation and select its reviewed destination paths explicitly.
See [updates and migration](docs/INSTALL.md#update-an-existing-installation).

## Validation and attribution

Run the applicable checks listed in [CONTRIBUTING.md](CONTRIBUTING.md).
Installation success is separate from project acceptance and does not prove that
every workflow or host integration has been exercised.

Adapted source provenance is recorded in
[THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md).
