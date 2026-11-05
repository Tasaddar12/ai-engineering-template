"""Synthetic provider paragraph ownership and refusal regressions."""
import json
import subprocess
import unittest
from unittest.mock import patch

try:
    from .test_artifacts import _load
except ImportError:
    from test_artifacts import _load

security = _load("security_tracking")
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
