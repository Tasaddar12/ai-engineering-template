"""Produce and schema-validate the immutable R2 review outputs."""
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[5]
TREE = ROOT / '.worktrees/TASK-006-a1'
sys.path.insert(0, str(TREE / 'src'))
from contracts import ContractRegistry

stem = '.ai/plans/current/PLAN-001/reviews/TASK-006-a1-c2-R2'
candidate_ref = '.ai/plans/current/PLAN-001/reviews/candidates/CANDIDATE-TASK-006-a1-ce4c8edb86b0.json'
r1_ref = '.ai/plans/current/PLAN-001/reviews/TASK-006-a1-c2-R1.json'
identity = stem + '-identity.txt'
probes = [stem + '-probes-windows.txt', stem + '-probes-linux311.txt']
rows = [
('R2-01', 'pass', 'One owned local adapter returns process facts through CommandRunner; configuration, authorization, state, validation and CLI wiring retain their declared owners.', [identity, '.ai/shared/architecture/service-contracts.md', stem + '-candidate.diff']),
('R2-02', 'pass', 'ADR-001 through ADR-005 retain flat Python 3.11+ modules, local immutable records, isolated worktree ownership, exact fresh reviews and injected ports. Native submission provenance is explicitly distinguished from unavailable provider confirmation.', [stem + '.md', '.ai/plans/current/PLAN-001/evidence/effort-provenance-clarification.md', identity, *probes]),
('R2-03', 'pass', 'Accepted 002/004/038 commits are ancestors of the exact base; source and handoff bytes match those accepted candidates. Saved configuration, command DTOs and offline validation work together.', [identity, *probes]),
('R2-04', 'pass', 'Frozen execute(CommandRequest)->CommandEvidence and direct submodule imports remain intact. Seven significant argv values and project/worktree/control nested cwd, including zero-plan identities, round-trip through actual child processes.', [*probes, 'src/local_ports.py', 'src/commands.py']),
('R2-05', 'pass', 'Observed nonzero exit stays exited; durable-write failure stays unknown with null exit and only a proven stdout ref. Required saved sandbox and explicit deny-all permissions refuse launch without authority inferred from configuration.', [*probes, 'src/commands.py']),
('R2-06', 'pass', 'No database, schema, migration or serialized field changed. Actual results validate against the exact closed v1 field set; sanitized content refs verify after relocation and partial storage does not fabricate a missing ref.', [identity, *probes, stem + '-foundation.txt']),
('R2-07', 'pass', 'Only commands.py, its owned leaf tests and task handoff differ. Flat-module imports, plan-local review/evidence paths and existing value/error conventions are preserved.', [identity, stem + '-candidate.diff']),
('R2-08', 'pass', 'No duplicate validation, fingerprint, Git, state or policy implementation. A real zero-test exit remains process evidence; the accepted ValidationCheck rejects an asserted positive-count pass for zero tests, leaving TASK-018 evaluation intact.', [*probes, '.ai/plans/current/PLAN-001/tasks/current/TASK-018.json']),
('R2-09', 'pass', 'Host-local observation and termination collaborators add no conflicting portable abstraction. Retained POSIX groups support best-effort signalling without claiming containment; uncertain cleanup returns unknown. Frozen redacted capture and durable refs match R1 evidence.', [stem + '-cancellation-linux311.txt', '.ai/plans/current/PLAN-001/reviews/TASK-006-a1-c2-R1-probes-windows.txt', '.ai/plans/current/PLAN-001/reviews/TASK-006-a1-c2-R1-probes-linux.txt']),
('R2-10', 'fail', 'The minimum-version suite fails two cancellation subcases because fixed 250 ms timers assume descendant startup/PID publication. The two tests reproduce the errors in isolation. Readiness-based actual cancellation passes; the tests must synchronize on their intended process state.', [stem + '-suite-linux311.txt', stem + '-focus-linux311.txt', stem + '-cancellation-linux311.txt', 'tests/unit/commands/test_commands.py:504', 'tests/unit/commands/test_commands.py:570']),
('R2-11', 'pass', 'The handoff accurately reports prior platform observations, both lifecycle repairs, unknown cleanup, frozen capture, saved settings and downstream ownership. Newly discovered Linux 3.11 fixture timing failure is preserved here without relabeling earlier passes or claiming integrated engine behavior.', ['.ai/plans/current/PLAN-001/evidence/implementation/TASK-006.md', stem + '.md', stem + '-cancellation-linux311.txt']),
('R2-12', 'pass', 'Approved graph r4, all 39 task structural digests, accepted interfaces and validation-before-review/fingerprint bindings remain valid. The finding is bounded to already owned tests; no sandbox, new service, scope expansion or architectural replan is demanded.', [identity, candidate_ref, r1_ref, stem + '.md']),
]
finding = {
    'id': 'R2-TASK-006-001', 'severity': 'major', 'category': 'defect',
    'description': 'The two new descendant cancellation regressions start threading.Timer(0.25, event.set) before execute, then unconditionally read the descendant PID file. On supported Linux Python 3.11.16 the parent had not published that file before cancellation, producing FileNotFoundError at lines 518 and 584. The declared suite discovered 22 tests, executed 21 with one platform skip and two errors; a focused repeat of the two tests reproduced both errors with observed exit 1. Independent readiness-based native probes observed child readiness at 0.504 seconds and returned correct unknown/null-exit evidence in 0.566/0.550 seconds. This is a candidate-owned timing-dependent test failure, not a reproduced command-runner failure.',
    'paths': ['tests/unit/commands/test_commands.py:504', 'tests/unit/commands/test_commands.py:518', 'tests/unit/commands/test_commands.py:570', 'tests/unit/commands/test_commands.py:584'],
    'expected_fix': 'Synchronize active cancellation with an observed descendant-ready/PID milestone under a bounded startup deadline instead of assuming readiness after 250 ms. Preserve exact descendant teardown, bounded execute return without a pre-return external killer, and conservative unknown assertions. Validate the repaired tests on Linux Python 3.11 as well as the existing declared platform matrix, then form a new candidate and run fresh R1/R2 through coordinator-owned recovery. No production or shared-contract change is established as necessary.',
    'acceptance_ids': ['TASK-006-AC2', 'AC-02', 'AC-09'], 'resolved': False,
}
token = uuid.uuid4().hex
request = 'REQUEST-TASK-006-a1-c2-R2-' + token
invocation = '/root/r2_006_c2/' + token
record = {
    'schema_version': '1.0', 'kind': 'review-result', 'id': 'TASK-006-a1-c2-R2',
    'stage': 'consistency', 'request_id': request, 'task_id': 'TASK-006', 'plan_id': 'PLAN-001',
    'candidate_ref': candidate_ref,
    'candidate_fingerprint': '7578a4d2cd986e5b69e7a6e0a6938d279aef2056be4f6130d7e17dccbb89cae4',
    'verdict': 'fail',
    'reviewer': {'profile': 'review_high', 'provider': 'OpenAI', 'model_id': 'gpt-6-astra',
        'capability_rank': 4, 'invocation_id': invocation},
    'independent_session_id': '/root/r2_006_c2', 'implementation_session_id': '/root/implement_006',
    'review_1_ref': r1_ref, 'checklist_version': 'PLAN-001-v1',
    'checks': [dict(id=id, status=status, rationale=why, evidence=refs) for id,status,why,refs in rows],
    'findings': [finding], 'created_at': datetime.now(timezone.utc).isoformat(),
}
markdown = f'''# TASK-006 a1 cycle 2 — independent consistency review

**Verdict: FAIL.** R2-10 fails on one bounded test defect, `R2-TASK-006-001`.
The other 11 consistency checks pass. No production cross-contract defect was
reproduced. This candidate cannot proceed to integration with a passing R2 gate.

Candidate `ce4c8edb86b02268a856a5f870932ade0e7e9b91`; base
`3acfcb0d700b05fbf78233b575e77db556cd9bcc`; fingerprint
`7578a4d2cd986e5b69e7a6e0a6938d279aef2056be4f6130d7e17dccbb89cae4`.
The [candidate](candidates/CANDIDATE-TASK-006-a1-ce4c8edb86b0.json) and
[identity evidence](TASK-006-a1-c2-R2-identity.txt) verify the clean exact tree,
raw binary diff, all 14 committed context and three ROOT validation hashes,
policy/model digest, r4 graph/39-task digest, and unchanged accepted
002/004/038 source and handoffs. Only the adapter, owned tests and task handoff
differ. The exact [passing R1](TASK-006-a1-c2-R1.json), SHA-256
`615110eaa88caccc380524ac4c86e30a6295498a7adaa4c974865a6aa190b2a3`, has all
11 checks and both old findings resolved. Its source/context remains unchanged.

Fresh session `/root/r2_006_c2` is distinct from `/root/r1_006_c2` and implementer
`/root/implement_006`. Request `{request}`;
invocation `{invocation}`. Coordinator-observed native submission is
OpenAI `gpt-6-astra` / `xhigh`, review_high rank 4, above submitted implementation
`gpt-5.6-sol` / `xhigh`, rank 3. These identifiers describe the manual review;
separate provider-returned model/effort confirmation is unavailable. Automatic
bindings remain false. The [provenance clarification](../evidence/effort-provenance-clarification.md)
governs this distinction; no policy or schema field was changed.

## Finding — cancellation tests assume 250 ms process startup

**R2-TASK-006-001, major, defect.** At test lines 504 and 570, a fixed 250 ms
timer starts before execution. Lines 518 and 584 then read the expected PID
file unconditionally. The supported Linux Python 3.11.16 interpreter starts the
fixture more slowly: both cancellation subcases raised `FileNotFoundError`.
The [declared suite](TASK-006-a1-c2-R2-suite-linux311.txt) discovered 22 tests,
executed 21, skipped one Windows-only case, and reported two errors. A
[focused repeat](TASK-006-a1-c2-R2-focus-linux311.txt) of exactly those two tests
reproduced both errors with observed process exit 1. The timeout subcases passed.

Independent [readiness-based cancellation](TASK-006-a1-c2-R2-cancellation-linux311.txt)
observed descendants at 0.504 seconds, then returned in 0.566 seconds for the
inherited-pipe fixture and 0.550 seconds for the detached-session fixture.
Both correctly returned `unknown/ambiguous_side_effect`, null exit code and
schema-valid durable refs without external intervention before return. The
ordinary descendant stopped; the escaped descendant remained live as reported
and was subsequently killed by its exact observed PID and confirmed gone.
All diagnostic reader threads settled. This isolates a test startup assumption
from the command runner's correct conservative cleanup behavior.

Required fix: cancel after a bounded, observed descendant-ready/PID milestone.
Retain bounded execution, exact fixture teardown and honest unknown assertions.
Validate Linux 3.11 and the existing platform matrix. The coordinator owns the
repair/recovery disposition and new candidate with fresh R1/R2; this review does
not authorize a budget, state or graph change. No production, sandbox or shared
contract change is established as necessary. Acceptance: TASK-006-AC2, AC-02,
and the Python/platform expectation in AC-09/ADR-001.

## Independent validation and consistency evidence

| Check | Observed result |
| --- | --- |
| [Windows 3.12 cross-contract probes](TASK-006-a1-c2-R2-probes-windows.txt) | 5 passed, no skips; 1.307 s |
| [Linux 3.11.16 cross-contract probes](TASK-006-a1-c2-R2-probes-linux311.txt) | 5 passed, no skips; 3.411 s |
| Linux 3.11 declared command | 22 discovered, 21 executed, one skip, two errors; 9.423 s |
| Focused Linux 3.11 repeat | 2 executed, two errors, exit 1; 3.571 s |
| Independent Linux 3.11 readiness probes | Both passed; descendants and readers explicitly settled |
| [Required foundation validator](TASK-006-a1-c2-R2-foundation.txt) | Passed: 27 schemas, 168 artifacts, 39 tasks, 280 pairs, four manifests, 321 links |
| Exact diff whitespace check | Passed |

The [five probe cases](TASK-006-a1-c2-R2-probes.py) exercise immutable saved
settings despite later policy/payload changes; explicit detached permission and
environment inputs; literal argv and zero-plan/project/worktree/control cwd;
bounded secret redaction and log hashes after relocation; and partial durable
storage failure preserving only its proven stdout reference. A real empty
unittest run remains exited-zero process evidence, while the accepted
`ValidationCheck` refuses an asserted nonzero-count pass for zero tests. An
actual exit 9 stays exited with code 9. TASK-018 still owns evaluation, and
TASK-034 still owns wiring; no unimplemented service is claimed.

Both probe processes verified all six imported modules came from candidate
`src`. Linux used WSL Ubuntu-24.04 `--exec` and the project-local 3.11.16
interpreter. Windows used the required project 3.12 interpreter. The bound
coordinator Windows 3.12/Linux 3.12/Windows 3.11 results each report 22/21/one
skip and success; they were inspected and hash-verified, not redundantly rerun.
R1's real late-write/frozen-capture and encoded-secret evidence was independently
traced through the repaired source. The two original runtime findings remain
resolved; the new test failure does not relabel their passing observations.

The initial identity harness mistakenly resolved the candidate-only handoff
solely under ROOT. Its [retained output](TASK-006-a1-c2-R2-identity-initial.txt)
and corrected resolver distinguish that reviewer setup error from this actual
candidate test failure. No candidate source, state, task, R1 or history changed.

## Complete consistency checklist — PLAN-001-v1

| ID | Result | Decisive rationale |
| --- | --- | --- |
'''
for id, status, why, refs in rows:
    markdown += f'| {id} | {status.upper()} | {why} |\n'
markdown += '\nThe JSON report carries precise evidence references for every check. Final schema and clean-head checks are recorded separately. Reports become immutable at FINAL; all candidate access stops before handoff.\n'
(ROOT / (stem + '.json')).write_text(json.dumps(record, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
(ROOT / (stem + '.md')).write_text(markdown, encoding='utf-8')
registry = ContractRegistry(TREE / 'schemas/v1')
registry.validate(record, source=stem + '.json')
assert len(record['checks']) == 12
assert {c['id'] for c in record['checks']} == {f'R2-{i:02}' for i in range(1, 13)}
for row in record['checks']:
    for ref in row['evidence']:
        path = ref.rsplit(':', 1)[0] if ref.rsplit(':', 1)[-1].isdigit() else ref
        assert (ROOT / path).is_file() or (TREE / path).is_file(), ref
print('PASS schema-valid R2 fail report; 12 complete checks; exact passing R1 reference; all evidence paths resolve.')
print('Review outputs:', stem + '.json', stem + '.md')
