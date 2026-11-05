"""Offline byte-exact publication and consumed-intent recovery boundaries."""
from contextlib import ExitStack, nullcontext
import copy
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

try:
    from .test_artifacts import _load
except ImportError:
    from test_artifacts import _load

security = _load('security_tracking')


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


if __name__ == '__main__':
    unittest.main()
