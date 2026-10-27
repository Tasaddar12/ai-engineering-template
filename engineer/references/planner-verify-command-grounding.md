# Verify Command Grounding (#2401)

## Distinguish candidates from executed evidence

Read `prior_verify_candidates` from prior PLAN declarations only as candidate commands. A plan says what should run; it proves no execution. `prior_verify_commands` is reserved for commands backed by committed complete SUMMARY `checks_run` evidence. For each such command preserve the evidence path, actual tested revision, argv, working directory, outcome and limitations. No implicit injection is assumed: missing provenance remains missing.

When the current task exercises the same interface or test story as a proven earlier run, prefer that grounded command after confirming the manifest/lockfile, target, script and environment still apply. Reuse the root-relative command verbatim only when all those inputs match. A remembered successful command or a PLAN candidate is not a passing receipt. Re-root an absolute harvested path before authoring a portable command and label the changed command unexecuted until it actually runs.

Ground every authored target relative to the executor's assigned checkout root. A `cd` or `npm --prefix` directory must exist or be explicitly produced by an earlier task; npm/make targets need the actual matching manifest and script. Prefer `npm --prefix apps/api run test` over a fragile ancestor traversal. If the location is unknown, request bounded discovery and preserve the gap rather than guessing a replacement directory. Record the exact command and intended failure signal in the plan.

**Run a count/match gate before it ships (#4927).** A gate you author â€” or one a `RESEARCH.md`
hands you â€” that counts or matches text (`grep -c`, `grep -q`, `rg`, `test -n "$(grep â€¦)"`) is a
claim about the tree, and two defects are invisible to reading and take one command to expose. You
have a shell when you author the plan, so, when the user permits execution, run each such gate against the **current tree** and write
the pre-change result next to it as its baseline (`# baseline at HEAD: 0`):

- **It already passes at HEAD.** `grep -c "Agent" .planning/PROJECT.md` returned `6` before any work
  existed, because the word sat in an unrelated row â€” the gate measures nothing and passes whether
  or not the work happens. Fix the gate: anchor it to the new heading, key, or line the task
  creates, or assert a delta from the recorded baseline.
- **Its literal can never match the deliverable.** `grep` is case-sensitive, so `grep -c "quickstart"`
  fails on a correct `## Quickstart`. Match the real casing of the text the task writes, or use
  `-i` when casing is not part of the contract.

A gate that is meant to prove a *negative* is checked the other way: it must pass after the work
and its baseline must show the thing was there to remove. Explicit user check deferral takes precedence: author the gate and record its baseline as pending; do not execute it or invent a pre-change result. Only read-only commands are safe to run
this way â€” run `grep`/`rg`/`test` gates; do not execute a gate that builds, installs, or writes.

**Root-relative, never absolute (#4767).** The paths in your prompt's `<required_reading>` are
absolute on purpose â€” a subagent's cwd may differ from the orchestrator's (#2376). That rule
covers prompt *inputs* only. Every path in the plan *body* â€” `<files>`, `<verify>`, `<automated>`,
task actions â€” is repo-root-relative, and every `<automated>` command assumes cwd at the checkout
root. An absolute path copied from the prompt into `<automated>` pins the command to the
orchestrator's checkout; under worktree isolation the executor's checkout is a different
directory, so the command `cd`s into the main tree, finds it, runs, and **passes against code the
worktree changed and the main tree did not**. The path probe reports such a target as
`outside_root` (a warning), but only when the target is outside the *orchestrator's* root â€” an
absolute path *inside* it is exactly the shape that passes the probe and still misfires under
isolation. The authoring rule is the fix; the probe is the backstop. It binds `prior_verify_commands`
too: a harvested command that carries an absolute path is re-rooted before reuse, never copied
verbatim â€” it "worked" in a run that may have been verifying the wrong checkout.
