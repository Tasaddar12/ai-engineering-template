"""Independent, read-only candidate review; scratch writes stay under review evidence."""
from __future__ import annotations

import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from unittest.mock import patch

ROOT = Path('D:/Codex Projects/ai-engineering-template')
SOURCE = ROOT / '.worktrees/TASK-005-a1'
REVIEWS = ROOT / '.ai/plans/current/PLAN-001/reviews'
STEM = 'TASK-005-a1-c1-R1'
PYTHON = ROOT / '.ai/local/full-plan-venv/Scripts/python.exe'
CANDIDATE = ROOT / '.ai/plans/current/PLAN-001/reviews/candidates/CANDIDATE-TASK-005-a1-0216c03b1869.json'
sys.dont_write_bytecode = True
sys.path.insert(0, str(SOURCE / 'src'))
import assets
import contracts
import domain_values
import install


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def git(*args: str) -> bytes:
    return subprocess.check_output(['git', *args], cwd=SOURCE)


class IndependentReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = contracts.load_contract_registry(SOURCE / 'schemas/v1')
        cls.catalogs = {p: assets.build_owned_asset_catalog(SOURCE, p, registry=cls.registry) for p in assets.ProviderRoot}
        cls.scratch = tempfile.TemporaryDirectory(prefix=STEM + '-scratch-', dir=REVIEWS)
        cls.scratch_path = Path(cls.scratch.name).resolve()
        assert cls.scratch_path.is_relative_to(REVIEWS.resolve())

    @classmethod
    def tearDownClass(cls) -> None:
        assert cls.scratch_path.is_relative_to(REVIEWS.resolve())
        cls.scratch.cleanup()

    def test_01_exact_candidate_scope_context_and_isolation(self) -> None:
        candidate = json.loads(CANDIDATE.read_bytes())
        self.assertEqual(git('rev-parse', 'HEAD').decode().strip(), candidate['head_oid'])
        self.assertEqual(git('status', '--porcelain'), b'')
        subprocess.run(['git', 'merge-base', '--is-ancestor', candidate['base_oid'], candidate['head_oid']], cwd=SOURCE, check=True)
        for oid in ('1ee6b06c46e4c626ab6d63be52bb11d7bdfeb518', 'e3c1177f993ee74815639a83ef3333faa4ba3957'):
            subprocess.run(['git', 'merge-base', '--is-ancestor', oid, candidate['base_oid']], cwd=SOURCE, check=True)
        self.assertEqual(sha(git('diff', '--binary', candidate['base_oid'], candidate['head_oid'])), candidate['diff_sha256'])
        changed = set(git('diff', '--name-only', candidate['base_oid'], candidate['head_oid']).decode().splitlines())
        self.assertEqual(changed, {'src/assets.py', 'tests/unit/templates/test_assets.py', 'docs/defaults/FRAMEWORK.json', '.ai/plans/current/PLAN-001/evidence/implementation/TASK-005.md'})
        for ref in candidate['context_refs']:
            self.assertEqual(sha((SOURCE / ref['path']).read_bytes()), ref['sha256'], ref['path'])
        for ref in candidate['validation_refs']:
            self.assertEqual(sha((ROOT / ref['path']).read_bytes()), ref['sha256'], ref['path'])
        self.assertEqual(sha((ROOT / '.ai/project/policy.json').read_bytes() + (ROOT / '.ai/project/agent-models.json').read_bytes()), candidate['policy_model_digest'])
        fingerprint = candidate.pop('fingerprint')
        self.assertEqual(sha(json.dumps(candidate, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()), fingerprint)
        plan = SOURCE / '.ai/plans/current/PLAN-001'
        tasks = [json.loads(p.read_bytes()) for p in (plan / 'tasks/current').glob('TASK-*.json')]
        graph = json.loads((plan / 'graph.json').read_bytes())
        isolation = json.loads((plan / 'reviews/r4-isolation-review.json').read_bytes())
        self.assertEqual(contracts.structural_task_digest(tasks), graph['task_set_sha256'])
        self.assertEqual(graph['task_set_sha256'], isolation['task_set_sha256'])
        self.assertEqual((graph['revision'], graph['status'], isolation['verdict']), (4, 'approved', 'pass'))
        self.assertEqual(next(n for n in graph['nodes'] if n['task_id'] == 'TASK-005')['depends_on'], ['TASK-004'])
        dep = next(t for t in tasks if t['id'] == 'TASK-004')
        self.assertEqual(dep['status'], 'accepted')
        for stage in ('R1', 'R2'):
            record = json.loads((plan / f'reviews/TASK-004-a2-c3-{stage}.json').read_bytes())
            self.assertEqual(record['verdict'], 'pass')
        print('IDENTITY: exact clean head/base, diff, all 12 context hashes, validation hash, policy/model digest, fingerprint, approved structural digest, accepted dependency ancestry and reports verified.')

    def test_02_independent_payload_oracle_and_ownership(self) -> None:
        for provider, catalog in self.catalogs.items():
            root = provider.value
            self.assertEqual((len(catalog.assets), len(catalog.framework_assets), len(catalog.seed_assets)), (86, 76, 10))
            self.assertEqual(catalog, assets.build_owned_asset_catalog(SOURCE, provider, registry=self.registry))
            installation = catalog.installation_record.to_dict()
            for asset in catalog.assets:
                path = asset.path.as_wire()
                source_ref = asset.source_ref.as_wire()
                self.assertTrue(path.startswith(root + '/'))
                if source_ref == 'generated/empty-file':
                    expected = b''
                else:
                    expected = (SOURCE / source_ref).read_bytes()
                    if Path(source_ref).suffix.lower() in {'.json', '.md', '.py', '.txt'} or Path(source_ref).name == 'GITATTRIBUTES':
                        expected = expected.replace(b'\r\n', b'\n').replace(b'\r', b'\n')
                        if source_ref.startswith('docs/'):
                            # The only template expansion is checked separately against actual installer output.
                            if b'{{PROVIDER_NOTE}}' not in expected:
                                if provider != assets.ProviderRoot.CODEX:
                                    expected = expected.replace(b'.codex', root.encode())
                                if provider == assets.ProviderRoot.CLAUDE:
                                    expected = expected.replace(b'AGENTS.md', b'CLAUDE.md')
                            else:
                                self.assertNotIn(b'{{PROVIDER_NOTE}}', asset.content)
                                self.assertIn(f'{root}/{provider.entry_name}'.encode(), asset.content)
                                expected = asset.content
                self.assertEqual(asset.content, expected, path)
                self.assertEqual(str(asset.sha256), sha(expected), path)
                self.assertFalse(source_ref.startswith(('.ai/', 'schemas/examples/')))
                expected_roots = installation['owned_roots'] if asset.is_framework_managed else installation['project_owned_roots']
                self.assertTrue(any(domain_values.ScopePath(p).contains(asset.path) for p in expected_roots), path)
            self.assertEqual({Path(a.path.as_wire()).name for a in catalog.assets if '/tools/' in a.path.as_wire()}, {'ai.py', 'contracts.py', 'domain_values.py', 'validate_foundation.py'})
        for module in (assets, contracts, domain_values, install):
            self.assertTrue(Path(module.__file__).resolve().is_relative_to((SOURCE / 'src').resolve()))
        print('PAYLOAD: 258 provider assets independently hashed and classified; exact 4-module flat closure; source-local imports confirmed.')

    def test_03_actual_installer_bytes_and_isolated_catalog_tools(self) -> None:
        for assistant in ('codex', 'claude'):
            provider = assets.ProviderRoot('.' + assistant)
            catalog = self.catalogs[provider]
            target = self.scratch_path / ('installed-' + assistant)
            install.install(str(target), assistant)
            installed_manifest = json.loads((target / str(catalog.manifest_path)).read_bytes())
            expected_entries = [a.manifest_entry() for a in catalog.framework_assets]
            self.assertEqual(installed_manifest['assets'], expected_entries)
            for asset in catalog.framework_assets:
                self.assertEqual((target / str(asset.path)).read_bytes(), asset.content, str(asset.path))
            dynamic = {'STATE.json', 'project/policy.json', 'project/agent-models.json'}
            for asset in catalog.seed_assets:
                relative = str(asset.path).removeprefix(provider.value + '/')
                self.assertTrue((target / str(asset.path)).is_file())
                if relative not in dynamic:
                    self.assertEqual((target / str(asset.path)).read_bytes(), asset.content)
            emitted = self.scratch_path / ('catalog-' + assistant)
            for asset in catalog.assets:
                output = emitted / str(asset.path)
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(asset.content)
            tools_dir = emitted / provider.value / 'tools'
            program = 'import json,sys; from pathlib import Path; sys.path.insert(0,sys.argv[1]); import ai,contracts,domain_values,validate_foundation; print(json.dumps({m.__name__:m.__file__ for m in (ai,contracts,domain_values,validate_foundation)}))'
            result = subprocess.run([str(PYTHON), '-I', '-B', '-c', program, str(tools_dir)], cwd=self.scratch_path, capture_output=True, text=True, check=True)
            origins = json.loads(result.stdout)
            self.assertEqual(len(origins), 4)
            self.assertTrue(all(Path(p).resolve().is_relative_to(tools_dir.resolve()) for p in origins.values()))
            result = subprocess.run([str(PYTHON), '-I', '-B', str(tools_dir / 'validate_foundation.py'), '--project', str(target)], cwd=self.scratch_path, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            print(f'EMITTED {assistant}: 76 exact managed file bytes and all seed destinations match actual installer; catalog-only tools imported in isolation and validated fresh target: {result.stdout.strip()}')

    def test_04_manifest_tamper_and_path_matrix(self) -> None:
        cases = 0
        for provider, catalog in self.catalogs.items():
            original = catalog.manifest_record.to_dict()
            root = provider.value
            variants = []
            for label, field, value in (
                ('hash', 'sha256', '0' * 64), ('ownership', 'ownership', 'seed_only'),
                ('source metadata', 'source_ref', 'docs/defaults/README.md'),
            ):
                manifest = copy.deepcopy(original)
                manifest['assets'][0][field] = value
                variants.append((label, manifest))
            manifest = copy.deepcopy(original); manifest['assets'].pop(); variants.append(('missing', manifest))
            manifest = copy.deepcopy(original); manifest['assets'].reverse(); variants.append(('reordered', manifest))
            manifest = copy.deepcopy(original); manifest['framework_version'] = 'tampered'; variants.append(('version', manifest))
            manifest = copy.deepcopy(original); manifest['migration_ids'] = ['injected']; variants.append(('migration', manifest))
            manifest = copy.deepcopy(original); manifest['unknown'] = True; variants.append(('unknown field', manifest))
            for path in ('../escape', '/absolute', 'C:/escape', '//server/share/file', root + '/../escape', root + '/tools/CON.txt', root + '/tools/file:stream', root + '/tools/trailing.', root + '/tools/foo\u200b.py', root + '/tools/x\uff1ay', '.unselected/file'):
                manifest = copy.deepcopy(original); manifest['assets'][0]['path'] = path; variants.append(('unsafe ' + path, manifest))
            for alias in (original['assets'][0]['path'], original['assets'][0]['path'].upper(), root + '/tools', root + '/tools/ai.py/child'):
                manifest = copy.deepcopy(original); extra = copy.deepcopy(manifest['assets'][0]); extra['path'] = alias; manifest['assets'].append(extra); variants.append(('alias/collision ' + alias, manifest))
            for left, right in ((root + '/caf\u00e9.md', root + '/cafe\u0301.md'), (root + '/K.md', root + '/\u212a.md'), (root + '/foo.md', root + '/\uff46oo.md')):
                manifest = copy.deepcopy(original)
                for path in (left, right):
                    extra = copy.deepcopy(manifest['assets'][0]); extra['path'] = path; manifest['assets'].append(extra)
                variants.append(('unicode alias ' + left, manifest))
            for label, manifest in variants:
                with self.subTest(provider=root, variant=label), self.assertRaises(domain_values.DomainException):
                    assets.verify_asset_manifest(manifest, catalog, self.registry)
                cases += 1
            changed_asset = replace(catalog.assets[0], content=catalog.assets[0].content + b'tampered')
            with self.assertRaises(domain_values.DomainException):
                assets.verify_asset_manifest(original, replace(catalog, assets=(changed_asset,) + catalog.assets[1:]), self.registry)
            for alias in (str(catalog.assets[0].path).upper(), root + '/tools', root + '/tools/ai.py/child'):
                with self.assertRaises(ValueError):
                    replace(catalog, assets=catalog.assets + (replace(catalog.assets[0], path=alias),))
        print(f'NEGATIVE: {cases} manifest mutation cases plus 3 payload tamper and 9 constructor alias/collision cases rejected.')

    def test_05_source_failures_and_transitive_tool_cycle(self) -> None:
        scratch_source = self.scratch_path / 'source'
        for directory in ('src', 'schemas/v1', 'docs'):
            shutil.copytree(SOURCE / directory, scratch_source / directory, ignore=shutil.ignore_patterns('__pycache__'))
        ai_path = scratch_source / 'src/ai.py'
        ai_path.write_bytes(ai_path.read_bytes() + b'\nimport review_helper\n')
        (scratch_source / 'src/review_helper.py').write_bytes(b'import review_leaf\n')
        (scratch_source / 'src/review_leaf.py').write_bytes(b'import review_helper\n')
        (scratch_source / 'src/unreachable_review_helper.py').write_bytes(b'raise RuntimeError("must not include")\n')
        catalog = assets.build_owned_asset_catalog(scratch_source)
        self.assertEqual({Path(a.source_ref.as_wire()).name for a in catalog.assets if a.source_ref.as_wire().startswith('src/')}, {'ai.py', 'contracts.py', 'domain_values.py', 'validate_foundation.py', 'review_helper.py', 'review_leaf.py'})
        helper = scratch_source / 'src/review_helper.py'
        before = helper.read_bytes()
        helper.write_bytes(b'not valid Python !\n')
        with self.assertRaises(domain_values.DomainException):
            assets.build_owned_asset_catalog(scratch_source)
        helper.write_bytes(before)
        required = scratch_source / 'src/contracts.py'
        required.rename(required.with_suffix('.saved'))
        with self.assertRaises(domain_values.DomainException):
            assets.build_owned_asset_catalog(scratch_source)
        required.with_suffix('.saved').rename(required)
        entry = scratch_source / 'docs/agents/README.md'
        entry.rename(entry.with_suffix('.saved'))
        with self.assertRaises(domain_values.DomainException):
            assets.build_owned_asset_catalog(scratch_source)
        entry.with_suffix('.saved').rename(entry)
        framework = scratch_source / 'docs/defaults/FRAMEWORK.json'
        original = framework.read_bytes()
        record = json.loads(original)
        record['owned_roots'].append('.codex/project/')
        framework.write_text(json.dumps(record), encoding='utf-8')
        with self.assertRaises(domain_values.DomainException):
            assets.build_owned_asset_catalog(scratch_source)
        framework.write_bytes(original)
        try:
            link = scratch_source / 'docs/templates/review-link.md'
            link.symlink_to(entry)
        except OSError as exc:
            print(f'LINK FIXTURE unavailable: {exc}; no successful linked-source probe claimed.')
        else:
            with self.assertRaises(domain_values.DomainException):
                assets.build_owned_asset_catalog(scratch_source)
            link.unlink()
            print('SOURCE: actual linked document rejected.')
        print('SOURCE: transitive helper cycle included once; unreachable helper excluded; malformed import source, missing required helper/index, and overlapping ownership rejected.')


if __name__ == '__main__':
    unittest.main(verbosity=2)
