"""Offline, pinned both-host provider-boundary checks for reviewed UTF-8 bodies.

The child runs the installed engineer.py, infers its namespace, and intercepts
only external provider/Git write boundaries. The Windows fidelity mode scopes
TextIO newline translation to provider temporary body files; it is not Windows
execution. Inputs supplied with --body exercise the reviewed string contract;
--body-file separately retains core.read's existing universal-newline contract.
"""
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1]
PREFIXES = ("agents", "commands", "engineer", "hooks", "scripts", "skills", "bin")
TITLE = "fix(acme): preserve reviewed body Δ"
ORIGIN = {"hostname": "github.com", "owner": "acme", "repository": "project",
          "slug": "github.com/acme/project"}
URL = "https://github.com/acme/project/issues/17"
PR_HEADINGS = ("Goal", "Changes", "Verification", "Known gaps", "Risks or rollback")
ISSUE_HEADINGS = ("User need", "Proposed outcome", "Current limitation and evidence",
                  "Impact", "Scope", "Acceptance", "Related links")

# Standalone child shim: no source-module imports or forced NAMESPACE/HOST.
CHILD = r'''
import base64, io, json, os, runpy, subprocess, sys
from pathlib import Path
runtime, state_file, mode = sys.argv[1:4]
sys.argv = [runtime, *sys.argv[4:]]
state_path = Path(state_file)
real_run, real_write_text = subprocess.run, Path.write_text

def load():
    return json.loads(state_path.read_bytes())

def save(state):
    state_path.write_bytes(json.dumps(state, ensure_ascii=False).encode('utf-8'))

def translated(path, text, encoding=None, errors=None, newline=None):
    if path.name == 'body.md' and path.parent.name.startswith(('engineer-pr-', 'engineer-issue-')):
        # TextIOWrapper's actual translation, including CRCRLF for input CRLF.
        with io.open(path, 'w', encoding=encoding, errors=errors,
                     newline='\r\n' if newline is None else newline) as stream:
            return stream.write(text)
    return real_write_text(path, text, encoding=encoding, errors=errors, newline=newline)

if mode == 'windows-fidelity':
    Path.write_text = translated

def boundary(argv, *args, **kwargs):
    argv = list(map(str, argv))
    state = load()
    if argv[0] == 'git' and argv[1] in ('push', 'fetch', 'pull', 'ls-remote'):
        assert argv == ['git', 'push', '--set-upstream', 'origin', 'reviewed'], argv
        state['pushes'] += 1
        save(state)
        return subprocess.CompletedProcess(argv, 0, '', '')
    if argv[0] != 'gh':
        return real_run(argv, *args, **kwargs)
    assert argv[-2:] == ['--repo', 'github.com/acme/project'], argv
    assert kwargs['env']['GH_PROMPT_DISABLED'] == '1'
    family, action = argv[1:3]
    key = 'pr' if family == 'pr' else 'issue'
    if action in ('create', 'edit'):
        assert '--body-file' in argv
        raw = Path(argv[argv.index('--body-file') + 1]).read_bytes()
        state['effects'].append({'family': family, 'action': action,
                                 'raw': base64.b64encode(raw).decode(), 'argv': argv})
        packet = dict(state.get(key) or {})
        packet.update(number=17, url='https://github.com/acme/project/' +
                      ('pull/17' if key == 'pr' else 'issues/17'), state='OPEN',
                      title=argv[argv.index('--title') + 1], body=raw.decode('utf-8'))
        if key == 'pr':
            packet.update(baseRefName=argv[argv.index('--base') + 1], headRefName='reviewed',
                          isDraft=True, statusCheckRollup=[])
        else:
            flag = '--label' if action == 'create' else '--add-label'
            packet['labels'] = [{'name': argv[i+1]} for i, value in enumerate(argv) if value == flag]
        fault = state.get('fault')
        if fault == 'body':
            packet['body'] += '\nProvider changed content.'
        elif fault == 'newlines':
            packet['body'] = packet['body'].replace('\n', '\r\n')
        elif fault == 'title':
            packet['title'] = 'Unexpected title'
        elif fault == 'base':
            packet['baseRefName'] = 'unexpected-base'
        elif fault == 'labels':
            packet['labels'] = []
        state[key] = packet
        save(state)
        if fault == 'exception-after-write':
            raise subprocess.TimeoutExpired(argv, kwargs.get('timeout'))
        return subprocess.CompletedProcess(argv, 0, packet['url'] + '\n', '')
    if action == 'view':
        if state['effects'] and state.get('fault') == 'readback-error':
            return subprocess.CompletedProcess(argv, 1, '', 'Provider readback unavailable')
        if state.get(key) is None:
            return subprocess.CompletedProcess(argv, 1, '', 'no pull requests found')
        return subprocess.CompletedProcess(argv, 0, json.dumps(state[key]), '')
    if action == 'list':
        items = [state[key]] if state.get(key) else []
        return subprocess.CompletedProcess(argv, 0, json.dumps(items), '')
    raise AssertionError(('unexpected provider operation', argv))

subprocess.run = boundary
runpy.run_path(runtime, run_name='__main__')
'''


def git(directory, *args):
    return subprocess.run(["git", "-C", str(directory), *args], check=True,
                          capture_output=True, text=True, encoding="utf-8", timeout=30).stdout.strip()


def body(headings, style):
    lines = []
    for heading in headings:
        lines.extend(("## " + heading, "", "Reviewed café 日本語 🧭.", ""))
    endings = {"lf": ("\n",), "crlf": ("\r\n",),
               "mixed": ("\r\n", "\n", "\r\n", "\n"), "unicode": ("\n", "\r\n")}[style]
    return "".join(line + endings[i % len(endings)] for i, line in enumerate(lines))


class InstalledProviderBodyBytes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="engineer-body-bytes-")
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.directory = Path(cls.temporary.name).resolve()
        # Capture current canonical source in a real Git snapshot, following the
        # installer suite's fixture contract. Never patch the installed copies.
        cls.source = cls.directory / "source"
        cls.source.mkdir()
        for name in PREFIXES:
            shutil.copytree(SOURCE / name, cls.source / name,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        git(cls.source, "init", "-b", "main")
        git(cls.source, "config", "user.name", "Body Bytes Fixture")
        git(cls.source, "config", "user.email", "fixture@example.invalid")
        git(cls.source, "config", "core.autocrlf", "false")
        git(cls.source, "add", *PREFIXES)
        git(cls.source, "commit", "-m", "Capture canonical provider body source")
        cls.pin = git(cls.source, "rev-parse", "HEAD")
        cls.targets = {}
        for host in ("claude", "codex"):
            target = cls.directory / host
            target.mkdir()
            git(target, "init", "-b", "main")
            git(target, "config", "user.name", "Body Bytes Fixture")
            git(target, "config", "user.email", "fixture@example.invalid")
            git(target, "config", "core.autocrlf", "false")
            (target / ".gitignore").write_bytes(b".claude/\n.codex/\n.agents/\n.planning/\nprovider-state.json\nreviewed-body.md\n")
            git(target, "add", ".gitignore")
            git(target, "commit", "-m", "Initialize inert acme fixture")
            git(target, "checkout", "-b", "reviewed")
            git(target, "remote", "add", "origin", "https://github.com/acme/project.git")
            installed = subprocess.run([sys.executable, "-I", str(SOURCE / "bin/install.py"),
                                       "--source", str(cls.source), "--ref", cls.pin,
                                       "--target", str(target), "--host", host, "--local", "--no-hooks"],
                                      capture_output=True, text=True, encoding="utf-8", timeout=120)
            if installed.returncode:
                raise AssertionError(installed.stderr)
            manifest = json.loads((target / ("." + host) / "engineer-install/manifest.json").read_bytes())
            if manifest["revision"] != cls.pin or manifest["host"] != host:
                raise AssertionError(manifest)
            git(target, "add", "CLAUDE.md" if host == "claude" else "AGENTS.md")
            git(target, "commit", "-m", "Capture installed host entry")
            cls.targets[host] = target

    def state(self, target, **changes):
        state = {"pr": None, "issue": None, "effects": [], "pushes": 0, **changes}
        (target / "provider-state.json").write_bytes(json.dumps(state).encode())

    def observed(self, target):
        return json.loads((target / "provider-state.json").read_bytes())

    def cli(self, target, mode, *args, status=0):
        host = target.name
        runtime = target / ("." + host) / "engineer/bin/engineer.py"
        environment = {key: value for key, value in os.environ.items()
                       if key not in ("ENGINEER_HOST", "ENGINEER_ROOT", "CLAUDE_CODE",
                                      "CLAUDE_CONFIG_DIR", "CODEX_HOME")}
        result = subprocess.run([sys.executable, "-I", "-c", CHILD, str(runtime),
                                 str(target / "provider-state.json"), mode, "query", *args],
                                cwd=target, env=environment, capture_output=True,
                                text=True, encoding="utf-8", timeout=60)
        self.assertEqual(status, result.returncode, result.stdout + result.stderr)
        return json.loads(result.stdout if status == 0 else result.stderr)

    def todo(self, target, name, linked=False):
        source = target / ".planning/todos/pending" / name
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes(("---\ntitle: Reviewed acme follow-up\n" +
                            ("issue_url: " + URL + "\n" if linked else "") +
                            "---\nPrivate local fixture.\n").encode())
        return source

    def issue_args(self, name, reviewed):
        return [name, "--title", TITLE, "--body", reviewed, "--variant", "Enhancement",
                "--labels", "triaged", "bug"]

    def preview(self, target, mode, args):
        return self.cli(target, mode, "todo.issue-preview", *args)["previewToken"]

    def expected_publication(self, name, reviewed):
        identity = {"origin": ORIGIN, "source": "todos/pending/" + name,
                    "family": "todo", "finding": None}
        key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
        return reviewed.rstrip() + "\n\n<!-- engineer-issue-intent:" + key + " -->"

    def assert_effect(self, target, expected, family, action):
        state = self.observed(target)
        self.assertEqual(1, len(state["effects"]))
        effect = state["effects"][0]
        self.assertEqual((family, action), (effect["family"], effect["action"]))
        self.assertEqual(expected.encode("utf-8"), base64.b64decode(effect["raw"]))
        self.assertEqual(expected, state[family]["body"])
        self.assertEqual(TITLE, state[family]["title"])
        self.assertEqual(1 if family == "pr" else 0, state["pushes"])

    def test_installed_identity_infers_both_hosts_and_uses_captured_source(self):
        for host, target in self.targets.items():
            self.state(target)
            identity = self.cli(target, "native", "runtime-identity")
            self.assertEqual(host, identity["host"])
            self.assertEqual(str(target / ("." + host)), identity["namespace"])
            for name in ("delivery.py", "issues.py"):
                self.assertEqual((SOURCE / "engineer/bin/lib" / name).read_bytes(),
                                 (target / ("." + host) / "engineer/bin/lib" / name).read_bytes())

    def test_pr_create_and_edit_preserve_reviewed_bytes(self):
        for host, target in self.targets.items():
            for mode in ("native", "windows-fidelity"):
                for style in ("lf", "crlf", "mixed", "unicode"):
                    reviewed = body(PR_HEADINGS, style)
                    for action in ("create", "edit"):
                        with self.subTest(host=host, mode=mode, style=style, action=action):
                            existing = {"number": 17, "url": "https://github.com/acme/project/pull/17",
                                        "headRefName": "reviewed", "baseRefName": "main"} if action == "edit" else None
                            self.state(target, pr=existing)
                            result = self.cli(target, mode, "pr.open", "reviewed", "--title", TITLE,
                                              "--body", reviewed, "--base", "main")
                            self.assertEqual(action == "create", result["created"])
                            self.assertEqual(reviewed, result["body"])
                            self.assertEqual("main", result["baseRefName"])
                            self.assert_effect(target, reviewed, "pr", action)

    def test_issue_publish_and_update_preserve_reviewed_bytes(self):
        for host, target in self.targets.items():
            for mode in ("native", "windows-fidelity"):
                for style in ("lf", "crlf", "mixed", "unicode"):
                    reviewed = body(ISSUE_HEADINGS, style)
                    for action in ("publish", "update"):
                        with self.subTest(host=host, mode=mode, style=style, action=action):
                            name = f"{host}-{mode}-{style}-{action}.md"
                            self.todo(target, name, linked=action == "update")
                            self.state(target)
                            args = self.issue_args(name, reviewed)
                            token = self.preview(target, mode, args)
                            result = self.cli(target, mode, "todo.issue-" + action, *args,
                                              "--preview-token", token)
                            expected = self.expected_publication(name, reviewed) if action == "publish" else reviewed
                            self.assertEqual(expected, result["issue"]["body"])
                            self.assertEqual([{"name": "bug"}, {"name": "triaged"}], result["issue"]["labels"])
                            self.assert_effect(target, expected, "issue", "create" if action == "publish" else "edit")
                            saved = json.loads((target / ".planning/issue-previews" / (token + ".json")).read_bytes())
                            self.assertIs(True, saved["used"])
                            if action == "publish":
                                self.cli(target, mode, "todo.issue-publish", *args, "--preview-token", token)
                                self.assertEqual(1, len(self.observed(target)["effects"]))

    def test_body_file_retains_existing_reviewed_text_read_contract(self):
        for target in self.targets.values():
            reviewed = body(PR_HEADINGS, "crlf")
            path = target / "reviewed-body.md"
            path.write_bytes(reviewed.encode())
            with path.open(encoding="utf-8-sig") as stream:
                accepted = stream.read()
            self.state(target)
            self.cli(target, "windows-fidelity", "pr.open", "reviewed", "--title", TITLE,
                     "--body-file", str(path), "--base", "main")
            self.assert_effect(target, accepted, "pr", "create")

    def test_pr_readback_and_exception_refusals_never_repeat_provider_write(self):
        for target in self.targets.values():
            for fault, error in (("body", "pr-readback-mismatch"), ("newlines", "pr-readback-mismatch"),
                                 ("title", "pr-readback-mismatch"), ("base", "pr-readback-mismatch"),
                                 ("readback-error", "provider-query-failed"),
                                 ("exception-after-write", "command-timeout")):
                with self.subTest(host=target.name, fault=fault):
                    self.state(target, fault=fault)
                    result = self.cli(target, "windows-fidelity", "pr.open", "reviewed", "--title", TITLE,
                                      "--body", body(PR_HEADINGS, "lf"), "--base", "main",
                                      status=124 if fault == "exception-after-write" else 1)
                    self.assertEqual(error, result["error"])
                    self.assertEqual(1, len(self.observed(target)["effects"]))
                    self.assertEqual(1, self.observed(target)["pushes"])

    def test_issue_mismatch_intent_retries_read_without_rewriting(self):
        for target in self.targets.values():
            for fault in ("body", "newlines", "title", "labels"):
                with self.subTest(host=target.name, fault=fault):
                    name = f"mismatch-{fault}.md"
                    self.todo(target, name)
                    self.state(target, fault=fault)
                    args = self.issue_args(name, body(ISSUE_HEADINGS, "lf"))
                    token = self.preview(target, "native", args)
                    for attempt in range(2):
                        result = self.cli(target, "windows-fidelity", "todo.issue-publish", *args,
                                          "--preview-token", token, status=1)
                        self.assertEqual("issue-readback-mismatch", result["error"])
                        self.assertEqual(1, len(self.observed(target)["effects"]))
                    preview = json.loads((target / ".planning/issue-previews" / (token + ".json")).read_bytes())
                    self.assertEqual("publishing", preview["used"])
                    intents = [json.loads(path.read_bytes()) for path in (target / ".planning/issue-intents").glob("*.json")]
                    self.assertEqual("readback", next(intent for intent in intents if intent["token"] == token)["state"])

    def test_issue_exception_and_failed_readback_reconcile_known_intent_without_second_effect(self):
        for target in self.targets.values():
            for fault in ("exception-after-write", "readback-error"):
                with self.subTest(host=target.name, fault=fault):
                    name = fault + ".md"
                    self.todo(target, name)
                    self.state(target, fault=fault)
                    args = self.issue_args(name, body(ISSUE_HEADINGS, "lf"))
                    token = self.preview(target, "native", args)
                    result = self.cli(target, "windows-fidelity", "todo.issue-publish", *args,
                                      "--preview-token", token, status=124 if fault == "exception-after-write" else 1)
                    self.assertEqual("command-timeout" if fault == "exception-after-write" else "command-failed", result["error"])
                    state = self.observed(target)
                    self.assertEqual(1, len(state["effects"]))
                    state.pop("fault")
                    (target / "provider-state.json").write_bytes(json.dumps(state).encode())
                    result = self.cli(target, "windows-fidelity", "todo.issue-publish", *args, "--preview-token", token)
                    self.assertTrue(result["reconciled"])
                    self.assert_effect(target, self.expected_publication(name, args[4]), "issue", "create")

    def test_stale_issue_preview_refuses_before_any_effect(self):
        for target in self.targets.values():
            name = "stale.md"
            source = self.todo(target, name)
            self.state(target)
            args = self.issue_args(name, body(ISSUE_HEADINGS, "lf"))
            token = self.preview(target, "native", args)
            source.write_bytes(source.read_bytes() + b"Source changed after review.\n")
            result = self.cli(target, "windows-fidelity", "todo.issue-publish", *args,
                              "--preview-token", token, status=1)
            self.assertEqual("stale-issue-preview", result["error"])
            self.assertEqual([], self.observed(target)["effects"])

    def test_uncertain_missing_issue_and_changed_intent_cannot_authorize_second_create(self):
        for target in self.targets.values():
            name = "uncertain.md"
            self.todo(target, name)
            self.state(target, fault="exception-after-write")
            args = self.issue_args(name, body(ISSUE_HEADINGS, "lf"))
            token = self.preview(target, "native", args)
            self.cli(target, "windows-fidelity", "todo.issue-publish", *args, "--preview-token", token, status=124)
            state = self.observed(target)
            state.update(issue=None, fault=None)
            (target / "provider-state.json").write_bytes(json.dumps(state).encode())
            result = self.cli(target, "windows-fidelity", "todo.issue-publish", *args,
                              "--preview-token", token, status=1)
            self.assertEqual("issue-publication-uncertain", result["error"])
            changed = [*args]
            changed[4] += "\nReviewed addition.\n"
            changed_token = self.preview(target, "native", changed)
            result = self.cli(target, "windows-fidelity", "todo.issue-publish", *changed,
                              "--preview-token", changed_token, status=1)
            self.assertEqual("issue-intent-conflict", result["error"])
            self.assertEqual(1, len(self.observed(target)["effects"]))


if __name__ == "__main__":
    unittest.main()
