"""Record an actual independent declared validation or foundation invocation."""
import importlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
tree = Path.cwd().resolve()
sys.path.insert(0, str(tree / 'src'))
print('Python:', sys.version, flush=True)
print('Executable:', sys.executable, flush=True)
print('Platform:', platform.platform(), flush=True)
print('jsonschema:', importlib.metadata.version('jsonschema'), flush=True)
for name in ('commands', 'config', 'contracts', 'domain_values', 'local_ports'):
    module = importlib.import_module(name)
    assert Path(module.__file__).resolve() == tree / 'src' / (name + '.py')
    print('Origin:', name, module.__file__, flush=True)
print('Head:', subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip(), flush=True)
if sys.argv[1] == 'declared':
    definition = json.loads((tree / '.ai/plans/current/PLAN-001/commands/test.TASK-006.json').read_bytes())
    args = [sys.executable, *definition['argv'][1:]]
    timeout = definition['timeout_seconds']
else:
    args = [sys.executable, 'src/validate_foundation.py']
    timeout = 180
print('Actual argv:', repr(args), 'cwd:', str(tree), flush=True)
result = subprocess.run(args, cwd=tree, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout, shell=False)
print(result.stdout.decode('utf-8', errors='replace'), flush=True)
print('Exit code:', result.returncode, flush=True)
if sys.argv[1] == 'declared' and result.returncode == 0:
    output = result.stdout.decode('utf-8', errors='replace')
    assert 'Ran 22 tests' in output and 'OK (skipped=1)' in output
    phases = [json.loads(line.split('TASK-006-FIXTURE ', 1)[1]) for line in output.splitlines() if line.startswith('TASK-006-FIXTURE ')]
    assert len(phases) == 4
    for phase in phases:
        assert phase['parent_pid'] > 0 and phase['child_pid'] > 0
        assert phase['parent_gone'] and phase['child_gone'] and phase['reader_threads_settled']
        assert not phase['watchdog_intervened'] and phase['native_termination_calls'] == 1
    print('Verified 22 discovered, 21 non-skipped, one established skip; all four phase cleanups passed.', flush=True)
sys.exit(result.returncode)
