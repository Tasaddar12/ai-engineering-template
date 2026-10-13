"""Offline origin/config and item URL ownership tests."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".ai/runtime"))
from lib import providers
from lib.results import VerbError


class Providers(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.workspace = SimpleNamespace(root=self.root, config=self.root / "config.yaml")
        self.settings = {"delivery": {"gitlab_hosts": {
            "gitlab.example.test": "https://gitlab.example.test:8443",
            "ssh.example.test": "https://gitlab.example.test:8443"}}}

    def resolve(self, remote, settings=None):
        self.workspace.config.write_text(yaml.safe_dump(settings or self.settings), encoding="utf-8")
        with patch.object(providers.gitops, "git", return_value=subprocess.CompletedProcess(
                [], 0, remote, "")) as git:
            target = providers.resolve(self.workspace, cwd="pinned-checkout")
            self.assertEqual(git.call_args.kwargs["cwd"], "pinned-checkout")
            return target

    def test_github_shapes_and_default(self):
        for origin in ("https://github.com/acme/project.git", "git@github.com:acme/project.git",
                       "ssh://git@github.com/acme/project", "https://github.com/acme/project/"):
            target = self.resolve(origin)
            self.assertEqual(target["provider"], "github")
            self.assertEqual(target["repository"], "github.com/acme/project")
            self.assertEqual(providers.item_number(target, "https://github.com/ACME/project/issues/2"), 2)

    def test_nested_gitlab_and_independent_ssh_web_ports(self):
        for origin in ("https://gitlab.example.test:8443/team/sub/project.git",
                       "git@gitlab.example.test:team/sub/project.git",
                       "ssh://git@gitlab.example.test:2222/team/sub/project.git",
                       "ssh://git@ssh.example.test:22/team/sub/project.git"):
            target = self.resolve(origin)
            self.assertEqual(target["provider"], "gitlab")
            self.assertEqual(target["host"], "gitlab.example.test:8443")
            self.assertEqual(target["project"], "team/sub/project")
            self.assertEqual(target["web_url"], "https://gitlab.example.test:8443/team/sub/project")
            self.assertEqual(target["remote"], origin)
            self.assertEqual(providers.item_number(target, target["web_url"] + "/-/issues/1"), 1)
            self.assertEqual(providers.item_number(target, target["web_url"] + "/-/merge_requests/9",
                                                    "merge_requests"), 9)

    def test_public_gitlab(self):
        self.assertEqual(self.resolve("git@gitlab.com:group/project.git")["host"], "gitlab.com")

    def test_unsafe_or_mismatched_origins_fail_offline(self):
        for origin in ("https://unknown.test/group/project", "https://github.com/team/sub/project",
                       "https://github.com:443/acme/project", "https://user:secret@github.com/acme/project",
                       "https://user@gitlab.example.test:8443/group/project", "http://gitlab.com/g/p",
                       "ssh://root@gitlab.com/g/p", "https://gitlab.com/g/../p",
                       "https://gitlab.com/g/%2e%2e/p", "https://gitlab.com/g/p?token=x",
                       "https://gitlab.com/g/p?", "https://gitlab.com/g/p#",
                       "https://gitlab.com/g/p#x", "https://gitlab.com/g//p", "https://gitlab.com/g/p\\x",
                       "https://gitlab.com/g/\np", "https://gitlab.com:0/g/p",
                       "https://gitlab.example.test/group/project", "https://gitlab.example.test:2222/g/p",
                       "git@gitlab..com:g/p", "ftp://gitlab.com/g/p"):
            with self.subTest(origin=origin), self.assertRaises(VerbError):
                self.resolve(origin)

    def test_explicit_provider_and_config_validation(self):
        for provider, origin in (("gitlab", "https://github.com/g/p"),
                                 ("github", "https://gitlab.com/g/p"),
                                 ("other", "https://github.com/g/p")):
            with self.assertRaises(VerbError):
                self.resolve(origin, {"delivery": {"provider": provider}})
        for hosts in ([], {"BadHost": "https://badhost"}, {"host.test": "http://host.test"},
                      {"host.test": "https://host.test/path"}, {"host.test": "https://user@host.test"},
                      {"github.com": "https://gitlab.com"}, {"host.test": "https://host.test?x=1"}):
            with self.subTest(hosts=hosts), self.assertRaises(VerbError):
                self.resolve("https://github.com/g/p", {"delivery": {"gitlab_hosts": hosts}})

    def test_item_url_pins_exact_gitlab_project_and_kind(self):
        target = self.resolve("git@gitlab.example.test:g/sub/p")
        base = target["web_url"]
        for url in (base + "/issues/1", base + "/-/issues/0", base + "/-/issues/01",
                    base + "/-/issues/1#x", base + "/-/issues/1/", base + "/-/merge_requests/1",
                    base.replace("/g/", "/G/") + "/-/issues/1",
                    base.replace(":8443", ":443") + "/-/issues/1",
                    base.replace("/p", "/other") + "/-/issues/1",
                    base.replace("https://", "https://user@") + "/-/issues/1"):
            with self.subTest(url=url), self.assertRaises(VerbError):
                providers.item_number(target, url)


if __name__ == "__main__":
    unittest.main()
