"""Offline installed-host contracts for canonical identity and checklist evidence."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1]
URL = 'https://github.com/acme/project/issues/7'
EXTERNAL = 'https://github.com/acme/project/issues/9'
KEY = 'acme/project|stored-read|foreign-owner'
HEADING = 'Stored read ownership'


def machine(key=KEY):
    return 'engineer-risk-' + hashlib.sha256(json.dumps(key, separators=(',', ':')).encode()).hexdigest()


def section(addresses=None, heading=HEADING, key=KEY):
    addresses = addresses if addresses is not None else ['canonical-old', 'user-content-' + machine(key)]
    return ''.join('<p dir="auto"><a name="' + value + '"></a></p>\n' for value in addresses) + \
        '<h3 dir="auto">' + heading + '</h3><p>Canonical risk key: ' + key + '</p>'


# Only the provider subprocess is replaced. The installed CLI, origin checks,
# source digests, consumed intent checks, selector, registration and audit run.
DRIVER = r'''import json, os, pathlib, runpy, subprocess, sys
runtime = pathlib.Path(os.environ['EXTERNAL_TARGET_RUNTIME'])
sys.path.insert(0, str(runtime.parent))
from lib import security_tracking as security
store = pathlib.Path(os.environ['EXTERNAL_TARGET_STORE'])
packet = json.loads(store.read_text()) if store.exists() else {'calls': []}
original = subprocess.run
def offline(command, **options):
    if not command or command[0] != 'gh':
        return original(command, **options)
    argv = command[1:]
    packet['calls'].append(argv)
    store.write_text(json.dumps(packet))
    if argv[:2] == ['issue', 'view']:
        target = next(value for value in argv if value.startswith('https://'))
        result = packet['issues'][target]
    elif argv[0] == 'api':
        result = {'body_html': packet['html']}
    else:
        raise AssertionError('Forbidden offline provider operation: ' + repr(argv))
    return subprocess.CompletedProcess(command, 0, json.dumps(result), '')
subprocess.run = offline
if sys.argv[1] == 'seed':
    ctx = security.scope(security.Args(['1']))
    root = pathlib.Path(os.environ['ENGINEER_ROOT'])
    tokens = []
    for index, risk in enumerate(packet['entries']):
        entries_file = root / ('entry-' + str(index) + '.json')
        entries, sources, threats = security._inputs(security.Args(['1', '--entries-file', str(entries_file)]), ctx)
        operation = {'key': 'container:' + ctx['key'], 'title': 'Canonical checklist',
                     'body': packet['reviewed_body'] + '<a name="canonical-old"></a>\n' +
                         security._entry_block(packet['entries'][0], packet['entries'][0]['canonical_url']),
                     'labels': ['phase-security-checklist'],
                     'action': 'edit', 'url': packet['container'], 'before': 'captured-before'}
        review = {'scope': {k: str(v) if isinstance(v, pathlib.Path) else v for k, v in ctx.items()},
                  'entries': entries, 'operations': [operation], 'source_files': [str(p.relative_to(root)) for p in sources],
                  'source_digest': security.digest(sources), 'revision': security._head(), 'ready': True,
                  'pending': [], 'title': operation['title'], 'label': 'phase-security-checklist'}
        token = security._hash(security._preview_identity(review))
        security.write_json(security._runtime_dir() / 'previews' / (token + '.json'),
            {**review, 'token': token, 'consumed': True, 'complete': False,
             'results': [{'key': operation['key'], 'url': packet['container']}]})
        tokens.append(token)
    intent_key = security._hash({'origin': ctx['origin'], 'key': operation['key']})
    marker = '<!-- engineer-security-intent:' + intent_key + ' -->'
    body = operation['body'].rstrip() + '\n\n' + marker + '\n'
    security.write_json(security._runtime_dir() / 'intents' / (intent_key + '.json'),
        {'origin': ctx['origin'], 'marker': marker, 'operation': {**operation, 'body': body},
         'state': 'complete', 'source_digest': review['source_digest'], 'url': packet['container']})
    packet['issues'][packet['container']]['body'] = body
    state_path, state = security._state(ctx)
    risk = packet['entries'][0]
    state['risks'][risk['key']] = {'canonical_url': risk['canonical_url'],
        'aliases_occurrences': 'Earlier preserved occurrence', 'occurrences': []}
    security.write_json(state_path, state)
    packet.update(tokens=tokens, state_path=str(state_path), scope_key=ctx['key'],
                  runtime_dir=str(security._runtime_dir()))
    store.write_text(json.dumps(packet))
    print(json.dumps({'tokens': tokens}))
elif sys.argv[1] == 'select':
    targets, pending = security.rendered_targets(packet['container'], packet['selection_entries'], security.repository.identity())
    print(json.dumps({'targets': targets, 'pending': pending}))
else:
    sys.argv = [str(runtime), 'query', *sys.argv[1:]]
    runpy.run_path(str(runtime), run_name='__main__')
'''


class InstalledExternalTargets(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix='engineer-external-hosts-')
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.base = Path(cls.temporary.name)
        cls.source = Path(os.environ.get('ENGINEER_EXTERNAL_TARGET_SOURCE', SOURCE))
        cls.pin = os.environ.get('ENGINEER_EXTERNAL_TARGET_REF', 'HEAD')
        cls.installs = {}
        for host in ('codex', 'claude'):
            target = cls.base / host
            process = subprocess.run([sys.executable, '-I', str(cls.source / 'bin/install.py'),
                '--source', str(cls.source), '--ref', cls.pin, '--target', str(target),
                '--host', host, '--local', '--no-hooks'], text=True, capture_output=True, timeout=60)
            if process.returncode:
                raise AssertionError(process.stderr or process.stdout)
            cls.installs[host] = target / ('.codex' if host == 'codex' else '.claude') / 'engineer/bin/engineer.py'

    def fixture(self, host, canonical=EXTERNAL, shared=False):
        temporary = tempfile.TemporaryDirectory(prefix='engineer-external-project-')
        self.addCleanup(temporary.cleanup)
        project = Path(temporary.name)
        self.project = project
        self.env = {**os.environ, 'ENGINEER_ROOT': str(project), 'ENGINEER_HOST': host,
                    'EXTERNAL_TARGET_RUNTIME': str(self.installs[host]),
                    'EXTERNAL_TARGET_STORE': str(project / 'provider.json')}
        self.git('init', '-b', 'main')
        self.git('config', 'user.name', 'Offline fixture')
        self.git('config', 'user.email', 'offline@example.invalid')
        self.git('remote', 'add', 'origin', 'https://github.com/acme/project.git')
        (project / 'README.md').write_text('Inert synthetic project\n')
        self.git('add', 'README.md')
        self.git('commit', '-m', 'fixture')
        self.cli('project.init', '--name', 'Fixture', '--description', 'Offline source fixture',
                 '--core-value', 'Preserve canonical identities')
        directory = Path(self.cli('phase.add', 'Evidence selection')['directory'])
        identifier = 'T-01-SC' if shared else 'T-01-01'
        selected = canonical if canonical.startswith(URL + '#') else URL + '#user-content-' + machine()
        entries = []
        for index in range(2 if shared else 1):
            name = '01-' + str(index + 1).zfill(2) + '-PLAN.md'
            (directory / name).write_text('<threat_model>\n'
                '| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |\n'
                '|---|---|---|---|---|---|\n| [' + identifier + '](' + selected +
                ') | T | stored read | high | mitigate | Verify owner before read |\n</threat_model>\n')
            risk = {'key': KEY, 'id': identifier, 'heading': HEADING, 'plan': name, 'threat_id': identifier,
                    'planned': True, 'owner': 'Fixture owner', 'scope_acceptance': 'Refuse foreign owner',
                    'assessment_uncertainty': 'Source fixture only', 'lifecycle_outcome': 'open',
                    'next_action': 'Verify stored read', 'revision_check_evidence': 'Inert offline source',
                    'aliases_occurrences': 'Shared owners in distinct PLAN registers' if shared else name,
                    'canonical_url': canonical,
                    'match_review': {'disposition': 'existing', 'url': canonical,
                        'evidence': 'Synthetic established identity', 'reviewed_issue_urls': [canonical.split('#')[0]],
                        'reviewed_pr_urls': []}}
            entries.append(risk)
            (project / ('entry-' + str(index) + '.json')).write_text(json.dumps([risk]))
        self.git('add', '.planning', *('entry-' + str(index) + '.json' for index in range(len(entries))))
        self.git('commit', '-m', 'captured source and entries')
        self.store = project / 'provider.json'
        issue = {'url': URL, 'title': 'Canonical checklist', 'body': '', 'state': 'OPEN',
                 'labels': ['phase-security-checklist']}
        self.save({'container': URL, 'entries': entries, 'selection_entries': entries[:1],
                   'reviewed_body': 'Exact inert already written checklist\r\n',
                   'issues': {URL: issue}, 'html': section(), 'calls': []})
        self.cli('seed')
        return self.packet()

    def git(self, *args):
        return subprocess.run(['git', *args], cwd=self.project, text=True, capture_output=True,
                              check=True, timeout=30).stdout.strip()

    def cli(self, *args, success=True):
        process = subprocess.run([sys.executable, '-I', '-B', '-c', DRIVER, *args],
            cwd=self.project, env=self.env, text=True, capture_output=True, timeout=30)
        self.assertEqual(success, process.returncode == 0, process.stderr or process.stdout)
        return json.loads(process.stdout if success else process.stderr)

    def packet(self):
        return json.loads(self.store.read_text())

    def save(self, packet):
        self.store.write_text(json.dumps(packet))

    def publish(self, token):
        return self.cli('security.threat-publish', '1', '--preview-token', token, '--publish')

    def no_writes(self):
        self.assertTrue(all(call[0] == 'api' or call[:2] == ['issue', 'view'] for call in self.packet()['calls']))

    def test_external_identity_selects_unique_native_evidence_and_consumed_readback_is_idempotent(self):
        for host in self.installs:
            with self.subTest(host=host):
                packet = self.fixture(host)
                target = URL + '#user-content-' + machine()
                exact = packet['issues'][URL]['body']
                runtime = Path(packet['runtime_dir'])
                intent_before = {p.name: p.read_bytes() for p in (runtime / 'intents').glob('*.json')}
                for _ in range(2):
                    result = self.publish(packet['tokens'][0])
                    self.assertTrue(result['ready'], result['pending'])
                    self.assertEqual({KEY: target}, result['targets'])
                    state = json.loads(Path(packet['state_path']).read_text())
                    self.assertEqual(EXTERNAL, state['risks'][KEY]['canonical_url'])
                    self.assertEqual([target], [v['target'] for v in state['risks'][KEY]['occurrences']])
                    self.assertIn('Earlier preserved occurrence', state['risks'][KEY]['aliases_history'])
                    self.assertEqual([{'key': 'container:' + packet['scope_key'], 'url': URL}], result['results'])
                    self.assertEqual(exact, self.packet()['issues'][URL]['body'])
                # Native completion may add completion metadata; immutable original operation stays exact.
                for path in (runtime / 'intents').glob('*.json'):
                    self.assertEqual(json.loads(intent_before[path.name])['operation'], json.loads(path.read_text())['operation'])
                self.assertTrue(self.cli('security.threat-audit', '1')['ready'])
                self.no_writes()

    def test_same_issue_old_anchor_and_shared_sc_owners_keep_one_canonical_identity(self):
        for host in self.installs:
            with self.subTest(host=host):
                canonical = URL + '#canonical-old'
                packet = self.fixture(host, canonical, shared=True)
                for token in packet['tokens']:
                    for _ in range(2):
                        result = self.publish(token)
                        self.assertTrue(result['ready'], result['pending'])
                        self.assertEqual({KEY: canonical}, result['targets'])
                state = json.loads(Path(packet['state_path']).read_text())
                self.assertEqual([KEY], list(state['risks']))
                self.assertEqual(canonical, state['risks'][KEY]['canonical_url'])
                self.assertEqual({'01-01-PLAN.md', '01-02-PLAN.md'},
                                 {item['plan'] for item in state['risks'][KEY]['occurrences']})
                self.assertEqual({canonical}, {item['target'] for item in state['risks'][KEY]['occurrences']})
                audit = self.cli('security.threat-audit', '1')
                self.assertTrue(audit['ready'], audit['errors'])
                self.assertEqual(2, len(audit['findings']))
                self.no_writes()

    def test_selector_boundaries_refuse_ambiguity_key_heading_and_conflicting_ownership(self):
        for host in self.installs:
            with self.subTest(host=host):
                original = self.fixture(host)
                raw, prefixed = machine(), 'user-content-' + machine()
                cases = [(section(['one', 'two']), EXTERNAL), (section(), None),
                         (section(), URL + '#missing'), (section([raw, prefixed]), EXTERNAL),
                         (section(['canonical-old', prefixed, prefixed]), EXTERNAL),
                         (section() + section(), EXTERNAL), (section(key='different-key'), EXTERNAL),
                         (section(heading='Wrong heading'), EXTERNAL),
                         (section() + section([prefixed], 'Other risk', 'other-key'), EXTERNAL),
                         (section().replace(HEADING + '</h3>', '<a class="anchor" aria-hidden="true" href="#one"></a>'
                            '<a class="anchor" aria-hidden="true" href="#two"></a>' + HEADING + '</h3>'), EXTERNAL)]
                for html, canonical in cases:
                    packet = self.packet()
                    packet['html'] = html
                    packet['selection_entries'][0]['canonical_url'] = canonical
                    self.save(packet)
                    result = self.cli('select')
                    self.assertEqual({}, result['targets'], (host, html, canonical))
                    self.assertEqual(1, len(result['pending']))
                for address in (raw, prefixed):
                    packet = self.packet()
                    packet['html'] = section(['canonical-old', address])
                    packet['selection_entries'] = original['entries'][:1]
                    self.save(packet)
                    self.assertEqual({KEY: URL + '#' + address}, self.cli('select')['targets'])
                self.no_writes()

    def test_consumed_source_provider_and_reservation_drift_refuse_without_new_writes(self):
        for host in self.installs:
            with self.subTest(host=host):
                packet = self.fixture(host)
                token = packet['tokens'][0]
                args = ('security.threat-publish', '1', '--preview-token', token, '--publish')
                source = self.project / 'entry-0.json'
                original = source.read_bytes()
                source.write_bytes(original + b'\n')
                self.assertEqual('security-recovery-source-drift', self.cli(*args, success=False)['error'])
                source.write_bytes(original)
                self.git('commit', '--allow-empty', '-m', 'revision drift')
                self.assertEqual('security-recovery-source-drift', self.cli(*args, success=False)['error'])
                self.git('reset', '--soft', 'HEAD~1')
                altered = self.packet()
                altered['issues'][URL]['body'] += 'Provider drift'
                self.save(altered)
                self.assertEqual('security-readback-mismatch', self.cli(*args, success=False)['error'])
                altered['issues'][URL]['body'] = packet['issues'][URL]['body']
                self.save(altered)
                state_path = Path(packet['state_path'])
                state = json.loads(state_path.read_text())
                state['risk_intents'] = {KEY: {'scope': 'another-owner', 'token': 'different-token'}}
                state_path.write_text(json.dumps(state))
                self.assertEqual('security-risk-publication-owned', self.cli(*args, success=False)['error'])
                self.no_writes()


if __name__ == '__main__':
    unittest.main()
