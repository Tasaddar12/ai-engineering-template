# Validate a quick plan independently

Run only when VALIDATE_MODE is selected. Capture PLAN_REVIEWED_REVISION after the complete planner commit is integrated. Resolve plan-checker model and effort inline with engineer_run query resolve-model/resolve-effort, omitting inherit.

Dispatch `Agent(subagent_type="plan-checker", model=<resolved value>, effort=<resolved value>, prompt=<complete packet>)`. Give the actual quick goal, user constraints, PLAN_INPUT_REVISION, PLAN_REVIEWED_REVISION, complete plan, current source paths, role/template contracts and any continuation evidence. Check observable goal coverage, concrete actions, meaningful automated/fails_when checks, ownership/deletions/resources, dependency order, threat mitigations and documentation. The checker is read-only and returns `## PLAN REVIEW` with `Verdict: approved | needs-revision`, stable BLOCKER IDs, INFO and cited evidence.

ORCHESTRATOR RULE: wait for the worker and all partial continuations before touching its paths or accepting its coverage. A missing or malformed verdict is not approval. An approved verdict with an outstanding BLOCKER is unusable. Show INFO as advisory without forcing a revision.

On needs-revision, dispatch `Agent(subagent_type="planner", model=<inline resolved value>, effort=<inline resolved value>, prompt=<bounded correction packet>)`. The packet contains exact BLOCKER IDs, source and reviewed revisions, quoted evidence, locked acceptance, authoritative decision references, permitted plan paths and the smallest required correction. Read engineer/references/planner-revision.md in full. Do not replan from scratch unless the actual defects require it. Require committed owned changes and a precise return. After confirmed stop, integrate and capture a fresh reviewed revision, then dispatch a new independent checker; reuse evidence only for explicitly unchanged inputs and coverage.

**If the planner returns `## REVISION_CONFLICT`:** a conflict is not resolvable by re-running the
same loop, so it must not consume retry budget. Do NOT increment `iteration_count` and do NOT
re-spawn the checker yet. Present the conflict table and its alternatives to the user and ask
which to take: adopt a named alternative / override the named constraint and apply the hint /
amend the constraint itself. Every option resolves the conflict. Accepting the plan with the
blocker still open is NOT offered here — the blocking `required_property` still fails, and that
a changed acceptance decision must be explicit, recorded and replanned before approval.

A quick task has no phase review arbitration; the named locked-constraint decision requires the user.

Re-spawn the planner with the chosen resolution, then **re-evaluate its return from the top of
this handler** — do not fall through to the checker spawn below. A second conflict is still a
conflict, not a revised plan.

**Bounded:** A conflict naming the SAME `required_property` twice in a row (no successful revision in between) is a stall, and so is the
THIRD conflict return of this loop whatever property it names — alternating property names
would otherwise never trip the repeat rule and the path would be unbounded. Stop re-spawning and
route it to the same iteration-count check below, so declining to spend an iteration cannot make
this path unbounded.

**Otherwise (the planner returns a revised plan, not `## REVISION_CONFLICT`):** spawn checker again, increment `iteration_count`.

**If iteration_count >= 2:**

Display: `Max iterations reached. ${N} issues remain:` + issue list

Offer: 1) Record an explicit decision changing the named constraint, then replan and recheck, 2) Abort. Neither option calls an unresolved blocker approved. Preserve every existing accepted outcome outside that exact decision.
