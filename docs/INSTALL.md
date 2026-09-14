# Install and set up the workflow

Use Python 3.11+ and Git on Windows, macOS or Linux. The installer downloads the
template from GitHub and installs PyYAML into a dedicated `.ai-venv`. Python's
`venv` and pip must be available. GitHub and the configured pip package index need
to be reachable. It does not require a GitHub login for this public template.

One command to download and run it, creating `./my-project`:

```text
python -c "from urllib.request import urlopen; exec(urlopen('https://raw.githubusercontent.com/Tasaddar12/ai-engineering-template/main/.ai/install.py').read())" --target ./my-project
```

Use `python3` on macOS/Linux if needed. For an existing project, use `--target .`
from its root or assigned worktree. This executes the repository's script in
memory; the saved-file commands below are an alternative.

## Download and run

For a new project, run the following from its intended parent directory. Change
`./my-project` to your destination. For an existing project, use its root or an
assigned worktree instead; use `.` when already there.

PowerShell:

```powershell
$installer = Join-Path ([IO.Path]::GetTempPath()) ([IO.Path]::GetRandomFileName() + '.py')
try {
    Invoke-WebRequest -UseBasicParsing 'https://raw.githubusercontent.com/Tasaddar12/ai-engineering-template/main/.ai/install.py' -OutFile $installer
    python $installer --target './my-project'
    if ($LASTEXITCODE -ne 0) { throw 'Workflow installation failed' }
} finally {
    Remove-Item -LiteralPath $installer -ErrorAction SilentlyContinue
}
```

macOS / Linux:

```sh
(
  installer="$(mktemp)" || exit 1
  trap 'rm -f "$installer"' EXIT
  curl -fsSL 'https://raw.githubusercontent.com/Tasaddar12/ai-engineering-template/main/.ai/install.py' -o "$installer" &&
    python3 "$installer" --target './my-project'
)
```

These commands execute code from this repository's `main` branch. To inspect it
first, download the URL to a local file and read it before running Python. To pin
an installation, replace `main` in the URL with a reviewed commit ID and pass that
same ID with `--ref COMMIT`. The installer prints the template revision it fetched.

From a local template checkout, the equivalent is:

```text
python .ai/install.py --target /path/to/project
```

The local script still fetches `main` from GitHub by default. Use
`--source /path/to/template --ref COMMIT` for a local, committed template revision.
Uncommitted source edits are not installed.

## What setup does

- Copies `.ai/`, repository skills, blank `.planning/` records, workflow guides
  under `docs/`, and `changes.log` for attribution/adaptation references.
- Excludes template maintenance history, its root README, tests and CI settings.
  Existing application code, README, Git history and remotes remain intact.
- Preserves an existing `AGENTS.md` and appends the template entry instructions
  once. Adds local workflow ignore rules to `.gitignore` without replacing it.
  These two files must use UTF-8; other encodings stop setup before copying.
- Checks all destination conflicts before copying. Identical files are accepted;
  differing workflow files or directories stop installation and list conflicts.
  Linked paths (including junctions) are refused.
- Initializes Git if the target is outside a repository. An existing Git root
  or linked worktree keeps its repository. A subdirectory of another repository
  is rejected to avoid installing at the wrong level.
- Creates `.ai-venv`, installs runtime requirements, and runs phase status as a
  smoke check. It does not install agent CLIs, configure credentials, register
  slash commands, fill project identity, commit files or publish anything.

This is an initial installer, not an updater for customized workflow files.
Use `--dry-run` to fetch and preview without changing the target. Use
`--skip-deps` to copy files without creating a virtual environment or contacting
the package index. Repeating the same install with `--skip-deps` preserves
identical files and does not duplicate the appended instructions/ignore block.

An existing `.ai-venv` is preserved: rerun with `--skip-deps` and use its Python to
install `.ai/runtime/requirements.txt` if dependency repair is needed. Network or
dependency failures return a nonzero exit code; files already installed remain
available for inspection and retry. Conflict detection is a preflight check,
not a transaction protecting against concurrent writers or disk failures.

## Existing projects and worktrees

For adoption by an agent, follow the [worktree procedure](../.ai/commands/worktree.md)
and run the installer against its assigned immediate-child worktree. For example,
after verifying the primary checkout and ensuring `.worktrees/` is ignored:

```text
git worktree add .worktrees/ai-setup -b codex/ai-setup HEAD
python /path/to/downloaded/install.py --target .worktrees/ai-setup
```

If this is the first bootstrap in a repository without workflow rules, a human
can install directly into its root, review the changes, and commit the installed
workflow before handing off to an agent. A worktree created from HEAD only gets
committed files. Subsequent agent edits and commits follow the installed
worktree procedure. Preserve any
conflicting guidance and reconcile it explicitly; the installer has no overwrite
switch. It leaves unrelated dirty files alone.

## Finish onboarding

**Commit the human bootstrap first when installing into a primary checkout.**
A newly initialized repository has no HEAD until its first commit, so it cannot
create the worktree required for agent onboarding. An existing repository also
needs the installed files committed before they can travel into a new worktree.
Git needs your author name and email configured for this step.

For a brand-new, otherwise empty project, review the installed files and run:

```text
git add -- AGENTS.md .ai .agents/skills .planning docs changes.log .gitignore
git commit -m "Install AI engineering workflow"
```

If the directory contained existing files, inspect `git status` and stage only
the installer additions and reviewed instruction/ignore changes; the directory
arguments above can also stage unrelated work. If installing into an already
assigned worktree, the agent can review and commit setup there directly.

Activate the environment from the project directory:

```powershell
.\.ai-venv\Scripts\Activate.ps1
python .ai/runtime/phase.py status
```

```sh
. .ai-venv/bin/activate
python .ai/runtime/phase.py status
```

If PowerShell prevents activation, run `.\.ai-venv\Scripts\python.exe` directly.
Keep this environment active when starting the coordinator so runtime subprocesses
using `python` can find the dependency. Install and authenticate your chosen agent
CLI separately. The [runtime guide](../.ai/runtime/README.md) describes configuration.

Give the agent your project description and the appropriate
[onboarding prompt](ONBOARDING-PROMPTS.md). It should inspect existing code,
preserve useful guidance, fill project intent, set actual worker routes and
nonempty verification commands, run baseline checks, and commit reviewed setup
in its assigned worktree. A successful install with an empty phase list proves
the runtime starts; onboarding establishes project readiness.

The virtual environment is local to this checkout. Before removing a setup
worktree, retain any local data you need; create an environment in your continuing
checkout using `python -m venv .ai-venv` and its Python's
`-m pip install -r .ai/runtime/requirements.txt` as needed.
