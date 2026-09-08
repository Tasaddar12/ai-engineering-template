from __future__ import annotations
import ast
import copy
import hashlib
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(r'D:/Codex Projects/ai-engineering-template')
WT = ROOT / '.worktrees/TASK-005-a1'
PREFIX = ROOT / '.ai/plans/current/PLAN-001/reviews/TASK-005-a1-c1-R2'
PLAN = '.ai/plans/current/PLAN-001/'
BASE = '60a2a37f04b5d23561ce1fbc66f71b130c212f90'
HEAD = '0216c03b18698a3ff4bc89c9b0ae9749255425ef'
CANDIDATE = PLAN + 'reviews/candidates/CANDIDATE-TASK-005-a1-0216c03b1869.json'
R1 = PLAN + 'reviews/TASK-005-a1-c1-R1.json'
FINGERPRINT = 'e38bebfb47b00e775c3c8462a7051f21cd41313ebd268c7b6426852e27010e58'
sys.dont_write_bytecode = True
sys.path.insert(0, str(WT / 'src'))
import assets
import contracts
import domain_values
import install


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(root, path):
    return json.loads((root / path).read_bytes())


def git(*args, root=WT):
    result = subprocess.run(['git', *args], cwd=root, capture_output=True, check=True)
    return result.stdout


def canonical(record):
    return json.dumps(record, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


class ConsistencyProbes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = contracts.load_contract_registry(WT / 'schemas/v1')
        cls.catalogs = {p: assets.build_owned_asset_catalog(WT, p, registry=cls.registry) for p in assets.ProviderRoot}
        for module in (assets, contracts, domain_values, install):
            assert Path(module.__file__).resolve().parent == (WT / 'src').resolve()
        print('All review imports resolve to candidate src; offline registry has', len(cls.registry.kinds), 'kinds.')

    def test_01_exact_candidate_r1_scope_and_dependency_bindings(self):
        candidate = read(ROOT, CANDIDATE)
        self.registry.validate(candidate)
        self.assertEqual(git('rev-parse', 'HEAD').decode().strip(), HEAD)
        self.assertEqual(git('rev-parse', 'HEAD', root=ROOT).decode().strip(), BASE)
        self.assertEqual(git('status', '--porcelain'), b'')
        git('merge-base', '--is-ancestor', BASE, HEAD)
        self.assertEqual(sha(git('diff', '--binary', BASE, HEAD)), candidate['diff_sha256'])
        changed = git('diff', '--name-only', BASE, HEAD).decode().splitlines()
        task = read(WT, PLAN + 'tasks/current/TASK-005.json')
        self.assertEqual(len(changed), 4)
        for path in changed:
            actual = domain_values.ScopePath.exact_file(path)
            self.assertTrue(any(domain_values.ScopePath(p).contains(actual) for p in task['scope']['write_paths']), path)
            self.assertFalse(any(domain_values.ScopePath(p).overlaps(actual) for p in task['scope']['prohibited_paths']), path)
        for reference in candidate['context_refs']:
            committed = git('show', HEAD + ':' + reference['path'])
            self.assertEqual(sha(committed), reference['sha256'], reference['path'])
        for reference in candidate['validation_refs']:
            self.assertEqual(sha((ROOT / reference['path']).read_bytes()), reference['sha256'])
        policy = ROOT / '.ai/project/policy.json'
        models = ROOT / '.ai/project/agent-models.json'
        self.assertEqual(sha(policy.read_bytes() + models.read_bytes()), candidate['policy_model_digest'])
        for path in ('.ai/project/policy.json', '.ai/project/agent-models.json'):
            self.assertEqual(read(ROOT, path), read(WT, path))
            self.assertEqual(git('show', BASE + ':' + path), git('show', HEAD + ':' + path))
        no_fp = {k: v for k, v in candidate.items() if k != 'fingerprint'}
        self.assertEqual(sha(canonical(no_fp)), FINGERPRINT)
        self.assertEqual(candidate['fingerprint'], FINGERPRINT)
        r1 = read(ROOT, R1)
        self.registry.validate(r1)
        self.assertEqual((r1['candidate_ref'], r1['candidate_fingerprint'], r1['stage'], r1['verdict']), (CANDIDATE, FINGERPRINT, 'implementation', 'pass'))
        self.assertEqual({c['id'] for c in r1['checks']}, {f'R1-{n:02}' for n in range(1, 12)})
        self.assertTrue(all(c['status'] == 'pass' for c in r1['checks']))
        self.assertEqual(r1['findings'], [])
        self.assertEqual(r1['independent_session_id'], '/root/r1_005_c1')
        self.assertEqual(r1['implementation_session_id'], '/root/implement_005')
        graph = read(WT, PLAN + 'graph.json')
        isolation = read(WT, PLAN + 'reviews/r4-isolation-review.json')
        self.registry.validate(graph)
        self.registry.validate(isolation)
        task_records = [json.loads(p.read_bytes()) for p in (WT / PLAN / 'tasks/current').glob('TASK-*.json')]
        digest = contracts.structural_task_digest(task_records)
        self.assertEqual(digest, isolation['task_set_sha256'])
        self.assertEqual((graph['revision'], isolation['graph_revision'], isolation['verdict']), (4, 4, 'pass'))
        self.assertEqual(next(n for n in graph['nodes'] if n['task_id'] == 'TASK-005')['depends_on'], task['depends_on'])
        dep_task = read(WT, PLAN + 'tasks/current/TASK-004.json')
        self.assertEqual(dep_task['status'], 'accepted')
        dep_candidate_ref = PLAN + 'reviews/candidates/CANDIDATE-TASK-004-a2-e3c1177f993e.json'
        dep_candidate = read(WT, dep_candidate_ref)
        for suffix in ('R1', 'R2'):
            report = read(WT, PLAN + 'reviews/TASK-004-a2-c3-' + suffix + '.json')
            self.registry.validate(report)
            self.assertEqual(report['candidate_ref'], dep_candidate_ref)
            self.assertEqual(report['candidate_fingerprint'], dep_candidate['fingerprint'])
            self.assertEqual(report['verdict'], 'pass')
        for oid in (dep_candidate['head_oid'], '1ee6b06c46e4c626ab6d63be52bb11d7bdfeb518'):
            git('merge-base', '--is-ancestor', oid, BASE)
        for module in ('contracts.py', 'domain_values.py', 'install.py', 'validate_foundation.py', 'ai.py'):
            self.assertEqual(git('show', dep_candidate['head_oid'] + ':src/' + module), git('show', HEAD + ':src/' + module))
        git('diff', '--check', BASE, HEAD)
        print('Identity PASS:', candidate['diff_sha256'], FINGERPRINT)
        print('12 committed context hashes, validation bytes, raw policy/model digest, 4 scope paths, schema-valid same-candidate R1, accepted TASK-004 ancestry/code and approved structural digest PASS:', digest)
        retained = sorted((ROOT / PLAN / 'reviews').glob('TASK-005-a1-c1-R1*'))
        snapshot = {str(p.relative_to(ROOT)).replace('\\', '/'): sha(p.read_bytes()) for p in retained if p.is_file()}
        (Path(str(PREFIX) + '-r1-bindings.txt')).write_text(json.dumps(snapshot, indent=2) + '\n', encoding='utf-8')
        print('Retained exact R1 and companion digests:', len(snapshot), 'files; R1 JSON SHA-256:', snapshot[R1])

    def test_02_ownership_schema_and_canonical_seed_boundary(self):
        json_seed_count = 0
        for provider, catalog in self.catalogs.items():
            root = provider.value
            installation = catalog.installation_record.to_dict()
            self.assertEqual(catalog.framework_version, install.VERSION)
            self.assertEqual(installation['schema_compatibility'], '1.0')
            self.assertEqual(catalog.migration_ids, ())
            owned = [domain_values.ScopePath(p) for p in installation['owned_roots']]
            project = [domain_values.ScopePath(p) for p in installation['project_owned_roots']]
            for asset in catalog.assets:
                target, other = (owned, project) if asset.is_framework_managed else (project, owned)
                self.assertEqual(sum(p.contains(asset.path) for p in target), 1)
                self.assertFalse(any(p.overlaps(asset.path) for p in other))
            self.assertTrue(any(p.contains(catalog.manifest_path) for p in owned))
            self.assertTrue(catalog.asset(root + '/framework.json').is_framework_managed)
            self.assertNotIn(catalog.manifest_path.as_wire(), {a.path.as_wire() for a in catalog.assets})
            self.assertEqual(len(catalog.framework_assets), 76)
            self.assertEqual(len(catalog.seed_assets), 10)
            for asset in catalog.seed_assets:
                self.assertFalse(asset.is_framework_managed)
                if asset.path.value.endswith('.json'):
                    record = json.loads(asset.content)
                    self.registry.validate(record, source=asset.path.value)
                    json_seed_count += 1
            state = json.loads(catalog.asset(root + '/STATE.json').content)
            self.assertEqual((state['project_id'], state['updated_at']), ('template-project', '1970-01-01T00:00:00Z'))
            models = json.loads(catalog.asset(root + '/project/agent-models.json').content)
            self.assertEqual(models['active_provider'], 'openai')
            policy = json.loads(catalog.asset(root + '/project/policy.json').content)
            self.assertTrue(all(p['provider'] is None and not p['configured'] for p in policy['model_profiles']))
            before = canonical(catalog.manifest_record.to_dict())
            state.update(project_id='review-consumer-project', updated_at='2026-09-08T00:00:00Z')
            self.registry.validate(state)
            self.assertEqual(before, canonical(catalog.manifest_record.to_dict()))
            self.assertNotEqual(sha(canonical(state)), str(catalog.asset(root + '/STATE.json').sha256))
            assets.verify_asset_manifest(json.loads(before), catalog, self.registry)
        print('3 provider catalogs: each 76 managed + 10 seed assets; ownership disjoint/complete including manifest metadata; 12 JSON seeds schema-valid. Static defaults stay detached from consumer instantiation.')

    def test_03_bootstrap_manifest_projection_and_helper_contract(self):
        for assistant, provider in (('codex', assets.ProviderRoot.CODEX), ('claude', assets.ProviderRoot.CLAUDE)):
            catalog = self.catalogs[provider]
            managed, seed, namespace, entry = install._planned_payload(WT, ROOT / 'unwritten-review-project', assistant)
            old = json.loads(managed[namespace + '/framework/manifest.json'])
            self.registry.validate(old)
            new = catalog.manifest_record.to_dict()
            framework_projection = {**new, 'assets': [e for e in new['assets'] if e['ownership'] == 'framework']}
            self.assertEqual(old, framework_projection)
            self.assertEqual({a.path.value for a in catalog.seed_assets}, set(seed))
            instantiated_models = json.loads(seed[namespace + '/project/agent-models.json'])
            self.assertEqual(instantiated_models['active_provider'], 'anthropic' if assistant == 'claude' else 'openai')
            self.assertEqual(json.loads(seed[namespace + '/STATE.json'])['project_id'], 'unwritten-review-project')
            installed_tools = {Path(a.path.value).name: a for a in catalog.framework_assets if '/tools/' in a.path.value}
            self.assertEqual(set(installed_tools), {'ai.py', 'contracts.py', 'domain_values.py', 'validate_foundation.py'})
            for name, asset in installed_tools.items():
                normalized = (WT / 'src' / name).read_bytes().replace(b'\r\n', b'\n').replace(b'\r', b'\n')
                self.assertEqual(asset.content, normalized)
                tree = ast.parse(asset.content)
                for node in ast.walk(tree):
                    local_names = []
                    if isinstance(node, ast.Import):
                        local_names = [a.name.split('.')[0] for a in node.names]
                    elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                        local_names = [node.module.split('.')[0]]
                    for imported in local_names:
                        if (WT / 'src' / (imported + '.py')).is_file():
                            self.assertIn(imported + '.py', installed_tools)
        print('Both bootstrap manifests equal the exact managed projection of the combined v1 manifest. Existing instantiation differs only at documented project seed boundary; accepted four-module flat tool payload/import closure preserved.')

    def test_04_contract_failure_semantics_and_version_rejection(self):
        catalog = self.catalogs[assets.ProviderRoot.CODEX]
        examples = []
        unknown = catalog.manifest_record.to_dict()
        unknown['assets'][0]['undeclared'] = True
        examples.append((unknown, domain_values.ErrorCategory.VALIDATION_FAILED))
        version = catalog.manifest_record.to_dict()
        version['schema_version'] = '2.0'
        examples.append((version, domain_values.ErrorCategory.UNSUPPORTED_CAPABILITY))
        payload_version = catalog.manifest_record.to_dict()
        payload_version['framework_version'] = '999.0'
        examples.append((payload_version, domain_values.ErrorCategory.VALIDATION_FAILED))
        ownership = catalog.manifest_record.to_dict()
        seed = next(e for e in ownership['assets'] if e['ownership'] == 'seed_only')
        seed['ownership'] = 'framework'
        examples.append((ownership, domain_values.ErrorCategory.VALIDATION_FAILED))
        escape = catalog.manifest_record.to_dict()
        escape['assets'][0]['source_ref'] = '../project-knowledge.json'
        examples.append((escape, domain_values.ErrorCategory.INVALID_INPUT))
        for manifest, expected in examples:
            with self.subTest(expected=expected.value):
                with self.assertRaises(domain_values.DomainException) as caught:
                    assets.verify_asset_manifest(manifest, catalog, self.registry)
                self.assertEqual(caught.exception.category, expected)
                self.assertFalse(caught.exception.error.retryable)
                self.assertIsInstance(caught.exception.error.details, domain_values.FrozenJsonObject)
        print('5 focused trust/contract cases rejected with accepted non-retryable typed errors: unknown nested field, unsupported schema version, framework version drift, seed ownership escalation and escaping source provenance.')


if __name__ == '__main__':
    command = read(WT, PLAN + 'commands/test.TASK-005.json')
    argv = [sys.executable, *command['argv'][1:]]
    env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONPATH': str(WT / 'src')}
    run = subprocess.run(argv, cwd=WT, env=env, capture_output=True, text=True, timeout=180)
    declared = 'cwd: ' + str(WT) + '\nargv: ' + repr(argv) + '\nexit: ' + str(run.returncode) + '\n' + run.stdout + run.stderr
    Path(str(PREFIX) + '-declared.txt').write_text(declared, encoding='utf-8')
    print(declared)
    assert run.returncode == 0 and 'Ran 10 tests' in run.stderr and '\nOK\n' in run.stderr
    unittest.main(verbosity=2)

