# TASK-006 Linux coordinator preflight and bounded correction

The committed owner candidate `c3c2ba21c6441abde52f6e340b29d0bf65910f8e`
was clean and changed only its three owned paths. It has not entered an independent
R1/R2 cycle. The coordinator discovered local Ubuntu-24.04 through WSL and ran the
declared task suite on Linux before freezing a review candidate.

The system Python was 3.12.3 with jsonschema 4.10.3, below the project's declared
`jsonschema>=4.18,<5`. The first run failed importing `referencing` before behavior
tests ran; its retained output is `TASK-006-linux-dependency-preflight.txt`. A project-
local Linux virtual environment with the declared dependency was then created.
An initial package-install invocation used WSL shell mode and interpreted the
version constraint as redirection. It did not install packages; its empty
`=4.18,` file in the workspace was verified and removed. The corrected invocation
used WSL `--exec` and installed the dependency successfully.

The exact task discovery command with that Linux environment then ran **18 tests**
and exited 1: **one failure, one error, one Windows-only skip**. Retained output:
`TASK-006-linux-behavior-preflight.txt`.

1. `test_native_terminator_does_not_infer_tree_quiescence_from_parent_exit` expected
   false, but the POSIX terminator returned true for an already-exited process.
   Source inspection shows the absent-process-group branch returns whether the
   parent has exited. The test's child was not launched as a new process group,
   so this does not establish termination of an owned group or all descendants.
2. The project-cwd subcase raised `ValueError: finished_at cannot precede started_at`
   while constructing evidence after a real command. The clock was real UTC time,
   not a synthetic fixture. This observed backward-clock result must be handled
   deliberately without fabricating timestamps or losing process evidence. Add a
   deterministic clock-regression probe rather than relying on another VM clock
   adjustment to reproduce it.

The owner is authorized to correct these bounded source/test/handoff issues in
the existing attempt and ownership, validate on Windows and Linux, and return a
new clean commit. Preserve honest unknown outcomes and actual clock observations;
do not weaken accepted DTO invariants or edit other tasks. No structural graph,
schema, permission, scope or prerequisite change is authorized or needed by this
decision. If investigation establishes a concrete prerequisite gap, report it.

This is a coordinator validation finding before the first independent review,
not a fabricated failed R1 cycle. Historical Windows passes and this Linux failure
remain retained. Fresh current-base validation and separate R1/R2 remain required.
TASK-006 stays running during the correction; its descendants remain undispatched.

Linux interpreter: `.ai/local/full-plan-linux-venv/bin/python` in the WSL-mounted
workspace. Use `wsl.exe -d Ubuntu-24.04 --cd <Linux worktree path> --exec <Linux
interpreter path> -m unittest discover -s tests/unit/commands/ -p test_*.py`.
The `--exec` form avoids interpreting argv through the default Linux shell.
