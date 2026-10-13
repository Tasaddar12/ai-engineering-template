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
        delivery = content.split("## Delivery\n", 1)[1].split("\n## ", 1)[0]
        normalized = " ".join(delivery.split())
        mandate = re.search(
            r"Every issue and pull request/merge request creation or edit must follow "
            r"the \[canonical Git workflow\]\(([^)]+)\), including its templates "
            r"and validation requirements, regardless of provider\.", normalized)
        self.assertIsNotNone(mandate, entrypoint)
        self.assertEqual(mandate[1], f"{namespace}/references/git-workflow.md")
        reference = entrypoint.parent / mandate[1]
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
        self.assert_routing(ROOT / "AGENTS.md", ".ai")
        # Asset links are authored relative to the eventual project root.
        asset = ROOT / ".ai/install-assets/agent-entry.txt"
        content = asset.read_text(encoding="utf-8")
        with self.subTest(entrypoint=asset):
            source = ROOT / "AGENTS.md"
            source_delivery = " ".join(source.read_text(encoding="utf-8").split("## Delivery\n", 1)[1].split())
            asset_delivery = " ".join(content.split("## Delivery\n", 1)[1].split())
            mandate = re.search(r"Every issue .*?regardless of provider\.", source_delivery)[0]
            self.assertIn(mandate, asset_delivery)

    def assert_installed_routing(self, host, entrypoint):
        self.target = self.base / f"fresh {host} project"
        result = self.install("--host", host, "--no-hooks")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assert_routing(self.target / entrypoint, "." + host)
        for name in ("issue.md", "pull-request.md"):
            source_path = f".ai/templates/{name}"
            expected = test_install.installer.render_asset(
                source_path, (ROOT / source_path).read_bytes(), host)
            installed = self.target / ("." + host) / "templates" / name
            self.assertEqual(installed.read_bytes(), expected, installed)

    def test_fresh_codex_install_routes_to_installed_policy_and_templates(self):
        self.assert_installed_routing("codex", "AGENTS.md")

    def test_fresh_claude_install_routes_to_installed_policy_and_templates(self):
        self.assert_installed_routing("claude", "CLAUDE.md")


if __name__ == "__main__":
    unittest.main()
