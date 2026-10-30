"""Run active documentation helpers against fixtures and guard tracked Markdown."""
import importlib.util
import json
import locale
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest

try:
    from .test_engineer_runtime import RuntimeCase, SOURCE
except ImportError:
    from test_engineer_runtime import RuntimeCase, SOURCE

posix_shell_spec = importlib.util.spec_from_file_location(
    "_engineer_posix_shell_test_helper", SOURCE/"engineer/bin/lib/posix_shell.py")
posix_shell = importlib.util.module_from_spec(posix_shell_spec)
posix_shell_spec.loader.exec_module(posix_shell)
find_posix_shell = posix_shell.find_posix_shell

spec = importlib.util.spec_from_file_location("markdown_python", SOURCE/"scripts/check_markdown_python.py")
scanner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scanner)


def snippets(file):
    text = (SOURCE/file).read_text(encoding="utf-8")
    result = []
    for match in re.finditer(r"\bpython(?:3)?(?: -X utf8)? -c\s+(['\"])", text):
        lexer = shlex.shlex(text[match.end()-1:], posix=True, punctuation_chars="();|&<>`")
        lexer.whitespace_split = True
        result.append(next(lexer))
    return result


class MarkdownScan(unittest.TestCase):
    def test_all_tracked_markdown(self):
        offenders = [(str(p), *item) for p in scanner.tracked_markdown()
                     for item in scanner.findings((SOURCE/p).read_text(encoding="utf-8-sig"), runtime_only=True)]
        self.assertEqual([], offenders)

    def test_runtime_guard_preserves_generic_node_examples(self):
        samples = ['`node -c {file}`', '```sh\nnode --version\n```',
                   '```sh\nnode -e "console.log(require(package).version)"\n```']
        for sample in samples:
            self.assertEqual([], scanner.findings(sample, runtime_only=True))
        self.assertTrue(scanner.findings('`node engineer/bin/lib/edge-probe.cjs input.json`', runtime_only=True))

    def test_command_variants_and_locations(self):
        examples = ["node -e 'console.log(1)'", 'node --eval "console.log(1)"',
                    'node -p "process.version"', 'node --print "1"', "node --test test.js",
                    "node - <<'JS'\nconsole.log(1)\nJS", 'node "helper.cjs"',
                    '/usr/bin/node -e "1"', '"/opt/node bin/node" -e "1"',
                    r'"C:\Program Files\nodejs\node.exe" -e "1"',
                    'nodejs -e "1"', 'env FOO=bar node -e "1"', 'command node -e "1"',
                    'node ./bin/cli', 'node < script.js', "printf 'console.log(1)' | node",
                    'node', '/usr/bin/node ./extensionless', 'bash -c "node < script.js"',
                    'printf "%s" "$(node ./cli)"',
                    'x=$(node -p "1")', 'node \\\n -e "1"',
                    'python engineer/bin/lib/edge-probe.cjs']
        for command in examples:
            with self.subTest(command=command):
                text = "# Example\n\n```sh\n"+command+"\n```\n"
                hits = scanner.findings(text)
                self.assertTrue(hits)
                self.assertEqual(4, hits[0][0])
        self.assertTrue(scanner.findings('Use `node -e "1"`.'))
        self.assertTrue(scanner.findings('    /usr/bin/node -e "1"\n'))
        self.assertTrue(scanner.findings('Run `node`.'))

    def test_prose_graph_and_application_source_are_not_commands(self):
        for text in ["A graph node branches into two nodes.", "Use Node.js for this app.",
                     '`npm run dev` and `npx eslint src/app.js`',
                     '```js\nconst node = document.createElement("div");\nnode.append(child);\n```',
                     'Prose identifiers `node` and `Node` describe a runtime.',
                     '```\nDifferences:\n- Node version: Same\n- Timezone: Different\n```',
                     '```js\nconst command = "node ./cli";\nconst node = graph.root;\n```',
                     '```sh\nprintf "node ./cli"\ngrep "node -e" file.md\n```',
                     '```sh\necho "node"\n# node -e is an old example\n```']:
            self.assertEqual([], scanner.findings(text), text)

    def test_wrapper_operands_balanced_substitutions_and_markdown_containers(self):
        positive = [
            'result=`node -p "1+1"`', 'printf "%s" "`node ./cli`"',
            'value=$(printf "%s" "$(node ./cli)")',
            'timeout 5s node ./cli', 'timeout -k 1s --signal TERM 5.5s env -u NODE -- node ./cli',
            'sudo -u root -g staff -- node ./cli', 'sudo --user=root node ./cli',
            'env -S "node ./cli"', "env --split-string='node ./cli'",
            'command -p -- node ./cli', 'exec -a display-name -- node ./cli',
            "sh -c 'node ./cli'", "bash -c 'printf x | node'",
        ]
        negative = [
            'env -u NODE python -V', 'env --unset NODE -- python -V',
            'sudo -u node python -V', 'exec -a node python -V',
            'timeout -s NODE 5s python -V', 'command -v node',
            "printf '%s' '`node ./cli`'", r'printf "%s" "\`node ./cli\`"',
            "printf '%s' '$(node ./cli)'", r'printf "%s" "\$(node ./cli)"',
            "env -S 'printf node'", "env -S 'python -V' node", '# ignored $(node ./cli)',
        ]
        for command in positive+negative:
            with self.subTest(command=command):
                hits=scanner.findings('```sh\n'+command+'\n```\n')
                self.assertEqual(command in positive,bool(hits))
                if hits:
                    self.assertEqual(2,hits[0][0])
        containers = ['> ```sh\n> node ./cli\n> ```',
                      '- ```sh\n  node ./cli\n  ```',
                      '1. ```sh\n   node ./cli\n   ```',
                      '> - ```sh\n>   node ./cli\n>   ```']
        for text in containers:
            hits=scanner.findings(text)
            self.assertTrue(hits,text)
            self.assertEqual(2,hits[0][0])
        self.assertTrue(scanner.findings('Run node script.js'))
        self.assertEqual([],scanner.findings('```js\nconst label = `node ./cli`;\n```'))

    def test_git_inventory_includes_hidden_case_and_unusual_locations(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", directory], check=True)
            names = [".hidden/NOTES.MD", "other space/guide.Markdown", "README.md"]
            for name in names:
                path = root/name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("# Example\n", encoding="utf-8")
            subprocess.run(["git", "-C", directory, "add", "--", *names], check=True)
            self.assertEqual(sorted(names), sorted(p.as_posix() for p in scanner.tracked_markdown(root)))

    def test_archived_and_planning_records_are_outside_the_scan(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", directory], check=True)
            excluded = [".ai/agents/verifier.md", ".planning/STATE.md",
                        "docs/maintenance/existing-SUMMARY.md", "PLANNED-UPDATES.md"]
            active = [".hidden/NOTES.MD", "engineer/workflows/example.md"]
            for name in excluded + active:
                path = root/name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("```sh\nnode engineer/bin/lib/edge-probe.cjs\n```\n" if name in excluded else "# Active\n", encoding="utf-8")
            subprocess.run(["git", "-C", directory, "add", "--", *excluded, *active], check=True)
            self.assertEqual(sorted(active), sorted(p.as_posix() for p in scanner.tracked_markdown(root)))
            self.assertEqual(0, scanner.main(root))
            (root/active[-1]).write_text("```sh\nnode engineer/bin/lib/edge-probe.cjs\n```\n", encoding="utf-8")
            self.assertEqual(1, scanner.main(root))

    def test_default_encoding_diagnostic_preserves_unicode_filename(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            subprocess.run(['git','init','-q',directory],check=True)
            name='café/漢.MD'
            path=root/name
            path.parent.mkdir()
            path.write_text('```sh\nnode engineer/bin/lib/edge-probe.cjs\n```\n',encoding='utf-8')
            subprocess.run(['git','-C',directory,'add','--',name],check=True)
            env={key:value for key,value in os.environ.items() if key not in ('PYTHONUTF8','PYTHONIOENCODING')}
            process=subprocess.run([sys.executable,'-B','-I',str(SOURCE/'scripts/check_markdown_python.py'),'--root',directory],
                                   env=env,capture_output=True)
            self.assertEqual(1,process.returncode,process.stderr.decode('utf-8'))
            self.assertIn(name+':2:',process.stdout.decode('utf-8'))


class InlineHelpers(RuntimeCase):
    def run_code(self, code, *argv, stdin="", status=0, encoding=None):
        # Execute the actual shell-decoded documentation argument as Python argv.
        environment = {key:value for key,value in self.env.items() if key not in ("PYTHONUTF8", "PYTHONIOENCODING")}
        process = subprocess.run([sys.executable, "-c", code, *map(str, argv)], cwd=self.root,
                                 env=environment, input=stdin,
                                 encoding=encoding or locale.getencoding(), capture_output=True, timeout=10)
        self.assertEqual(status, process.returncode, process.stderr+"\n"+code)
        return process

    def code(self, file, contains):
        matches = [code for code in snippets(file) if contains in code]
        self.assertEqual(1, len(set(matches)), contains)
        return matches[0]

    def bash(self, script):
        executable = find_posix_shell()
        self.assertIsNotNone(executable, "Git Bash is required for shell-decoded fixtures")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"fixture.sh"
            path.write_text(script, encoding="utf-8")
            environment = {**self.env, "ENGINEER_PYTHON": Path(sys.executable).as_posix(),
                           "ENGINEER_RUNTIME": (SOURCE/"engineer/bin/engineer.py").as_posix(),
                           "PYTHONIOENCODING": "cp1252"}
            return subprocess.run([executable, path.as_posix()], cwd=self.root, env=environment,
                                  capture_output=True, timeout=15)

    def test_runtime_field_reader_is_utf8_and_preserves_null_false_and_missing(self):
        file = "engineer/workflows/new-milestone.md"
        line = next(line for line in (SOURCE/file).read_text(encoding="utf-8").splitlines()
                    if line.startswith("_engineer_field()"))
        path_json = json.dumps({"path": f"C:/work/{chr(0x6f22)}/STATE.md"}, ensure_ascii=False)
        script = "\n".join([
            "set -e",
            "engineer_run() { \"$ENGINEER_PYTHON\" -I \"$ENGINEER_RUNTIME\" \"$@\"; }",
            line,
            f"printf '%s\\n' \"$(_engineer_field '{path_json}' path)\"",
            f"printf '%s\\n' \"$(_engineer_field '{json.dumps({'path': None})}' path)\"",
            f"printf '%s\\n' \"$(_engineer_field '{json.dumps({'path': False})}' path)\"",
            "printf '%s\\n' \"$(_engineer_field '{}' path)\"",
            "set +e",
            "_engineer_field '{bad' path >/dev/null; printf '%s\\n' \"$?\"",
        ])
        result = self.bash(script)
        self.assertEqual(0, result.returncode, result.stderr.decode("utf-8"))
        self.assertEqual(f"C:/work/{chr(0x6f22)}/STATE.md\n\nfalse\n\n2\n", result.stdout.decode("utf-8"))

    def test_native_manifest_root_is_utf8_and_rejects_invalid_ownership(self):
        manifest = self.root/"manifest.json"
        self.env["WAVE_WORKTREE_MANIFEST"] = str(manifest)
        script = '\n'.join([
            'engineer_run() { "$ENGINEER_PYTHON" -I "$ENGINEER_RUNTIME" "$@"; }',
            'engineer_run query worktree.manifest root --manifest "$WAVE_WORKTREE_MANIFEST" --pick orchestrator_root --raw',
        ])
        owner = f"C:/work/{chr(0x6f22)}/lane"
        manifest.write_text(json.dumps({"orchestrator_root": owner, "worktrees": []}, ensure_ascii=False), encoding="utf-8")
        result = self.bash(script)
        self.assertEqual(0, result.returncode, result.stderr.decode("utf-8"))
        self.assertEqual(owner, result.stdout.decode("utf-8").strip())
        for invalid in ('{bad', '{"orchestrator_root":null,"worktrees":[]}'):
            manifest.write_text(invalid, encoding="utf-8")
            result = self.bash(script)
            self.assertNotEqual(0, result.returncode)
            self.assertEqual(b'', result.stdout)

    def test_standalone_readers_emit_utf8_for_non_cp1252_paths(self):
        sentinel = self.root/"recovery.json"
        sentinel.write_text(json.dumps({"worktree_path": f"C:/work/{chr(0x6f22)}/orphan", "reviewfix_branch": "repair/01"}),
                            encoding="utf-8")
        recovery = self.code("agents/code-fixer.md", "malformed recovery sentinel")
        script = "prior_recovery=$(\"$ENGINEER_PYTHON\" -c "+shlex.quote(recovery)+" \"$1\")\nprintf '%s' \"$prior_recovery\"\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"fixture.sh"
            path.write_text(script, encoding="utf-8")
            result = subprocess.run([find_posix_shell(), path.as_posix(), sentinel.as_posix()], cwd=self.root,
                                    env={**self.env, "ENGINEER_PYTHON": Path(sys.executable).as_posix(),
                                         "PYTHONIOENCODING": "cp1252"}, capture_output=True, timeout=15)
        self.assertEqual(0, result.returncode, result.stderr.decode("utf-8"))
        self.assertEqual(f"C:/work/{chr(0x6f22)}/orphan\nrepair/01", result.stdout.decode("utf-8").replace("\r\n", "\n"))

        manifest = self.root/"cleanup.json"
        manifest.write_text(json.dumps({"orchestrator_root": str(self.root), "worktrees": [
            {"worktree_path": f"C:/work/{chr(0x6f22)}/agent"}]}, ensure_ascii=False), encoding="utf-8")
        self.env["WAVE_WORKTREE_MANIFEST"] = str(manifest)
        result = self.bash('engineer_run() { "$ENGINEER_PYTHON" -I "$ENGINEER_RUNTIME" "$@"; }\n'
                           'engineer_run query worktree.manifest paths --manifest "$WAVE_WORKTREE_MANIFEST" --lines --raw')
        self.assertEqual(0, result.returncode, result.stderr.decode("utf-8"))
        self.assertEqual(f"C:/work/{chr(0x6f22)}/agent\n", result.stdout.decode("utf-8").replace("\r\n", "\n"))

    def test_config_and_recovery_sentinels(self):
        file = "agents/code-fixer.md"
        config = self.code(file, 'use_worktrees')
        self.env["ENGINEER_PROJECT_DIR"] = str(self.root)
        self.assertEqual("true", self.run_code(config).stdout)
        self.put('.planning/config.json', '{"workflow":{"use_worktrees":false}}')
        self.assertEqual("false", self.run_code(config).stdout)
        self.put('.planning/config.json', 'malformed')
        self.assertEqual("true", self.run_code(config).stdout)
        sentinel = self.root/'recovery with spaces.json'
        writer = self.code(file, 'started_at')
        self.run_code(writer, sentinel, 'C:/work tree/quoted "é"', 'codex/base', 'reviewfix/01', '01')
        data = json.loads(sentinel.read_text(encoding="utf-8"))
        self.assertEqual('C:/work tree/quoted "é"', data['worktree_path'])
        self.assertTrue(data['started_at'])
        reader = self.code(file, 'malformed recovery sentinel')
        self.assertEqual(data['worktree_path']+'\nreviewfix/01', self.run_code(reader, sentinel, encoding="utf-8").stdout)
        sentinel.write_text('{bad', encoding="utf-8")
        failed = self.run_code(reader, sentinel)
        self.assertEqual('\n', failed.stdout)
        self.assertIn('Warning: malformed recovery sentinel', failed.stderr)

    def test_documented_native_manifest_init_and_fail_closed_cleanup(self):
        source = (SOURCE/'engineer/workflows/execute-phase.md').read_text(encoding='utf-8')
        initializer = next(line.strip() for line in source.splitlines() if line.strip().startswith('MANIFEST_STATE='))
        selector = next(line.strip() for line in source.splitlines() if line.strip().startswith('WAVE_WORKTREE_MANIFEST=$('))
        script = '\n'.join([
            'set -e',
            'engineer_run() { "$ENGINEER_PYTHON" -I "$ENGINEER_RUNTIME" "$@"; }',
            'PHASE_NUMBER=1', 'ORCH_ROOT='+shlex.quote(self.root.as_posix()),
            initializer, selector, 'printf "%s" "$WAVE_WORKTREE_MANIFEST"',
        ])
        result = self.bash(script)
        self.assertEqual(0, result.returncode, result.stderr.decode('utf-8'))
        path = Path(result.stdout.decode('utf-8'))
        data = json.loads(path.read_text(encoding='utf-8'))
        self.assertEqual([], data['worktrees'])
        self.assertEqual(self.root, Path(data['orchestrator_root']))
        unrelated = self.put('unrelated/preserve.txt', 'keep')
        path.write_text('{bad', encoding='utf-8')
        self.cli('worktree.cleanup-wave', '--manifest', path, status=2, raw=True)
        self.assertEqual('keep', unrelated.read_text(encoding='utf-8'))

    def test_json_frontmatter_and_depth_snippets(self):
        file='engineer/workflows/code-review.md'
        report=self.put('review with spaces.md', '---\r\nstatus: clean\r\n---\r\nBody\r\n')
        self.env.update(REVIEW_PATH=str(report), FIX_REPORT_PATH=str(report))
        for doc in (file, 'engineer/workflows/code-review-fix.md'):
            status=self.code(doc,'print("valid"')
            self.assertEqual('valid\n', self.run_code(status).stdout)
            report.write_text('no frontmatter', encoding='utf-8')
            self.assertEqual('invalid\n', self.run_code(status).stdout)
            report.write_text('---\nstatus: clean\n---\n', encoding='utf-8')
        errors=self.run_code(self.code(file,'workflow.code_review_depth_overrides:'),stdin='{"errors":["bad rule"]}')
        self.assertIn('Error: workflow.code_review_depth_overrides: bad rule',errors.stderr)

    def test_milestone_field_reader_preserves_unicode_and_missing_fields(self):
        line = next(line for line in (SOURCE/'engineer/workflows/complete-milestone.md').read_text(encoding='utf-8').splitlines()
                    if line.startswith('_engineer_field()'))
        value = json.dumps({'archive_dir': f'C:/work/{chr(0x6f22)}/milestones'}, ensure_ascii=False)
        script = '\n'.join([
            'set -e',
            'engineer_run() { "$ENGINEER_PYTHON" -I "$ENGINEER_RUNTIME" "$@"; }',
            line,
            'printf "%s\\n" "$(_engineer_field '+shlex.quote(value)+' archive_dir)"',
            'printf "%s\\n" "$(_engineer_field '+shlex.quote('{}')+' archive_dir)"',
        ])
        result = self.bash(script)
        self.assertEqual(0, result.returncode, result.stderr.decode('utf-8'))
        self.assertEqual(f'C:/work/{chr(0x6f22)}/milestones\n\n', result.stdout.decode('utf-8'))

    def test_api_and_module_examples(self):
        api=self.code('agents/verifier.md','d=json.load')
        self.run_code(api,stdin='[1]')
        self.run_code(api,stdin='[]',status=1)
        for value,status in [('"nonempty"',0),('""',1),('123',1),('true',1),('null',1),('{}',1),('{"key":1}',0)]:
            self.run_code(api,stdin=value,status=status)
        module=self.put('module with spaces.py','def exposed():\n    return 1\n')
        self.assertEqual('function\n',self.run_code(self.code('agents/verifier.md','importlib.util'),module,'exposed').stdout)


class RuntimeAdapters(RuntimeCase):
    def shell(self, script):
        shell=Path('C:/Program Files/Git/bin/bash.exe') if os.name=='nt' else Path(shutil.which('bash') or '')
        if not shell.is_file():
            self.skipTest('Bash unavailable for actual workflow shell fixture')
        # Feed UTF-8 script bytes through a file, avoiding Windows ANSI command-line conversion.
        script_path=self.put('documented-fixture.sh',script)
        env={key:value for key,value in self.env.items() if key not in ('PYTHONUTF8','PYTHONIOENCODING')}
        return subprocess.run([str(shell),str(script_path)],cwd=self.root,env=env,encoding='utf-8',capture_output=True,timeout=30)

    def preamble(self):
        return '\n'.join(['set -euo pipefail',
            'python() { '+shlex.quote(Path(sys.executable).as_posix())+' "$@"; }',
            'engineer_run() { python -B -I '+shlex.quote((SOURCE/'engineer/bin/engineer.py').as_posix())+' "$@"; }'])

    def test_documented_shell_flag_and_depth_roundtrip(self):
        text=(SOURCE/'engineer/workflows/code-review.md').read_text(encoding='utf-8')
        flags=next(line for line in text.splitlines() if line.startswith('FLAGS_JSON=$('))
        depth=next(line for line in text.splitlines() if line.startswith('DEPTH_PAYLOAD=$('))
        script='\n'.join([
            self.preamble(),
            'set -- 01 --auto --gemini "--files=src/café/漢.py"', flags,
            'printf "%s\\n--payload--\\n" "$FLAGS_JSON"',
            'REVIEW_FILES=("src/café/漢.py" "README.md")',
            'DEPTH_OVERRIDE=""; CONFIG_DEPTH=quick; DEPTH_OVERRIDES='+shlex.quote(json.dumps([{'paths':['src/café'],'depth':'deep'}])),
            'REPO_ROOT='+shlex.quote(self.root.as_posix()), depth,
            'printf "%s\\n--depth--\\n" "$DEPTH_PAYLOAD"',
            'printf "%s" "$DEPTH_PAYLOAD" | engineer_run query review.resolve-depth | engineer_run query json.depth-fields --raw',
        ])
        process=self.shell(script)
        self.assertEqual(0,process.returncode,process.stderr)
        first,rest=process.stdout.strip().split('\n--payload--\n')
        payload,second=rest.split('\n--depth--\n')
        self.assertTrue(json.loads(first)['fix'])
        self.assertEqual('src/café/漢.py',json.loads(first)['files'])
        self.assertEqual(['src/café/漢.py','README.md'],json.loads(payload)['files'])
        self.assertEqual(['deep','rule','0','src/café','false','false','false'],second.split('\x1f'))

    def test_documented_scope_fields_preserve_unicode_without_startup_flags(self):
        text=(SOURCE/'engineer/workflows/code-review.md').read_text(encoding='utf-8')
        block=re.search(r"scope_field\(\) \{.*?\n\}", text, re.S)[0]
        data={'files':['src/café/漢.py','a path.py'],'status':'resolved','rangeBase':'base'}
        script='\n'.join([self.preamble(), 'SCOPE_JSON='+shlex.quote(json.dumps(data,ensure_ascii=False)), block,
                          'scope_field files', 'scope_field status', 'scope_field missingOnDisk'])
        process=self.shell(script)
        self.assertEqual(0,process.returncode,process.stderr)
        self.assertEqual(['src/café/漢.py','a path.py','resolved',''],process.stdout.splitlines())
        empty=self.cli('json.depth-input','--flag-depth','deep',stdin='\n')
        self.assertEqual([],empty['files'])
        self.assertEqual('deep',empty['flagDepth'])

    def test_isolated_cli_utf8_json_raw_stdin_file_and_errors(self):
        env={key:value for key,value in self.env.items() if key not in ('PYTHONUTF8','PYTHONIOENCODING')}
        runtime=SOURCE/'engineer/bin/engineer.py'
        def launch(*argv,stdin=b''):
            return subprocess.run([sys.executable,'-B','-I',str(runtime),*argv],cwd=self.root,env=env,input=stdin,capture_output=True)
        result=launch('query','review.parse-flags','--','01','--files=src/café/漢.py')
        self.assertEqual(0,result.returncode,result.stderr.decode('utf-8'))
        self.assertEqual('src/café/漢.py',json.loads(result.stdout.decode('utf-8'))['files'])
        result=launch('query','json.get','--field','path','--raw',stdin='{"path":"src/café/漢.py"}'.encode('utf-8'))
        self.assertEqual(0,result.returncode,result.stderr.decode('utf-8'))
        self.assertEqual(['src/café/漢.py'],result.stdout.decode('utf-8').splitlines())
        source=self.put('café 漢.json','{"path":"src/café/漢.py"}')
        result=launch('query','json.get','--input',str(source),'--field','path','--raw')
        self.assertEqual(0,result.returncode,result.stderr.decode('utf-8'))
        self.assertEqual(['src/café/漢.py'],result.stdout.decode('utf-8').splitlines())
        missing=self.root/'不存在.json'
        result=launch('query','json.get','--input',str(missing))
        self.assertEqual(2,result.returncode)
        self.assertIn('不存在.json',result.stderr.decode('utf-8'))

    def test_python_cli_help_example_success_and_missing_subcommand(self):
        cli=self.put('cli with spaces.py','import argparse\np=argparse.ArgumentParser()\np.add_subparsers().add_parser("scan")\np.parse_args()\n')
        for document in ('agents/verifier.md',):
            command=next(line for line in (SOURCE/document).read_text(encoding='utf-8').splitlines() if line.startswith('python "$CLI_PATH" --help'))
            for expected,status in (('scan',0),('missing-command',1)):
                script=self.preamble()+'\nCLI_PATH='+shlex.quote(cli.as_posix())+'\nEXPECTED_SUBCOMMAND='+shlex.quote(expected)+'\n'+command
                result=self.shell(script)
                self.assertEqual(status,result.returncode,result.stderr)

    def test_quick_scope_fallback_survives_set_e_and_pipefail(self):
        text=(SOURCE/'engineer/workflows/quick.md').read_text(encoding='utf-8')
        changed=next(line for line in text.splitlines() if line.startswith('CHANGED_FILES=$('))
        why=next(line.strip() for line in text.splitlines() if line.strip().startswith('QUICK_SCOPE_WHY=$('))
        for data,files,reason in [('', '', 'unresolvable: no resolver output'),
                                  ('{bad', '', 'unresolvable: no resolver output'),
                                  ('{"files":[],"status":"unresolvable","reason":"missing"}', '', 'unresolvable: missing'),
                                  ('{"files":["src/café/漢.py"],"status":"resolved"}', 'src/café/漢.py', 'resolved')]:
            script='\n'.join([self.preamble(),'QUICK_SCOPE_JSON='+shlex.quote(data),changed,why,
                              'printf "%s\\0%s" "$CHANGED_FILES" "$QUICK_SCOPE_WHY"'])
            result=self.shell(script)
            self.assertEqual(0,result.returncode,result.stderr)
            self.assertEqual([files,reason],result.stdout.split('\0'))

    def test_json_helper_contracts(self):
        data={'files':['a path','b.py'],'commits':[{'sha':'1234567890abcdef','subject':'A title'}],
              'status':'unresolvable','reason':'bad input','isolation':'orchestrator-worktree','exec':{'command':'python'}}
        payload=json.dumps(data)
        self.assertEqual('a path b.py', self.cli('json.lines','--field','files','--separator',' ','--raw',stdin=payload,raw=True))
        self.assertEqual('1234567890 A title', self.cli('json.commits','--raw',stdin=payload,raw=True))
        self.assertEqual('1234567890 A title', self.cli('json.commits','--first','--raw',stdin=payload,raw=True))
        self.assertEqual('1234567890abcdef',self.cli('json.get','--field','commits.0.sha','--raw',stdin=payload,raw=True))
        self.assertEqual('unresolvable: bad input',self.cli('json.status-reason','--raw',stdin=payload,raw=True))
        self.assertTrue(self.cli('json.exec-ready',stdin=payload))
        self.assertEqual(2,self.cli('json.length','--field','files',stdin=payload))
        self.assertEqual('fallback',self.cli('json.get','--field','missing','--default','fallback','--raw',stdin=payload,raw=True))
        self.cli('json.validate','--schema','coverage',stdin='{}',status=2,raw=True)
        self.cli('json.validate','--schema','coverage',stdin='{"items":[],"coverage":{}}')
        self.cli('json.validate','--schema','coverage',stdin='garbage',status=2,raw=True)
        for schema in ('requirements','elements'):
            self.cli('json.validate','--schema',schema,stdin='[]',status=2,raw=True)
            self.cli('json.validate','--schema',schema,stdin='[{"id":"R1","text":"<replace: placeholder>"}]',status=2,raw=True)
            self.cli('json.validate','--schema',schema,stdin='[{"id":"R1","text":"Real form"}]')

    def test_review_flags_depth_fields_and_summary_paths(self):
        flags=self.cli('review.parse-flags','--','01','--auto','--gemini','--files=src/a path.py,README.md')
        self.assertTrue(flags['fix'])
        self.assertTrue(flags['auto'])
        self.assertEqual('src/a path.py,README.md',flags['files'])
        result=self.cli('review.resolve-depth',stdin='{"files":["src/a path.py"],"flagDepth":"deep","configDepth":"quick","overrides":[]}')
        self.assertEqual('deep',result['depth'])
        fields=self.cli('json.depth-fields','--raw',stdin=json.dumps(result),raw=True)
        self.assertEqual(['deep','flag','','','false','false','false'],fields.split('\x1f'))
        rules={'files':['src/a.py'],'overrides':[{'paths':['src'],'depth':'quick'}, {'paths':['src/a.py'],'depth':'deep'}]}
        self.assertEqual('deep',self.cli('review.resolve-depth',stdin=json.dumps(rules))['depth'])
        rules['overrides']=[{'paths':['../outside'],'depth':'deep'}]
        failed=self.cli('review.resolve-depth',stdin=json.dumps(rules))
        self.assertFalse(failed['ok'])
        self.assertEqual('path_traversal',failed['errors'][0]['reason'])
        summary=self.put('SUMMARY.md','---\nkey_files:\n  created: ["Dockerfile", "src/a path.py (reason)"]\n  modified: ["README.md — explanation"]\n---\n')
        self.assertEqual('Dockerfile\nsrc/a path.py\nREADME.md',self.cli('review.summary-files','--report',summary,'--raw',raw=True))
        report=self.put('review.md','---\nstatus: clean\nfiles_reviewed_list: ["a path.py", "README.md"]\n---\n')
        self.assertEqual('clean',self.cli('review.field','--report',report,'--field','status','--raw',raw=True))
        self.assertEqual('a path.py\nREADME.md',self.cli('review.field','--report',report,'--field','files_reviewed_list','--raw',raw=True))
        self.assertIn('status: clean',self.cli('review.frontmatter','--report',report,'--raw',raw=True))

    def test_external_review_warnings_and_structural_normalization(self):
        runtime=SOURCE/'engineer/bin/engineer.py'
        data={'ok':False,'results':[{'ok':True,'slug':'one','reviewPath':'review with spaces.md'},
             {'ok':False,'slug':'two','reason':'missing','detail':'not installed'}], 'selection':{'errors':['unknown lane']}}
        process=subprocess.run([sys.executable,'-I',str(runtime),'query','review.evidence-lines','--raw'],cwd=self.root,
                               env=self.env,input=json.dumps(data),text=True,capture_output=True)
        self.assertEqual(0,process.returncode,process.stderr)
        self.assertEqual('- one: review with spaces.md',process.stdout.strip())
        self.assertIn("lane 'two' failed",process.stderr)
        self.assertIn('Warning: unknown lane',process.stderr)
        report=self.put('fallow.json','{"summary":"real summary","findings":[{"message":"real finding"}]}')
        output=self.root/'normalized.json'
        self.cli('review.normalize-structural','--input',report,'--output',output)
        self.assertEqual('real finding',json.loads(output.read_text(encoding='utf-8'))['findings'][0]['message'])
        report.write_text('{"unknown":[]}',encoding='utf-8')
        self.cli('review.normalize-structural','--input',report,'--output',output,status=2,raw=True)


if __name__ == '__main__':
    unittest.main()
