"""Render the immutable R1 decision and validate it against the frozen ROOT schema."""
from datetime import datetime, timezone
import json
from pathlib import Path
import uuid
import jsonschema

ROOT = Path(__file__).resolve().parents[5]
DIR = Path(__file__).parent
STEM = 'TASK-006-a1-c1-R1'
REL = '.ai/plans/current/PLAN-001/reviews/'
candidate_ref = REL + 'candidates/CANDIDATE-TASK-006-a1-64a48f6bde98.json'
candidate = json.loads((ROOT/candidate_ref).read_bytes())
request_id = 'REQUEST-' + STEM + '-' + uuid.uuid4().hex
invocation_id = '/root/r1_006_c1/' + uuid.uuid4().hex
identity = REL + STEM + '-identity.txt'
win = REL + STEM + '-suite-windows.txt'
linux = REL + STEM + '-suite-linux.txt'
winprobe = REL + STEM + '-probes-windows.txt'
linuxprobe = REL + STEM + '-probes-linux.txt'
report_ref = REL + STEM + '.md'
handoff = '.ai/plans/current/PLAN-001/evidence/implementation/TASK-006.md'
checks = [
 ('R1-01','fail','AC1/AC2 ordinary execution, output and failure paths work, but inherited pipes can block return and POSIX escaped descendants survive purportedly confirmed timeout.',[win,linux,winprobe,linuxprobe]),
 ('R1-02','fail','Local-only exclusions are respected; REQ-09 bounded command execution and explicit uncertainty are violated by findings 001/002.',[report_ref,'.ai/plans/current/PLAN-001/spec.md']),
 ('R1-03','fail','Traced typed request through preflight, unchanged shell=False argv, capture and durable evidence; drain close and group-only confirmation have reproducible defects.',[report_ref,winprobe,linuxprobe]),
 ('R1-04','fail','Both platforms block at commands.py:607 with inherited pipes; Linux commands.py:186-189 confirms only group absence while a live descendant remains.',[winprobe,linuxprobe]),
 ('R1-05','fail','Zero-plan/cwd, byte/read boundaries, empty environment and backward clocks pass; parent-exit/open-pipe and detached-descendant boundaries do not.',[win,linux,winprobe,linuxprobe]),
 ('R1-06','fail','The meaningful 20-case suite passes on each host with 19 executed and one platform skip; it lacks both decisive cleanup regressions and uses an injected false terminator for its surviving-child case.',[win,linux,REL+STEM+'-probes.py',winprobe,linuxprobe]),
 ('R1-07','pass','Exactly one owned adapter and its leaf tests/handoff; no concrete downstream implementation, schema or policy expansion.',[identity]),
 ('R1-08','pass','Verified binary diff, clean exact head/base, all context/evidence hashes, accepted dependency ancestry and r4 structural digest; only three allowed added paths.',[identity]),
 ('R1-09','pass','Actual CommandRunner Protocol and frozen CommandRequest/CommandEvidence are used with explicit immutable settings and injected clock/IDs/log/cancellation/termination collaborators; no mapping API or central export change.',[report_ref,winprobe,linuxprobe,'.ai/shared/architecture/service-contracts.md']),
 ('R1-10','fail','Permissions, explicit environment, sandbox refusal, Windows batch refusal, cwd checks and encoded secret redaction pass; group-only cleanup incorrectly asserts quiescence across the process-resource boundary.',[win,linux,winprobe,linuxprobe]),
 ('R1-11','fail','The handoff preserves preflight history and describes the clock fix accurately, but must document/correct bounded drain completion and distinguish observed group absence from confirmed descendant cleanup.',[handoff,report_ref,winprobe,linuxprobe]),
]
findings = [
 {
  'id':'R1-TASK-006-001','severity':'major','category':'defect',
  'description':'When a child starts a descendant that inherits stdout/stderr and the parent exits, execute leaves its timeout/cancellation loop and enters _finish_drains. After the two timed joins, pipe.close() waits for the BufferedReader lock held by the blocked reader thread. On Windows and Linux the 1-second request was still blocked at commands.py:607 when a reviewer watchdog killed the live descendant at 7 seconds; execute returned only after that external intervention (7.266s/7.122s). A long-lived descendant can therefore prevent evidence return indefinitely, and cleanup at line 362 is unreachable while close is blocked.',
  'paths':['src/commands.py:333','src/commands.py:356','src/commands.py:596','tests/unit/commands/test_commands.py'],
  'expected_fix':'Make drain completion and handle shutdown bounded without closing a buffered pipe from another thread while its read holds the lock. Retain owned process facts early enough to attempt cleanup after parent exit, preserve timeout/cancellation while drains are pending, and return schema-valid unknown evidence when quiescence cannot be confirmed. Add Windows and Linux real-descendant regression tests that complete within a bounded deadline without an external killer.',
  'acceptance_ids':['TASK-006-AC1','TASK-006-AC2','AC-02'],'resolved':False
 },
 {
  'id':'R1-TASK-006-002','severity':'major','category':'defect',
  'description':'The POSIX terminator observes getpgid(parent)==parent and later treats disappearance of that one group as complete tree quiescence. A real parent that launches a descendant with start_new_session=True and redirects its output produces timed_out evidence with exit_code=-15 while the descendant remains alive in its own process group (observed PID/PGID 349). The same boolean is used for active cancellation. Owning and stopping one group does not establish that all descendants stopped.',
  'paths':['src/commands.py:164','src/commands.py:186','src/commands.py:198','src/commands.py:350','tests/unit/commands/test_commands.py'],
  'expected_fix':'Track/contain and observe descendant ownership sufficiently to confirm cleanup, or conservatively return false and unknown/ambiguous_side_effect when full descendant quiescence is not established. Do not promote group absence alone to tree confirmation. Add a real POSIX new-session descendant regression for timeout/cancellation and update the handoff to state the actual confirmed boundary.',
  'acceptance_ids':['TASK-006-AC1','TASK-006-AC2','AC-02'],'resolved':False
 }
]
result = dict(schema_version='1.0',kind='review-result',id=STEM,stage='implementation',request_id=request_id,
 task_id='TASK-006',plan_id='PLAN-001',candidate_ref=candidate_ref,candidate_fingerprint=candidate['fingerprint'],verdict='fail',
 reviewer=dict(profile='review_high',provider='OpenAI',model_id='gpt-6-astra',capability_rank=4,invocation_id=invocation_id),
 independent_session_id='/root/r1_006_c1',implementation_session_id='/root/implement_006',review_1_ref=None,
 checklist_version='PLAN-001-v1',checks=[dict(id=i,status=s,rationale=r,evidence=e) for i,s,r,e in checks],
 findings=findings,created_at=datetime.now(timezone.utc).isoformat())
md = f'''# TASK-006 a1 cycle 1 — independent implementation review

**Verdict: FAIL.** Two reproducible resource-cleanup defects remain. Both ordinary
platform suites pass; those passes do not establish the missing behaviors below.

Candidate `{candidate['head_oid']}`; base `{candidate['base_oid']}`;
fingerprint `{candidate['fingerprint']}`. Candidate record: `{candidate_ref}`.
Verified clean task tree, raw binary diff hash, all 14 committed context hashes,
both ROOT validation hashes, policy/model hash, accepted 002/004/038 ancestry and
the approved r4 structural digest. The diff adds only `src/commands.py`, its owned
leaf test and TASK-006 handoff; see [{STEM}-identity.txt]({STEM}-identity.txt).

This is the first R1, a fresh session `/root/r1_006_c1`, separate from implementer
`/root/implement_006`. Request `{request_id}`; review invocation `{invocation_id}`.
The coordinator observed submitted OpenAI `gpt-6-astra` / `xhigh`, review_high rank 4,
above implementation `gpt-5.6-sol` / `xhigh`, rank 3. These internal invocation IDs
and submitted settings are not provider-returned identity/effort confirmation;
that confirmation is unavailable. The configured automatic bindings remain false.
This follows the explicit manual dispatch and the retained
`evidence/effort-provenance-clarification.md`; no schema fields or policy were changed.

## Findings

**R1-TASK-006-001 — major: inherited pipes can block the runner indefinitely.**
A real parent launches a 30-second descendant inheriting stdout/stderr, writes the
descendant PID and exits. For a 1-second request, both hosts were still blocked at
`src/commands.py:607` (`pipe.close()`) at the 7-second watchdog. The timed thread
joins do not bound close: the reader holds the buffered pipe lock while waiting
for EOF. Timeout/cancellation polling has already ended with the parent, and the
cleanup call after `_finish_drains` has not been reached. Only the independent
watchdog killing the known descendant released the call: 7.266 seconds on Windows,
7.122 seconds on Linux. Both eventually returned unknown/ambiguous_side_effect,
but without intervention evidence return can wait for the descendant indefinitely.
Make drain/handle shutdown bounded, retain sufficient owned process facts for
post-parent cleanup, continue timeout/cancellation handling while drains remain,
and return honest uncertainty if cleanup cannot be confirmed. Add real descendant
regressions on both platforms that need no external killer.

**R1-TASK-006-002 — major: POSIX group absence is mistaken for tree quiescence.**
A parent launches a descendant using `start_new_session=True` with redirected
output, records its PID, then sleeps. The native 1-second timeout returns
`timed_out`, exit -15, error `timeout`, while descendant PID/PGID 349 is still live.
`src/commands.py:186-189` confirms absence of only the parent's owned group; the
same inference at 198-200 also cannot establish descendant quiescence. That true
result prevents `execute` from selecting unknown. Active cancellation uses the
same path. Confirm the actual descendant boundary through ownership/containment
observations, or conservatively report false/unknown when it is not established.
Add a real detached-descendant timeout/cancellation regression and align the
handoff's cleanup claims with the observed boundary.

These findings affect TASK-006-AC1, TASK-006-AC2 and plan AC-02. They require a new
candidate, validation, fresh R1 and then R2; this report authorizes no acceptance,
merge, policy change or source repair by the reviewer.

## Executed evidence

| Check | Windows | Ubuntu-24.04 via WSL --exec |
| --- | --- | --- |
| Exact declared unittest arguments, required interpreter | Exit 0; 20 discovered, 19 executed, POSIX-only skip; 4.518s | Exit 0; 20 discovered, 19 executed, Windows-only skip; 4.192s |
| Fresh independent probe script | Exit 0, observed finding 001 | Exit 0, observed findings 001 and 002 |
| Positive independent boundaries | Actual typed API; UTF-16/UTF-8 split-read redaction and combined 8199-byte cap; corrupt digest destination rejection; backward-clock unknown with retained logs | Same checks plus actual cwd symlink rejection |

Probe exit 0 means the harness completed and recorded observations; it is not an
acceptance pass. Windows symlink and POSIX session probes were explicitly skipped
on Windows; Linux exercised them. All probe-owned live descendants were killed by
their exact observed PIDs and confirmed gone. The suite imported commands, config,
contracts and local_ports from the exact candidate `src`, never editable ROOT.

The source tests also exercise zero-plan/project/control/worktree cwd selection,
literal whitespace/newline/tab argv, nonzero exit, explicit permission/environment,
empty sensitive binding, NUL/escape/batch refusal, required sandbox refusal,
combined dual-stream draining, content identity reuse, launch/storage failures,
pre/active cancellation and owned-group cleanup. The accepted 002 DTO semantics,
004 offline registry, and 038 settings APIs are used unchanged. Success-rule
interpretation and runtime wiring remain owned downstream. The backward-clock
correction is sound: it retains observed start and durable refs, omits unrepresentable
finish, clears exit code and reports schema-valid unknown/clock_regression.

Reproduce from ROOT with the declared Windows interpreter and `-B`:
`{REL}{STEM}-verify.py suite`, then `{REL}{STEM}-probes.py`.
For Linux use the same scripts through WSL Ubuntu-24.04 `--exec` with the project
Linux venv; the verification script records the exact child argv and origins.
The initial reviewer probe cap mistake and correction are retained in
[{STEM}-harness-note.txt]({STEM}-harness-note.txt), separate from source findings.
Coordinator pre-R1 Linux failures remain in the cited assessment and were not
counted as an R1 cycle or discarded.

Evidence: [{STEM}-suite-windows.txt]({STEM}-suite-windows.txt),
[{STEM}-suite-linux.txt]({STEM}-suite-linux.txt),
[{STEM}-probes-windows.txt]({STEM}-probes-windows.txt),
[{STEM}-probes-linux.txt]({STEM}-probes-linux.txt).
The latter two retain main-thread stack observations, live PID facts, final
statuses and fixture cleanup results. The scripts and candidate diff are retained
as same-stem companions.

## Complete implementation checklist — PLAN-001-v1

| ID | Result | Rationale |
| --- | --- | --- |
'''
for i,s,r,_ in checks:
    md += f'| {i} | {s.upper()} | {r} |\n'
md += '\nAll findings remain unresolved. No candidate, source, task, state, policy, historical evidence or commit was edited.\n'
schema = json.loads((ROOT/'schemas/v1/review-result.schema.json').read_bytes())
jsonschema.Draft202012Validator(schema,format_checker=jsonschema.FormatChecker()).validate(result)
(DIR/(STEM+'.md')).write_text(md,encoding='utf-8')
(DIR/(STEM+'.json')).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
jsonschema.Draft202012Validator(schema,format_checker=jsonschema.FormatChecker()).validate(json.loads((DIR/(STEM+'.json')).read_bytes()))
(DIR/(STEM+'-schema-validation.txt')).write_text('PASS: final review-result JSON validates against ROOT schemas/v1/review-result.schema.json with Draft202012Validator and FormatChecker; 11 complete numbered checks; 2 unresolved major findings; verdict fail.\n',encoding='utf-8')
print('Final report JSON schema validation PASS; verdict FAIL; two major findings.')
