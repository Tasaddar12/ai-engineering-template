"""Mandatory Git routing survives both source entrypoints and real installs."""

from pathlib import Path
import re
import unittest

import test_install


ROOT = Path(__file__).resolve().parents[1]


class EntrypointGitRouting(unittest.TestCase):
    # Reuse the real Git-source fixture, without inheriting its unrelated tests.
    setUpClass = classmethod(test_install.InstallerTests.setUpClass.__func__)
    tearDownClass = classmethod(test_install.InstallerTests.tearDownClass.__func__)
    setUp = test_install.InstallerTests.setUp
    install = test_install.InstallerTests.install

    def assert_routing(self, entrypoint, namespace):
        content = entrypoint.read_text(encoding="utf-8")
        normalized = " ".join(content.split())
        mandate = re.search(
            r"Every issue and pull request/merge request creation or edit must follow "
            r"the \[canonical Git workflow\]\(([^)]+)\), including its templates "
            r"and validation requirements, regardless of provider\.", normalized)
        if mandate:
            policy_path = mandate[1]
        else:
            mandate = re.search(
                r"Follow `([^`]+/references/git-workflow\.md)` and its complete templates "
                r"for all issue/PR creation or edits\.", normalized)
            self.assertIsNotNone(mandate, entrypoint)
            policy_path = mandate[1]
        self.assertEqual(policy_path, f"{namespace}/references/git-workflow.md")
        reference = entrypoint.parent / policy_path
        self.assertTrue(reference.is_file(), reference)
        # Follow the policy's actual links to both templates on disk.
        template_links = re.findall(r"\[[^\]]+\]\(([^)]+)\)",
                                    reference.read_text(encoding="utf-8"))
        for name in ("issue.md", "pull-request.md"):
            target = f"../templates/{name}"
            self.assertIn(target, template_links)
            resolved = (reference.parent / target).resolve()
            self.assertEqual(resolved, (entrypoint.parent / namespace / "templates" / name).resolve())
            self.assertTrue(resolved.is_file(), resolved)

    def test_source_entrypoints_require_complete_routing(self):
        self.assertFalse((ROOT / "CLAUDE.md").exists())
        self.assert_routing(ROOT / "AGENTS.md", "engineer")
        # Asset links are authored relative to the eventual project root.
        asset = ROOT / "bin/install-assets/agent-entry.txt"
        content = asset.read_text(encoding="utf-8")
        with self.subTest(entrypoint=asset):
            normalized = " ".join(content.split())
            self.assertRegex(normalized,
                             r"Follow `engineer/references/git-workflow\.md` and its complete templates "
                             r"for all issue/PR creation or edits\.")
            self.assertIn("Merge only on explicit user instruction", normalized)

    def assert_installed_routing(self, host, entrypoint):
        self.target = self.base / f"fresh {host} project"
        result = self.install("--host", host, "--no-hooks")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assert_routing(self.target / entrypoint, "." + host + "/engineer")
        for name in ("issue.md", "pull-request.md"):
            source_path = f"engineer/templates/{name}"
            expected = test_install.installer.render_asset(
                source_path, (ROOT / source_path).read_bytes(), host)
            installed = self.target / ("." + host) / "engineer/templates" / name
            self.assertEqual(installed.read_bytes(), expected, installed)

    def test_fresh_codex_install_routes_to_installed_policy_and_templates(self):
        self.assert_installed_routing("codex", "AGENTS.md")

    def test_fresh_claude_install_routes_to_installed_policy_and_templates(self):
        self.assert_installed_routing("claude", "CLAUDE.md")


if __name__ == "__main__":
    unittest.main()
