"""Run documentation helpers against fixtures and guard every tracked Markdown path."""
import http.server
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest

try:
    from .test_engineer_runtime import RuntimeCase, SOURCE
except ImportError:
    from test_engineer_runtime import RuntimeCase, SOURCE

spec = importlib.util.spec_from_file_location("markdown_python", SOURCE/"scripts/check_markdown_python.py")
scanner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scanner)


def snippets(file):
    text = (SOURCE/file).read_text(encoding="utf-8")
    result = []
    for match in re.finditer(r"\bpython(?:3)? -c\s+(['\"])", text):
        lexer = shlex.shlex(text[match.end()-1:], posix=True, punctuation_chars="();|&<>`")
        lexer.whitespace_split = True
        result.append(next(lexer))
    return result


class MarkdownScan(unittest.TestCase):
    def test_all_tracked_markdown(self):
        offenders = [(str(p), *item) for p in scanner.tracked_markdown()
                     for item in scanner.findings((SOURCE/p).read_text(encoding="utf-8-sig"))]
        self.assertEqual([], offenders)

    def test_command_variants_and_locations(self):
        examples = ["node -e 'console.log(1)'", 'node --eval "console.log(1)"',
                    'node -p "process.version"', 'node --print "1"', "node --test test.js",
                    "node - <<'JS'\nconsole.log(1)\nJS", 'node "helper.cjs"',
                    '/usr/bin/node -e "1"', '"/opt/node bin/node" -e "1"',
                    r'"C:\Program Files\nodejs\node.exe" -e "1"',
                    'nodejs -e "1"', 'env FOO=bar node -e "1"', 'command node -e "1"',
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

    def test_prose_graph_and_application_source_are_not_commands(self):
        for text in ["A graph node branches into two nodes.", "Use Node.js for this app.",
                     '`npm run dev` and `npx eslint src/app.js`',
                     '```js\nconst node = document.createElement("div");\nnode.append(child);\n```',
                     '```sh\necho "node"\n# node -e is an old example\n```']:
            self.assertEqual([], scanner.findings(text), text)

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


class InlineHelpers(RuntimeCase):
    def run_code(self, code, *argv, stdin="", status=0):
        # Execute the actual shell-decoded documentation argument as Python argv.
        process = subprocess.run([sys.executable, "-c", code, *map(str, argv)], cwd=self.root,
                                 env={**self.env, "PYTHONUTF8": "1"}, input=stdin,
                                 encoding="utf-8", capture_output=True, timeout=10)
        self.assertEqual(status, process.returncode, process.stderr+"\n"+code)
        return process

    def code(self, file, contains):
        matches = [code for code in snippets(file) if contains in code]
        self.assertEqual(1, len(set(matches)), contains)
        return matches[0]

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
        self.assertEqual(data['worktree_path']+'\nreviewfix/01', self.run_code(reader, sentinel).stdout)
        sentinel.write_text('{bad', encoding="utf-8")
        failed = self.run_code(reader, sentinel)
        self.assertEqual('\n', failed.stdout)
        self.assertIn('Warning: malformed recovery sentinel', failed.stderr)

    def test_manifest_write_read_and_fail_closed_cleanup(self):
        file = 'engineer/workflows/execute-phase.md'
        path = self.root/'manifest with spaces.json'
        self.env.update(MANIFEST=str(path), WAVE_WORKTREE_MANIFEST=str(path), ORCH_ROOT='C:/quoted "é" root')
        self.run_code(self.code(file, 'write_text'), stdin='')
        data = json.loads(path.read_text(encoding='utf-8'))
        self.assertEqual([], data['worktrees'])
        self.assertEqual(self.env['ORCH_ROOT'], self.run_code(self.code(file, 'get("orchestrator_root")')).stdout)
        data['worktrees'] = [{'worktree_path':'C:/space tree'}, {}]
        path.write_text(json.dumps(data), encoding='utf-8')
        cleanup = self.code(file, 'WAVE_WORKTREE_MANIFEST is unset')
        self.assertEqual('C:/space tree\n', self.run_code(cleanup).stdout)
        path.write_text('{bad', encoding='utf-8')
        self.assertIn('ERROR: cannot read worktree manifest', self.run_code(cleanup, status=1).stderr)
        self.assertEqual('', self.run_code(self.code(file, 'get("orchestrator_root")')).stdout)
        del self.env['WAVE_WORKTREE_MANIFEST']
        self.assertIn('(unset)', self.run_code(cleanup, status=1).stderr)

    def test_json_frontmatter_depth_and_contribution_snippets(self):
        file='engineer/workflows/code-review.md'
        report=self.put('review with spaces.md', '---\r\nstatus: clean\r\n---\r\nBody\r\n')
        self.env.update(REVIEW_PATH=str(report), FIX_REPORT_PATH=str(report))
        for doc in (file, 'engineer/workflows/code-review-fix.md'):
            status=self.code(doc,'print("valid"')
            self.assertEqual('valid\n', self.run_code(status).stdout)
            report.write_text('no frontmatter', encoding='utf-8')
            self.assertEqual('invalid\n', self.run_code(status).stdout)
            report.write_text('---\nstatus: clean\n---\n', encoding='utf-8')
        field=self.code(file,'v=json.load(sys.stdin).get(sys.argv[1])')
        self.assertEqual('a path\nb"q', self.run_code(field,'files',stdin=json.dumps({'files':['a path','b"q']})).stdout)
        self.assertEqual('false', self.run_code(field,'value',stdin='{"value":false}').stdout)
        depth=self.code(file,'flagDepth=')
        self.env.update(FLAG_DEPTH='deep',CONFIG_DEPTH='quick',DEPTH_OVERRIDES='[]',REPO_ROOT=str(self.root))
        payload=json.loads(self.run_code(depth,stdin='a path\nb"q\n').stdout)
        self.assertEqual(['a path','b"q'],payload['files'])
        self.assertEqual('deep',payload['flagDepth'])
        errors=self.run_code(self.code(file,'workflow.code_review_depth_overrides:'),stdin='{"errors":["bad rule"]}')
        self.assertIn('Error: workflow.code_review_depth_overrides: bad rule',errors.stderr)
        hooks={'activeHooks':[{'kind':'contribution','into':'code-reviewer','fragment':{'inline':'Do </capability_review_rules> safely'}},None]}
        contribution=self.run_code(self.code(file,'activeHooks'),stdin=json.dumps(hooks)).stdout
        self.assertIn('<capability_review_rules>\n',contribution)
        self.assertIn('Do <\\/capability_review_rules> safely',contribution)

    def test_section_fields_and_optional_manifest(self):
        file='engineer/workflows/complete-milestone.md'
        status=self.code(file,'PROJECT_MD_REVIEW=')
        self.assertEqual('PROJECT_MD_REVIEW=run\n',self.run_code(status,'{}').stdout)
        self.assertEqual('PROJECT_MD_REVIEW=skip\n',self.run_code(status,'{"section_manifest":{"included":[]}}').stdout)
        field=self.code(file,'get(sys.argv[2])')
        self.assertEqual('false',self.run_code(field,'{"flag":false}','flag').stdout)
        self.assertEqual('',self.run_code(field,'{}','missing').stdout)
        gate=self.code(file,'sys.exit(0 if m')
        self.run_code(gate,'{}','any')
        self.run_code(gate,'{"section_manifest":{"included":[]}}','any',status=1)

    def test_api_module_package_and_verdict_examples(self):
        api=self.code('agents/verifier.md','d=json.load')
        self.run_code(api,stdin='[1]')
        self.run_code(api,stdin='[]',status=1)
        module=self.put('module with spaces.py','def exposed():\n    return 1\n')
        self.assertEqual('function\n',self.run_code(self.code('agents/verifier.md','importlib.util'),module,'exposed').stdout)
        package=self.put('node_modules/test-pkg/package.json','{"version":"1.2.3","exports":{".":"./index.js"}}')
        self.put('package-lock.json','{"packages":{"node_modules/test-pkg":{"version":"1.2.3"}}}')
        for code in snippets('agents/ui-researcher.md'):
            result=self.run_code(code.replace('<pkg>','test-pkg')).stdout.strip()
            self.assertIn(result,('1','1.2.3'))
        verdict=self.code('engineer/workflows/ship.md','INVALID_JSON')
        self.assertEqual('APPROVED\n',self.run_code(verdict,stdin='{"verdict":"APPROVED"}').stdout)
        self.assertEqual('INVALID_JSON\n',self.run_code(verdict,stdin='{bad').stdout)

    def test_http_examples_use_actual_local_response(self):
        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.end_headers()
            def log_message(self,*args):
                pass
        with http.server.ThreadingHTTPServer(('127.0.0.1',0), Handler) as server:
            thread=threading.Thread(target=server.serve_forever,daemon=True)
            thread.start()
            try:
                codes=set(snippets('engineer/references/checkpoints.md')+snippets('.ai/references/methods/checkpoints.md'))
                self.assertEqual(3,len(codes))
                for code in codes:
                    result=self.run_code(code.replace('localhost:3000','127.0.0.1:'+str(server.server_port)))
                    self.assertIn(result.stdout,('', '200\n'))
            finally:
                server.shutdown()
                thread.join()


class RuntimeAdapters(RuntimeCase):
    def test_documented_shell_flag_and_depth_roundtrip(self):
        shell = Path('C:/Program Files/Git/bin/bash.exe') if os.name == 'nt' else Path(shutil.which('bash') or '')
        if not shell.is_file():
            self.skipTest('Bash unavailable for actual workflow shell fixture')
        text=(SOURCE/'engineer/workflows/code-review.md').read_text(encoding='utf-8')
        flags=next(line for line in text.splitlines() if line.startswith('FLAGS_JSON=$('))
        depth=next(line for line in text.splitlines() if line.startswith('DEPTH_PAYLOAD=$('))
        script='\n'.join([
            'python() { '+shlex.quote(Path(sys.executable).as_posix())+' "$@"; }',
            'engineer_run() { python -I '+shlex.quote((SOURCE/'engineer/bin/engineer.py').as_posix())+' "$@"; }',
            'set -- 01 --auto --gemini "--files=src/a path.py"', flags,
            'printf "%s\\n--depth--\\n" "$FLAGS_JSON"',
            'REVIEW_FILES=("src/a path.py" "README.md")',
            'DEPTH_OVERRIDE=deep; CONFIG_DEPTH=quick; DEPTH_OVERRIDES=\'[]\'',
            'REPO_ROOT='+shlex.quote(self.root.as_posix()), depth,
            'printf "%s" "$DEPTH_PAYLOAD" | engineer_run query review.resolve-depth | engineer_run query json.depth-fields --raw',
        ])
        process=subprocess.run([str(shell),'-c',script],cwd=self.root,env=self.env,text=True,capture_output=True,timeout=30)
        self.assertEqual(0,process.returncode,process.stderr)
        first,second=process.stdout.strip().split('\n--depth--\n')
        self.assertTrue(json.loads(first)['fix'])
        self.assertEqual('src/a path.py',json.loads(first)['files'])
        self.assertEqual(['deep','flag','','','false','false','false'],second.split('\x1f'))

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
