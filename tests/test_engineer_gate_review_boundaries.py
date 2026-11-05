"""Offline disconfirmation boundaries from the joined Engineer gate review."""
import json
import os
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

try:
    from .test_artifacts import _load
    from .test_engineer_runtime import RuntimeCase
    from .test_engineer_gate_contracts import register
except ImportError:
    from test_artifacts import _load
    from test_engineer_runtime import RuntimeCase
    from test_engineer_gate_contracts import register

security = _load('security_tracking')
text_format = _load('text')
URL = 'https://github.com/acme/project/issues/497'
KEY = 'acme/project|shared-results|incompatible-reuse'


def risk_section(heading='Requested risk', key=KEY, attributes='', anchor=''):
    return anchor + '<h3 ' + attributes + '>' + heading + '</h3><p>Canonical risk key: ' + key + '</p>'


class RenderedAddressOwnership(unittest.TestCase):
    def render(self, html, established=None):
        entry = {'id': 'T-01-01', 'key': KEY, 'heading': 'Requested risk', 'canonical_url': established}
        origin = {'owner': 'acme', 'repository': 'project', 'hostname': 'github.com'}
        response = subprocess.CompletedProcess([], 0, json.dumps({'body_html': html}), '')
        with patch.object(security.repository, 'require_url', return_value=497), \
                patch.object(security.issues, 'provider', return_value=response):
            return security.rendered_targets(URL, [entry], origin)

    def test_arbitrary_missing_reused_and_wrong_owner_hrefs_never_authenticate(self):
        bare = '<a href="#unproved">Requested risk</a>'
        wrong = risk_section('<a href="#other">Requested risk</a>') + risk_section('Other risk', 'other-key', 'id="other"')
        reused = risk_section(bare) + risk_section('<a href="#unproved">Other risk</a>', 'other-key')
        for html, fragment in ((risk_section(bare), 'unproved'), (wrong, 'other'), (reused, 'unproved')):
            for established in (None, URL + '#' + fragment):
                with self.subTest(html=html, established=established):
                    targets, pending = self.render(html, established)
                    self.assertEqual({}, targets)
                    self.assertEqual(1, len(pending))

    def test_actual_heading_declaration_and_verified_native_permalink_are_supported(self):
        native = '<a class="anchor" aria-hidden="true" id="user-content-native" href="#native"></a>Requested risk'
        for html, fragment in ((risk_section(attributes='id="declared"'), 'declared'),
                               (risk_section(native), 'native')):
            with self.subTest(fragment=fragment):
                targets, pending = self.render(html, URL + '#' + fragment)
                self.assertEqual({KEY: URL + '#' + fragment}, targets)
                self.assertEqual([], pending)

    def test_single_native_permalink_is_initial_choice_and_preserves_owned_aliases(self):
        native = '<a id="user-content-native" class="anchor" aria-hidden="true" href="#native"></a>Requested risk'
        html = risk_section(native)
        self.assertEqual(({KEY: URL + '#native'}, []), self.render(html))
        for address in ('native', 'user-content-native'):
            with self.subTest(address=address):
                self.assertEqual(({KEY: URL + '#' + address}, []), self.render(html, URL + '#' + address))

    def test_initial_native_choice_requires_marker_unique_choice_and_ownership(self):
        marked = '<a class="anchor" aria-hidden="true" href="#native"></a>Requested risk'
        cases = [risk_section('<a href="#native">Requested risk</a>'),
                 risk_section(marked) + risk_section('<a class="anchor" aria-hidden="true" href="#native"></a>Other risk', 'other-key'),
                 risk_section(marked + '<a class="anchor" aria-hidden="true" href="#different"></a>'),
                 risk_section(marked) + risk_section('Other risk', 'other-key', 'id="native"')]
        for html in cases:
            with self.subTest(html=html):
                self.assertEqual({}, self.render(html)[0])
        no_marker = risk_section('<a id="user-content-native" href="#native"></a>Requested risk')
        self.assertEqual({}, self.render(no_marker, URL + '#native')[0])

    def test_native_permalink_cannot_claim_address_declared_elsewhere(self):
        native = '<a class="anchor" aria-hidden="true" href="#other"></a>Requested risk'
        html = risk_section(native) + risk_section('Other risk', 'different-key', 'id="other"')
        for established in (None, URL + '#other'):
            with self.subTest(established=established):
                self.assertEqual({}, self.render(html, established)[0])

    def test_distinct_id_and_name_preserve_either_established_address(self):
        html = risk_section(anchor='<a id="user-content-kept" name="kept"></a>')
        for fragment in ('user-content-kept', 'kept'):
            with self.subTest(fragment=fragment):
                self.assertEqual(({KEY: URL + '#' + fragment}, []), self.render(html, URL + '#' + fragment))
        targets, pending = self.render(html)
        self.assertEqual({}, targets)
        self.assertEqual(1, len(pending))

    def test_duplicate_declared_address_rejects_even_established_target(self):
        html = risk_section(attributes='id="same"', anchor='<a name="same"></a>')
        self.assertEqual({}, self.render(html, URL + '#same')[0])

    def test_conflicting_address_does_not_fall_back_to_other_permalink(self):
        native = '<a class="anchor" aria-hidden="true" href="#native"></a>Requested risk'
        html = risk_section(native, anchor='<a name="conflict"></a>') + risk_section('Other risk', 'other-key', 'id="conflict"')
        self.assertEqual({}, self.render(html)[0])

    def test_nonanchor_name_attribute_is_not_a_provider_address(self):
        self.assertEqual({}, self.render(risk_section(attributes='name="not-an-address"'))[0])


class RegisterStructuralBoundaries(RuntimeCase):
    def fixture(self, content):
        directory = Path(self.phase())
        self.plan(directory, content)
        return directory

    def test_mitigation_alias_retains_owned_rows_and_missing_canonical_targets(self):
        directory = self.fixture(register('T-01-01').replace('Mitigation Plan', 'Mitigation'))
        rows = security.plan_threats(directory)
        self.assertEqual(['T-01-01'], [row['threat_id'] for row in rows])
        self.assertEqual('Verify lock', rows[0]['mitigation_plan'])
        with patch.object(security, '_state', return_value=(None, {'risks': {}})):
            packet = security.threat_audit({'directory': directory, 'id': '01', 'key': 'scope', 'origin': {}})
        self.assertFalse(packet['ready'])

    def test_malformed_attempted_registers_raise_instead_of_becoming_empty(self):
        good = register('T-01-01')
        cases = [good.replace(' | Mitigation Plan', '').replace('|---|---|---|---|---|---|', '|---|---|---|---|---|').replace(' | Verify lock', ''),
                 good.replace('Category', 'Category | Category'),
                 good.replace('Component', 'Unsupported'),
                 good.replace('Mitigation Plan', 'Unsupported'),
                 good.replace('Category | Component | Severity | Disposition | Mitigation Plan', 'A | B | C | D | E'),
                 good.replace(' | Verify lock |', ' | Verify lock | extra |'),
                 good.replace('|---|---|---|---|---|---|\n', ''),
                 good.replace('| T-01-01', 'T-01-01'),
                 good.replace('| T-01-01', 'invalid label'),
                 good.replace('</threat_model>', 'invalid label | T | dependency | high | mitigate | Verify lock |\n</threat_model>'),
                 good.replace('</threat_model>', ''),
                 register()]
        directory = self.fixture(good)
        plan = directory / '01-01-PLAN.md'
        for content in cases:
            with self.subTest(content=content):
                plan.write_text(content)
                for reader in (security.plan_threats, security.threat_id_duplicates):
                    with self.assertRaises(security.Failure):
                        reader(directory)
                with patch.object(security, '_state', return_value=(None, {'risks': {}})), self.assertRaises(security.Failure):
                    security.threat_audit({'directory': directory, 'id': '01', 'key': 'scope', 'origin': {}})

    def test_malformed_register_blocks_real_handoff_consumer(self):
        directory = self.fixture(register('T-01-01').replace('Mitigation Plan', 'Unsupported'))
        summary = directory / '01-01-SUMMARY.md'
        summary.write_text('---\nphase: "01"\nplan: "01"\nstatus: complete\nissue_refs: []\n---\nActual fixture summary\n')
        self.git('add', '.planning')
        self.git('commit', '-m', 'actual complete fixture')
        self.cli('phase.handoff', '1', status=1, raw=True)

    def test_malformed_register_cannot_skip_requirement_security_gate(self):
        self.fixture(register('T-01-01').replace('Mitigation Plan', 'Unsupported'))
        requirements = _load('requirements')
        with patch.dict(os.environ, self.env), \
                patch.object(requirements.verification, 'status', return_value={'status': 'passed'}), \
                patch.object(requirements.verification, 'current_evidence', return_value={'current': True}), \
                patch.object(requirements.phase_issues, 'handoff', return_value={'ready': True, 'findings': []}), \
                patch.object(requirements, '_coverage', return_value=self.root / 'README.md'), \
                self.assertRaises(security.Failure):
            requirements._gate('1', [])

    def test_narrative_assessment_and_fenced_registers_remain_nonowning(self):
        directory = self.fixture('References T-01-01.\n```md\n' + register('T-01-01') + '```\n' +
                                 '<threat_model>\n| Threat ID | Impact | Uncertainty |\n|---|---|---|\n'
                                 '| T-01-02 | narrative impact | conditional |\n</threat_model>\n')
        self.assertEqual([], security.plan_threats(directory))

    def test_linked_and_backticked_ids_normalize_but_keep_original_metadata(self):
        for cell in ('T-01-01', '`T-01-01`', '[T-01-01](https://github.com/acme/project/issues/1)',
                     '[`T-01-01`](https://github.com/acme/project/issues/1)'):
            with self.subTest(cell=cell):
                directory = self.fixture(register(cell))
                row = security.plan_threats(directory)[0]
                self.assertEqual('T-01-01', row['threat_id'])
                self.assertEqual(cell, row['threat_id_cell'])
                self.assertEqual('https://github.com/acme/project/issues/1' if cell.startswith('[') else None, row['threat_url'])

    def test_linked_duplicate_and_reserved_exemption_use_canonical_local_label(self):
        directory = self.fixture(register('[T-01-01](https://github.com/acme/project/issues/1)',
                                          '[T-01-SC](https://github.com/acme/project/issues/3)',
                                          '[T-02-SC](https://github.com/acme/project/issues/4)'))
        source = directory / '01-01-PLAN.md'
        other = directory / '01-02-PLAN.md'
        other.write_text(source.read_text().replace('issues/1)', 'issues/2)'))
        duplicates = security.threat_id_duplicates(directory)
        self.assertEqual({'T-01-01', 'T-02-SC'}, {item['id'] for item in duplicates})
        source.write_text(register('[T-01-SC](https://github.com/acme/project/issues/3)',
                                   '[T-01-SC](https://github.com/acme/project/issues/3)'))
        other.unlink()
        self.assertEqual([{'id': 'T-01-SC', 'plans': ['01-01', '01-01']}], security.threat_id_duplicates(directory))

    def test_ambiguous_or_malformed_local_id_cells_fail_closed(self):
        directory = self.fixture(register('T-01-01'))
        plan = directory / '01-01-PLAN.md'
        for cell in ('T-01-01 and T-01-02', '[T-01-01](one) [T-01-02](two)',
                     '[other T-01-01](one)', '`T-01-01', '[T-01-01](one', 'T-01-01 extra', ''):
            with self.subTest(cell=cell):
                plan.write_text(register(cell))
                with self.assertRaises(security.Failure):
                    security.plan_threats(directory)

    def test_linked_reserved_owners_keep_canonical_occurrence_audit(self):
        target = URL + '#shared-supply-chain'
        directory = self.fixture(register('[T-01-SC](' + target + ')'))
        (directory / '01-02-PLAN.md').write_text(register('[T-01-SC](' + target + ')'))
        occurrences = [{'scope': 'scope', 'plan': name, 'threat_id': 'T-01-SC', 'target': target}
                       for name in ('01-01-PLAN.md', '01-02-PLAN.md')]
        state = {'risks': {KEY: {'entry_id': 'SC', 'heading': 'Requested risk', 'canonical_url': target,
                                 'occurrences': occurrences}}}
        ctx = {'directory': directory, 'id': '01', 'key': 'scope',
               'origin': {'owner': 'acme', 'repository': 'project', 'hostname': 'github.com'}}
        html = risk_section(anchor='<a name="shared-supply-chain"></a>')
        response = subprocess.CompletedProcess([], 0, json.dumps({'body_html': html}), '')
        with patch.dict(os.environ, self.env), patch.object(security, '_state', return_value=(None, state)), \
                patch.object(security.issues, 'issue_get', return_value={'url': URL}), \
                patch.object(security.repository, 'require_url', return_value=497), \
                patch.object(security.issues, 'provider', return_value=response):
            result = security.threat_audit(ctx)
            self.assertTrue(result['ready'], result['errors'])
            self.assertEqual(2, len(result['findings']))
            wrong = directory / '01-02-PLAN.md'
            wrong.write_text(register('[T-01-SC](' + URL + '#different-risk)') + '\nOther reference: ' + target + '\n')
            self.assertFalse(security.threat_audit(ctx)['ready'])
            wrong.write_text(register('[T-01-SC](' + target + ')'))
            occurrences.pop()
            self.assertFalse(security.threat_audit(ctx)['ready'])


class SuppliedSecurityFieldTypes(RuntimeCase):
    def test_every_supplied_field_rejects_invalid_to_invalid_replacement_without_write(self):
        directory = Path(self.phase())
        report = directory / '01-SECURITY.md'
        values = {'audit_completed': ('old-invalid', 'new-invalid'), 'asvs_level': (True, False),
                  'covered_files': ({'old': 1}, {'new': 2}), 'threat_evidence': ({'old': 1}, {'new': 2}),
                  'issue_refs': ({'old': 1}, {'new': 2}), 'threats_open': ('old', 'new'),
                  'status': (1, 2), 'revision': ([], {}), 'audit_revision': ([], {}),
                  'auditor': ([], {}), 'fingerprint': ([], {}),
                  'no_applicable_threats': ('old', 'new'), 'coverage_rationale': ([], {})}
        for field, (old, replacement) in values.items():
            with self.subTest(field=field):
                report.write_text(text_format.join_frontmatter({'phase': '01', 'status': 'draft', field: old}, 'Actual evidence\n'))
                original = report.read_bytes()
                source = self.put('resolution.json', json.dumps({field: replacement}))
                preview = self.cli('security.resolve', '1', '--entries-file', source)
                self.cli('security.resolve', '1', '--entries-file', source, '--apply',
                         '--expect-digest', preview['snapshotDigest'], status=1, raw=True)
                self.assertEqual(original, report.read_bytes())

    def test_valid_repair_preserves_unrelated_preexisting_corruption(self):
        directory = Path(self.phase())
        report = directory / '01-SECURITY.md'
        report.write_text('---\nphase: "01"\nstatus: draft\naudit_completed: invalid\nauditor: []\n---\nActual evidence\n')
        source = self.put('resolution.json', json.dumps({'audit_completed': False}))
        preview = self.cli('security.resolve', '1', '--entries-file', source)
        result = self.cli('security.resolve', '1', '--entries-file', source, '--apply', '--expect-digest', preview['snapshotDigest'])
        self.assertTrue(result['applied'])
        metadata = self.cli('frontmatter.get', report)
        self.assertIs(False, metadata['audit_completed'])
        self.assertEqual([], metadata['auditor'])


if __name__ == '__main__':
    unittest.main()
