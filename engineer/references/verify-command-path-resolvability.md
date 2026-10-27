# Verify Command Path Resolvability (#2401)

> Reference file for plan-checker agent. Loaded on-demand via `@` reference.

**Question:** Does each `<automated>` command's target directory actually resolve from the
executor's cwd (the project root)? Format sanity above asks whether the *pattern* can match;
this asks whether the command can *run at all*.

**Do not hand-reason the filesystem.** #2401 is precisely the failure of doing so: this
checker flagged a bad `cd ../../frontend` (correct), then prescribed two successively-wrong
replacement paths — the second citing a `package.json` that did not exist. Consume the
deterministic probe result, never re-derive it yourself.

The coordinator supplies `engineer_run query check.verify-command-paths PHASE` (or `--plan PLAN_PATH`) output as `{VERIFY_PATHS}` in the review packet when execution is permitted. The result carries `valid`, `findings` and detailed `commands` rows with `severity` and `reason`; consume the actual returned fields, not a guessed legacy shape. A structural/probe pass is not behavioral execution evidence.

When `{VERIFY_PATHS}` is absent, inspect literal command targets in the assigned source: resolve relative to the assigned checkout, check existence or an explicitly declared producer, and inspect the actual manifest/script. Preserve why probe execution is missing or deferred. Absence of output is not a silent pass and does not authorize running user-deferred checks.

The probe never executes PLAN command text. It recognizes supported literal forms, including a leading `cd <literal>` and `npm --prefix <literal>`, and flags dynamic targets it cannot establish. Do not supply a guessed replacement path. Report exact command, target, source plan/task, severity and reason to the planner.

**Process:** inspect every `.commands` row and reconcile `.findings` with `.valid`:

| `severity` | `reason` / condition | Action |
|---|---|---|
| `blocker` | Required literal target or declared script absent, without a real producing prerequisite | BLOCKER with the exact missing target and acceptance impact. |
| `warning` | `dynamic_path`, `outside_root`, `script_missing`, `manifest_unreadable`, or probe cannot ground the command | Report the actual reason and inspected scope; do not guess. |
| `none` | Existing supported target, or `pending_creation` with an explicit producer | No path finding; preserve the producer dependency. |

Inspect literal targets relative to the assigned project root; an absolute target outside it is `outside_root`, never silently accepted. If actual returned reasons differ, quote them faithfully and inspect their source contract rather than inventing a parser success.

Rules:
- **Report, never prescribe.** State the target that failed to resolve and what was missing.
  Choosing the replacement is the planner's job. Supplied `prior_verify_commands` must carry complete committed SUMMARY `checks_run` evidence; prior PLAN declarations are `prior_verify_candidates`, never proven runs.
- `status: pending_creation` means an earlier task in this phase creates that directory. **Not
  a finding.** Say nothing.
- `unresolvable` means the probe could not ground the path (a variable, glob, substitution, or
  `~`). That is a WARNING, never a BLOCKER — and never a licence to guess the literal path.
- `outside_root` covers two shapes: a bare ancestor climb (`cd ../..`) and an **absolute target
  outside the project root** (#4767). Both are ambiguous across worktrees; the absolute one is
  pinned to a single checkout, so under worktree isolation it runs against the wrong tree and
  passes. Report it as a WARNING with the target verbatim. Note the probe's root is the
  *orchestrator's*: an absolute path inside it passes here and still misfires under isolation,
  which is why the planner's path-form rule (root-relative, cwd at the checkout root) is the fix
  and this probe the backstop.
- A non-empty `readError` means the probe **could not look**. Report that as a WARNING in its
  own words; it is not a clean bill of health.
- `MISSING …` sentinels are Dimension 8's business — this dimension stays silent on them.
