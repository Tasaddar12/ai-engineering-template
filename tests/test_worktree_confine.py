"""Run the hook's path handling in Bash, including Windows-style inputs."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import unittest

HOOK = Path(__file__).resolve().parents[1] / '.ai/hooks/worktree-confine.sh'
BASH = str(Path(os.environ.get('ProgramFiles', 'C:/Program Files')) / 'Git/bin/bash.exe') if os.name == 'nt' else shutil.which('bash')


@unittest.skipUnless(BASH and Path(BASH).is_file(), 'Bash is unavailable')
class ConfinementTests(unittest.TestCase):
    def functions(self, commands):
        source = HOOK.read_text(encoding='utf-8')
        functions = source[source.index('norm()'):source.index('\ndeny()')]
        result = subprocess.run([BASH, '-c', functions + '\n' + commands], text=True, capture_output=True, check=True)
        return result.stdout.splitlines()

    def test_norm_preserves_slashes_and_converts_backslashes(self):
        self.assertEqual(self.functions(r"""
norm 'C:\Repo\child/file.txt'; printf '\n'
norm '/Repo/child/file.txt'; printf '\n'
norm 'C:/Repo//child/'; printf '\n'
"""), ['c:/repo/child/file.txt', '/repo/child/file.txt', 'c:/repo/child'])

    def test_resolve_windows_and_relative_parent_segments(self):
        self.assertEqual(self.functions(r"""
cwd='C:/Repo/worktree'
resolve 'C:\Repo\worktree\src\file.py'; printf '\n'
resolve '..\sibling\file.py'; printf '\n'
resolve 'src\..\file.py'; printf '\n'
resolve '/repo/src/../file.py'; printf '\n'
"""), ['C:/Repo/worktree/src/file.py', 'C:/Repo/sibling/file.py', 'C:/Repo/worktree/file.py', '/repo/file.py'])

    def invoke_hook(self, tool, **tool_input):
        script = r'''
git() {
  case "$*" in
    *--show-toplevel) printf 'C:/Repo/worktree' ;;
    *--git-common-dir) printf 'C:/Repo/.git' ;;
    *) return 1 ;;
  esac
}
source "$1"
'''
        payload = json.dumps({'cwd': 'C:/Repo/worktree', 'tool_name': tool, 'tool_input': tool_input})
        return subprocess.run([BASH, '-c', script, 'hook-test', HOOK.as_posix()], input=payload,
                              text=True, capture_output=True, check=True).stdout.strip()

    def test_hook_accepts_owned_paths_and_rejects_sibling_prefixes(self):
        for path, denied in [('C:/Repo/worktree/src/a.py', False),
                             (r'C:\Repo\worktree\src\a.py', False),
                             ('C:/Repo/worktree-other/a.py', True),
                             (r'C:\Repo\sibling\a.py', True),
                             ('C:/Repo/sibling/a"quoted.py', True),
                             ('../sibling/a.py', True)]:
            with self.subTest(path=path):
                output = self.invoke_hook('Write', file_path=path)
                self.assertEqual(bool(output), denied)
                if denied:
                    self.assertEqual(json.loads(output)['hookSpecificOutput']['permissionDecision'], 'deny')

    def test_standard_devices_are_allowed(self):
        for path in ('/dev/null', '/dev/zero', '/dev/full', '/dev/random', '/dev/urandom',
                     '/dev/stdout', '/dev/stdin', '/dev/stderr', '/dev/tty',
                     '/dev/fd/0', '/dev/fd/1', '/dev/fd/2', '/dev/fd/63'):
            with self.subTest(path=path):
                self.assertEqual(self.invoke_hook('Write', file_path=path), '')
                self.assertEqual(self.invoke_hook('Bash', command=f"printf x > '{path}'"), '')

    def test_device_exemption_keeps_normal_paths_confined(self):
        for path in ('/dev/null-output', '/dev/fd/not-a-number', '/dev/fd/1/file.txt',
                     '/DEV/STDOUT', '/tmp/outside.txt', '/dev/zero/../outside.txt'):
            with self.subTest(path=path):
                output = self.invoke_hook('Bash', command=f"printf x > '{path}'")
                self.assertEqual(json.loads(output)['hookSpecificOutput']['permissionDecision'], 'deny')


if __name__ == '__main__':
    unittest.main()
