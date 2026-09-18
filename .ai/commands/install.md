# Install and set up the workflow

Use Python 3.11+ and Git on Windows, macOS or Linux. The installer downloads the
template from GitHub and installs PyYAML into a host-specific virtual environment. Python's
`venv` and pip must be available. GitHub and the configured pip package index need
to be reachable. It does not require a GitHub login for this public template.

Choose the host integration when creating `./my-project`:

```text
python -c "from urllib.request import urlopen; exec(urlopen('https://raw.githubusercontent.com/Tasaddar12/ai-engineering-template/main/.ai/install.py').read())" --target ./my-project --host codex
python -c "from urllib.request import urlopen; exec(urlopen('https://raw.githubusercontent.com/Tasaddar12/ai-engineering-template/main/.ai/install.py').read())" --target ./my-project --host claude
```

Use `python3` on macOS/Linux if needed. For an existing project, use `--target .`
from its root or assigned worktree. This executes the repository's script in
memory; the saved-file commands below are an alternative.

Choose `--host codex` or `--host claude`; the downloaded script defaults to Codex.
An installed `.claude/install.py` defaults to Claude when repeated locally.
Commands, agents, rules and runtime are installed inside the selected host directory.
Complete skills are installed directly at the host discovery location. A fresh
installation has no separate `.ai` directory. Project records remain under `.planning`.

| Installed location | Codex | Claude Code |
|---|---|---|
| Root instructions | `AGENTS.md` | `CLAUDE.md` with the complete project instructions |
| Rules, guides, templates and runtime | `.codex` | `.claude` |
| Commands | `.codex/commands` | `.claude/commands` |
| Agents | `.codex/agents/*.toml` plus full `.md` methods | `.claude/agents/*.md` with model frontmatter |
| Complete skills, discovered directly | `.agents/skills` | `.claude/skills` |
| Hook registration | `.codex/config.toml` | `.claude/settings.json` |
| Local Python environment | `.codex-venv` | `.claude-venv` |
| Initial worker routes | Codex | Claude Code |

References in installed instructions, skills, procedures and runtime routes point
to the selected host layout. Agents stay under `agents` and commands
stay under `commands`. Codex TOML definitions explicitly select a model and direct
the agent to read its full Markdown role; Claude roles explicitly select their
model in Markdown frontmatter. See [native host models](../agents/README.md#native-host-models)
for defaults and the separate runtime-route behavior. A fresh Claude installation uses CLAUDE.md and `.claude/skills`.

The Claude directory is lowercase `.claude`, including on Windows. These are
project files intended for Git. Once committed, they propagate into fresh Git
worktrees along with rules, full skills and hook implementations. The
installer never copies your home `.codex`/`.claude`, credentials, trust approvals,
session history, or local settings. It leaves existing worker routes authoritative.

## Hooks and existing host settings

Selected profiles add advisory `PreToolUse` and `PostToolUse` registrations for
the existing [Bash hook scripts](../hooks/README.md). Existing hook groups and
unrelated settings are retained; identical registrations are not added twice.
Invalid JSON/TOML, duplicate keys, incompatible hook structures, edited managed
registrations or conflicting instruction blocks stop setup before any writes.
Claude JSON settings may be reformatted; existing values are retained. Codex hook
tables are appended to `config.toml`, preserving existing text and settings.
Incompatible inline hook arrays stop preflight instead of rewriting user settings.

Use `--no-hooks` to skip adding registrations. This preserves any existing hooks;
it does not disable or uninstall them. Existing disabled-hook settings, personal
overrides and managed policies still apply. Codex uses inline hook tables in `.codex/config.toml`. Existing TOML settings and hooks are retained. Codex configuration uses TOML. See [inline hooks](https://learn.chatgpt.com/docs/config-file/config-advanced#hooks).

Codex needs a version supporting project lifecycle hooks, a trusted project, and
review of each new or changed hook in `/hooks`. The installer does not grant
trust. See [Codex hooks](https://learn.chatgpt.com/docs/hooks) and
[config layers](https://learn.chatgpt.com/docs/config-file/config-basic).
Claude uses project settings and root CLAUDE.md; inspect `/hooks` and `/status`
after opening the project. See [Claude settings](https://code.claude.com/docs/en/settings),
[shared instructions](https://code.claude.com/docs/en/memory#agentsmd) and
[hooks](https://code.claude.com/docs/en/hooks). Restart a host if it has not picked
up new project files. Installed registrations are not proof of trusted live execution.

Python 3.11+ and Git must be on PATH for installation and the runtime. Hooks run
Bash directly. On Windows, the Codex launcher locates Git Bash beside the Git
executable, so WSL's `bash.exe` does not intercept the hook. Claude uses Git Bash. Hook commands locate their script from the active Git checkout, and
the scripts inspect payload paths. No separate Python hook adapter is installed.

To repeat the selected installation from the same template revision, use its
installed script. For example, in a Claude project:

```text
python .claude/install.py --target . --host claude --skip-deps --ref COMMIT --dry-run
python .claude/install.py --target . --host claude --skip-deps --ref COMMIT
```

Replace COMMIT with the revision that installed the workflow. A newer template
can conflict with customized or older files and requires reconciliation. Existing
project context, settings and runtime config remain authoritative; choosing a
host does not rewrite an existing project's worker routes.

When updating the former 40-turn defaults, reconcile both Claude limit surfaces:
set the inherited `.planning/config.yaml` `execution.claude_max_turns` to null and
remove inherited `maxTurns: 40` from `.claude/agents/{coder,doc-writer,code-reviewer,verifier}.md`.
Preserve any limit explicitly requested by the user and all unrelated configuration.
The installer preserves existing config and conflicting customized files, so copying
new runtime files alone does not remove an old cap. Follow the runtime guide's
[turn-limit contract](../runtime/README.md#independent-component-review-and-bounded-assignments).

An older installation with a separate `.ai` directory needs migration in an
assigned worktree. The installer refuses to leave that older workflow beside a
new host layout. Use the migration mode below to preserve existing project data
and custom material. Changing `--host` alone is not a migration command.

## Migrate an existing `.ai` and `.planning` project

Use an assigned worktree with the existing setup committed. Download the current
installer as described below, then preview the selected destination:

```text
python /path/to/install.py --target . --host claude --migrate-existing --skip-deps --dry-run
python /path/to/install.py --target . --host claude --migrate-existing --skip-deps
```

Use `--host codex` for Codex. Omit `--skip-deps` to create the selected host's
virtual environment and install its requirements. The old `.ai-venv` is left
intact; it is not copied into the new environment.

Migration preflights the entire change and creates a verified copy of the
original files under the ignored `.workflow-backups/` directory before writing.
Each snapshot has a `files/` tree with the originals and a `MANIFEST.json` recording
their paths, SHA-256 hashes and file modes. Its own ignore file also protects an
incomplete backup when setup fails before the project ignore rules are updated. Keep that local
backup until you have reviewed and tested the migration; it is not included in
Git commits or automatically propagated to another worktree. The backup holds
the original bytes for recovery, including replaced runtime files and settings.

- All existing `.planning` records, phase summaries, specs, decisions and history
  are preserved. Only necessary workflow/virtual-environment paths in config are
  translated; existing custom worker commands and checks remain authoritative.
  An unchanged template-default config selects the new host's worker defaults.
- Existing rules, templates, skills and custom workflow material move into the
  selected host directory. Local paths in supported text guidance are translated;
  unknown binary files retain their bytes. Shipped runtime, hook and installer
  files are refreshed from the selected template revision, with their originals
  retained in the backup.
- The selected root entry gets current workflow instructions while preserving
  custom guidance.
- Existing native settings and hooks are retained and merged. Conflicting native
  files, linked paths and ambiguous instruction blocks stop preflight rather
  than overwrite a second setup. Original files and empty directories are removed
  from `.ai` only after backup; no separate `.ai` directory remains on success.
  Ignore patterns for relocated custom workflow paths move with those paths.

Review the reported refreshed files and the Git diff, reconcile any local runtime
customizations from the backup, run the selected host's `runtime/phase.py status`
and your project checks, and commit the migration slice. A Claude migration
preserves customized worker routes even when they invoke Codex; update those
routes deliberately if the project should run only Claude workers.

PLAN ownership and Read first paths must name the actual installed files before
dispatch. Migration does not add aliases or historical path mappings.

Migration does not modify Git-common-directory checkpoints, running processes or
other worktrees. Finish or reconcile old attempts with their original runtime
before starting new work; changed runtime inputs invalidate old verification.
Do not remove the original backup when inspecting a failed or interrupted setup.

## Download and run

For a new project, run the following from its intended parent directory. Change
`./my-project` to your destination. For an existing project, use its root or an
assigned worktree instead; use `.` when already there.

PowerShell:

```powershell
$installer = Join-Path ([IO.Path]::GetTempPath()) ([IO.Path]::GetRandomFileName() + '.py')
try {
    Invoke-WebRequest -UseBasicParsing 'https://raw.githubusercontent.com/Tasaddar12/ai-engineering-template/main/.ai/install.py' -OutFile $installer
    python $installer --target './my-project' --host codex
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
    python3 "$installer" --target './my-project' --host codex
)
```

These commands execute code from this repository's `main` branch. To inspect it
first, download the URL to a local file and read it before running Python. To pin
an installation, replace `main` in the URL with a reviewed commit ID and pass that
same ID with `--ref COMMIT`. The installer prints the template revision it fetched.
Replace `codex` with `claude` in either command as needed. The download URL always
names the upstream packaging script; it is independent of the installed layout.

The saved or installed script also fetches `main` from GitHub by default. Use
`--source /path/to/template --ref COMMIT` for a local, committed template revision.
Uncommitted source edits are not installed.

## What setup does

- Installs reusable tooling and full instructional templates into `.codex` or
  `.claude`, and complete skills into `.agents/skills` for Codex or `.claude/skills`
  for Claude. Commands and prompts live in `commands`, with
  supporting material in `guides`. No files are installed into the project's `docs/` directory. Source attribution remains
  in third-party notices.
- Creates a project agent entry point and clean onboarding-pending planning records
  from dedicated installation assets. It does not copy the source repository's
  `AGENTS.md`, illustrative requirements, phases, metrics or project identity.
- Preserves existing PROJECT, REQUIREMENTS, ROADMAP, STATE and config files as
  authoritative. Onboarding reconciles them with actual code and user intent.
- Preserves existing application code, README, Git history and remotes.
- Preserves the selected root entry file, AGENTS.md or CLAUDE.md, and appends
  complete project workflow instructions once in a delimited block.
  Adds local ignore rules to `.gitignore`
  without replacing it. Files receiving appended text must use UTF-8; other
  encodings stop setup before copying.
- Checks all destination conflicts before copying. Identical resources are accepted;
  differing reusable tools/guides or incompatible directories stop installation
  and list conflicts. Existing project records are preserved rather than conflicts.
  Linked paths (including junctions) are refused.
- Initializes Git if the target is outside a repository. An existing Git root
  or linked worktree keeps its repository. A subdirectory of another repository
  is rejected to avoid installing at the wrong level.
- Creates `.codex-venv` or `.claude-venv`, installs runtime requirements, and runs phase status as a
  smoke check. It registers selected-host hooks and installs complete skills. The AI references
  commands and agents directly in their installed folders. Setup does not install
  agent CLIs, configure credentials, fill project identity, commit files or publish anything.

This is an initial installer, not an updater for customized workflow files.
Use `--dry-run` to fetch and preview without changing the target. Use
`--skip-deps` to copy files without creating a virtual environment or contacting
the package index. Repeating the same install with `--skip-deps` preserves
identical files and does not duplicate the appended instructions/ignore block.

An existing host virtual environment is preserved: rerun with `--skip-deps` and
use its Python to install the selected host's `runtime/requirements.txt` if
dependency repair is needed. Network or
dependency failures return a nonzero exit code; files already installed remain
available for inspection and retry. Conflict detection is a preflight check,
not a transaction protecting against concurrent writers or disk failures.

## Existing projects and worktrees

For adoption by an agent, follow the [worktree procedure](worktree.md)
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

For a brand-new, otherwise empty Codex project, review the installed files and run:

```text
git add -- AGENTS.md .codex .agents/skills .planning .gitignore
git commit -m "Install AI engineering workflow"
```

For a fresh Claude project, stage `CLAUDE.md`, `.claude`, `.planning` and
`.gitignore` instead.

If the directory contained existing files, inspect `git status` and stage only
the installer additions and reviewed instruction/ignore changes; the directory
arguments above can also stage unrelated work. If installing into an already
assigned worktree, the agent can review and commit setup there directly.
Inspect individual paths before staging a pre-existing host directory; never
stage personal settings or credentials.

Activate the environment from the project directory. Codex examples:

```powershell
.\.codex-venv\Scripts\Activate.ps1
python .codex/runtime/phase.py status
```

```sh
. .codex-venv/bin/activate
python .codex/runtime/phase.py status
```

For Claude, replace `.codex-venv` with `.claude-venv` and run
`python .claude/runtime/phase.py status`. If PowerShell prevents activation, use
the selected environment's `Scripts/python.exe` directly.
Keep this environment active when starting the coordinator so runtime subprocesses
using `python` can find the dependency. Install and authenticate your chosen agent
CLI separately. The [runtime guide](../runtime/README.md) describes configuration.

Give the agent your project description and the appropriate
[onboarding prompt](onboard.md). Once onboarding is complete, use
[goal planning](goal-plan.md) to define the first goal or order several goals
into phases. The agent should inspect existing code,
preserve useful guidance, fill project intent, set actual worker routes and
nonempty verification commands, run baseline checks, and commit reviewed setup
in its assigned worktree. A successful install with an empty phase list proves
the runtime starts; onboarding establishes project readiness.

The virtual environment is local to this checkout. Before removing a setup
worktree, retain any local data you need; create an environment in your continuing
checkout using `python -m venv .codex-venv` and its Python's
`-m pip install -r .codex/runtime/requirements.txt` as needed. Use the matching
`.claude-venv` and `.claude/runtime/requirements.txt` paths for Claude.
