from pathlib import Path
import posixpath
import re
import subprocess
import sys
import unittest

import test_orchestrate as fixture

orch = fixture.orch
ROOT = fixture.RUNTIME.parents[2]


class RecordLinkTests(unittest.TestCase):
    def test_supplied_templates_keep_guidance_links_when_copied_and_archived(self):
        for kind, directory in (('PLAN', 'plans/backlog'), ('FIX', 'fixes/open')):
            source = f'.ai/templates/{kind}.md'
            active = f'.ai/{directory}/{kind}-999-example.md'
            done = f'.ai/{directory.split("/")[0]}/done/2026-Q3/{kind}-999-example.md'
            original = (ROOT / source).read_text(encoding='utf-8')
            rendered = orch.rebase_record_links(original, source, active)
            archived = orch.rebase_record_links(rendered, active, done)
            for name, text in ((source, original), (active, rendered), (done, archived)):
                for link in re.findall(r'\]\(([^)]+)\)', text):
                    path = link.split('#')[0]
                    if path and '://' not in path:
                        with self.subTest(record=name, link=link):
                            self.assertTrue((ROOT / posixpath.normpath(posixpath.join(posixpath.dirname(name), path))).exists())

    def test_rebasing_preserves_anchors_titles_code_and_relocated_peer_links(self):
        source = '.ai/plans/backlog/PLAN-001-example.md'
        target = '.ai/plans/done/2026-Q3/PLAN-001-example.md'
        peer = '.ai/plans/intake/INTAKE-001-example.md'
        peer_target = '.ai/plans/done/2026-Q3/INTAKE-001-example.md'
        text = ('[peer](../intake/INTAKE-001-example.md#proof)\n'
                '[guide](<../../../docs/My%20Guide.md> "Guide")\n'
                '[rules]: ../../RULES.md#bug-fixes "Rules"\n'
                '[local](#proof) [web](https://example.org/a)\n'
                '`[inline example](../intake/INTAKE-001-example.md)`\n'
                '```md\n[example](../intake/INTAKE-001-example.md)\n```\n')
        updated = orch.rebase_record_links(text, source, target, {peer: peer_target})
        self.assertIn('[peer](INTAKE-001-example.md#proof)', updated)
        self.assertIn('[guide](<../../../../docs/My%20Guide.md> "Guide")', updated)
        self.assertIn('[rules]: ../../../RULES.md#bug-fixes "Rules"', updated)
        self.assertIn('[local](#proof) [web](https://example.org/a)', updated)
        self.assertIn('`[inline example](../intake/INTAKE-001-example.md)`', updated)
        self.assertIn('```md\n[example](../intake/INTAKE-001-example.md)\n```', updated)

    def test_renderer_outputs_rebased_template_without_creating_a_record(self):
        target = '.ai/plans/backlog/PLAN-999-template-smoke.md'
        result = subprocess.run([sys.executable, str(fixture.RUNTIME.with_name('render_record.py')),
                                 '.ai/templates/PLAN.md', target], cwd=ROOT, text=True, capture_output=True, check=True)
        self.assertEqual(len(orch.execution_contract(result.stdout)['steps']), 2)
        self.assertIn('(../../RULES.md#intent-and-plan-approval)', result.stdout)
        self.assertFalse((ROOT / target).exists())

    def test_markdown_escapes_nested_parentheses_and_multiline_references(self):
        text = ('[guide](../../docs/Guide\\(draft\\).md)\n'
                '[nested](../../docs/Guide(draft(v2)).md)\n'
                '[guide-reference]:\n  ../../docs/Guide\\(draft\\).md "Guide"\n')
        updated = orch.rebase_record_links(text, '.ai/plans/PLAN-001.md', '.ai/plans/done/PLAN-001.md')
        self.assertIn('[guide](../../../docs/Guide%28draft%29.md)', updated)
        self.assertIn('[nested](../../../docs/Guide%28draft%28v2%29%29.md)', updated)
        self.assertIn('[guide-reference]:\n  ../../../docs/Guide%28draft%29.md "Guide"', updated)

    def test_exact_backtick_delimiters_preserve_the_entire_code_span(self):
        code = '``[a](first.md) `[b](second.md)` [c](third.md)``'
        updated = orch.rebase_record_links(code + '\n[real](fourth.md)\n', 'plans/PLAN-001.md', 'plans/done/PLAN-001.md')
        self.assertTrue(updated.startswith(code + '\n'))
        self.assertIn('[real](../fourth.md)', updated)
        escaped = '\\` [real](fourth.md) \\`'
        self.assertEqual(orch.rebase_record_links(escaped, 'plans/PLAN-001.md', 'plans/done/PLAN-001.md'),
                         '\\` [real](../fourth.md) \\`')


if __name__ == '__main__':
    unittest.main()
