# Component TDD Evidence Gate

> Local procedure adapted from the upstream execution gate. This is an agent
> evidence review, not an additional command or automatic Python runtime gate.
> See [TDD](tdd.md) and [third-party notices](../../THIRD-PARTY-NOTICES.md).

## Applicability

Apply when the committed assignment requires TDD (for example `type: tdd` or a
`tdd="true"` task) and the task adds or changes behavior. MVP status is irrelevant.
Read the task's expected behavior and files: a behavior change in non-test source
requires RED evidence before implementation. A documentation-only or test-only
task is not behavior-adding. Treat executable configuration according to its
actual effect, not its extension. Missing expected behavior in a TDD assignment
is a preparation gap, not permission to bypass the gate.

## Before implementation

1. **Identify the RED commit.** Inspect `git log --oneline <assigned-base>..HEAD`
   and `git show --stat <red-commit>` for the specific regression test. A matching
   `test(<phase>-<plan>)` subject helps locate it but is not proof; inspect its
   diff and match its assertions to the assigned behavior.
2. **Review intentional failure evidence.** Record the tested revision, exact
   argv or command, exit code, discovered target test, expected result, actual
   assertion failure and output excerpt in the assigned SUMMARY. Confirm the
   target assertion failed for the intended missing behavior. Syntax errors,
   discovery failures, fixture crashes, unrelated assertions and an unexpectedly
   passing test are INVALID_RED. A nonzero exit or RED commit label alone does
   not authorize GREEN. Use the actual runner output; there is no evidence-check
   SDK command in this repository.
3. **Check order.** Inspect the changed source and commit history to confirm
   the implementation was not already present before the failing-test evidence.
   Commit prefixes alone cannot establish order or behavior. Record the RED
   hash, implementation hash and GREEN evidence separately.

## If evidence is invalid or missing

Stop dependent implementation and return this result to the coordinator:

```text
### TDD GATE TRIPPED — Plan {plan_id}, Task {task_id}
Reason: {missing_red_commit | red_commit_not_failing | implementation_before_test | invalid_red}
Behavior expected to be tested: {observable outcome}
Evidence: {revision, test identity, result or missing record}
Next step: repair the target test/fixture/discovery, record a real intended
failure and commit the RED slice before resuming implementation.
```

Preserve previous commits; do not roll back unrelated work or mutate shared
STATE. Put the exact task and gate failure in assigned SUMMARY Remaining. The
coordinator reconciles continuation using the local phase-resume procedure.
No force-gate flag exists. An explicit user instruction deferring tests must be
honored and reported as unverified work; it does not fabricate RED or GREEN.

## Completion review

After implementation, run the target and relevant neighboring checks under the
project's authorized validation scope. Record GREEN output and revision. A
required RED or GREEN result that is missing or failed prevents claiming the
TDD outcome verified. The coordinator carries gaps into phase verification;
workers do not mark the shared phase complete.

Refactor assigned changed code only to remove duplication, simplify control flow,
improve names, extract constants/helpers or meet project conventions. Preserve
behavior and rerun affected checks; do not create a no-op refactor commit. Review assertion quality separately: a passing test that suppresses
the symptom or repeats implementation is weak evidence. This method consumes
real check results; inspecting Git history alone does not run or verify a test.
