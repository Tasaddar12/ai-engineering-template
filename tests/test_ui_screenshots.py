"""Fixture capture adapters exercise coverage, never real browser observations."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.ai/runtime'))
from lib.ui_screenshots import produce, requirements, validate
from lib.results import VerbError

REVISION = 'a' * 40


def scope(kind='local'):
    return {'schema': 1, 'revision': REVISION, 'change_kind': kind,
            'affected_routes': ['settings'], 'routes': [
                {'route': 'home', 'url': 'http://localhost:3000/', 'criteria': ['A-01'],
                 'states': {'default': 'Open home with fixture account; wait for heading'},
                 'viewports': {'wide': {'width': 1280, 'height': 800}}},
                {'route': 'settings', 'url': 'http://localhost:3000/settings', 'criteria': ['A-02'],
                 'states': {'default': 'Load fixture settings; wait for form',
                            'error': 'Reject fixture save; wait for error banner'},
                 'viewports': {'wide': {'width': 1280, 'height': 800},
                               'narrow': {'width': 360, 'height': 800}}}]}


class ScreenshotCoverageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.calls = []

    def fake_capture(self, requirement, target):
        self.calls.append(requirement)
        target.write_bytes(b'fixture bytes, not a browser screenshot')

    def evidence(self, plan):
        return produce(plan, REVISION, self.fake_capture, self.root)

    def check(self, plan, manifest):
        return validate(plan, manifest, REVISION, self.root)

    def test_local_cartesian_matrix_and_single_producer(self):
        plan = scope()
        report = self.check(plan, self.evidence(plan))
        self.assertEqual(('complete', 4, 4), (report['status'], report['required_count'], report['covered_count']))
        self.assertEqual(4, len(self.calls))
        self.assertEqual({'settings'}, {r['route'] for r in self.calls})
        self.assertEqual({('default', 'wide'), ('default', 'narrow'), ('error', 'wide'), ('error', 'narrow')},
                         {(r['state'], r['viewport']) for r in report['covered']})

    def test_shared_edit_requires_every_dependent_route(self):
        plan = scope('shared')
        manifest = self.evidence(plan)
        self.assertEqual(5, len(manifest['captures']))
        manifest['captures'] = [r for r in manifest['captures'] if r['route'] == 'home']
        report = self.check(plan, manifest)
        self.assertEqual('gaps_found', report['status'])
        self.assertEqual((1, 4), (report['covered_count'], len(report['missing'])))
        self.assertEqual({'settings'}, {r['route'] for r in report['missing']})

    def test_each_binding_mismatch_is_missing(self):
        for field, bad in [('revision', 'b' * 40), ('url', 'http://wrong/'), ('procedure', 'wrong'),
                           ('width', 99), ('height', True), ('criterion', 'OTHER'), ('state', 'other'),
                           ('viewport', 'other'), ('route', 'home')]:
            with self.subTest(field=field):
                plan = scope()
                manifest = self.evidence(plan)
                manifest['captures'][0][field] = bad
                report = self.check(plan, manifest)
                self.assertEqual(3, report['covered_count'])
                self.assertEqual(1, len(report['missing']))

    def test_missing_failed_duplicate_stale_and_tampered_captures(self):
        for mode in ('missing', 'failed', 'duplicate', 'stale', 'digest', 'unavailable', 'invalid-path', 'no-digest', 'contradiction', 'empty'):
            with self.subTest(mode=mode):
                plan = scope()
                manifest = self.evidence(plan)
                row = manifest['captures'][0]
                if mode == 'missing':
                    manifest['captures'].pop(0)
                elif mode == 'failed':
                    row['result'] = 'failed'
                elif mode == 'duplicate':
                    manifest['captures'].append(copy.deepcopy(row))
                elif mode == 'stale':
                    manifest['revision'] = 'b' * 40
                elif mode == 'digest':
                    Path(row['artifact']).write_bytes(b'tampered')
                elif mode == 'no-digest':
                    del row['sha256']
                elif mode == 'contradiction':
                    row['error'] = 'fixture browser failed'
                elif mode == 'invalid-path':
                    row['artifact'] = 'bad\0path'
                elif mode == 'unavailable':
                    Path(row['artifact']).unlink()
                else:
                    Path(row['artifact']).write_bytes(b'')
                report = self.check(plan, manifest)
                self.assertEqual('gaps_found', report['status'])
                self.assertEqual(0 if mode == 'stale' else 3, report['covered_count'])

    def test_adapter_failure_and_noop_cannot_reuse_prior_capture(self):
        plan = scope()
        self.evidence(plan)
        def failing(row, target):
            if row['state'] == 'error':
                raise RuntimeError('fixture browser unavailable')
            self.fake_capture(row, target)
        manifest = produce(plan, REVISION, failing, self.root)
        self.assertEqual(2, self.check(plan, manifest)['covered_count'])
        self.assertIn('fixture browser unavailable', manifest['captures'][2]['error'])
        noop = produce(plan, REVISION, lambda row, target: None, self.root)
        self.assertEqual(0, self.check(plan, noop)['covered_count'])

    def test_private_absolute_and_manifest_relative_artifacts(self):
        plan = scope()
        manifest = self.evidence(plan)
        manifest['captures'][0]['artifact'] = Path(manifest['captures'][0]['artifact']).name
        self.assertEqual('complete', self.check(plan, manifest)['status'])

    def test_multiple_criteria_expand_and_malformed_inputs_fail_closed(self):
        plan = scope()
        plan['routes'][1]['criteria'].append('A-03')
        self.assertEqual(8, len(requirements(plan, REVISION)))
        for mutate in (lambda s: s.update(affected_routes=[]),
                       lambda s: s.update(change_kind='unknown'),
                       lambda s: s.update(revision='b' * 40),
                       lambda s: s['routes'].append(copy.deepcopy(s['routes'][0])),
                       lambda s: s['routes'][0].update(viewports={'wide': {'width': True, 'height': 10}})):
            broken = scope()
            mutate(broken)
            with self.assertRaises(VerbError):
                requirements(broken, REVISION)
        for broken in (None, [], {'schema': True, 'revision': REVISION}, {'schema': 1, 'revision': REVISION, 'captures': {}},
                       {'schema': 1, 'revision': REVISION, 'captures': [None]}):
            self.assertEqual(0, self.check(scope(), broken)['covered_count'])

    def test_real_runtime_verb_reads_producer_manifest_and_reports_gaps(self):
        plan = scope('shared')
        manifest = self.evidence(plan)
        manifest['captures'].pop()
        scope_path, manifest_path = self.root / 'scope.json', self.root / 'manifest.json'
        scope_path.write_text(json.dumps(plan), encoding='utf-8')
        manifest_path.write_text(json.dumps(manifest), encoding='utf-8')
        result = subprocess.run([sys.executable, str(ROOT / '.ai/runtime/phase.py'), 'query',
                                 'verification.screenshots', '--scope-file', str(scope_path),
                                 '--manifest-file', str(manifest_path), '--expected-revision', REVISION],
                                cwd=self.root, capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual('gaps_found', data['status'])
        self.assertEqual(4, data['covered_count'])
        self.assertEqual(1, len(data['missing']))
        self.assertFalse((self.root / '.planning').exists())


if __name__ == '__main__':
    unittest.main()
