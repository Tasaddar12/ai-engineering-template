# Verify a completed plan

## Purpose

Check that a completed plan's delivered work matches its acceptance, current specs
and observed behavior. Use before merge or for retrospective verification.

## Inputs

A plan with implementation complete in review (review_type: result), or a done plan;
its task/feature references, affected specs, exact branch/revision, environment,
agreed checks and available review/test evidence.

## Gates

Before running checks: [action-approved](../gates/action-approved.md) for the agreed
validation scope. Additional inspection can identify missing evidence without executing.
Before merge: [delivery-ready](../gates/delivery-ready.md), using this verification
report as evidence. Verification supplies no merge authority.

## Steps

1. The orchestrator identifies the plan, checked-out revision, baseline/diff and
   completion evidence. If the plan is incomplete, report FAIL with remaining work.
   Record the exact revision and any pending diff; before merge use a clean commit.
2. Map every task and acceptance condition to its feature, owning spec and required
   observation. Include every affected spec and agreed regression check; never infer
   completion from checked boxes alone.
3. The tester runs agreed checks; e2e covers agreed journeys across system boundaries.
   Reuse evidence only when its revision, environment and scope still apply.
   A documentation-only plan uses agreed document checks; explain why product
   journeys are not applicable. Never describe them as executed tests.
4. Compare actual results with both the approved outcome and current specs. The
   reviewer inspects the full relevant diff independently of the implementor when
   implementation review is required. Link that review rather than treating
   verification as a substitute for it.
5. Return plan-verification.md with PASS only when every required acceptance,
   spec comparison and check passes with current evidence and no unresolved
   in-scope defect. Failed, unavailable, stale or unrun required checks produce FAIL.
   Not applicable needs a scope-based reason; it cannot waive a required check.
6. Separate confirmed defects from suspected drift. Recommend linked FIX or INTAKE
   records through the report workflow. Propose repairs without performing them.
7. The orchestrator returns a decision summary. Record authorized evidence in the
   mutable plan's validation section. For a done plan, append a journal entry linked
   to the plan and revision; preserve its historical record. A report-only request
   returns the report without changing repository files.

## Output and handoff

An evidence matrix, overall PASS/FAIL, limits and next action. Before merge, delivery
uses this report for the exact intended revision and required hosting checks.
A later relevant change invalidates affected verification and requires rechecking.

## Stop conditions

Do not repair code/specs, rewrite historical plans, move stages or merge from this
command. Missing scope or authority leaves the affected check NOT_RUN and the overall
verification FAIL; report what would resolve it.
