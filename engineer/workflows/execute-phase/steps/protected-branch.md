# Session branch preflight

Read `engineer_run query git.base-branch --raw` and the existing phase session identity. Compare `git rev-parse --show-toplevel` and `git branch --show-current` with the recorded session worktree and branch. If the current branch is the default branch, stop execution and open or reuse the phase session first. Do not continue on a protected branch, switch the user's branch, or infer permission to create work in an unrelated checkout. Re-run the identity preflight inside the returned session checkout before any executor dispatch or integration.
