# Execute-Phase — TDD Gate (Runtime Enforcement)

> Loaded by `execute-phase` workflow and `executor` agent when the assignment requires TDD (#4011 — the gate no longer requires MVP mode; MVP may imply TDD, but TDD never requires MVP). Defines the runtime gate that blocks behavior-adding tasks until a failing-test commit exists.

## When this gate fires

The committed assignment requires TDD through `type: tdd` or `tdd="true"`, and the task changes behavior. A mode flag is not a substitute for the assignment. Configuration changes are classified by their observable effect, not by file suffix.

## What the gate checks

For each task gated by TDD, the executor MUST verify (before running the implementation step):

1. **A failing-test commit exists.** Search git log on the current branch for a commit matching `test({phase}-{plan})` whose subject mentions the same plan as the current task. The commit must touch a test file (`*.test.*`, `*.spec.*`, `tests/**`).
2. **The test was actually red — INTENTIONALLY (#3770).** Read `engineer/references/tdd.md`, "Red-Green-Refactor Cycle", RED step 4, and follow its complete evidence contract before GREEN. That section owns format selection (TAP, including Node/Vitest; JUnit XML, including Surefire/Failsafe; swift-testing console; or Python `unittest` text), reporter reruns, report freshness, the classifier invocation, and semantic inspection. Require `RED_EVIDENCE_OK` for the actual run and verify the planned target assertion failed for the intended reason. An `INVALID_RED` verdict, unsupported format, or failed semantic assessment trips this gate; self-attestation cannot substitute for machine validation. A `RED:` prefix or `(RED)` tag in the commit message is not evidence.
3. **No implementation commit yet.** No `feat({phase}-{plan})` commit may exist for the same plan ID before the failing-test commit.

If any check fails, the gate trips. A non-zero exit from `engineer_run query check.tdd-red-evidence RED_RECORD.json` (`69` `UNAVAILABLE`: the record could not be read, #5170) is a command failure that has NOT authorized GREEN — the gate trips. For check 2, an `INVALID_RED` classifier verdict or a failed semantic assessment trips the gate (halt reason `invalid_red`) — the executor MUST halt and block the implementation step.

## What "behavior-adding task" means

A task is behavior-adding when its effect changes an observable contract and the assignment requires TDD. Classify configuration by effect rather than extension: a YAML authorization change can add behavior, while a source comment does not. Pure documentation or fixture-only changes may be inapplicable with an explicit reason.

## What happens when the gate trips

The executor MUST:

1. Halt before running the task's implementation step.
2. Emit a structured halt report:

   ```
### TDD GATE TRIPPED — Plan {plan_id}, Task {task_id}

   Reason: {missing_red_commit | red_commit_not_failing | feat_before_test | invalid_red}

   Behavior expected to be tested:
   - {first behavior bullet}

   Required next step:
   1. Write a failing test for the behavior above.
   2. Commit it as: test({phase}-{plan}): {short description}
   3. Re-run /execute-phase
   ```

3. Exit the current group cleanly and preserve prior commits.
4. Record the gap and first continuation in the assigned SUMMARY Remaining. The coordinator reconciles shared STATE; the worker does not write it.

## Escalation: end-of-phase TDD review under TDD

The coordinator performs end-of-phase TDD evidence review under the consuming execute-phase workflow. Required missing evidence remains blocking.

Required RED/GREEN evidence is blocking. The coordinator records the review table and reconciles the gap; no force flag waives it. Preserve the user instruction if checks are deferred and do not report a passing verification until required evidence is actually available.

## What this gate does NOT do

- It does not enforce REFACTOR commits. REFACTOR remains optional (per `engineer/references/tdd.md`).
- It does not check test quality (the test could be trivially weak). That's the planner's job. It DOES check that the RED failure was intentional — the target test failing an assertion (#3770).
- It does not start implementation by running tests. During RED, the executor runs the planned test and captures its result, rerunning the planned target with a supported reporter when the first report is unsupported (`tdd.md` RED step 4); before GREEN, this gate inspects that persisted evidence, git history, and test assertion. The implementation step starts only after the RED gate passes.
- It classifies configuration by observable effect; pure documentation is inapplicable only with an explicit reason.

## Compatibility with assigned discipline

Apply this gate to every assigned `type: tdd` plan or `tdd="true"` task. Honor explicit user test deferral and keep the deferred evidence pending. Refactor only changed code needed by the authorized outcome; unrelated cleanup needs separate scope.
