"""Offline byte-exact publication and consumed-intent recovery boundaries."""
from contextlib import ExitStack, nullcontext
import copy
import io
import json
from pathlib import Path, PureWindowsPath
import subprocess
import tempfile
import unittest
from unittest.mock import patch

try:
    from .test_artifacts import _load
except ImportError:
    from test_artifacts import _load

security = _load('security_tracking')
REAL_RENDERED_TARGETS = security.rendered_targets


def entry():
    return {'key': 'acme/project|service|foreign-owner', 'id': 'T-04-01',
            'heading': 'T-04-01 owner selection', 'plan': '04-01-PLAN.md',
            'threat_id': 'T-04-01', 'owner': 'Phase coordinator', 'planned': True,
            'scope_acceptance': 'Refuse a foreign owner before effects.',
            'assessment_uncertainty': 'Source control checked; runtime acceptance pending.',
            'lifecycle_outcome': 'mitigated: source fixtures pass; runtime pending',
            'next_action': 'Retain source evidence and pending runtime acceptance.',
            'revision_check_evidence': 'Frozen source and inert test result.',
            'aliases_occurrences': '04-01-PLAN.md/T-04-01'}


class PublicationBoundaries(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.origin = {'hostname': 'github.com', 'owner': 'acme', 'repository': 'project'}
        self.ctx = {'origin': self.origin, 'key': 'scope-key', 'stable_identity': 'original-plan',
                    'kind': 'phase', 'id': '04', 'directory': self.directory}
        self.url = 'https://github.com/acme/project/issues/526'
        self.preview_path = self.directory / 'preview.json'
        self.preview = {'source_digest': 'original-source', 'consumed': False}
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(security, '_runtime_dir', return_value=self.directory))
        self.stack.enter_context(patch.object(security, 'planning_lock', side_effect=nullcontext))

    def operation(self, body, action='edit'):
        return {'key': 'container:scope-key', 'body': body, 'title': 'Canonical checklist',
                'labels': ['phase-security-checklist'], 'action': action,
                'url': self.url if action == 'edit' else None, 'before': None}

    def intent(self, operation, state='attempting'):
        key = security._hash({'origin': self.origin, 'key': operation['key']})
        marker = '<!-- engineer-security-intent:' + key + ' -->'
        body = operation['body'] if marker in operation['body'] else operation['body'].rstrip() + '\n\n' + marker + '\n'
        intent = {'origin': self.origin, 'marker': marker, 'operation': {**operation, 'body': body},
                  'state': state, 'source_digest': self.preview['source_digest'], 'url': self.url}
        return self.directory / 'intents' / (key + '.json'), intent

    def issue(self, body):
        return {'url': self.url, 'title': 'Canonical checklist', 'body': body, 'state': 'OPEN',
                'labels': ['phase-security-checklist']}

    def exercise_serialization(self, body, action='edit'):
        operation = self.operation(body, action)
        original = self.issue('Original provider body')
        operation['before'] = security._issue_digest(original) if action == 'edit' else None
        _, expected = self.intent(operation)
        observed = []
        provider_issue = [original]

        def provider(argv, origin):
            self.assertEqual(self.origin, origin)
            actual = Path(argv[argv.index('--body-file') + 1]).read_bytes()
            observed.append(actual)
            provider_issue[0] = self.issue(actual.decode('utf-8'))
            return subprocess.CompletedProcess(argv, 0, self.url, '')

        # Emulate Windows text-mode newline conversion, not a normalized oracle.
        def windows_write_text(path, text, encoding=None, errors=None, newline=None):
            with io.open(path, 'w', encoding=encoding, errors=errors,
                         newline='\r\n' if newline is None else newline) as stream:
                return stream.write(text)

        with patch.object(Path, 'write_text', windows_write_text), \
                patch.object(security.issues, 'provider', side_effect=provider), \
                patch.object(security.issues, 'issue_get', side_effect=lambda *args: provider_issue[0]):
            result = security._mutate(operation, self.ctx, self.preview_path, self.preview)
        self.assertEqual([expected['operation']['body'].encode('utf-8')], observed)
        self.assertEqual(expected['operation']['body'], result['body'])
        path, _ = self.intent(operation)
        self.assertEqual('complete', security.load_json(path)['state'])

    def test_windows_publication_preserves_lf_crlf_mixed_and_unicode_bytes(self):
        bodies = ['One\nTwo\n', 'One\r\nTwo\r\n',
                  'Legacy\r\n\r\n### New entry\nKey: reviewed\n',
                  'Δοκιμή\r\n日本語\nemoji: 🧭\r\n']
        for index, body in enumerate(bodies):
            for action in ('create', 'edit'):
                with self.subTest(index=index, action=action):
                    # Each subcase has its own durable intent identity.
                    self.ctx['origin'] = self.origin = {**self.origin, 'repository': f'project-{index}-{action}'}
                    self.exercise_serialization(body, action)

    def test_matching_attempting_and_complete_retries_read_without_writing(self):
        operation = self.operation('Legacy\r\nNew\nΔ')
        path, intent = self.intent(operation)
        for state in ('attempting', 'complete'):
            with self.subTest(state=state):
                security.write_json(path, {**intent, 'state': state})
                with patch.object(security.issues, 'issue_get', return_value=self.issue(intent['operation']['body'])) as get, \
                        patch.object(security.issues, 'provider') as provider:
                    security._mutate(operation, self.ctx, self.preview_path, self.preview)
                get.assert_called_once_with(self.url, self.origin)
                provider.assert_not_called()
                self.assertEqual('complete', security.load_json(path)['state'])

    def test_readback_mismatch_retains_uncertainty_and_retry_never_rewrites(self):
        operation = self.operation('Reviewed\r\nbody\n')
        path, intent = self.intent(operation)
        security.write_json(path, intent)
        for wrong in ('Reviewed\r\r\nbody\n', 'Different reviewed-looking content'):
            with self.subTest(wrong=wrong):
                with patch.object(security.issues, 'issue_get', return_value=self.issue(wrong)), \
                        patch.object(security.issues, 'provider') as provider:
                    with self.assertRaises(security.Failure) as error:
                        security._mutate(operation, self.ctx, self.preview_path, self.preview)
                self.assertEqual('security-readback-mismatch', error.exception.code)
                provider.assert_not_called()
                self.assertEqual('attempting', security.load_json(path)['state'])

    def test_changed_attempting_intent_refuses_before_provider_read_or_write(self):
        operation = self.operation('Original reviewed body')
        path, intent = self.intent(operation)
        security.write_json(path, intent)
        with patch.object(security.issues, 'issue_get') as get, patch.object(security.issues, 'provider') as provider:
            with self.assertRaises(security.Failure) as error:
                security._mutate({**operation, 'body': 'Add an anchor'}, self.ctx, self.preview_path, self.preview)
        self.assertEqual('security-publication-uncertain', error.exception.code)
        get.assert_not_called()
        provider.assert_not_called()
        self.assertEqual(intent, security.load_json(path))

    def tracking_fixture(self):
        review = {'scope': {'key': self.ctx['key'], 'origin': self.origin}, 'entries': [entry()],
                  'operations': [self.operation('Original published body', 'create')],
                  'source_digest': 'original-source', 'source_files': ['original-PLAN.md'],
                  'revision': 'a' * 40, 'ready': True, 'pending': [],
                  'title': 'Canonical checklist', 'label': 'phase-security-checklist'}
        token = security._hash({k: review[k] for k in ('scope', 'entries', 'operations', 'source_digest', 'revision')})
        preview_path = self.directory / 'previews' / (token + '.json')
        saved = {**review, 'token': token, 'consumed': True,
                 'results': [{'key': 'container:scope-key', 'url': self.url}]}
        security.write_json(preview_path, saved)
        state_path = self.directory / 'state.json'
        reservation = {'scope': self.ctx['key'], 'token': token}
        security.write_json(state_path, {'schema': 1, 'risks': {}, 'scopes': {},
                                        'risk_intents': {entry()['key']: reservation}})
        self.stack.enter_context(patch.object(security, 'scope', return_value=self.ctx))
        self.stack.enter_context(patch.object(security, '_state', side_effect=lambda ctx: (state_path, security.load_json(state_path))))
        self.stack.enter_context(patch.object(security, '_head', return_value=review['revision']))
        self.stack.enter_context(patch.object(security, 'safe_path', side_effect=Path))
        self.stack.enter_context(patch.object(security, 'digest', return_value=review['source_digest']))
        self.stack.enter_context(patch.object(security, 'acquire', side_effect=lambda *args: nullcontext()))
        return review, token, state_path, reservation

    def test_frozen_consumed_resume_keeps_missing_targets_and_reservations_pending(self):
        review, token, state_path, reservation = self.tracking_fixture()
        with patch.object(security, '_review') as fresh, \
                patch.object(security, '_mutate', return_value=self.issue('Original published body')) as mutate, \
                patch.object(security, 'rendered_targets', return_value=({}, ['Actual heading address missing'])):
            result = security._tracking(security.Args(['04', '--preview-token', token, '--publish']), 'threat-publish')
        self.assertTrue(result['published'])
        self.assertFalse(result['ready'])
        self.assertEqual({}, result['targets'])
        self.assertEqual(reservation, security.load_json(state_path)['risk_intents'][entry()['key']])
        self.assertEqual(review['operations'][0], mutate.call_args.args[0])
        fresh.assert_not_called()

    def test_consumed_resume_refuses_changed_head_or_digest_before_mutation(self):
        _, token, state_path, _ = self.tracking_fixture()
        original = state_path.read_bytes()
        for name, value in (('_head', 'b' * 40), ('digest', 'changed-source')):
            with self.subTest(name=name), patch.object(security, name, return_value=value), \
                    patch.object(security, '_mutate') as mutate:
                with self.assertRaises(security.Failure) as error:
                    security._tracking(security.Args(['04', '--preview-token', token, '--publish']), 'threat-publish')
                self.assertEqual('security-recovery-source-drift', error.exception.code)
                mutate.assert_not_called()
                self.assertEqual(original, state_path.read_bytes())

    def test_fresh_preview_cannot_take_consumed_missing_target_reservations(self):
        review, old_token, state_path, reservation = self.tracking_fixture()
        fresh = copy.deepcopy(review)
        fresh['operations'][0].update(action='edit', url=self.url, body='Reviewed additive anchors')
        token = security._hash({k: fresh[k] for k in ('scope', 'entries', 'operations', 'source_digest', 'revision')})
        self.assertNotEqual(old_token, token)
        security.write_json(self.directory / 'previews' / (token + '.json'), {**fresh, 'token': token, 'consumed': False})
        with patch.object(security, '_review', return_value=fresh), patch.object(security, '_mutate') as mutate:
            with self.assertRaises(security.Failure) as error:
                security._tracking(security.Args(['04', '--preview-token', token, '--publish']), 'threat-publish')
        self.assertEqual('security-risk-publication-owned', error.exception.code)
        mutate.assert_not_called()
        self.assertEqual(reservation, security.load_json(state_path)['risk_intents'][entry()['key']])


class AuthoredAnchorBoundaries(unittest.TestCase):
    def test_new_entries_emit_safe_stable_named_addresses_without_claiming_provider_url(self):
        risk = entry()
        marker = security._hash(risk['key'])
        block = security._entry_block(risk)
        self.assertIn('<a name="engineer-risk-' + marker + '"></a>\n### ' + risk['heading'], block)
        self.assertNotIn('user-content-', block)
        self.assertIn('actual provider-rendered target is pending readback', block)
        self.assertEqual(block, security._entry_block({**risk, 'next_action': 'New reviewed action'}).replace('New reviewed action', risk['next_action']))
        self.assertIn(block, security._container_body([risk]))

    def test_merge_is_idempotent_and_preserves_legacy_named_anchor_and_canonical_url(self):
        risk = {**entry(), 'canonical_url': 'https://github.com/acme/project/issues/515#legacy-proof'}
        body = security._container_body([risk]).replace('## Risk assessment and lifecycle\n\n',
                                                       '## Risk assessment and lifecycle\n\n<a name="legacy-proof"></a>\n\n')
        merged = security._merge_container(body, [risk])
        self.assertEqual(merged, security._merge_container(merged, [risk]))
        self.assertEqual(1, merged.count('<a name="legacy-proof"></a>'))
        self.assertEqual(1, merged.count('<a name="engineer-risk-' + security._hash(risk['key']) + '"></a>'))
        self.assertIn(risk['canonical_url'], merged)

    def test_actual_provider_address_is_required_and_wrong_key_or_duplicate_fails(self):
        risk = entry()
        url = 'https://github.com/acme/project/issues/526'
        address = 'actual-provider-address-not-derived-from-source'
        section = '<a name="' + address + '"></a><h3>' + risk['heading'] + '</h3><p>Canonical risk key: ' + risk['key'] + '</p>'
        for html, ready in ((section, True), (section.replace('<a name="' + address + '"></a>', ''), False),
                            (section.replace(risk['key'], 'other/key'), False), (section + section, False)):
            with self.subTest(html=html), patch.object(security.repository, 'require_url', return_value=526), \
                    patch.object(security.issues, 'provider', return_value=subprocess.CompletedProcess([], 0, json.dumps({'body_html': html}), '')):
                targets, pending = security.rendered_targets(url, [risk],
                    {'owner': 'acme', 'repository': 'project', 'hostname': 'github.com'})
                self.assertEqual({risk['key']: url + '#' + address} if ready else {}, targets)
                self.assertEqual(not ready, bool(pending))


class AnchorReconciliation(PublicationBoundaries):
    def repair_fixture(self):
        risk = entry()
        marker = security._hash(risk['key'])
        # The legacy operation is intentionally anchorless. Never regenerate it.
        block = ('<!-- engineer-risk:' + marker + ':begin -->\n### ' + risk['heading'] +
                 '\n\n**Canonical risk key:** ' + risk['key'] + '\nLegacy Δ\r\n' +
                 '<!-- engineer-risk:' + marker + ':end -->')
        original = 'Preserve legacy narrative\r\n\r\n' + block + '\nTail\r\n'
        operation = self.operation(original, 'create')
        intent_path, intent = self.intent(operation, 'complete')
        security.write_json(intent_path, intent)
        review = {'scope': {'key': self.ctx['key'], 'origin': self.origin}, 'entries': [risk],
                  'operations': [operation], 'source_digest': 'original-source',
                  'source_files': ['original-PLAN.md'], 'revision': 'a' * 40,
                  'ready': True, 'pending': [], 'title': operation['title'],
                  'label': operation['labels'][0]}
        old_token = security._hash({k: review[k] for k in ('scope', 'entries', 'operations', 'source_digest', 'revision')})
        old_path = self.directory / 'previews' / (old_token + '.json')
        security.write_json(old_path, {**review, 'token': old_token, 'consumed': True, 'complete': False,
                                      'results': [{'key': operation['key'], 'url': self.url}]})
        state_path = self.directory / 'state.json'
        reservation = {'scope': self.ctx['key'], 'token': old_token}
        security.write_json(state_path, {'schema': 1, 'risks': {}, 'scopes': {},
                                        'risk_intents': {risk['key']: reservation}})
        self.provider_issue = self.issue(intent['operation']['body'])
        self.writes = []

        def provider(argv, origin):
            self.assertEqual(['issue', 'edit', self.url], argv[:3])
            body = Path(argv[argv.index('--body-file') + 1]).read_bytes().decode('utf-8')
            self.writes.append(body)
            self.provider_issue = self.issue(body)
            return subprocess.CompletedProcess(argv, 0, self.url, '')

        self.stack.enter_context(patch.object(security, 'scope', return_value=self.ctx))
        self.stack.enter_context(patch.object(security, '_state', side_effect=lambda ctx: (state_path, security.load_json(state_path))))
        self.stack.enter_context(patch.object(security, '_head', return_value='b' * 40))
        self.stack.enter_context(patch.object(security, 'safe_path', side_effect=Path))
        self.stack.enter_context(patch.object(security, 'digest', return_value='original-source'))
        self.stack.enter_context(patch.object(security, 'run', return_value=subprocess.CompletedProcess([], 0, '', '')))
        self.stack.enter_context(patch.object(security, 'root', return_value=Path('.')))
        self.stack.enter_context(patch.object(security.repository, 'identity', return_value={
            **self.origin, 'slug': 'github.com/acme/project'}))
        self.stack.enter_context(patch.object(security, 'acquire', side_effect=lambda *args: nullcontext()))
        self.stack.enter_context(patch.object(security, '_inputs', return_value=([risk], [Path('original-PLAN.md')], [])))
        self.stack.enter_context(patch.object(security, '_review', side_effect=AssertionError('Do not rebuild reviewed body')))
        self.stack.enter_context(patch.object(security, '_merge_container', side_effect=AssertionError('Do not rebuild reviewed body')))
        self.stack.enter_context(patch.object(security.issues, 'issue_get', side_effect=lambda *args: self.provider_issue))
        self.stack.enter_context(patch.object(security.issues, 'provider', side_effect=provider))
        self.stack.enter_context(patch.object(security, 'rendered_targets', return_value=({}, ['No actual address'])))
        return old_token, old_path, intent_path, state_path

    def repair_preview(self, old_token):
        return security._tracking(security.Args(['04', '--entries-file', 'original-entries.json',
            '--reconcile-token', old_token]), 'threat-preview')

    def repair_publish(self, old_token, token):
        return security._tracking(security.Args(['04', '--entries-file', 'original-entries.json',
            '--reconcile-token', old_token, '--preview-token', token, '--publish']), 'threat-publish')

    def test_repair_preview_is_additive_bound_to_current_source_and_preserves_receipts(self):
        old_token, old_path, intent_path, _ = self.repair_fixture()
        original_receipts = (old_path.read_bytes(), intent_path.read_bytes())
        original_body = self.provider_issue['body']
        preview = self.repair_preview(old_token)
        self.assertEqual('b' * 40, preview['revision'])
        self.assertNotEqual(old_token, preview['preview_token'])
        self.assertEqual('edit', preview['operations'][0]['action'])
        self.assertEqual(self.url, preview['operations'][0]['url'])
        self.assertNotEqual('container:scope-key', preview['operations'][0]['key'])
        anchor = '<a name="engineer-risk-' + security._hash(entry()['key']) + '"></a>\n'
        self.assertEqual(original_body, preview['operations'][0]['body'].replace(anchor, ''))
        self.assertEqual(original_receipts, (old_path.read_bytes(), intent_path.read_bytes()))
        self.assertEqual([], self.writes)

    def test_repair_publishes_once_pending_retry_is_readonly_then_actual_proof_registers(self):
        old_token, old_path, intent_path, state_path = self.repair_fixture()
        original_receipts = (old_path.read_bytes(), intent_path.read_bytes())
        token = self.repair_preview(old_token)['preview_token']
        first = self.repair_publish(old_token, token)
        self.assertTrue(first['published'])
        self.assertFalse(first['ready'])
        self.assertEqual(1, len(self.writes))
        self.assertEqual({'scope': self.ctx['key'], 'token': old_token},
                         security.load_json(state_path)['risk_intents'][entry()['key']])
        self.assertFalse(self.repair_publish(old_token, token)['ready'])
        self.assertEqual(1, len(self.writes))
        actual = self.url + '#observed-provider-proof'
        with patch.object(security, 'rendered_targets', return_value=({entry()['key']: actual}, [])):
            self.assertTrue(self.repair_publish(old_token, token)['ready'])
            self.assertTrue(self.repair_publish(old_token, token)['ready'])
        self.assertEqual(1, len(self.writes))
        self.assertEqual(original_receipts, (old_path.read_bytes(), intent_path.read_bytes()))
        state = security.load_json(state_path)
        self.assertEqual(actual, state['risks'][entry()['key']]['canonical_url'])
        self.assertNotIn(entry()['key'], state['risk_intents'])
        self.assertTrue(state['reconciliations'])
        self.assertEqual(2, len(state['reconciliations']), 'Identical pending/complete retries do not duplicate history')

    def test_repair_crash_after_external_effect_retries_readback_without_second_edit(self):
        old_token, old_path, intent_path, _ = self.repair_fixture()
        original_receipts = (old_path.read_bytes(), intent_path.read_bytes())
        token = self.repair_preview(old_token)['preview_token']
        provider = security.issues.provider.side_effect

        def uncertain(argv, origin):
            provider(argv, origin)
            raise OSError('Response lost after provider effect')

        with patch.object(security.issues, 'provider', side_effect=uncertain):
            with self.assertRaises(OSError):
                self.repair_publish(old_token, token)
        self.assertFalse(self.repair_publish(old_token, token)['ready'])
        self.assertEqual(1, len(self.writes))
        self.assertEqual(original_receipts, (old_path.read_bytes(), intent_path.read_bytes()))

    def test_repair_crash_before_external_effect_never_retries_the_edit(self):
        old_token, _, _, _ = self.repair_fixture()
        token = self.repair_preview(old_token)['preview_token']
        with patch.object(security.issues, 'provider', side_effect=OSError('Unknown before response')):
            with self.assertRaises(OSError):
                self.repair_publish(old_token, token)
        with self.assertRaises(security.Failure):
            self.repair_publish(old_token, token)
        self.assertEqual([], self.writes)

    def test_repair_rejects_original_source_intent_provider_and_ownership_drift(self):
        old_token, old_path, intent_path, state_path = self.repair_fixture()
        old_bytes, intent_bytes, state_bytes = old_path.read_bytes(), intent_path.read_bytes(), state_path.read_bytes()
        original_issue = self.provider_issue
        cases = [('intent-state', lambda: security.write_json(intent_path, {**security.load_json(intent_path), 'state': 'attempting'})),
                 ('provider-body', lambda: setattr(self, 'provider_issue', self.issue(original_issue['body'] + 'Changed'))),
                 ('provider-closed', lambda: setattr(self, 'provider_issue', {**original_issue, 'state': 'CLOSED'})),
                 ('reservation', lambda: security.write_json(state_path, {'risks': {}, 'scopes': {}, 'risk_intents': {entry()['key']: {'scope': 'other', 'token': old_token}}})),
                 ('marker', lambda: setattr(self, 'provider_issue', self.issue(original_issue['body'].replace(':begin -->', ':unknown -->'))))]
        for name, mutate in cases:
            with self.subTest(name=name):
                old_path.write_bytes(old_bytes)
                intent_path.write_bytes(intent_bytes)
                state_path.write_bytes(state_bytes)
                self.provider_issue = original_issue
                mutate()
                with self.assertRaises(security.Failure):
                    self.repair_preview(old_token)
                self.assertEqual([], self.writes)
        intent_path.write_bytes(intent_bytes)
        state_path.write_bytes(state_bytes)
        self.provider_issue = original_issue
        for dependency, value in (('digest', 'different-source'),
                                  ('run', subprocess.CompletedProcess([], 1, '', 'not ancestor'))):
            with self.subTest(dependency=dependency), patch.object(security, dependency, return_value=value):
                with self.assertRaises(security.Failure):
                    self.repair_preview(old_token)
        for field in security.FIELDS:
            with self.subTest(field=field), patch.object(security, '_inputs', return_value=(
                    [{**entry(), field: 'changed authored fact'}], [Path('original-PLAN.md')], [])):
                with self.assertRaises(security.Failure):
                    self.repair_preview(old_token)

    def test_repair_consumed_retry_rejects_changed_original_receipt_bytes(self):
        old_token, old_path, intent_path, _ = self.repair_fixture()
        token = self.repair_preview(old_token)['preview_token']
        self.repair_publish(old_token, token)
        for path in (old_path, intent_path):
            original = path.read_bytes()
            path.write_bytes(original + b'\n')
            with self.subTest(path=path), self.assertRaises(security.Failure):
                self.repair_publish(old_token, token)
            path.write_bytes(original)
        self.assertEqual(1, len(self.writes))

    def resign_original(self, old_path, intent_path, state_path, original):
        """Model an originally reviewed packet, not an after-preview corruption."""
        token = security._hash(security._preview_identity(original))
        path = old_path.parent / (token + '.json')
        security.write_json(path, {**original, 'token': token})
        _, intent = self.intent(original['operations'][0], 'complete')
        security.write_json(intent_path, intent)
        self.provider_issue = self.issue(intent['operation']['body'])
        security.write_json(state_path, {'risks': {}, 'scopes': {}, 'risk_intents': {
            e['key']: {'scope': self.ctx['key'], 'token': token} for e in original['entries']}})
        return token

    def test_original_provenance_structure_and_every_authored_value_fail_closed(self):
        _, old_path, intent_path, state_path = self.repair_fixture()
        original = security.load_json(old_path)
        variations = [lambda r: r.update(consumed=False),
                      lambda r: r['scope'].update(key='other-scope'),
                      lambda r: r['scope'].update(origin={**self.origin, 'repository': 'foreign'}),
                      lambda r: r['operations'].append(copy.deepcopy(r['operations'][0])),
                      lambda r: r['entries'][0].update(planned=False),
                      lambda r: r['results'][0].update(url='https://github.com/acme/foreign/issues/526'),
                      lambda r: r.update(results=[]), lambda r: r.update(entries=[])]
        for index, vary in enumerate(variations):
            with self.subTest(index=index):
                changed = copy.deepcopy(original)
                vary(changed)
                # Multiple operations still have a well-defined signed identity.
                token = self.resign_original(old_path, intent_path, state_path, changed)
                with self.assertRaises(security.Failure):
                    self.repair_preview(token)
        token = self.resign_original(old_path, intent_path, state_path, original)
        for supplied in ('bad-token', '0' * 64):
            with self.subTest(supplied=supplied), self.assertRaises(security.Failure):
                self.repair_preview(supplied)
        for values in ([{**entry(), 'additional_authored_fact': 'changed'}], [], [entry(), entry()]):
            with self.subTest(values=values), patch.object(security, '_inputs', return_value=(values, [Path('original-PLAN.md')], [])):
                with self.assertRaises(security.Failure):
                    self.repair_preview(token)
        with patch.object(security, '_inputs', return_value=([entry()], [Path('other-source.md')], [])), self.assertRaises(security.Failure):
            self.repair_preview(token)
        self.assertEqual([], self.writes)

    def test_malformed_block_key_heading_order_and_anchor_collisions_fail_closed(self):
        _, old_path, intent_path, state_path = self.repair_fixture()
        original = security.load_json(old_path)
        original_body = original['operations'][0]['body']
        marker = security._hash(entry()['key'])
        variations = [original_body.replace(':begin -->', ':unknown -->'),
                      original_body.replace(':end -->', ':begin -->'),
                      original_body.replace(entry()['heading'], 'Other heading'),
                      original_body.replace('**Canonical risk key:** ' + entry()['key'], '**Canonical risk key:** wrong-key'),
                      original_body + '\n<a id="engineer-risk-' + marker + '"></a>',
                      original_body + original_body,
                      original_body.replace('Legacy Δ', '<!-- engineer-risk:' + 'a' * 64 + ':begin -->\nLegacy Δ'),
                      original_body.replace('### ' + entry()['heading'], '<!-- engineer-risk:' + marker + ':end -->\n### ' + entry()['heading'])]
        for body in variations:
            with self.subTest(body=body):
                changed = copy.deepcopy(original)
                changed['operations'][0]['body'] = body
                token = self.resign_original(old_path, intent_path, state_path, changed)
                with self.assertRaises(security.Failure):
                    self.repair_preview(token)
        self.assertEqual([], self.writes)

    def test_absent_reservation_or_conflicting_canonical_target_is_never_adopted(self):
        old_token, _, _, state_path = self.repair_fixture()
        for state in ({'risks': {}, 'scopes': {}, 'risk_intents': {}},
                      {'risks': {entry()['key']: {'canonical_url': self.url + '#conflict'}}, 'scopes': {},
                       'risk_intents': {entry()['key']: {'scope': self.ctx['key'], 'token': old_token}}}):
            with self.subTest(state=state):
                security.write_json(state_path, state)
                before = state_path.read_bytes()
                with self.assertRaises(security.Failure):
                    self.repair_preview(old_token)
                self.assertEqual(before, state_path.read_bytes())

    def test_preview_drift_in_provider_labels_body_state_head_or_source_prevents_edit(self):
        old_token, _, _, _ = self.repair_fixture()
        self.provider_issue['labels'].append('retained-owner-label')
        preview = self.repair_preview(old_token)
        token = preview['preview_token']
        self.assertEqual(['phase-security-checklist', 'retained-owner-label'], preview['operations'][0]['labels'])
        original = copy.deepcopy(self.provider_issue)
        for field, value in (('body', original['body'] + 'changed'), ('title', 'Changed title'),
                             ('state', 'CLOSED'), ('labels', ['phase-security-checklist', 'new-label'])):
            with self.subTest(field=field):
                self.provider_issue = {**original, field: value}
                with self.assertRaises(security.Failure):
                    self.repair_publish(old_token, token)
                self.assertEqual([], self.writes)
        self.provider_issue = original
        for dependency, value in (('_head', 'c' * 40), ('digest', 'changed-source')):
            with self.subTest(dependency=dependency), patch.object(security, dependency, return_value=value):
                with self.assertRaises(security.Failure):
                    self.repair_publish(old_token, token)
                self.assertEqual([], self.writes)

    def test_consumed_repair_requires_explicit_original_token_and_exact_after_image(self):
        old_token, _, _, _ = self.repair_fixture()
        token = self.repair_preview(old_token)['preview_token']
        self.repair_publish(old_token, token)
        after = copy.deepcopy(self.provider_issue)
        for field, value in (('body', after['body'].replace('engineer-security-intent:', 'missing-marker:')),
                             ('title', 'Changed'), ('labels', after['labels'] + ['new-label']), ('state', 'CLOSED'),
                             ('url', self.url + '0')):
            with self.subTest(field=field):
                self.provider_issue = {**after, field: value}
                with self.assertRaises(security.Failure):
                    self.repair_publish(old_token, token)
                self.assertEqual(1, len(self.writes))
        self.provider_issue = after
        with self.assertRaises(security.Failure):
            security._tracking(security.Args(['04', '--preview-token', token, '--publish']), 'threat-publish')
        self.assertEqual(1, len(self.writes))

    def test_crashes_at_journal_and_registration_boundaries_never_repeat_effect(self):
        old_token, _, _, state_path = self.repair_fixture()
        token = self.repair_preview(old_token)['preview_token']
        original_write = security.write_json
        fired = []

        def crash_before_complete(path, value):
            if path.parent.name == 'intents' and value.get('state') == 'complete' and not fired:
                fired.append(path)
                raise OSError('Crash after exact readback, before intent completion')
            return original_write(path, value)

        with patch.object(security, 'write_json', side_effect=crash_before_complete), self.assertRaises(OSError):
            self.repair_publish(old_token, token)
        self.assertEqual(1, len(fired))
        self.assertEqual('intents', fired[0].parent.name)
        self.assertEqual('attempting', security.load_json(fired[0])['state'])
        self.assertEqual(1, len(self.writes))
        self.assertFalse(self.repair_publish(old_token, token)['ready'])
        self.assertEqual(1, len(self.writes))
        actual = {entry()['key']: self.url + '#actual-proof'}
        for after_write in (False, True):
            fired.clear()

            def crash_registration(path, value):
                ready = any(e.get('ready') for e in value.get('reconciliations', []))
                if path == state_path and ready and not fired:
                    fired.append(True)
                    if after_write:
                        original_write(path, value)
                    raise OSError('Crash at risk-index update')
                return original_write(path, value)

            with patch.object(security, 'rendered_targets', return_value=(actual, [])), \
                    patch.object(security, 'write_json', side_effect=crash_registration), self.assertRaises(OSError):
                self.repair_publish(old_token, token)
            with patch.object(security, 'rendered_targets', return_value=(actual, [])):
                self.assertTrue(self.repair_publish(old_token, token)['ready'])
            self.assertEqual(1, len(self.writes))
        self.assertEqual(2, len(security.load_json(state_path)['reconciliations']))

    def test_actual_crash_hook_handles_windows_spelling_and_excludes_other_directories(self):
        native_str = str
        native_write = security.write_json
        negatives = []

        def windows_spelling(value, *args, **kwargs):
            # Only this test module's display conversion changes. Real I/O paths
            # and all production-module conversions remain native.
            return native_str(PureWindowsPath(value)) if isinstance(value, Path) else native_str(value, *args, **kwargs)

        def observe_write(path, value):
            if path.parent.name == 'intents' and value.get('state') == 'attempting' and not negatives:
                other = self.directory / 'not-intents' / 'complete.json'
                negatives.append(other)
                self.assertIn('\\', windows_spelling(path))
                self.assertNotIn('/intents/', windows_spelling(path))
                # This call enters the real locally installed crash hook with
                # complete state at the wrong directory and must return normally.
                security.write_json(other, {'state': 'complete'})
            return native_write(path, value)

        with patch.dict(globals(), {'str': windows_spelling}), \
                patch.object(security, 'write_json', side_effect=observe_write):
            self.test_crashes_at_journal_and_registration_boundaries_never_repeat_effect()
        self.assertEqual(1, len(negatives))
        self.assertEqual({'state': 'complete'}, security.load_json(negatives[0]))

    def test_journal_exists_before_consumption_failure_and_empty_intent_never_authorizes_retry(self):
        old_token, _, _, _ = self.repair_fixture()
        token = self.repair_preview(old_token)['preview_token']
        path = self.directory / 'previews' / (token + '.json')
        original_write = security.write_json

        def crash_consumption(target, value):
            if target == path and value.get('consumed'):
                raise OSError('Crash after repair intent persisted')
            return original_write(target, value)

        with patch.object(security, 'write_json', side_effect=crash_consumption), self.assertRaises(OSError):
            self.repair_publish(old_token, token)
        with self.assertRaises(security.Failure):
            self.repair_publish(old_token, token)
        repair = next(p for p in (self.directory / 'intents').glob('*.json')
                      if ':anchor-reconcile:' in security.load_json(p)['operation']['key'])
        security.write_json(repair, {})
        with self.assertRaises(security.Failure):
            self.repair_publish(old_token, token)
        self.assertEqual([], self.writes)

    def test_foreign_owner_arriving_before_registration_prevents_identity_promotion(self):
        old_token, _, _, state_path = self.repair_fixture()
        token = self.repair_preview(old_token)['preview_token']

        def competing_owner(*args):
            state = security.load_json(state_path)
            state['risk_intents'][entry()['key']] = {'scope': 'foreign', 'token': 'foreign'}
            security.write_json(state_path, state)
            return {entry()['key']: self.url + '#actual-proof'}, []

        with patch.object(security, 'rendered_targets', side_effect=competing_owner), self.assertRaises(security.Failure):
            self.repair_publish(old_token, token)
        state = security.load_json(state_path)
        self.assertNotIn(entry()['key'], state['risks'])
        self.assertEqual({'scope': 'foreign', 'token': 'foreign'}, state['risk_intents'][entry()['key']])
        self.assertEqual(1, len(self.writes))

    def test_reconcile_option_is_rejected_outside_explicit_preview_and_publish(self):
        self.repair_fixture()
        for action in ('threat-review', 'threat-audit', 'fingerprint', 'status', 'resolve'):
            with self.subTest(action=action), self.assertRaises(security.Failure):
                security.command(security.Args(['04', '--reconcile-token', 'a' * 64]), action)

    def test_incomplete_denied_or_known_not_executed_original_never_creates_repair_intent(self):
        old_token, old_path, intent_path, state_path = self.repair_fixture()
        original_intent = security.load_json(intent_path)
        original_state = state_path.read_bytes()
        for state in ('attempting', 'denied', 'known-not-executed'):
            with self.subTest(state=state):
                security.write_json(intent_path, {**original_intent, 'state': state})
                with self.assertRaises(security.Failure):
                    self.repair_preview(old_token)
                self.assertEqual([intent_path], list((self.directory / 'intents').glob('*.json')))
                self.assertEqual(original_state, state_path.read_bytes())
                self.assertEqual([], self.writes)
        security.write_json(intent_path, original_intent)
        original = security.load_json(old_path)
        original['results'] = []
        token = self.resign_original(old_path, intent_path, state_path, original)
        before = state_path.read_bytes()
        with self.assertRaises(security.Failure):
            self.repair_preview(token)
        self.assertEqual(before, state_path.read_bytes())
        self.assertEqual([intent_path], list((self.directory / 'intents').glob('*.json')))
        self.assertEqual([], self.writes)

    def test_changed_captured_security_bytes_refuse_even_when_other_source_is_identical(self):
        _, old_path, intent_path, state_path = self.repair_fixture()
        original = security.load_json(old_path)
        original['source_files'].append('04-SECURITY.md')
        token = self.resign_original(old_path, intent_path, state_path, original)
        captured = Path('04-SECURITY.md')

        def changed_security(paths):
            return 'changed-security-bytes' if captured in paths else 'original-source'

        before = state_path.read_bytes()
        with patch.object(security, 'digest', side_effect=changed_security), self.assertRaises(security.Failure) as error:
            self.repair_preview(token)
        self.assertEqual('security-reconciliation-source-drift', error.exception.code)
        self.assertEqual(before, state_path.read_bytes())
        self.assertEqual([], self.writes)

    def test_source_enumeration_order_does_not_change_byte_bound_identity(self):
        _, old_path, intent_path, state_path = self.repair_fixture()
        original = security.load_json(old_path)
        original['source_files'].append('04-SECURITY.md')
        token = self.resign_original(old_path, intent_path, state_path, original)
        with patch.object(security, '_inputs', return_value=(
                [entry()], [Path('04-SECURITY.md'), Path('original-PLAN.md')], [])):
            preview = self.repair_preview(token)
        self.assertEqual(original['source_files'], preview['source_files'])
        self.assertEqual([], self.writes)

    def test_reconcile_option_cannot_resume_an_ordinary_consumed_intent(self):
        old_token, _, _, state_path = self.repair_fixture()
        before = state_path.read_bytes()
        with patch.object(security, '_head', return_value='a' * 40), \
                patch.object(security, '_mutate', return_value=self.provider_issue) as ordinary:
            with self.assertRaises(security.Failure):
                self.repair_publish(old_token, old_token)
        ordinary.assert_not_called()
        self.assertEqual(before, state_path.read_bytes())

    def test_partial_actual_html_proof_retains_unresolved_owner_and_history_is_idempotent(self):
        _, old_path, intent_path, state_path = self.repair_fixture()
        original = security.load_json(old_path)
        other = {**entry(), 'key': 'acme/project|other-service|unsafe-owner', 'id': 'T-04-02',
                 'threat_id': 'T-04-02', 'heading': 'T-04-02 second owner'}
        original['entries'].append(other)
        marker = security._hash(other['key'])
        original['operations'][0]['body'] += ('\n<!-- engineer-risk:' + marker + ':begin -->\r\n### ' + other['heading'] +
            '\r\n\r\n**Canonical risk key:** ' + other['key'] + '\r\n<!-- engineer-risk:' + marker + ':end -->\r\n')
        old_token = self.resign_original(old_path, intent_path, state_path, original)
        entries = original['entries']
        provider = security.issues.provider.side_effect
        complete = [False]

        def actual_html(argv, origin):
            if argv[0] != 'api':
                return provider(argv, origin)
            html = ''
            for index, risk in enumerate(entries):
                authored = 'engineer-risk-' + security._hash(risk['key'])
                if index == 0 or complete[0]:
                    self.assertIn('<a name="' + authored + '"></a>', self.provider_issue['body'])
                    html += '<a name="provider-observed-' + authored + '"></a>'
                html += '<h3>' + risk['heading'] + '</h3><p>Canonical risk key: ' + risk['key'] + '</p>'
            return subprocess.CompletedProcess(argv, 0, json.dumps({'body_html': html}), '')

        with patch.object(security, '_inputs', return_value=(entries, [Path('original-PLAN.md')], [])), \
                patch.object(security.issues, 'provider', side_effect=actual_html), \
                patch.object(security, 'rendered_targets', side_effect=REAL_RENDERED_TARGETS):
            token = self.repair_preview(old_token)['preview_token']
            first = self.repair_publish(old_token, token)
            self.assertFalse(first['ready'])
            self.assertEqual(1, len(first['targets']))
            state = security.load_json(state_path)
            self.assertNotIn(entries[0]['key'], state['risk_intents'])
            self.assertEqual({'scope': self.ctx['key'], 'token': old_token}, state['risk_intents'][other['key']])
            self.assertFalse(self.repair_publish(old_token, token)['ready'])
            complete[0] = True
            final = self.repair_publish(old_token, token)
            self.assertTrue(final['ready'])
            self.assertEqual(2, len(final['targets']))
            self.assertTrue(self.repair_publish(old_token, token)['ready'])
            self.assertEqual(1, len(self.writes))
            self.assertEqual({}, security.load_json(state_path)['risk_intents'])
            self.assertEqual(2, len(security.load_json(state_path)['reconciliations']))
        with patch.object(security, '_inputs', return_value=(list(reversed(entries)), [Path('original-PLAN.md')], [])), \
                self.assertRaises(security.Failure):
            self.repair_preview(old_token)




if __name__ == '__main__':
    unittest.main()
