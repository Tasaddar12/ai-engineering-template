"""Actual prohibition projector output is authored plan data, not enforcement proof."""
try:
    from .test_artifacts import _load
    from .test_engineer_runtime import RuntimeCase
except ImportError:
    from test_artifacts import _load
    from test_engineer_runtime import RuntimeCase

probe = _load('probe_core')
text_format = _load('text')


class ProhibitionPlanSchema(RuntimeCase):
    def replace_prohibitions(self, path, value):
        metadata, body = text_format.split_frontmatter(path.read_text())
        metadata['must_haves']['prohibitions'] = value
        path.write_text(text_format.join_frontmatter(metadata, body))

    def test_actual_projection_is_accepted_by_plan_structure_gate(self):
        path = self.plan(self.phase())
        self.replace_prohibitions(path, probe.project_prohibitions([
            {'statement': 'MUST NOT invent evidence', 'status': 'resolved', 'verification': 'test'}]))
        self.assertTrue(self.cli('verify.plan-structure', path)['valid'])

    def test_actual_projection_round_trips_through_both_cli_plan_gates(self):
        path = self.plan(self.phase())
        # The two descriptor kinds exercise exactly the canonical serializer's
        # field selection; no descriptor is invented by a second serializer.
        examples = [[], [{'statement': 'MUST NOT conceal uncertainty', 'status': 'unresolved'}],
                    [{'statement': 'MUST NOT conceal uncertainty', 'status': 'resolved', 'verification': 'judgment'}],
                    [{'statement': 'MUST NOT conceal uncertainty', 'status': 'resolved', 'verification': 'test'}],
                    [{'statement': 'MUST NOT conceal uncertainty', 'status': 'dismissed', 'reason': 'Outside the authored surface'}]]
        for kind in ('node-test', 'lint-rule'):
            examples.append([{'statement': 'MUST NOT conceal uncertainty', 'status': 'resolved', 'verification': 'test',
                              'check_kind': kind, 'check_target': 'tests/check.cjs', 'check_rule': 'local/exact-rule',
                              'check_violation_fixture': 'fixtures/bad.cjs', 'check_clean_fixture': 'fixtures/clean.cjs'}])
        for items in examples:
            with self.subTest(items=items):
                projected = probe.project_prohibitions(items)
                self.replace_prohibitions(path, projected)
                self.assertTrue(self.cli('frontmatter.validate', path, '--schema', 'plan')['valid'])
                self.assertTrue(self.cli('verify.plan-structure', path)['valid'])
                self.assertEqual(projected, self.cli('frontmatter.get', path)['must_haves']['prohibitions'])

    def test_unresolved_and_descriptorless_items_remain_flagged_after_authoring(self):
        path = self.plan(self.phase())
        projected = probe.project_prohibitions([
            {'statement': 'MUST NOT invent evidence', 'status': 'unresolved'},
            {'statement': 'MUST NOT invent evidence', 'status': 'resolved', 'verification': 'test'},
            {'statement': 'MUST NOT invent evidence', 'status': 'resolved', 'verification': 'judgment'},
        ])
        self.replace_prohibitions(path, projected)
        self.assertTrue(self.cli('frontmatter.validate', path, '--schema', 'plan')['valid'])
        self.assertTrue(self.cli('verify.plan-structure', path)['valid'])
        for item in self.cli('frontmatter.get', path)['must_haves']['prohibitions']:
            disposition = probe.disposition_for_prohibition(item)
            self.assertEqual('unverified', disposition['status'])
            self.assertTrue(disposition['flagged'])

    def test_malformed_types_unknown_fields_and_vocabulary_still_reject(self):
        path = self.plan(self.phase())
        valid = {'statement': 'MUST NOT invent evidence', 'status': 'resolved', 'verification': 'test'}
        invalid = [{}, 'invalid', ['not-a-mapping'], [{'status': 'unresolved'}], [{'statement': 'text'}],
                   [{**valid, 'statement': []}], [{**valid, 'status': []}], [{**valid, 'status': 'unknown'}],
                   [{**valid, 'verification': 'explicit'}], [{**valid, 'verification': []}],
                   [{**valid, 'reason': {}}], [{**valid, 'check_kind': 'invented'}],
                   [{**valid, 'check_kind': []}], [{**valid, 'check_target': {}}],
                   [{**valid, 'check_rule': False}], [{**valid, 'check_violation_fixture': 1}],
                   [{**valid, 'check_clean_fixture': None}], [{**valid, 'check': {'nested': 'not projected'}}],
                   [{**valid, 'unsupported': 'field'}]]
        for value in invalid:
            with self.subTest(value=value):
                self.replace_prohibitions(path, value)
                self.assertFalse(self.cli('frontmatter.validate', path, '--schema', 'plan', status=1)['valid'])
                self.assertFalse(self.cli('verify.plan-structure', path, status=1)['valid'])

    def test_original_must_haves_siblings_and_unknown_rejection_remain(self):
        path = self.plan(self.phase())
        self.assertTrue(self.cli('frontmatter.validate', path, '--schema', 'plan')['valid'])
        metadata, body = text_format.split_frontmatter(path.read_text())
        metadata['must_haves']['unsupported'] = []
        path.write_text(text_format.join_frontmatter(metadata, body))
        self.assertFalse(self.cli('frontmatter.validate', path, '--schema', 'plan', status=1)['valid'])
