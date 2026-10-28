import importlib
import importlib.util
from pathlib import Path
import sys
import unittest.mock
import subprocess
import json
try:
    from .test_engineer_runtime import RuntimeCase, SOURCE
except ImportError:
    from test_engineer_runtime import RuntimeCase, SOURCE


LIB = SOURCE/"engineer/bin/lib"


def _load(name):
    """Import engineer/bin/lib/<name> under a private package name; `lib` also names .ai/runtime/lib."""
    if "engineer_bin_lib" not in sys.modules:
        spec = importlib.util.spec_from_file_location("engineer_bin_lib", LIB/"__init__.py", submodule_search_locations=[str(LIB)])
        package = importlib.util.module_from_spec(spec)
        sys.modules["engineer_bin_lib"] = package
        spec.loader.exec_module(package)
    return importlib.import_module("engineer_bin_lib."+name)


PROJECT_FIELDS = {"project": {"name": "Fixture", "description": "Fixture project", "core_value": "Observable behavior"}}


class MiscVerbs(RuntimeCase):
    def initialize_project(self):
        """Initialize the project records through the runtime's own onboarding verb."""
        return self.cli("project.init", "--fields", json.dumps(PROJECT_FIELDS))

    def phase(self, name="Behavior"):
        self.initialize_project()
        return super().phase(name)

    def test_classification_instructions_and_user_stories(self):
        self.assertEqual("rate_limit", self.cli("agent.classify-failure", "--", "HTTP 429: retry in 30 seconds")["kind"])
        self.assertEqual("AGENTS.md", self.cli("project-instruction-file"))
        self.assertEqual("CLAUDE.md", self.cli("project-instruction-file", "claude"))
        self.assertTrue(self.cli("user-story.validate", "As a user, I want to sign in, so that I can work.")["valid"])
        self.assertFalse(self.cli("user-story.validate", "A vague feature")["valid"])

    def test_state_summary_and_new_project(self):
        self.assertFalse(self.cli("init.new-project")["project_exists"])
        directory = self.phase()
        self.cli("state.patch", '{"Phase":"01"}')
        self.cli("state.update", "Last Activity", "Work complete")
        self.assertEqual("Work complete", self.cli("state.get", "last_activity"))
        summary = self.put("SUMMARY.md", '---\nphase: "01"\nplan: "01"\nstatus: complete\none_liner: "Feature delivered"\n---\n')
        self.assertEqual("Feature delivered", self.cli("summary-extract", summary)["one_liner"])
        (self.root/".planning/config.yaml").unlink()  # onboarding wrote defaults; exercise creation from an absent file
        self.assertTrue(self.cli("config-new-project", '{"auto_advance":true}')["created"])
        self.assertFalse(self.cli("config-new-project", '{}')["created"])
        self.assertTrue(self.cli("init.new-project")["project_exists"])
        self.put(".planning/PROJECT.md", "# Product\n\nProduct narrative\n")
        self.put("AGENTS.md", "User-owned instructions\n")
        self.cli("generate-claude-md", "--output", "AGENTS.md")
        content = (self.root/"AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("User-owned instructions", content)
        self.assertIn("<!-- engineer:managed:start -->", content)
        self.assertEqual("01", self.cli("init.code-review", "1", "--fix")["padded_phase"])

    def test_timeout_returns_124(self):
        result = self.cli("run-with-timeout", "--json", "--timeout", "0.05", "--", sys.executable, "-c", "import time; time.sleep(2)", status=124)
        self.assertTrue(result["timed_out"])

    def test_package_offline_is_unknown(self):
        packages, core = _load("packages"), _load("core")
        Args = core.Args
        with unittest.mock.patch.object(packages, "urlopen", side_effect=OSError("offline")):
            self.assertEqual("UNKNOWN", packages.check(Args(["requests"]))["packages"][0]["verdict"])

    def test_args_take_triple_dash_values_and_keep_option_parsing(self):
        Args = _load("core").Args
        content = "---" + chr(10) + "files_modified: []" + chr(10) + "---"
        parsed = Args(["--plan-content", content, "--raw", "positional", "--key=value", "--", "--body", "---"])
        self.assertEqual([content], parsed.all("plan-content"))
        self.assertTrue(parsed.has("raw"))
        self.assertEqual(["positional"], parsed.pos)
        self.assertEqual("value", parsed.get("key"))
        self.assertEqual(["--body", "---"], parsed.all("_body"))
        self.assertTrue(Args(["--other", "--flag"]).has("flag"))

    def test_integrity_is_strict_and_validate_is_warning_only(self):
        directory = self.phase()
        path = self.plan(directory)
        path.write_text(path.read_text().replace("wave: 1", "wave: wrong"), encoding="utf-8")
        self.assertFalse(self.cli("planning.integrity", status=1)["valid"])
        self.assertFalse(self.cli("planning.validate")["valid"])


ISSUE_DRIVER = r'''
import json, os, sys
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0, sys.argv[1])
from lib import models, delivery
import engineer
models.NAMESPACE = Path(os.environ["ENGINEER_ROOT"])/"namespace"
state_path = Path(os.environ["ENGINEER_ROOT"])/"provider.json"
def gh(argv, check=True, timeout=60):
    state = json.loads(state_path.read_text()) if state_path.exists() else {"creates": 0}
    if argv[:2] == ["issue", "create"]:
        state["creates"] += 1
        state["issue"] = {"url":"https://github.com/example/project/issues/1", "state":"OPEN",
            "title":argv[argv.index("--title")+1],
            "body":Path(argv[argv.index("--body-file")+1]).read_text(encoding="utf-8")}
        state_path.write_text(json.dumps(state))
        return SimpleNamespace(stdout=state["issue"]["url"]+"\n", stderr="", returncode=0)
    if argv[:2] == ["issue", "list"] or argv[:2] == ["pr", "list"]:
        listed = [state["issue"]] if argv[0] == "issue" and "issue" in state else []
        return SimpleNamespace(stdout=json.dumps(listed), stderr="", returncode=0)
    if argv[:2] == ["issue", "view"]:
        return SimpleNamespace(stdout=json.dumps(state["issue"]), stderr="", returncode=0)
    raise RuntimeError("Unexpected provider operation: "+repr(argv))
delivery.gh = gh
raise SystemExit(engineer.main(["query", *sys.argv[2:]]))
'''


class IssuePublicationSafety(RuntimeCase):
    def setUp(self):
        super().setUp()
        self.git("remote", "add", "origin", "https://github.com/example/project.git")
        # The installed catalog is the source template; its File Template blocks define every canonical variant.
        self.put("namespace/engineer/templates/issue.md", (SOURCE/".ai/templates/issue.md").read_text(encoding="utf-8"))
        self.todo = self.put(".planning/todos/pending/issue.md", "---\ntitle: Private finding\n---\nPrivate implementation evidence\n")
        self.public = self.put("public.md", "\n".join([
            "## User need", "Reviewers need a public statement of the observed behavior.", "",
            "## Proposed outcome", "The public record states the reviewed behavior without private notes.", "",
            "## Current limitation and evidence", "The behavior is observable in the public fixture output.", "",
            "## Impact", "Reviewers can act on the public record alone.", "",
            "## Scope", "- In: the public issue body", "- Out: private todo evidence", "",
            "## Acceptance", "- The public body matches the reviewed text", "",
            "## Related links", "https://github.com/example/project/pull/1", ""]))

    def issue_cli(self, *args, status=0):
        process = subprocess.run([sys.executable, "-I", "-c", ISSUE_DRIVER, str(SOURCE/"engineer/bin"), *map(str, args)], cwd=self.root, env=self.env, text=True, capture_output=True)
        self.assertEqual(status, process.returncode, process.stderr or process.stdout)
        return json.loads(process.stdout) if process.stdout.strip() else None

    def test_preview_binds_public_body_and_readback_preserves_private_record(self):
        options = ["issue.md", "--title", "Public reviewed title", "--variant", "Enhancement", "--body-file", self.public]
        preview = self.issue_cli("todo.issue-preview", *options)
        published = self.issue_cli("todo.issue-publish", *options, "--preview-token", preview["previewToken"])
        self.assertTrue(published["published"])
        self.assertIn("Private implementation evidence", self.todo.read_text(encoding="utf-8"))
        state = json.loads((self.root/"provider.json").read_text(encoding="utf-8"))
        self.assertNotIn("Private", state["issue"]["body"])
        self.assertEqual(1, state["creates"])
        # An identical-token replay reconciles against the linked issue and never creates a second one.
        replay = self.issue_cli("todo.issue-publish", *options, "--preview-token", preview["previewToken"])
        self.assertTrue(replay["reconciled"])
        self.assertEqual(published["url"], replay["url"])
        self.assertEqual(1, json.loads((self.root/"provider.json").read_text())["creates"])

    def test_source_or_public_body_drift_refuses_provider_call(self):
        options = ["issue.md", "--title", "Public reviewed title", "--variant", "Enhancement", "--body-file", self.public]
        preview = self.issue_cli("todo.issue-preview", *options)
        self.public.write_text(self.public.read_text()+"\nChanged evidence\n", encoding="utf-8")
        self.issue_cli("todo.issue-publish", *options, "--preview-token", preview["previewToken"], status=1)
        self.assertFalse((self.root/"provider.json").exists())
