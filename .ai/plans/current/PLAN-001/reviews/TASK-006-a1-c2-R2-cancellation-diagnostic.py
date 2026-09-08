"""Linux minimum-version cancellation after observed descendant readiness."""
import importlib.util
import json
import os
import signal
import sys
import threading
import time
from pathlib import Path

sys.dont_write_bytecode = True
path = Path(__file__).with_name('TASK-006-a1-c2-R2-probes.py')
spec = importlib.util.spec_from_file_location('r2_probes', path)
probes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probes)
from commands import NativeProcessTreeTerminator

assert os.name != 'nt', 'This diagnostic uses Linux PID observations.'
probes.CrossContractTests.setUpClass()

def exists(pid):
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False

for detached in (False, True):
    fixture = probes.CrossContractTests('test_01_saved_snapshot_and_permission_authority_remain_separate')
    fixture.setUp()
    pid_file = fixture.project / 'diagnostic.pid'
    observations = {}
    start = time.monotonic()
    class ReadyCancellation:
        def is_cancelled(self):
            try:
                pid = int(pid_file.read_text())
            except (FileNotFoundError, ValueError):
                return False
            if 'child_pid' not in observations:
                observations.update(child_pid=pid, child_pgid=os.getpgid(pid),
                    child_alive_at_cancel=exists(pid), ready_seconds=time.monotonic() - start)
            return True
    class ObservedTerminator:
        native = NativeProcessTreeTerminator()
        def observe(self, process):
            result = self.native.observe(process)
            observations.update(root_pid=process.pid, root_pgid=result.posix_process_group)
            return result
        def terminate(self, process, observation):
            result = self.native.terminate(process, observation)
            observations['cleanup_claim'] = result
            return result
    child_code = 'import time; time.sleep(30)'
    extra = ',stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True' if detached else ''
    suffix = '; time.sleep(30)' if detached else ''
    parent_code = "import os,pathlib,subprocess,sys,time; p=subprocess.Popen([sys.executable,'-c',sys.argv[1]]" + extra + "); pathlib.Path(os.environ['PID_FILE']).write_text(str(p.pid))" + suffix
    request = fixture.request(parent_code, arguments=(child_code,),
        environment=(probes.EnvironmentBinding('PID_FILE', str(pid_file), False),))
    try:
        evidence = fixture.runner(cancellation=ReadyCancellation(), tree_terminator=ObservedTerminator()).execute(request)
        elapsed = time.monotonic() - start
        fixture.assertEqual(evidence.status, probes.CommandStatus.UNKNOWN)
        fixture.assertEqual(evidence.error_category, 'ambiguous_side_effect')
        fixture.assertIsNone(evidence.exit_code)
        fixture.evidence(evidence)
        pid = observations['child_pid']
        alive = exists(pid)
        if detached:
            fixture.assertTrue(alive)
            fixture.assertNotEqual(observations['root_pgid'], observations['child_pgid'])
        else:
            fixture.assertFalse(alive)
        fixture.assertLess(elapsed, 5)
        print(json.dumps({'case': 'ready_cancellation_detached' if detached else 'ready_cancellation_inherited',
            **observations, 'elapsed_seconds': elapsed, 'status': evidence.status.value,
            'exit_code': evidence.exit_code, 'child_alive_after_return': alive,
            'stdout_bytes': len(fixture.log(evidence.stdout_ref)),
            'stderr_bytes': len(fixture.log(evidence.stderr_ref)),
            'external_intervention_before_return': False}), flush=True)
    finally:
        pid = observations.get('child_pid')
        if pid and exists(pid):
            os.kill(pid, signal.SIGKILL)
            deadline = time.monotonic() + 5
            while exists(pid) and time.monotonic() < deadline:
                time.sleep(.05)
        if pid:
            fixture.assertFalse(exists(pid), 'exact diagnostic descendant must be gone')
        fixture.doCleanups()
        print(json.dumps({'case': 'fixture_cleanup', 'pid': pid, 'confirmed_gone': bool(pid) and not exists(pid)}), flush=True)
assert not [t.name for t in threading.enumerate() if t.name.startswith('command-')]
print('PASS readiness-based actual minimum-version cancellation; no reader threads remain.')
