"""Synthetic provider paragraphs and ordinary consumed readback regressions."""
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

try:
    from . import test_engineer_publication_boundaries as publication
except ImportError:
    import test_engineer_publication_boundaries as publication

security = publication.security
REAL_DIGEST = security.digest
ORIGIN = {'owner': 'acme', 'repository': 'project', 'hostname': 'github.com'}
URL = 'https://github.com/acme/project/issues/7'
KEY = 'acme/project|supply-chain|unsafe-install'
HEADING = 'Supply chain control'


def paragraph(name):
    return '<p dir="auto"><a name="' + name + '"></a></p>\n'


def section(anchors=None, key=KEY, heading=HEADING):
    return (anchors if anchors is not None else paragraph('canonical-old') + '\n' + paragraph('machine-new')) + \
           '<h3 dir="auto">' + heading + '</h3><p>Canonical risk key: ' + key + '</p>'


class ParagraphOwnership(unittest.TestCase):
    def render(self, html, established=URL + '#canonical-old'):
        risk = {'id': 'T-04-SC', 'key': KEY, 'heading': HEADING, 'canonical_url': established}
        with patch.object(security.repository, 'require_url', return_value=7), \
                patch.object(security.issues, 'provider', return_value=subprocess.CompletedProcess(
                    [], 0, json.dumps({'body_html': html}), '')):
            return security.rendered_targets(URL, [risk], ORIGIN)

    def test_separate_empty_anchor_paragraphs_have_one_exact_heading_owner(self):
        parser = security._Anchors()
        parser.feed(section())
        owner = parser.items[HEADING][0]
        for address in ('canonical-old', 'machine-new'):
            with self.subTest(address=address):
                self.assertEqual(1, len(parser.declarations[address]))
                self.assertIs(owner, parser.declarations[address][0]['owner'])
        self.assertEqual({'canonical-old', 'machine-new'}, parser.owned_addresses(owner))

    def test_established_old_target_is_preserved_across_multiple_empty_anchor_paragraphs(self):
        for anchors in (paragraph('canonical-old') + paragraph('machine-new'),
                        paragraph('canonical-old') + '\n  \n' + paragraph('machine-new') + paragraph('third-alias'),
                        '<a name="canonical-old"></a>' + paragraph('machine-new'),
                        paragraph('canonical-old') + '<a name="machine-new"></a>'):
            with self.subTest(anchors=anchors):
                self.assertEqual(({KEY: URL + '#canonical-old'}, []), self.render(section(anchors)))

    def test_single_anchor_paragraph_retains_single_address_and_multiple_unestablished_aliases_are_pending(self):
        self.assertEqual(({KEY: URL + '#canonical-old'}, []), self.render(section(paragraph('canonical-old')), None))
        self.assertEqual({}, self.render(section(), None)[0])

    def test_unrelated_text_markup_addressed_paragraph_and_other_heading_break_adjacency(self):
        boundaries = ['<p></p>', '<p>Unrelated visible text</p>', '<div></div>', '<br>',
                      '<span></span>', '<h2>Another section</h2>',
                      '<p id="unrelated-address"><a name="unrelated-name"></a></p>']
        for boundary in boundaries:
            html = section(paragraph('canonical-old') + boundary + paragraph('machine-new'))
            with self.subTest(boundary=boundary):
                self.assertEqual({}, self.render(html)[0])
        invalid_paragraphs = ['<p>Unrelated<a name="canonical-old"></a></p>',
                              '<p><a name="canonical-old">Visible label</a></p>',
                              '<p><a name="canonical-old"></a><span></span></p>',
                              '<div><a name="canonical-old"></a></div>',
                              '<p id="unrelated-address"><a name="canonical-old"></a></p>']
        for anchors in invalid_paragraphs:
            with self.subTest(anchors=anchors):
                self.assertEqual({}, self.render(section(anchors + paragraph('machine-new')))[0])

    def test_duplicate_address_or_heading_and_wrong_key_never_fall_back_to_machine_alias(self):
        native = '<a class="anchor" aria-hidden="true" href="#machine-new"></a>'
        cases = [section(paragraph('canonical-old') + paragraph('canonical-old') + paragraph('machine-new')),
                 '<a name="canonical-old"></a><h3>Other risk</h3><p>Canonical risk key: other-key</p>' + section(),
                 section() + section(), section(key='acme/project|different|risk'),
                 section(heading='Wrong heading'),
                 section().replace(HEADING + '</h3>', native + HEADING + '</h3>').replace(
                     paragraph('machine-new'), paragraph('canonical-old') + paragraph('machine-new'))]
        for html in cases:
            for established in (URL + '#canonical-old', None):
                with self.subTest(html=html, established=established):
                    self.assertEqual({}, self.render(html, established)[0])
        self.assertEqual({}, self.render(section(paragraph('machine-new')))[0])


class OrdinaryConsumedParagraphs(unittest.TestCase):
    def setUp(self):
        self.f = publication.PublicationBoundaries()
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        f = self.f
        f.url = URL
        self.risk = {**publication.entry(), 'key': KEY, 'heading': HEADING, 'canonical_url': URL + '#canonical-old'}
        self.source = f.directory / 'captured-PLAN.md'
        self.source.write_bytes(b'Inert captured source\r\n')
        f.stack.enter_context(patch.object(security, 'scope', return_value=f.ctx))
        f.stack.enter_context(patch.object(security, 'root', return_value=f.directory))
        f.stack.enter_context(patch.object(security, 'safe_path', side_effect=Path))
        f.stack.enter_context(patch.object(security, '_head', return_value='a' * 40))
        f.stack.enter_context(patch.object(security, 'digest', side_effect=lambda paths: REAL_DIGEST(paths, base=f.directory)))
        f.stack.enter_context(patch.object(security, 'acquire', side_effect=lambda *args: publication.nullcontext()))
        self.operation = f.operation('Exact reviewed inert entry body', 'edit')
        review = {'scope': {'origin': f.origin, 'key': f.ctx['key']}, 'entries': [self.risk],
                  'operations': [self.operation], 'source_files': [str(self.source)],
                  'source_digest': security.digest([self.source]), 'revision': 'a' * 40,
                  'ready': True, 'pending': [], 'title': 'Canonical checklist', 'label': 'phase-security-checklist'}
        self.token = security._hash(security._preview_identity(review))
        self.preview_path = f.directory / 'previews' / (self.token + '.json')
        security.write_json(self.preview_path, {**review, 'token': self.token, 'consumed': True,
            'results': [{'key': self.operation['key'], 'url': URL}], 'complete': False})
        f.preview['source_digest'] = review['source_digest']
        self.intent_path, intent = f.intent(self.operation, 'complete')
        security.write_json(self.intent_path, intent)
        self.provider_issue = f.issue(intent['operation']['body'])
        self.exact_body = self.provider_issue['body'].encode('utf-8')
        self.state_path = f.directory / 'state.json'
        security.write_json(self.state_path, {'schema': 1, 'risks': {KEY: {'canonical_url': self.risk['canonical_url']}},
            'scopes': {}, 'risk_intents': {}})
        f.stack.enter_context(patch.object(security, '_state', side_effect=lambda ctx: (self.state_path, security.load_json(self.state_path))))
        f.stack.enter_context(patch.object(security.issues, 'issue_get', side_effect=lambda *args: self.provider_issue))
        f.stack.enter_context(patch.object(security, '_review', side_effect=AssertionError('Never rebuild a consumed operation')))
        f.stack.enter_context(patch.object(security.repository, 'require_url', return_value=7))
        self.html = section()
        self.effects = []

        def provider(argv, origin):
            if argv[0] != 'api':
                self.effects.append(argv)
                raise AssertionError('No new provider mutation is expected')
            return subprocess.CompletedProcess(argv, 0, json.dumps({'body_html': self.html}), '')

        f.stack.enter_context(patch.object(security.issues, 'provider', side_effect=provider))

    def publish(self):
        return security.command(security.Args(['04', '--preview-token', self.token, '--publish']), 'threat-publish')

    def test_exact_consumed_readback_registers_preserved_old_target_with_zero_provider_edits(self):
        for _ in range(2):
            result = self.publish()
            self.assertTrue(result['ready'], result['pending'])
            self.assertEqual({KEY: URL + '#canonical-old'}, result['targets'])
            self.assertEqual(self.exact_body, self.provider_issue['body'].encode('utf-8'))
            state = security.load_json(self.state_path)
            self.assertEqual(URL + '#canonical-old', state['risks'][KEY]['canonical_url'])
            self.assertEqual(URL + '#canonical-old', state['risks'][KEY]['occurrences'][0]['target'])
            self.assertEqual(1, len(state['risks'][KEY]['occurrences']))
        self.assertEqual([], self.effects)

    def test_source_provider_and_ownership_drift_refuse_without_new_provider_effect(self):
        with patch.object(security, '_head', return_value='b' * 40), self.assertRaises(security.Failure):
            self.publish()
        original = self.source.read_bytes()
        self.source.write_bytes(original + b'Drift\n')
        with self.assertRaises(security.Failure):
            self.publish()
        self.source.write_bytes(original)
        self.provider_issue['body'] += 'Provider drift'
        with self.assertRaises(security.Failure):
            self.publish()
        self.provider_issue['body'] = self.exact_body.decode('utf-8')
        state = security.load_json(self.state_path)
        state['risk_intents'][KEY] = {'scope': 'different-owner', 'token': 'different-token'}
        security.write_json(self.state_path, state)
        with self.assertRaises(security.Failure):
            self.publish()
        self.assertEqual([], self.effects)


if __name__ == '__main__':
    unittest.main()
