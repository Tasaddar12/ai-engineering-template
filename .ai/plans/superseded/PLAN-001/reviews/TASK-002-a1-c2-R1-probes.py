"""Fresh R1 c2 evidence; frozen candidate is read-only and bytecode is disabled."""
import ast
import dataclasses as dc
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import unittest

ROOT = Path('D:/Codex Projects/ai-engineering-template')
WT = ROOT / '.worktrees/TASK-002-a1'
REVIEWS = ROOT / '.ai/plans/current/PLAN-001/reviews'
PREFIX = REVIEWS / 'TASK-002-a1-c2-R1'
BASE = '43c8004c7313105f63d3b8d21726f8a056b96842'
HEAD = '460ab567d01912167557f2f671ed07c63f0a31e7'
FINGERPRINT = 'cd07a45f07d55964abcb8b1d0fe84ee44d84a0df2d2af6f3174fc1786524c253'
sys.dont_write_bytecode = True
sys.path.insert(0, str(WT / 'src'))
import contracts
import domain_values as dv
import local_ports as p

# Retain and reuse the exact two prior independent reproductions, not their old verdict/identity.
historical = REVIEWS / 'TASK-002-a1-c1-R1-probes.py'
prior = runpy.run_path(str(historical), run_name='retained_c1_reproductions')
wire, definition, command_evidence, record = [prior[n] for n in ('wire', 'definition', 'command_evidence', 'record')]
NOW, E, PROJECT, WORKTREE = [prior[n] for n in ('NOW', 'E', 'PROJECT', 'WORKTREE')]
REGISTRY = contracts.ContractRegistry(WT / 'schemas/v1')
sha = lambda b: hashlib.sha256(b).hexdigest()
def git(*args):
    return subprocess.check_output(['git', *args], cwd=WT)

def verify_identity():
    candidate = json.loads((REVIEWS / 'candidates/CANDIDATE-TASK-002-a1-460ab567d019.json').read_bytes())
    REGISTRY.validate(candidate)
    assert candidate['base_oid'] == BASE and candidate['head_oid'] == HEAD
    assert git('rev-parse', 'HEAD').decode().strip() == HEAD
    assert git('status', '--porcelain=v1') == b''
    subprocess.run(['git', 'merge-base', '--is-ancestor', BASE, HEAD], cwd=WT, check=True)
    assert sha(git('diff', '--binary', BASE, HEAD)) == candidate['diff_sha256']
    assert sha(json.dumps({k:v for k,v in candidate.items() if k != 'fingerprint'}, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()) == candidate['fingerprint'] == FINGERPRINT
    for ref in candidate['context_refs']:
        assert sha(git('show', HEAD + ':' + ref['path'])) == ref['sha256'], ref['path']
    for ref in candidate['validation_refs']:
        assert sha((ROOT / ref['path']).read_bytes()) == ref['sha256'], ref['path']
    assert sha((ROOT / '.ai/project/policy.json').read_bytes() + (ROOT / '.ai/project/agent-models.json').read_bytes()) == candidate['policy_model_digest']
    plan = WT / '.ai/plans/current/PLAN-001'
    tasks = [json.loads(f.read_bytes()) for bucket in ('current','completed','archived') for f in (plan / 'tasks' / bucket).glob('TASK-*.json')]
    graph = json.loads((plan / 'graph.json').read_bytes())
    isolation = json.loads((plan / 'reviews/r4-isolation-review.json').read_bytes())
    assert contracts.structural_task_digest(tasks) == graph['task_set_sha256'] == isolation['task_set_sha256'] == 'c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e'
    assert graph['revision'] == isolation['graph_revision'] == candidate['graph_revision'] == 4
    assert isolation['verdict'] == 'pass' and all(c['status'] == 'pass' for c in isolation['checks'])
    graph_digest = sha(json.dumps({k:graph[k] for k in ('schema_version','kind','id','plan_id','revision','nodes','task_set_sha256')},sort_keys=True,separators=(',', ':')).encode())
    assert graph_digest == '5fa7578c40f6897562a450aaa933f2b2fc307db2dbc6e415483c03abe4c24337'
    by_id = {t['id']:t for t in tasks}
    assert by_id['TASK-002']['depends_on'] == ['TASK-001', 'TASK-004']
    assert next(n for n in graph['nodes'] if n['task_id'] == 'TASK-002')['depends_on'] == by_id['TASK-002']['depends_on']
    dependencies = []
    for task, commit, report in [('TASK-001','d1fc917466410febc6238479e65816dd39591a4f','TASK-001-a2-c2-R2.json'), ('TASK-004','1ee6b06c46e4c626ab6d63be52bb11d7bdfeb518','TASK-004-a2-c3-R2.json')]:
        subprocess.run(['git','merge-base','--is-ancestor',commit,BASE],cwd=WT,check=True)
        r2 = json.loads((plan / 'reviews' / report).read_bytes())
        r1 = json.loads((WT / r2['review_1_ref']).read_bytes())
        assert by_id[task]['status'] == 'accepted'
        assert r1['verdict'] == r2['verdict'] == 'pass'
        assert r1['candidate_fingerprint'] == r2['candidate_fingerprint']
        dependencies.append({'task':task,'accepted_commit_in_base':commit,'passing_r2':report})
    paths = git('diff','--name-only',BASE,HEAD).decode().splitlines()
    assert set(paths) == {'src/local_ports.py','tests/unit/domain_local_ports/test_local_ports.py','.ai/plans/current/PLAN-001/evidence/implementation/TASK-002.md'}
    scope = by_id['TASK-002']['scope']
    def contains(owner, path):
        return path.startswith(owner) if owner.endswith('/') else owner == path
    assert all(any(contains(owner,path) for owner in scope['write_paths']) and not any(contains(owner,path) for owner in scope['prohibited_paths']) for path in paths)
    assert git('show','f38680d2d892d38abaf95402f7470c90a838b68c:src/local_ports.py') == git('show','3f4b42f40d8eb23fa2a3304253573804fe69870c^:src/local_ports.py')
    assert git('show','3f4b42f40d8eb23fa2a3304253573804fe69870c:src/local_ports.py') == git('show',HEAD + ':src/local_ports.py')
    assert git('diff','--name-only',BASE,HEAD,'schemas/v1','.ai/shared','.ai/plans/current/PLAN-001/graph.json','src/domain_values.py','src/contracts.py') == b''
    for module in (p,dv,contracts):
        assert Path(module.__file__).parent == WT / 'src'
    subprocess.run(['git','diff','--check',BASE,HEAD],cwd=WT,check=True)
    print(json.dumps({'candidate':candidate['id'],'base':BASE,'head':HEAD,'fingerprint':FINGERPRINT,'diff_sha256':candidate['diff_sha256'],'context_hashes_verified':len(candidate['context_refs']),'validation_hashes_verified':len(candidate['validation_refs']),'policy_model_digest':candidate['policy_model_digest'],'graph_digest':graph_digest,'task_set_sha256':graph['task_set_sha256'],'isolation':'r4 pass, exact digest','accepted_dependencies':dependencies,'changed_paths':paths,'repair_lineage':'old source -> bounded repair -> byte-identical source at current head','historical_probe_sha256':sha(historical.read_bytes()),'imports':{m.__name__:m.__file__ for m in (p,dv,contracts)},'working_tree':'clean','diff_check':'pass'},indent=2),flush=True)

class FreshRepairTests(unittest.TestCase):
    def test_exact_argument_roundtrip_repeats_tabs_and_detachment(self):
        payloads = ['  payload  ', ' ', '\t', 'one\ntwo', 'one\r\ntwo', 'semi; literal $(text)', 'same', 'same']
        argv = [sys.executable, '-c', 'import json,sys; print(json.dumps(sys.argv[1:]))', *payloads]
        definition_dto, evidence_dto = definition(argv=argv), command_evidence(argv=argv)
        expected = tuple(argv)
        argv.append('caller mutation')
        self.assertEqual(definition_dto.argv, expected)
        self.assertEqual(evidence_dto.argv_redacted, expected)
        for dto in (definition_dto,evidence_dto):
            REGISTRY.validate(wire(dto))
            self.assertEqual(json.loads(json.dumps(wire(dto)))[('argv' if isinstance(dto,p.CommandDefinition) else 'argv_redacted')],list(expected))
        completed = subprocess.run(definition_dto.argv,cwd=WT,shell=False,capture_output=True,text=True,timeout=5)
        self.assertEqual(completed.returncode,0)
        self.assertEqual(json.loads(completed.stdout),payloads)
        print('Fresh process roundtrip: spaces, tabs, LF/CRLF, repeated values and shell metacharacters preserved.',flush=True)

    def test_rejected_arguments_and_unchanged_metadata(self):
        for factory in (definition,command_evidence):
            for value in ('python',b'python',None,(),('python',''),('python',0),('python',False),('python',None),('python','before\0after')):
                with self.subTest(factory=factory.__name__,value=repr(value)):
                    with self.assertRaises((ValueError,TypeError)):
                        factory(argv=value)
        for dto,field in ((definition(),'id'),(command_evidence(),'command_id')):
            for bad in (' leading','trailing ','embedded\nlabel','embedded\tlabel'):
                with self.assertRaises((TypeError,ValueError)):
                    dc.replace(dto,**{field:bad})
        for bad in (' BAD','BAD\nNAME'):
            with self.assertRaises(ValueError):
                dc.replace(definition(),environment_bindings=(bad,))

    def test_missing_unborn_and_actual_git_observations(self):
        branch = git('symbolic-ref','HEAD').decode().strip()
        missing = 'refs/heads/reviewer-TASK-002-c2-absent'
        self.assertEqual(subprocess.run(['git','show-ref','--verify','--quiet',missing],cwd=WT).returncode,1)
        for status,name,oid in [('attached',branch,HEAD),('detached',None,HEAD),('unborn','main',None),('missing',None,None)]:
            self.assertEqual(p.GitHead(status,name,oid).status.value,status)
        for status,oid in [('present',HEAD),('missing',None),('unborn',None)]:
            self.assertEqual(p.GitRefExpectation('refs/heads/main',status,oid).status.value,status)
            self.assertEqual(p.GitRefObservation('refs/heads/main',status,oid).oid,oid)
        with self.assertRaises(ValueError):
            p.GitRefObservation(missing,'missing',HEAD)
        for a,b,status in [(BASE,HEAD,'ancestor'),(HEAD,BASE,'not_ancestor')]:
            code = subprocess.run(['git','merge-base','--is-ancestor',a,b],cwd=WT).returncode
            self.assertEqual(code,0 if status=='ancestor' else 1)
            self.assertEqual(p.AncestryObservation(p.AncestryQuery(a,b),status).status.value,status)

    def test_repair_changes_no_public_signature_or_schema_fields(self):
        before = ast.parse(git('show','f38680d2d892d38abaf95402f7470c90a838b68c:src/local_ports.py').decode())
        after = ast.parse((WT / 'src/local_ports.py').read_text(encoding='utf-8'))
        def public_shapes(tree):
            return [ast.dump(ast.ClassDef(name=n.name,bases=n.bases,keywords=n.keywords,body=[m for m in n.body if isinstance(m,ast.AnnAssign)] + [ast.FunctionDef(name=m.name,args=m.args,body=[ast.Pass()],decorator_list=m.decorator_list,returns=m.returns,type_comment=m.type_comment) for m in n.body if isinstance(m,ast.FunctionDef) and not m.name.startswith('_')],decorator_list=n.decorator_list)) for n in tree.body if isinstance(n,ast.ClassDef)]
        self.assertEqual(public_shapes(before),public_shapes(after))

if __name__ == '__main__':
    verify_identity()
    # Small retained boundary probes are rerun on the new candidate; no old verdict is reused.
    names = ['test_01_exact_protocol_annotations','test_02_schema_fieldsets_and_zero_plan_event','test_03_qualified_reads_atomic_relocation_and_detachment','test_04_transaction_evidence_and_errors','test_05_command_bindings_environment_and_cwd','test_06_all_command_observation_states','test_08_git_effect_expectations_and_ambiguity','test_09_worktree_ensure_control_and_binding_guards','test_10_reconciliation_and_cleanup_are_guarded_requests','test_11_schema_valid_whitespace_argument_must_roundtrip','test_12_schema_valid_multiline_argument_must_roundtrip']
    suite = unittest.TestSuite(prior['BoundaryTests'](name) for name in names)
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(FreshRepairTests))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    assert git('rev-parse','HEAD').decode().strip() == HEAD and git('status','--porcelain=v1') == b''
    sys.exit(0 if result.wasSuccessful() else 1)
