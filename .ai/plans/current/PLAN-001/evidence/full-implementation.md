# Full implementation run

The user requested implementation of the full current plan on 2026-09-07.
The starting code commit is `501b512`. This run preserves the revised product
layout and the existing bootstrap rather than restoring the superseded package
layout. Repository implementation uses the recorded Sol/xhigh override and
independent Astra/xhigh reviews.

## Baseline

On Windows with Python 3.12 and the declared `jsonschema` dependency:

- `python -m unittest discover -s tests -v`: 24 tests passed.
- `python src/validate_foundation.py`: passed; 27 schemas, 121 artifacts,
  one plan, 39 tasks, 280 unordered pairs, three historical manifests, and
  173 local links checked.

The first attempt using the bundled Python without a virtual environment could
not import `jsonschema`. Installing the declared development dependency into
an ignored local environment resolved that environment issue; no source fix
was required.

## Execution boundary

Graph r3 was proposed at the start of this run. Its independent review failed
on installed helper dependency ownership and missing digest-compatibility
requirements. Graph r4 corrects these requirements and passed all 12 ISO
checks. The original failed graph and review are retained in `history/engine-r3`.
TASK-001 attempt a2, TASK-003 attempt a1 and TASK-004 attempt a2 are accepted; the remaining 36 tasks are in progress or backlog.
Task implementations will use separate branches and worktrees, observed test
results, and independent implementation and consistency review before accepted
dependency handoffs. Integration, completion, and cleanup will be recorded as
they occur; proposed or unexecuted work is not evidence of completion.

The product milestone is the local deterministic engine described by the
current specification. Production model/hosting adapters, external publication,
and public release remain separate scope.

## Accepted shared values and next dispatch

TASK-001 candidate `d1fc917466410febc6238479e65816dd39591a4f` passed
cycle 2 implementation and consistency reviews, then integrated at
`15dacd3fc544e433e3602d5403c6b476e547eae0`. Both review reports and their
independent execution evidence are retained under `reviews/TASK-001-a2-c2-R1*`
and `reviews/TASK-001-a2-c2-R2*`. The failed first review is preserved. The final
candidate passed 15 focused tests; independent review additionally verified the
path-conflict repair, schema vocabularies, all approved graph scopes, and the
existing 24-test bootstrap suite. Git removed the clean merged task worktree.

Post-integration foundation validation passed: 27 schemas, 123 artifacts,
39 tasks, 280 unordered pairs, four historical manifests, and 192 local links.
TASK-003 (workflow ports) and TASK-004 (offline contracts and installed helper
closure) are dispatched in separate worktrees. Their implementation results
remain unaccepted until actual validation and both independent reviews pass.

## Accepted workflow interfaces and bounded validator recovery

TASK-003 candidate `d51b72ce71ea3ac3ad31adf41e3eddc84738ac0b` passed fresh
cycle2 R1 and R2 and integrated at `c749ec19056dd6d215c51a9896f35785391d0ace`.
All three prior observation-coherence findings were repaired. Actual validation
passed26 focused tests; R1 additionally passed118 boundary cases, and R2 passed
7 independent contract/integration tests. The clean merged worktree was removed.
TASK-039 is dispatched from the accepted interfaces at `4087c71693fbdd502bce9ea92d3bf1312fd04fa3`.

TASK-004 retained two failed R1 cycles. Independent recovery authorized exactly
one bounded repair in fresh attempt a2 without changing graph r4, scope, public
contracts or acceptance. The repair is committed at `6fc948540ff9797fac138c9382f65f0ea6960de0`
and now awaits cumulative R1 cycle3 and fresh R2. Its closed known-reference
language preserves unmatched contract prose and bootstrap digest compatibility.
See the retained recovery assessment, coordinator decision and budget checkpoint
under evidence/recovery. No failed candidate is an accepted dependency.

At this checkpoint the native dispatch count is25 conservatively counted calls
plus one continuing coordinator invocation:26 charged of300. This includes every
prior rejected/withdrawn/follow-up call and the new004a2 implementer,003c2 R1/R2,
and039 implementer. Reserve2 more calls for004a2 R1/R2. Historical rewrite usage
remains3 of3, not reset. No extra repair beyond the recovery allowance is granted.

## Accepted offline contracts and next implementation group

TASK-004 a2 candidate `e3c1177f993ee74815639a83ef3333faa4ba3957` passed
cumulative cycle3 R1 and separate R2 after the recorded bounded recovery, then
integrated at `1ee6b06c46e4c626ab6d63be52bb11d7bdfeb518`. Both earlier
failed candidates and their reports remain retained. The clean accepted a2
worktree was removed; the clean failed a1 worktree/branch remains retained.

Actual candidate validation passed21 focused tests. R1 additionally passed24
bootstrap tests, foundation validation, all27 record kinds,54 relocation cases,
28 prose cases, physical approval checks, and source-isolated installed imports.
R2 passed21 declared tests, six accepted workflow-record projections, two-plan
physical completion/archive relocation with snapshot-byte enforcement, six stale
approval prose rejections, and a future installed helper dependency cycle check.
Both reports have all required checks, exact identity, and no unresolved findings.

TASK-002 starts from `29df4a8fa00582614ce2ac36cf0f1803766f8417`; TASK-005
starts from `7731f1e4118e330c3fe5b5ce7e961fa49050ba6a`. TASK-039 continues
independently. Native invocation accounting is30 charged of300 (29 conservatively
counted dispatch/follow-up calls plus the continuing coordinator). The earlier
reserved004 reviews have now run, and002/005 implementation calls are charged.
Rewrite usage remains3 of3. Recovery and review histories remain cumulative.

Post-integration foundation validation passed:27 schemas,142 artifacts,39 tasks,
280 unordered pairs,4 historical manifests and246 local links. This validates
the updated records and links; it is separate from the task behavior suites.
