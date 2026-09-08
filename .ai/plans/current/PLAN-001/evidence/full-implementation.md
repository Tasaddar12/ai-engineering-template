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
Accepted prerequisites and subsequent dispatches are recorded in the dated checkpoints below; current task records and project state carry the latest status.
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

### Configuration dispatch and completed candidates (2026-09-08)

Three of 39 tasks remain accepted. TASK-005 and the first bounded TASK-039 repair have clean committed owner handoffs and await exact-candidate independent reviews. TASK-002 remains in implementation. TASK-038 was dispatched from accepted TASK-004 to unblock command, context, agent, and review configuration dependencies; its write paths and component resource are disjoint from the active owners. Manual native accounting is 36 charged invocations of 300, including rejected attempts and the continuing coordinator invocation. Graph rewrite accounting remains 3 of 3 used, with no new rewrite. Production adapter bindings remain unconfigured; this is manually observed native development coordination.

### Fourth task accepted; state-transition dispatch (2026-09-08)

TASK-005 is accepted at integration commit 85f87b3536990970fbcf9d2cf6b299696eb008ec, after exact candidate 0216c03b18698a3ff4bc89c9b0ae9749255425ef passed its 10 declared tests and separate fresh R1/R2. R1 added five independent probe tests and R2 four; both found no defects. The clean merged worktree was removed. Four of 39 tasks are accepted. TASK-008 now implements pure guarded transitions from accepted TASK-001/TASK-004, while TASK-038 implements configuration. Local interfaces TASK-002 and the bounded TASK-039 repair have clean owner handoffs queued for review.

Manual native accounting is 39 charged invocations of 300, including rejected attempts and the continuing root invocation. Graph rewrite accounting remains 3 of 3 used. A [saved-configuration integration note](configuration-resume-clarification.md) records how existing policy and hashed payload references can preserve resumed settings without adding workflow-run fields; TASK-009/TASK-034 still own persistence and composition.

### Local-port argument repair (2026-09-08)

TASK-002 candidate f38680d2d892d38abaf95402f7470c90a838b68c passed 25 declared tests, but fresh R1 found one major representation defect: command definitions and evidence rejected schema-valid multiline and whitespace-significant arguments. The reviewer reproduced real fixed-argv execution success followed by both DTO constructor failures. The immutable failing report and probes were preserved at integration commit 8446225b832db582e49598670ef1f0f3345be415. The owner is performing its first bounded local correction; no schema, signature, graph, or permission change is authorized. Fresh validation and both independent reviews remain required. Manual native accounting is 41 charged invocations of 300; four tasks remain accepted and graph rewrites remain 3 of 3 used.

### Local interfaces accepted; bounded asset-test follow-up (2026-09-08)

TASK-002 candidate 460ab567d01912167557f2f671ed07c63f0a31e7 passed 27 declared tests, a fresh R1 with 15 independent probes, and separate R2 with five cross-contract scenarios. It was accepted at 4e4dc60178f073042d989f517ee1d363cbe6777c and its clean merged worktree was removed. Five tasks had then been accepted. The independently reproduced asset-test closure limitation led to the [scoped TASK-005 follow-up decision](assessment/TASK-005-coordinator-follow-up.md); its historical accepted code/reviews remain preserved, but current TASK-005 status was reopened before any descendant dispatch. Four of 39 tasks are therefore currently accepted: TASK-001, TASK-002, TASK-003, and TASK-004.

TASK-005 a2 now changes only its test/handoff, and TASK-013 implements dependency-graph validation in a disjoint worktree. TASK-038 has a clean first repair for its two preserved R1 findings (29 declared tests reported); TASK-008 has a clean initial handoff (19 declared tests reported); TASK-039 has a clean first repair (20 declared tests reported). These queued candidates still require coordinator validation and fresh independent reviews. Manual native accounting is 48 charged invocations of 300 before the next reviewer dispatch. The approved graph/task structure and three-of-three rewrite accounting remain unchanged.

### Configuration accepted; command and scope implementations (2026-09-08)

TASK-038 repaired candidate `6f2b12c3283ed7d6e3d4876020fe690c6e0061a3`
passed its 29 declared tests and both fresh cycle2 reviews. R1 passed 48
effective-policy validations and 28 expected rejections; R2 independently passed
96 validations and 54 rejections, plus actual source and provider installations.
Both original findings remain preserved and are repaired: source `local_containers`
loads, and configured invocation limits enforce the schema minimum of one while
zero rewrites remain valid. Integration commit `ab36f09f7775201882bf863a90bc264be022adbd`
accepts TASK-038, making five of 39 currently accepted. The clean merged tree was
removed. Saved configuration persistence remains TASK-009/034 work.

TASK-006 command execution is dispatched at `e9bb424e9fadaa1845b5f5b146cbb4c576b7b10f`;
TASK-014 scope detection at `0881d34129b54584c29ce8db11a66cae7f1bd1be`. Their
component/path claims are disjoint and their prerequisites are accepted. TASK-005
a2 is clean at `bc9b5a6e34a2cdb34582fffa09f1d43171820c7d` with 11 reported tests;
TASK-013 a1 is clean at `8423040c44e24a295a7ebf8027e5dc7d05afb9c6` with 13
reported tests and an actual 39-node r4 build. They join TASK-008 and TASK-039 in
the review queue; owner handoffs are not acceptance evidence. Native manual
accounting is 52 charged invocations of 300 before the next TASK-008 R1 dispatch.
Graph rewrites remain three of three used, and all 39 outcomes remain required.

### Guarded transitions accepted; agent adapter dispatch (2026-09-08)

TASK-008 candidate `fcb01a93f0e1022c70fa296f7342ced71bbf3250` passed its
19 declared tests and separate fresh cycle1 reviews, then integrated at
`62b899af5c57f651175cd6f304f52218acb12adb`. R1 covered 377 state pairs,
269 missing and 269 failed guards, all 17 resumable states, and 95 schema-valid
event mappings. R2 independently passed six consistency tests covering vocabulary,
generation-checked projection transactions, resume guard rechecks, grouped task
and plan completion relocation, stale identities and terminal history. Both reports
have no findings. The clean merged tree was removed; six of 39 tasks are accepted.
These are pure decision/representation checks, not proof of durable state IO.

TASK-014 has a clean owner candidate `b63735f4da282ad1b0376586683d994b3c8b028f`
with 17 reported tests and a 64-pair comparison with accepted ScopeClaim behavior;
it still requires both reviews. TASK-006 continues actual process validation.
TASK-017 starts at `bd962bd0c68f4803d07a16136d55c2ec8707fba8`, with accepted
TASK-003/004/038 inputs and disjoint ownership. TASK-039's bounded repair is next
for current-base validation and fresh reviews. Native manual accounting is
55 charged invocations of 300 before that R1 dispatch. Historical rewrite usage
remains three of three; no new rewrite or authority was introduced.

### Orchestration interfaces accepted; Linux preflight correction (2026-09-08)

TASK-039 repaired candidate `314ef09d59f494223bec02556c6e3d9a8108636f`
passed its 20 declared tests and both fresh cycle2 reviews, then integrated at
`bc8a5f47d8e1a66bc2b8929b099349cb199c0100`. R1 passed 30 usage boundaries and
55 malformed-number probes. R2 independently checked 24 usage boundaries, 44
numeric rejections, all ten signatures, schema shapes, uneven four-R1/three-R2
history retention, and compatibility with accepted configuration and completion
transitions. The old finding is resolved and retained. Seven of 39 tasks are
accepted; Git removed the clean merged tree.

TASK-019 is dispatched at `b4fe29bf40bd017d638072ad3920dca8b240a3a3`.
TASK-017 continues its deterministic adapter implementation. TASK-006 returned
clean candidate `c3c2ba21c6441abde52f6e340b29d0bf65910f8e` with 18 passing
Windows tests, including actual descendant cleanup. Before its first R1, local
Ubuntu-24.04 capability was discovered and a project-local Python environment was
prepared with the declared dependency. The Linux run exposed one cleanup assertion
failure and one backward-clock evidence error. The [retained preflight and bounded
correction decision](assessment/TASK-006-linux-preflight.md) records both diagnostics
and environment setup; the owner is correcting the same attempt's three paths.
This is not a failed independent-review cycle or a structural rewrite.

Manual native accounting is 59 charged invocations of 300, including the TASK-019
dispatch and TASK-006 correction invocation. Graph rewrites remain three of three
used. No candidate review is currently frozen while the three scoped owners work.
TASK-005 a2, TASK-013 and TASK-014 remain clean in the review queue. Linux and Windows
validation will be used for applicable process/platform behavior before final gates.

TASK-006's bounded pre-R1 correction is now clean at
`86bc27af026d8b7b00303fa6d62b12218e0947b8`. It requires observed POSIX process-group
ownership before confirmed cleanup and emits schema-valid unknown evidence with
retained stream refs for a backward clock observation, without fabricated timestamps.
The owner ran the declared suite and ResourceWarning-as-error variant on Windows
and Ubuntu: 20 discovered, 19 executed, one platform-specific skip on each; all pass.
The coordinator will bind fresh current-base Windows and Linux validation in one
candidate before independent R1. Native accounting remains 59 before that dispatch.

### Command cleanup review and context dispatch (2026-09-08)

TASK-006 first R1 failed with two independently reproduced major cleanup findings:
an exited parent can leave inherited pipes blocking the runner on both platforms,
and a Linux descendant escaping the process group survives while timeout cleanup
is reported as confirmed. The exact candidate, both platform suites, independent
probes and complete failed report are preserved at commit
`214e44d07cbfbd937a86ef74dbc4969792fbf0d6`. The same attempt owner is repairing
only commands.py, its owned tests and handoff. This is the first failed review
cycle; earlier coordinator preflight history remains separate. Fresh R1/R2 are
required on the corrected candidate. Seven of 39 tasks remain accepted.

TASK-017 is clean at `71e0ccf697c132082bb17f7f3814ffb6abee5df6` with 20
reported tests, including sequential provider-file recovery across three fresh
Python processes. TASK-019 is clean at `f9e32b0ce8c8950dcb541356cae23a2a7202adc5`
with 12 reported fingerprint tests. Git and handoffs confirm each changed only its
three owned paths; both remain review candidates, not accepted dependencies.
TASK-016 context construction is dispatched at
`0b918080f30a5b7831ec4c30ae96351282bfc940`, using accepted003/004/038.
It runs independently of the command repair. TASK-013 is next for candidate
validation and separate R1/R2. Native manual accounting is 62 charged invocations
of 300 before the next reviewer; graph rewrites remain three of three used.
