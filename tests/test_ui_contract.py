"""Exercise UI guidance delivery through both real installer host renderings.

The template has no consumer app to render. These fixtures check packaging and
producer/consumer navigation, not the visual behavior of an invented UI.
"""
import importlib.util
from pathlib import Path, PurePosixPath
import posixpath
import re
import unittest
import tempfile
import subprocess
import sys
import json


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ui_installer", ROOT / ".ai/install.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


def local_links(name, content):
    """Follow real relative Markdown navigation, ignoring code examples."""
    text = re.sub(r"(?ms)^```[^\n]*\n.*?^```\s*$", "", content.decode("utf-8-sig"))
    text = re.sub(r"`+[^`\n]*`+", "", text)
    for target in re.findall(r"\[[^\]\n]+\]\(([^)\n]+)\)", text):
        target = target.split("#", 1)[0]
        if target and not re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*:", target):
            yield posixpath.normpath(str(PurePosixPath(name).parent / target))


class UIContractDeliveryTests(unittest.TestCase):
    def test_both_host_payloads_deliver_reachable_ui_contract_and_scaffolds(self):
        for host in ("codex", "claude"):
            with self.subTest(host=host):
                payload = installer.payload(ROOT, host)
                namespace = "." + host
                contract = namespace + "/references/ui-contract.md"
                templates = {namespace + "/templates/" + name for name in
                             ("ui-contract.md", "component-reference.md", "screenshot-manifest.md")}
                for entry in ("agents/phase-preparer.md", "agents/coder.md", "agents/verifier.md",
                              "workflows/plan-phase.md", "workflows/execute-phase.md",
                              "workflows/verify-work.md", "templates/project.md"):
                    start = namespace + "/" + entry
                    direct = set(local_links(start, payload[start]))
                    self.assertIn(contract, direct, start)
                    reached = set(local_links(contract, payload[contract]))
                    self.assertTrue(templates <= reached, start)
                for name in {contract, *templates}:
                    for target in local_links(name, payload[name]):
                        self.assertIn(target, payload, (name, target))
                    self.assertNotIn(b".ai/", payload[name], name)

    def test_installed_screenshot_validator_consumes_producer_evidence(self):
        from test_ui_screenshots import scope, REVISION
        sys.path.insert(0, str(ROOT / ".ai/runtime"))
        from lib.ui_screenshots import produce
        for host in ("codex", "claude"):
            with self.subTest(host=host), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                for name, content in installer.payload(ROOT, host).items():
                    if name.startswith("." + host + "/runtime/"):
                        target = root / name
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_bytes(content)
                plan = scope("shared")
                def fake_capture(row, target):
                    target.write_bytes(b"fixture bytes, not browser observations")
                manifest = produce(plan, REVISION, fake_capture, root / "private")
                (root / "scope.json").write_text(json.dumps(plan), encoding="utf-8")
                (root / "captures.json").write_text(json.dumps(manifest), encoding="utf-8")
                result = subprocess.run([sys.executable, str(root / ("." + host) / "runtime/phase.py"),
                                         "query", "verification.screenshots", "--scope-file", str(root / "scope.json"),
                                         "--manifest-file", str(root / "captures.json"), "--expected-revision", REVISION],
                                        cwd=root, capture_output=True, text=True)
                self.assertEqual(0, result.returncode, result.stderr)
                report = json.loads(result.stdout)
                self.assertEqual("complete", report["status"])
                self.assertEqual(5, report["covered_count"])

    def test_shared_contract_scaffold_does_not_fill_installed_project_identity(self):
        for host in ("codex", "claude"):
            with self.subTest(host=host):
                project = installer.payload(ROOT, host)[".planning/PROJECT.md"]
                asset = (ROOT / ".ai/install-assets/PROJECT.txt").read_bytes()
                self.assertEqual(installer.render_asset(".planning/PROJECT.md", asset, host), project)
                self.assertIn(b"Onboarding pending", project)
                self.assertNotIn(b"## UI Contract", project)


if __name__ == "__main__":
    unittest.main()
