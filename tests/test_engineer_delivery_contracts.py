"""Offline PR-body validation against the canonical optional Stack contract."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
try:
    from .test_artifacts import _load
except ImportError:
    from test_artifacts import _load

delivery = _load('delivery')
SOURCE = Path(__file__).resolve().parents[1]
CORE = ('Goal', 'Changes', 'Verification', 'Known gaps', 'Risks or rollback')


def body(headings=CORE):
    return '\n\n'.join('## ' + heading + '\n\nActual maintained facts.' for heading in headings)


class PullRequestBodyContracts(unittest.TestCase):
    def test_independent_pr_omits_stack_with_actual_template_and_fallback(self):
        with patch.object(delivery.issue_format, 'github_directory', return_value=SOURCE / '.github'):
            delivery.validate_body(body())
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(delivery.issue_format, 'github_directory', return_value=Path(temporary) / '.github'):
                delivery.validate_body(body())

    def test_stacked_pr_can_include_actual_stack_metadata(self):
        with patch.object(delivery.issue_format, 'github_directory', return_value=SOURCE / '.github'):
            delivery.validate_body(body() + '\n\n## Stack\n\n- stackParent: https://github.com/acme/project/pull/1\n')

    def test_optional_sections_do_not_make_any_core_section_optional(self):
        for missing in CORE:
            with self.subTest(missing=missing), patch.object(delivery.issue_format, 'github_directory', return_value=SOURCE / '.github'):
                with self.assertRaises(delivery.Failure) as error:
                    delivery.validate_body(body([heading for heading in CORE if heading != missing]) +
                                           '\n\n## Requirements or Issues\n\nActual issue relation.\n\n## Stack\n\nActual parent.\n')
                self.assertEqual('invalid-pr-body', error.exception.code)
                self.assertIn(missing, error.exception.details['missing'])

    def test_empty_bodies_and_placeholders_still_fail(self):
        for candidate in ('', body() + '\n[TODO]', body() + '\n<summary placeholder>'):
            with self.subTest(candidate=candidate), self.assertRaises(delivery.Failure):
                delivery.validate_body(candidate)
