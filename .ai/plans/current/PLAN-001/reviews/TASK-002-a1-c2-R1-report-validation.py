"""Write only the c2 R1 report and validate its final frozen candidate binding."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
sys.dont_write_bytecode = True
ROOT = Path('D:/Codex Projects/ai-engineering-template')
WT = ROOT / '.worktrees/TASK-002-a1'
PLAN = '.ai/plans/current/PLAN-001/'
STEM = PLAN + 'reviews/TASK-002-a1-c2-R1'
sys.path.insert(0,str(WT / 'src'))
from contracts import ContractRegistry
from jsonschema import Draft202012Validator, FormatChecker
registry = ContractRegistry(WT / 'schemas/v1')
candidate_ref = PLAN + 'reviews/candidates/CANDIDATE-TASK-002-a1-460ab567d019.json'
candidate = json.loads((ROOT / candidate_ref).read_bytes())
probes = STEM + '-probes.txt'
handoff = PLAN + 'evidence/implementation/TASK-002.md'
source = 'src/local_ports.py'
tests = 'tests/unit/domain_local_ports/test_local_ports.py'
provenance = PLAN + 'evidence/effort-provenance-clarification.md'
checks = [
('R1-01','Both ACs pass: all 11 typed port signatures, qualified state access, transaction/process/Git values and guarded WorktreeManager requests/results are representable; repaired argv crosses both DTOs exactly.',[probes,source,handoff]),
('R1-02','REQ-01/02 and applicable REQ-09 representation requirements respect ADR-001 through ADR-005 and the interface-only exclusion; no concrete IO adapter, authority or product expansion.',[source,PLAN+'spec.md','.ai/shared/architecture/service-contracts.md']),
('R1-03','Full added source and repair diff traced. Argument-specific validation preserves content/order/repeats, rejects invalid items/NUL, freezes caller collections and leaves public shapes unchanged.',[source,probes]),
('R1-04','Committed outcomes require evidence/checkpoints; conflicts/unknown effects remain explicit. Process termination codes and unresolved leases survive representation. Cleanup carries immutable managed/clean/no-live-lease/merged-or-retained guards with no force option; adapters must re-observe.',[source,probes,'.ai/shared/state/persistence.md']),
('R1-05','Independent probes cover prior argv triggers, tabs/CRLF/repeats, invalid arguments/strict metadata, zero-plan events, relocation grouping, root dot, unknown/cancelled process facts, missing/unborn Git, unmanaged/absent worktrees and lease/retention constraints.',[probes]),
('R1-06','27 declared tests pass. 15 independently executed probes include retained exact defect reproductions plus fresh process roundtrips and boundary tests; nonzero leaf discovery and candidate-local imports are verified.',[STEM+'-declared.txt',probes,tests]),
('R1-07','Only one owned production module plus task tests/handoff; no source API, schema, graph, dependency or concrete algorithm expansion in repair.',[probes,source]),
('R1-08','Recomputed binary diff and changed paths are exactly the three allowed additions; no prohibited or unrelated change.',[probes,candidate_ref]),
('R1-09','Explicit flat-module Protocols and frozen typed dataclasses reuse accepted TASK-001 values/errors and TASK-004 validation; public fields and method signatures are unchanged by repair.',[source,probes,'.ai/shared/architecture/service-contracts.md']),
('R1-10','No IO in candidate; shell=False is fixed, cwd uses selected host-local roots and traversal-resistant relative values, environment names are permitted and values hidden from repr. Repair preserves literal metacharacters; downstream process/realpath validation remains explicit.',[source,probes,handoff]),
('R1-11','Handoff accurately records preserved failed review, bounded repair, argument limitations, 27 leaf versus 24 aggregate tests, portable/local separation and later adapter responsibilities; provenance states submitted settings and unavailable provider confirmation.',[handoff,STEM+'.md',provenance])
]
report = {
'schema_version':'1.0','kind':'review-result','id':'TASK-002-a1-c2-R1','stage':'implementation',
'request_id':'manual:PLAN-001:TASK-002:a1:c2:R1','task_id':'TASK-002','plan_id':'PLAN-001',
'candidate_ref':candidate_ref,'candidate_fingerprint':candidate['fingerprint'],'verdict':'pass',
'reviewer':{'profile':'review_high','provider':'OpenAI','model_id':'gpt-6-astra','capability_rank':4,'invocation_id':'/root/r1_002_c2:PLAN-001:TASK-002:a1:c2:R1'},
'independent_session_id':'/root/r1_002_c2','implementation_session_id':'/root/implement_002','review_1_ref':None,
'checklist_version':'PLAN-001-v1','checks':[{'id':i,'status':'pass','rationale':r,'evidence':e} for i,r,e in checks],
'findings':[{'id':'R1-TASK-002-001','severity':'major','category':'defect','description':'Resolved on this candidate: both CommandDefinition.argv and CommandEvidence.argv_redacted now preserve the exact schema-valid significant-space and multiline arguments rejected by c1. The original independent reproductions and fresh tab/CRLF/repeated-argument execution pass. The prior failing report remains unchanged.','paths':[source,tests],'expected_fix':'Satisfied by the bounded argument-specific validator and regression coverage; no further repair required for this finding.','acceptance_ids':['TASK-002-AC1','AC-02'],'resolved':True}],
'created_at':datetime.now(timezone.utc).isoformat()
}
markdown = '''# PLAN-001 / TASK-002 a1 c2 — R1

Verdict: **pass** for the exact candidate below. All 11 checks pass; prior finding `R1-TASK-002-001` is resolved. No new finding or source edit.

| Identity | Verified value |
| --- | --- |
| Candidate | `CANDIDATE-TASK-002-a1-460ab567d019` |
| Base → head | `43c8004c7313105f63d3b8d21726f8a056b96842` → `460ab567d01912167557f2f671ed07c63f0a31e7` |
| Fingerprint | `cd07a45f07d55964abcb8b1d0fe84ee44d84a0df2d2af6f3174fc1786524c253` |
| Binary diff SHA-256 | `477b5884a49f409e9a7cb990869849567af46ea6b750cca5aaf3221cdc0b8695` |
| Approved graph / task digest | r4 / `c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e` |
| Policy/model digest | `b8d895be89333b372c65f1f95c3e7e2b911b850a44be3ec8f64dc344ca806a42` |

The companion probes recomputed all 13 committed context hashes, the ROOT validation hash, canonical fingerprint, approved structural graph identity and allowed scope. TASK-001 `d1fc917466410febc6238479e65816dd39591a4f` and TASK-004 integration `1ee6b06c46e4c626ab6d63be52bb11d7bdfeb518` are accepted ancestors of the base with passing matching R1/R2 evidence. Git shows exactly three owned additions: `src/local_ports.py`, its task leaf test file and the TASK-002 handoff. Schema, shared contracts, graph and accepted dependency source are unchanged.

Reviewer session `/root/r1_002_c2`, request `manual:PLAN-001:TASK-002:a1:c2:R1`, invocation `/root/r1_002_c2:PLAN-001:TASK-002:a1:c2:R1` are manual session identities, distinct from implementation `/root/implement_002`; they are not provider-issued UUIDs. The coordinator observed native OpenAI `gpt-6-astra` / `xhigh`, `review_high` rank 4, above implementation `gpt-5.6-sol` / `xhigh`, rank 3. Separate provider-returned effective model/effort confirmation is unavailable. This follows the reviewer brief and `evidence/effort-provenance-clarification.md` without adding schema fields or claiming production provider configuration.

**Repair closure.** `_arguments` at `src/local_ports.py:81`, used by both command DTOs at lines 525 and 692, preserves whitespace, newlines, tabs, order and repeats while rejecting scalar/empty collections, empty/non-string items and process-invalid NUL. Metadata retains its stricter checks. The retained c1 significant-space and multiline probes now pass for both schema-valid DTOs and actual `shell=False` execution. Fresh probes additionally preserve tabs, CRLF, repeated values and literal shell metacharacters, and verify detached immutable collections. Repair commit `3f4b42f40d8eb23fa2a3304253573804fe69870c` has byte-identical source to the candidate; its public class fields and method signatures match c1. Historical failed reports/probes were preserved.

TASK-002-AC1 passes for qualified reads, direct zero-plan events, single-generation relocation/reference/manifest effects, Clock/IdFactory, command and Git requests/results. TASK-002-AC2 passes for typed ensure/reconcile/cleanup and shared errors. Unknown/cancelled process states, observed termination codes, missing/unborn Git heads, ambiguous `changed=None`, plan-free control roots, unmanaged/absent/dirty trees and unknown leases remain representable. Cleanup guards require matching identities and managed, clean, quiescent, merged-or-retained facts; their construction does not prove those facts or perform cleanup.

| Checklist PLAN-001-v1 | Result | Decisive evidence |
| --- | --- | --- |
| R1-01 Acceptance | pass | Both acceptance mappings above; all 11 signatures and DTO boundaries verified. |
| R1-02 Spec/exclusions | pass | REQ-01/02 and applicable process representation; ADR-001–005; interface-only module. |
| R1-03 Correctness | pass | Full source traced; exact argument roundtrip and public-shape checks pass. |
| R1-04 Errors/cleanup | pass | Explicit conflicts/unknown effects, evidence requirements and immutable non-force cleanup guards. |
| R1-05 Boundaries | pass | Repair cases, zero-plan/relocation/root dot, process/Git uncertainty and ownership/lease facts. |
| R1-06 Tests | pass | 27 task tests and 15 independent probes, including actual process argument preservation. |
| R1-07 Scope | pass | One owned production module; no adapter, dependency, schema or interface expansion. |
| R1-08 Unrelated changes | pass | Exact binary diff contains only the three allowed additions. |
| R1-09 Maintainability | pass | Frozen dataclasses, explicit Protocols, accepted shared values and offline registry. |
| R1-10 Trust boundaries | pass | Fixed shell=False, explicit local roots, relative path checks and permitted environment; no concrete IO. |
| R1-11 Documentation | pass | Accurate repair lineage, validation limits, provenance and adapter responsibilities. |

All Python checks used `D:/Codex Projects/ai-engineering-template/.ai/local/full-plan-venv/Scripts/python.exe` from the task worktree with bytecode disabled; imports resolve its `src`.

| Actual independent validation | Result / companion |
| --- | --- |
| Declared `-m unittest discover -s tests/unit/domain_local_ports/ -p test_*.py` | Exit 0; 27 tests; `-declared.txt`. |
| `TASK-002-a1-c2-R1-probes.py` | Exit 0; 15 tests; `-probes.txt`. Nine small retained boundary checks and both original failure reproductions rerun against this candidate, plus four fresh checks. No old verdict reused. |
| `src/validate_foundation.py` | Exit 0; 27 schemas, 151 artifacts, 1 plan, 39 tasks, 280 unordered pairs, 4 manifests, 262 links; `-foundation.txt`. |
| Final identity, diff check and report schema | Passed; `-report-validation.txt`. |

Only Windows was exercised. The handoff's aggregate 24-test run remains implementer evidence; it does not discover this leaf. Concrete persistence, realpath security, process-tree termination, Git effects and safe cleanup are later adapter responsibilities. Proceed to fresh independent R2 on this identical candidate; this R1 is not task acceptance. Reports are immutable at FINAL and the reviewer stops all worktree access then.
'''
(ROOT / (STEM + '.md')).write_text(markdown,encoding='utf-8')
(ROOT / (STEM + '.json')).write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
registry.validate(report,source=STEM+'.json')
Draft202012Validator(json.loads((WT / 'schemas/v1/review-result.schema.json').read_bytes()),format_checker=FormatChecker()).validate(report)
assert [c['id'] for c in report['checks']] == [f'R1-{i:02}' for i in range(1,12)]
assert all(c['status']=='pass' for c in report['checks']) and all(f['resolved'] for f in report['findings'])
for check in report['checks']:
    for ref in check['evidence']:
        assert (ROOT / ref).is_file() or (WT / ref).is_file(),ref
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=WT).decode().strip() == candidate['head_oid']
assert subprocess.check_output(['git','status','--porcelain=v1'],cwd=WT) == b''
subprocess.run(['git','diff','--check',candidate['base_oid'],candidate['head_oid']],cwd=WT,check=True)
old = [str(p.relative_to(ROOT)).replace('\\','/') for p in (ROOT / (PLAN+'reviews')).glob('TASK-002-a1-c1-R1*')]
subprocess.run(['git','diff','--exit-code','HEAD','--',*old],cwd=ROOT,check=True)
checks_output = {'review':report['id'],'verdict':report['verdict'],'registry_and_draft202012_with_formats':'pass','numbered_checks':'R1-01 through R1-11 once each; all pass','resolved_findings':['R1-TASK-002-001'],'candidate_head':candidate['head_oid'],'candidate_status':'clean','diff_check':'pass','historical_c1_files':'unchanged against ROOT HEAD','report_sha256':hashlib.sha256((ROOT / (STEM+'.json')).read_bytes()).hexdigest(),'markdown_sha256':hashlib.sha256((ROOT / (STEM+'.md')).read_bytes()).hexdigest()}
(ROOT / (STEM+'-report-validation.txt')).write_text(json.dumps(checks_output,indent=2)+'\n',encoding='utf-8')
print(json.dumps(checks_output,indent=2))
