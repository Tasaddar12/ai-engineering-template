from pathlib import Path
import sys
import unittest.mock
try:
    from .test_engineer_runtime import RuntimeCase, SOURCE
except ImportError:
    from test_engineer_runtime import RuntimeCase, SOURCE


class MiscVerbs(RuntimeCase):
    def test_classification_instructions_and_user_stories(self):
        self.assertEqual("rate_limit", self.cli("agent.classify-failure", "--", "HTTP 429: retry in 30 seconds")["kind"])
        self.assertEqual("AGENTS.md", self.cli("project-instruction-file"))
        self.assertEqual("CLAUDE.md", self.cli("project-instruction-file", "claude"))
        self.assertTrue(self.cli("user-story.validate", "As a user, I want to sign in, so that I can work.")["valid"])
        self.assertFalse(self.cli("user-story.validate", "A vague feature")["valid"])

    def test_mvp_state_summary_and_new_project(self):
        directory = self.phase()
        self.assertFalse(self.cli("phase.mvp-mode", "1")["active"])
        self.assertEqual("flag", self.cli("phase.mvp-mode", "1", "--mvp")["source"])
        self.cli("state.patch", '{"Phase":"01"}')
        self.cli("state.update", "Last Activity", "Work complete")
        self.assertEqual("Work complete", self.cli("state.get", "last_activity"))
        summary = self.put("SUMMARY.md", '---\nphase: "01"\nplan: "01"\nstatus: complete\none_liner: "Feature delivered"\n---\n')
        self.assertEqual("Feature delivered", self.cli("summary-extract", summary)["one_liner"])
        self.assertTrue(self.cli("config-new-project", '{"auto_advance":true}')["created"])
        self.assertFalse(self.cli("config-new-project", '{}')["created"])
        self.assertFalse(self.cli("init.new-project")["project_exists"])
        self.put(".planning/PROJECT.md", "# Product\n\nProduct narrative\n")
        self.put("AGENTS.md", "User-owned instructions\n")
        self.cli("generate-claude-md", "--output", "AGENTS.md")
        content = (self.root/"AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("User-owned instructions", content)
        self.assertIn("<!-- engineer:managed:start -->", content)
        self.assertEqual("01", self.cli("init.code-review", "1", "--fix")["padded_phase"])

    def test_timeout_returns_124(self):
        result = self.cli("run-with-timeout", "--timeout", "0.05", "--", sys.executable, "-c", "import time; time.sleep(2)", status=124)
        self.assertTrue(result["timed_out"])

    def test_package_offline_is_unknown(self):
        sys.path.insert(0, str(SOURCE/"engineer/bin"))
        self.addCleanup(sys.path.pop, 0)
        from lib import packages
        from lib.core import Args
        with unittest.mock.patch.object(packages, "urlopen", side_effect=OSError("offline")):
            self.assertEqual("UNKNOWN", packages.check(Args(["requests"]))["packages"][0]["verdict"])

    def test_integrity_is_strict_and_validate_is_warning_only(self):
        directory = self.phase()
        path = self.plan(directory)
        self.cli("frontmatter.set", path, "--field", "wave", "--value", "wrong")
        self.assertFalse(self.cli("planning.integrity", status=1)["valid"])
        self.assertFalse(self.cli("planning.validate")["valid"])
