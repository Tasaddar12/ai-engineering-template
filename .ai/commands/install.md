# Install and set up the workflow

Use Python 3.11+ and Git on Windows, macOS or Linux. The installer downloads the
template from GitHub and installs PyYAML into a dedicated `.ai-venv`. Python's
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

Use `--host both` to share a project between Codex and Claude Code. Omitting
`--host` selects Codex. Every profile installs the shared `.ai/` workflow,
canonical `.agents/skills/`, AGENTS.md and pending onboarding records.

| Profile | Native project integration | New worker routes |
|---|---|---|
| `codex` | `.codex/hooks.json`; Codex reads AGENTS.md and `.agents/skills/` | Codex |
| `claude` | `.claude/settings.json`, root CLAUDE.md importing AGENTS.md, `.claude/skills/` entry points | Claude Code |
| `both` | Both sets of native files | Codex; configure another route during onboarding if desired |

The Claude directory is lowercase `.claude`, including on Windows. These are
project files intended for Git. Once committed, they propagate into fresh Git
worktrees along with shared rules, full skills and hook implementations. The
installer never copies your home `.codex`/`.claude`, credentials, trust approvals,
session history, or local settings. It leaves existing worker routes authoritative.

## Hooks, host settings and adding another host

Selected profiles add advisory `PreToolUse` and `PostToolUse` registrations for
the [portable Python hook adapter](../hooks/README.md). Existing hook groups and
unrelated settings are retained; identical registrations are not added twice.
Invalid JSON, duplicate keys, incompatible hook structures, edited managed
registrations or conflicting instruction blocks stop setup before any writes.
Settings may be reformatted when groups are added; existing values are retained.

Use `--no-hooks` to skip adding registrations. This preserves any existing hooks;
it does not disable or uninstall them. Existing disabled-hook settings, personal
overrides and managed policies still apply. Codex config.toml is left untouched;
if it already has inline hooks, both sources load under Codex's normal rules.

Codex needs a version supporting project lifecycle hooks, a trusted project, and
review of each new or changed hook in `/hooks`. The installer does not grant
trust. See [Codex hooks](https://learn.chatgpt.com/docs/hooks) and
[config layers](https://learn.chatgpt.com/docs/config-file/config-basic).
Claude uses project settings and CLAUDE.md imports; inspect `/hooks` and `/status`
after opening the project. See [Claude settings](https://code.claude.com/docs/en/settings),
[shared instructions](https://code.claude.com/docs/en/memory#agentsmd) and
[hooks](https://code.claude.com/docs/en/hooks). Restart a host if it has not picked
up new project files. Installed registrations are not proof of trusted live execution.

Python 3.11+ and Git must be on the host's PATH. Codex uses `python3` on Unix and
`python` on Windows. Claude's shell hook probes `python3`, falling back to `python`;
its command shell requires Bash (Git Bash on Windows). The Python adapter itself
does not invoke Bash. Hook commands locate the Git checkout from their working
directory; the adapter uses the payload's `cwd`, even when `CLAUDE_PROJECT_DIR`
still names the primary checkout.

To add Claude to an existing installation from the same template revision:

```text
python .ai/install.py --target . --host claude --skip-deps --ref COMMIT --dry-run
python .ai/install.py --target . --host claude --skip-deps --ref COMMIT
```

Replace COMMIT with the revision that installed the shared files. Keep that
revision when adding a host; a newer template can conflict with customized or
older shared files and requires reconciliation. Adding Claude preserves existing
Codex integration and runtime config; it does not switch an active project's
workers. Switching profiles never removes the other host. Review the generated
diff, then commit and deliver it through the normal worktree procedure.

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
Replace `codex` with `claude` or `both` in either command as needed.

From a local template checkout, the equivalent is:

```text
python .ai/install.py --target /path/to/project
```

The local script still fetches `main` from GitHub by default. Use
`--source /path/to/template --ref COMMIT` for a local, committed template revision.
Uncommitted source edits are not installed.

## What setup does

- Installs reusable `.ai/` tooling, full instructional templates and repository skills.
  Procedures and prompts live in `.ai/commands/`, with supporting guides in
  `.ai/guides/`. No files are installed into the project's `docs/` directory. Source attribution remains
  in third-party notices.
- Creates a project agent entry point and clean onboarding-pending planning records
  from dedicated installation assets. It does not copy the source repository's
  `AGENTS.md`, illustrative requirements, phases, metrics or project identity.
- Preserves existing PROJECT, REQUIREMENTS, ROADMAP, STATE and config files as
  authoritative. Onboarding reconciles them with actual code and user intent.
- Preserves existing application code, README, Git history and remotes.
- Preserves an existing `AGENTS.md` and appends project workflow instructions
  once in a delimited block. Claude profiles similarly preserve CLAUDE.md and
  append a shared-instructions import. Adds local ignore rules to `.gitignore`
  without replacing it. Files receiving appended text must use UTF-8; other
  encodings stop setup before copying.
- Checks all destination conflicts before copying. Identical resources are accepted;
  differing reusable tools/guides or incompatible directories stop installation
  and list conflicts. Existing project records are preserved rather than conflicts.
  Linked paths (including junctions) are refused.
- Initializes Git if the target is outside a repository. An existing Git root
  or linked worktree keeps its repository. A subdirectory of another repository
  is rejected to avoid installing at the wrong level.
- Creates `.ai-venv`, installs runtime requirements, and runs phase status as a
  smoke check. It registers selected-host hooks and skill discovery entries, but
  does not install agent CLIs, configure credentials, register `.ai/commands/` as
  native slash commands, fill project identity, commit files or publish anything.

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

## Repair template context

When an installation contains template identity instead of project context, run:

```text
python -c "from urllib.request import urlopen; exec(urlopen('https://raw.githubusercontent.com/Tasaddar12/ai-engineering-template/main/.ai/install.py').read())" --target . --skip-deps --repair-template-context
```

Add `--dry-run` to inspect the writes and removals first. The repair recognizes
the original shipped content directly from its pinned Git release (allowing
LF/CRLF differences). Repair fetches that release from the selected source;
custom source repositories must retain the original release to support repair.
It replaces matching old workflow files and untouched example project records,
and replaces the exact old AGENTS entry (marked or unmarked) while preserving surrounding
user guidance. Real project records and config stay byte-for-byte intact.

Repair cleans matching source artifacts from the destination and preserves
existing or customized application documentation. Empty directories can remain
after cleanup. Use `--dry-run` for the exact proposed changes.
An edited old AGENTS block or customized conflicting tooling requires manual
reconciliation; the repair does not guess which user edits to overwrite.
Use an assigned worktree for agent-driven repair and review the diff before
committing. The source template repository itself is not a repair target.

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

For a brand-new, otherwise empty project, review the installed files and run:

```text
git add -- AGENTS.md .ai .agents/skills .planning .gitignore
git commit -m "Install AI engineering workflow"
```

If the directory contained existing files, inspect `git status` and stage only
the installer additions and reviewed instruction/ignore changes; the directory
arguments above can also stage unrelated work. If installing into an already
assigned worktree, the agent can review and commit setup there directly.
Also stage the selected native integration files shown by `git status`: `.codex`
for Codex; CLAUDE.md and `.claude` for Claude. Inspect individual paths before
staging a pre-existing host directory; never stage personal settings or credentials.

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
checkout using `python -m venv .ai-venv` and its Python's
`-m pip install -r .ai/runtime/requirements.txt` as needed.
