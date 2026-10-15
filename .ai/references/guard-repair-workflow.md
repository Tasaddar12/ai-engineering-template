<!-- generated-by: doc-writer -->
# Guard repair workflow

Use this procedure when repairing a security or static guard: a check that
decides whether an operation is denied, warned about or allowed. Establish the
actual parser and operation, challenge both bypasses and false positives, and
observe a failing behavioral regression before changing guard logic. A regex
match or source-string assertion alone cannot establish a security repair.

This procedure supplies evidence obligations within the approved assignment.
[Phase authority](../RULES.md#phase-authority), owned paths, isolation and
[canonical threat tracking](git-workflow.md#canonical-threat-tracking) still
apply. The coordinator routes independent agents and owns shared records,
integration and publication. The coder owns test implementation and repairs.

## Repair sequence

1. **Locate the boundary.** Inspect the public entry point, callers, existing
   executable tests, parser/normalization layers and protected operation. State
   the expected deny/warn/allow result and accepted legitimate behavior. Follow
   the input to its consumer; do not assume two parsers interpret it alike.
2. **Challenge the design independently before implementation.** Have a different
   reviewer or scout propose bypass and false-positive cases from that boundary.
   A coder reviewing their own list is not independent case generation. Route
   this through the coordinator's existing dispatch and isolation authority;
   workers do not gain permission to dispatch implementation agents.
3. **Record the paired matrix.** For each scenario give its ID, concrete safe
   input, parser/entry point, expected result, rationale, regression test name
   and observation. Cover each dimension below or record a concrete reason it
   does not apply at this boundary. Use only encodings, methods and bodies the
   entry point actually accepts; do not invent extra decoding or routes.
4. **Write and run regressions before guard logic changes.** Exercise the affected
   public entry point in temporary repositories, harmless fixtures or stubbed
   providers. Never use real destructive targets. Pair deny/bypass cases with
   legitimate controls. Assert side effects, exit/result and preservation when
   those are part of the contract, rather than checking only warning text.
5. **Inspect RED at the captured revision.** A named target assertion must fail
   for the expected behavioral reason before the implementation commit. Record
   expected and actual results. Missing tools, setup or syntax errors, parser
   crashes, zero discovered tests, unrelated failures and unexpected passes are
   `INVALID_RED`. Fix the test/setup or report the precise blocker; do not
   manufacture failure or weaken the expected result to obtain a receipt.
6. **Implement, then verify.** Change only owned scope. Rerun the same scenarios
   for GREEN, then relevant regression suites and required checks. New in-scope
   discoveries extend the matrix and tests before more guard logic changes.
   Record any refactor and its passing rerun; if no refactor is needed, say so
   without creating an extra commit. Preserve the actual RED and implementation
   commits under the ordinary slice commit rules.
7. **Return evidence and obtain independent review.** Supply the receipt fields
   below. The independent reviewer checks case completeness and evidence order,
   adds counterexamples and reruns relevant safe cases. Missing required evidence
   remains a gap even when the final suite passes. Untested variants do not
   become safe by inference from a green suite.

## Paired scenario matrix

These examples guide case design. They are not executed evidence or authority to
operate on a real checkout or service. Substitute safe inputs supported by the
actual parser and record the concrete contract for that boundary.

| Dimension | Bypass/edge candidate | Legitimate paired control | Required observation |
|---|---|---|---|
| Case | Mixed-case command, option, method or key where accepted | Same spelling in an inert argument or description | Parsed operation receives the intended policy; inert text remains allowed |
| Empty/missing | Empty value, omitted field, whitespace or null where supported | Valid optional omission or empty harmless payload | Defined deny/warn/allow result; no accidental privileged fallback |
| Encoding | Supported percent, Unicode, escape or nested representation | Literal escaped text or valid encoded benign value | Guard and consumer agree after actual decoding; no speculative decoder |
| Alternate methods/bodies | Equivalent destructive verb/flag; POST, JSON, form or body override if accepted | Read-only method/flag and harmless JSON/form body | All accepted routes to the operation covered; valid reads preserved |
| Quoting/tokenization | Quoted executable/path, spaces, escapes, option ordering and separators accepted by the shell | Quoted inert text, a path containing spaces and ordinary scratchpad write | Actual argv/parser semantics govern the result, not a substring |
| Parser differences | Tool JSON versus raw shell; Bash versus PowerShell or API route if supported | Equivalent benign input through each supported entry | Producer and consumer paths tested independently; unsupported variants explained |
| Existing advisory policy | PR86 primary-checkout edit/scratchpad notice | Properly isolated or read-only call | Existing warning/success contract retained; destructive enforcement has its separate owner |

Use one row per concrete scenario, including paired controls. An unrun row says
`Pending`, with the missing prerequisite; it must not say passed. For example,
for a hypothetical JSON guard whose documented policy denies DELETE but allows
GET against a stubbed fixture resource:

| ID | Concrete safe input | Parser/entry point | Expected | Rationale | Regression test | Observation |
|---|---|---|---|---|---|---|
| M-01 | `{"method":"DELETE","resource":"fixture-item"}` | Hypothetical JSON guard with stub provider | Deny; stub deletion count 0 | Protect destructive route | `test_delete_keeps_fixture` | Pending; example only |
| M-02 | `{"method":"GET","resource":"fixture-item"}` | Same JSON guard and stub | Allow; read count 1, deletion count 0 | Preserve legitimate read | `test_get_reads_fixture` | Pending; example only |
| M-03 | `{"method":"GET","description":"DELETE fixture-item"}` | Same JSON guard and stub | Allow read; no deletion | Destructive spelling is inert text | `test_description_is_inert` | Pending; example only |

An actual repair also supplies the other dimensions or a boundary-specific reason
such as “this entry accepts an already-decoded JSON object with no raw shell
route; shell quoting is not parsed here,” supported by inspected callers.

## Evidence receipts

Record input revision, scenario IDs, exact command, exit code, test name,
expected/actual assertion, RED commit, GREEN commit/revision and final result.
Include the original RED observation, not a reconstruction after implementation.
Preserve safe logs or enough assertion detail for independent review; exclude
sensitive payloads from publishable material under canonical threat tracking.

This hypothetical receipt shows the required shape; its symbols are placeholders
and its numbers are illustrative, not a test run:

```text
Input revision: <base revision before guard changes>
Scenario: M-01; control: M-02
Command: python -m unittest discover -s tests -p test_example_guard.py -v
RED: exit 1; test_delete_keeps_fixture
Expected: deny, deletion_count == 0
Actual assertion: 0 != 1 (stub recorded a deletion)
Control: test_get_reads_fixture passed; read_count == 1
RED commit: <test-only commit>; implementation follows this observed RED
GREEN: <implementation commit/revision>; same command, exit 0
Final: M-01 denies with deletion_count == 0; M-02 still reads once
Regression checks: <exact commands, exits and tested revision>
Refactor: none needed, or <commit and passing rerun>
Independent review: <reviewer, revision, counterexamples and safe rerun results>
```

If a runner instead crashes importing a dependency, record `INVALID_RED` and the
dependency/check it blocks. It supplies no authority to claim a completed
RED/GREEN cycle. Fix available setup within scope or return the blocker while
continuing independent authorized work.

The fixture-copy tests in `tests/test_guard_repair_contract.py` protect direct
instruction links and target existence. They cannot prove that future agents
obey this procedure or that a runtime guard is secure.

## Concise updates and bounded approvals

Report the outcome or finding, the next meaningful check and a specific blocker.
Use concrete paths or revisions when they help; avoid repeating the plan or a
large checklist. An approval request identifies the exact action, target,
effect, missing authority and why it is needed. Continue unrelated authorized
work while the dependent action awaits a decision.

| Category | Boundary and handling |
|---|---|
| Network, DNS, tunnel and infrastructure changes | Reuse explicit approval for its recorded target and effect. A new external route, DNS change, tunnel exposure or infrastructure mutation beyond that scope needs a concrete request before that action. Ordinary already-authorized reads/checks do not become a blanket network approval prompt. |
| Tool/package installation | Inspect installed tools first and reuse available runners. For a new install outside recorded authority, identify the exact tool/version/source, purpose and affected environment; request that bounded install. Missing capability blocks only its dependent check. This procedure grants no installation authority. |
| New scope or changed decisions | Show the concrete acceptance or ownership change and obtain the human decision through the coordinator. Routine fixes and implementation choices inside existing scope continue. Preserve prior explicit phase implementation and delivery authorization; internal plan/execute/verify transitions do not reopen it. |
| Existing phase authority and destructive actions | Phase discussion and explicit implementation permission remain required when not already supplied. Existing deletion, exact-target cleanup, credentials/spending and merge limits still apply. No automatic approval, fuzzy permission match or merge authority is introduced. |

PR86 worktree guard notices remain advisory, including ordinary scratchpad writes:
they warn and return success. This procedure changes no hook, parser or runtime
gate. Existing stop conditions retain their own contracts; destructive-operation
enforcement is a separate control. A draft PR grants no merge authority, and an
explicit no-merge instruction continues to apply.
