"""Contribution contracts: navigable guidance and real validator outcomes.

Fixtures exercise runtime entry points in memory or temporary repositories. The
canonical artifact table selects coverage; this file is not another registry.
"""
from pathlib import Path
import json
import re
import sys
import subprocess
import tempfile
import unittest

import yaml

from workflow_navigation import audit, links

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.ai/runtime'))
from lib import issue_format, planning_integrity
from lib.results import VerbError


class NavigationFixtures(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / 'template.md'
        (self.root / 'Guide.md').write_text(
            '# Heading\n## Heading\n## Heading-1\n## Heading\n'
            '## Café & `Code`\n## **Formatted** [title](elsewhere.md)\n'
            '~~~md\n## Hidden\n~~~\n<a id="ExplicitCase"></a>\n', encoding='utf-8')

    def check(self, content):
        self.source.write_text(content, encoding='utf-8')
        return audit(self.source, self.root)

    def test_real_template_guidance_and_literal_examples(self):
        self.assertEqual([], self.check('```markdown\n[fiction](missing.md)\n```\n'
                                       '~~~text\n[fake](also-missing.md)\n~~~\n'
                                       '`[sample](fake.md)`\n[real](Guide.md#heading)'))
        self.assertEqual(1, len(self.check('[real](missing.md)')))
        self.assertEqual(1, len(self.check('[`real`](missing.md)')))
        self.assertEqual(1, len(self.check('- Guidance\n    - [real](missing.md)')))
        self.assertEqual(1, len(self.check('```md\n[fake](fake.md)\n```\n[real](missing.md)')))
        (self.root / 'With (space).md').write_text('# Target\n', encoding='utf-8')
        self.assertEqual([], self.check('[encoded](With%20%28space%29.md#target)'))
        self.assertEqual([], self.check('[angle](<With (space).md#target>)'))
        self.assertEqual([], self.check('# Local\n[local](#local)'))

    def test_duplicates_encoding_and_anchor_case(self):
        for fragment in ('heading', 'heading-1', 'heading-1-1', 'heading-2',
                         'caf%C3%A9--code', 'formatted-title', 'ExplicitCase'):
            with self.subTest(fragment=fragment):
                self.assertEqual([], self.check('[guide](Guide.md#' + fragment + ')'))
        for target in ('Guide.md#Heading', 'Guide.md#missing', 'Guide.md#hidden',
                       'guide.md#heading', 'Guide.md#explicitcase', '../outside.md'):
            with self.subTest(target=target):
                self.assertTrue(self.check('[broken](' + target + ')'))

    def test_reference_links_and_exact_placeholder_annotation(self):
        self.assertEqual([], self.check('[guide][owner]\n\n[owner]: Guide.md#heading-1'))
        self.assertTrue(self.check('[guide][owner]\n\n[owner]: Guide.md#absent'))
        self.assertTrue(self.check('[guide][unresolved]'))
        body = ('<!-- guidance-placeholder: {phase}-SETUP.md | Replace phase when authoring. -->\n'
                '[output]({phase}-SETUP.md)\n')
        self.assertEqual([], self.check(body))
        self.assertEqual(1, len(self.check(body + '[required](missing.md)')))
        self.assertTrue(self.check('[output]({phase}-SETUP.md)'))

    def test_literal_annotations_cannot_exempt_real_links(self):
        annotation = '<!-- guidance-placeholder: missing.md | instructional example -->'
        for literal in ('```markdown\n' + annotation + '\n```',
                        '`' + annotation + '`',
                        '`literal example\n' + annotation + '\n`',
                        '``literal ` example\n' + annotation + '\n``',
                        '<!-- guidance-placeholder: missing.md |    -->',
                        '<!-- guidance-placeholder: missing.md |\t -->'):
            with self.subTest(literal=literal):
                self.assertEqual(1, len(self.check(literal + '\n[real](missing.md)')))
        genuine = ('<!-- guidance-placeholder: {phase}-SETUP.md | Replace phase. -->\n'
                   '[output]({phase}-SETUP.md)\n[real](missing.md)')
        for unmatched in ('`literal example\n', '`literal example\n``\n'):
            with self.subTest(unmatched=unmatched):
                # Unmatched/different-sized runs cannot swallow genuine comments
                # or navigation. Only the exact genuine target is exempted.
                self.assertEqual(1, len(self.check(unmatched + genuine)))


    def test_list_contained_fences_preserve_real_nested_navigation(self):
        for body in ('- Example:\n\n    ```markdown\n    [sample](missing.md)\n    ```',
                     '- Example:\n    - Nested:\n\n        ~~~markdown\n        [sample](missing.md)\n        ~~~',
                     '- ```markdown\n  [sample](missing.md)\n  ```'):
            with self.subTest(body=body):
                self.assertEqual([], self.check(body))
                self.assertEqual(1, len(self.check(body + '\n    - [real](required.md)')))
        self.assertEqual(1, len(self.check('- Guidance\n\n    [real](missing.md)')))
        self.assertEqual([], self.check('    - [literal](missing.md)'))


class BehaviorFixtures(unittest.TestCase):
    def record(self, kind, data, invalid):
        name = '01-' + ('01-' if kind in ('PLAN', 'SUMMARY') else '') + kind + '.md'
        path = '.planning/phases/01-fixture/' + name
        def body(value):
            return '---\n' + yaml.safe_dump(value) + '---\n# Authored fixture\n'
        self.assertTrue(planning_integrity.validate_record(path, body(data))['valid'])
        with self.assertRaises(VerbError) as caught:
            planning_integrity.validate_record(path, body(dict(data, **invalid)))
        self.assertEqual('planning-integrity', caught.exception.code)

    def test_context(self):
        self.record('CONTEXT', dict(phase='01-fixture', discussion='complete', issue_refs=[]),
                    dict(discussion='approved-means-authorized'))

    def test_plan(self):
        data = dict(phase='01-fixture', plan='01', type='execute', wave=1,
                    depends_on=[], files_modified=[], autonomous=True, requirements=['REQ-01'],
                    acceptance=[], documentation=[], checks=[['python', '--version']],
                    must_haves=dict(truths=[], artifacts=[], key_links=[]), issue_refs=[])
        self.record('PLAN', data, dict(checks=['python --version']))
        self.record('PLAN', data, dict(wave=0))

    def test_summary(self):
        data = dict(phase='01-fixture', plan='01', status='complete', acceptance=[],
                    documentation=[], issue_refs=[], **{'requirements-completed': ['REQ-01']})
        self.record('SUMMARY', data, dict(status='passed'))

    def test_issue_bodies(self):
        # The fixture extractor follows the actual schema location. It supports
        # the old combined source and the per-type sources supplied by item 1.
        source = issue_format.template_path()
        if source.is_dir():
            bodies = {variant: file_template(source / filename)
                      for variant, filename in issue_format.TEMPLATES.items()}
        else:
            bodies = dict(re.findall(r'^### ([^\n]+)\n\n```markdown\n(.*?)\n```',
                                     source.read_text(encoding='utf-8'), re.M | re.S))
        self.assertEqual(set(issue_format.schema()), set(bodies))
        for variant, body in bodies.items():
            with self.subTest(variant=variant):
                self.assertTrue(issue_format.validate(body, variant)['valid'])
                broken = re.sub(r'^## .+\n', '', body, count=1, flags=re.M)
                with self.assertRaises(VerbError):
                    issue_format.validate(broken, variant)

    def test_pr_body(self):
        if not hasattr(issue_format, 'validate_pr'):
            self.assertTrue(issue_format.template_path().is_file(),
                            'Per-type publication schema requires the pr.validate implementation')
            self.skipTest('pr.validate arrives with prerequisite item 1; rerun after restack')
        from publication_fixtures import pr_body
        body = pr_body()
        self.assertTrue(issue_format.validate_pr(body)['valid'])
        broken = re.sub(r'^## .+\n', '', body, count=1, flags=re.M)
        with self.assertRaises(VerbError):
            issue_format.validate_pr(broken)
        with tempfile.TemporaryDirectory() as directory:
            draft = Path(directory) / 'pr.md'
            for content, expected in ((body, 0), (broken, 1)):
                draft.write_text(content, encoding='utf-8')
                result = subprocess.run([sys.executable, str(ROOT / '.ai/runtime/phase.py'),
                                         'query', 'pr.validate', '--body-file', str(draft)],
                                        cwd=directory, capture_output=True, text=True)
                self.assertEqual(expected, result.returncode, result.stdout + result.stderr)
                self.assertIsInstance(json.loads(result.stdout), dict)

    def test_verification_report(self):
        from lib import planning_review, verification
        from lib.paths import Workspace, write_text
        from test_planning_review import PROJECT, REQUIREMENTS, ROADMAP, STATE
        with tempfile.TemporaryDirectory() as directory:
            workspace = Workspace(Path(directory))
            for name, content in (('PROJECT.md', PROJECT), ('REQUIREMENTS.md', REQUIREMENTS),
                                  ('STATE.md', STATE), ('ROADMAP.md', ROADMAP.replace('- [ ] 01-01', '- [x] 01-01'))):
                write_text(workspace.planning / name, content)
            report = workspace.phases_dir / '01-foundation/01-VERIFICATION.md'
            valid = dict(status='passed', revision='a' * 40,
                         verified_at='2026-10-22T16:00:00Z', findings={})
            def inspect(data):
                write_text(report, '---\n' + yaml.safe_dump(data) + '---\n# Authored verification\n')
                result = verification.status(workspace, '1')
                findings = planning_review.review(workspace)['findings']
                completion = [finding for finding in findings if finding['check'] == 'completion-evidence'
                              and finding['record'] == '.planning/phases/01-foundation']
                return result, completion
            result, findings = inspect(valid)
            self.assertTrue(result['exists'])
            self.assertTrue(result['known_status'])
            self.assertEqual(valid['revision'], result['revision'])
            self.assertEqual(valid['verified_at'], result['verified_at'])
            self.assertEqual([], findings)
            for invalid in (dict(status='invented'), dict(status='gaps_found'),
                            dict(revision=''), dict(verified_at='')):
                with self.subTest(invalid=invalid):
                    result, findings = inspect(dict(valid, **invalid))
                    self.assertEqual(1, len(findings))
                    if 'status' in invalid:
                        self.assertEqual(invalid['status'] in verification.STATUSES, result['known_status'])
            # Negative evidence: these consumers check presence, not SHA/date
            # syntax, attestation authenticity or the truth of report claims.
            result, findings = inspect(dict(valid, revision='not-a-revision', verified_at='not-a-date'))
            self.assertEqual('not-a-revision', result['revision'])
            self.assertEqual('not-a-date', result['verified_at'])
            self.assertEqual([], findings)

    def test_verification_receipts(self):
        # Reuse existing runtime scenarios rather than implementing a second
        # receipt schema here. Both run real subprocess checks in temp repos.
        suite = unittest.defaultTestLoader.loadTestsFromNames([
            'test_verification_receipts.ReceiptTests.test_legacy_reuse_retains_logs_and_original_revision',
            'test_verification_receipts.ReceiptTests.test_failures_are_logged_and_never_reused'])
        result = unittest.TestResult()
        suite.run(result)
        self.assertEqual(2, result.testsRun)
        self.assertTrue(result.wasSuccessful(), str(result.errors + result.failures))


def file_template(path):
    matches = re.findall(r'^## File Template\n\n```markdown\n(.*?)\n```',
                         path.read_text(encoding='utf-8'), re.M | re.S)
    if len(matches) != 1:
        raise AssertionError(str(path) + ': expected exactly one File Template')
    return matches[0]


class ArtifactCoverage(unittest.TestCase):
    def test_canonical_table_resolves_owners_and_selects_executable_coverage(self):
        source = ROOT / '.ai/runtime/TEMPLATE-CONTRACT.md'
        text = source.read_text(encoding='utf-8')
        table = text[text.index('| Artifact |'):].split('\n\n', 1)[0]
        rows = [[cell.strip() for cell in line.strip('|').split('|')]
                for line in table.splitlines()]
        self.assertEqual(5, len(rows[0]))
        fixtures, artifacts = set(), set()
        for row in rows[2:]:
            with self.subTest(artifact=row[0]):
                self.assertEqual(5, len(row))
                artifacts.add(row[0])
                for column in (row[1], row[2], row[4]):
                    self.assertTrue(list(links(column)), 'Missing owner/validator reference: ' + column)
                fixture = re.findall(r'`BehaviorFixtures\.(test_\w+)`', row[4])
                if fixture:
                    self.assertEqual(1, len(fixture))
                    self.assertTrue(callable(getattr(BehaviorFixtures, fixture[0], None)))
                    fixtures.add(fixture[0])
                else:
                    self.assertTrue(row[4].startswith('Manual:'), 'Declare manual review limits explicitly')
        for kind in planning_integrity.REQUIRED:
            self.assertTrue(any(name.endswith('-' + kind + '.md') for name in artifacts),
                            'Runtime record missing from canonical contract: ' + kind)
        # Discovering this suite executes every selected scenario. This equality
        # also rejects a stale/omitted table entry instead of silently losing it.
        self.assertEqual(set(unittest.defaultTestLoader.getTestCaseNames(BehaviorFixtures)), fixtures)
        self.assertEqual([], audit(source, ROOT))


if __name__ == '__main__':
    unittest.main()
