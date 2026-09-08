"""Fresh process and trust-boundary probes of the exact repaired candidate.

Synthetic secrets and temporary fixture roots only. Every observed fixture PID
is explicitly settled after return; no external watchdog releases execute().
"""
import ctypes
import dataclasses
from datetime import datetime, timezone, timedelta
from enum import Enum
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[5]
TREE = ROOT / '.worktrees/TASK-006-a1'
HEAD = 'ce4c8edb86b02268a856a5f870932ade0e7e9b91'
OUT = Path(__file__).with_name('TASK-006-a1-c2-R1-probes-' + ('windows' if os.name == 'nt' else 'linux') + '.txt')
sys.path.insert(0, str(TREE / 'src'))
import commands, config, contracts, local_ports
from commands import LocalCommandRunner, FileCommandLogStore, NativeProcessTreeTerminator
from config import load_project_settings, load_installation_record, RunSettings
from contracts import ContractRegistry
from domain_values import EntityId, PlanId, Revision, Sha256Digest
from local_ports import CommandDefinition, CommandRequest, CommandRootBindings, LocalProjectBinding, LocalWorktreeBinding, LocalControlBinding, EnvironmentBinding, CommandRunner

RESULTS = []
def record(case, **facts):
    RESULTS.append(dict(case=case, **facts))
    OUT.write_text(json.dumps(RESULTS, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(RESULTS[-1]), flush=True)

def wire(value):
    if isinstance(value, (EntityId, PlanId, Revision, Sha256Digest)):
        return value.value
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if dataclasses.is_dataclass(value):
        return {f.name:wire(getattr(value, f.name)) for f in dataclasses.fields(value)}
    if isinstance(value, tuple):
        return [wire(v) for v in value]
    return value

def alive(pid):
    if os.name == 'nt':
        dll = ctypes.windll.kernel32
        dll.OpenProcess.restype = ctypes.c_void_p
        dll.GetExitCodeProcess.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong)]
        dll.CloseHandle.argtypes = [ctypes.c_void_p]
        handle = dll.OpenProcess(0x1000, False, pid)
        if not handle:
            return False
        code = ctypes.c_ulong()
        try:
            assert dll.GetExitCodeProcess(handle, ctypes.byref(code))
            return code.value == 259
        finally:
            dll.CloseHandle(handle)
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False

def cleanup(pid):
    live_before = alive(pid)
    if live_before:
        if os.name == 'nt':
            subprocess.run(['taskkill','/PID',str(pid),'/T','/F'], shell=False, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
        else:
            os.kill(pid, 9)
    deadline = time.monotonic() + 5
    while alive(pid) and time.monotonic() < deadline:
        time.sleep(.05)
    gone = not alive(pid)
    record('fixture_cleanup', pid=pid, was_alive=live_before, confirmed_gone=gone)
    assert gone

class Ids:
    next = 0
    def new(self, kind, plan_id=None):
        self.next += 1
        return EntityId('R1C2-' + str(self.next))

class Clock:
    def now(self):
        return datetime.now(timezone.utc)

class ObservingTerminator:
    def __init__(self):
        self.native = NativeProcessTreeTerminator()
        self.process = None
        self.observation = None
        self.confirmed = None
    def observe(self, process):
        self.process = process
        self.observation = self.native.observe(process)
        return self.observation
    def terminate(self, process, observation):
        self.confirmed = self.native.terminate(process, observation)
        return self.confirmed

class ReadyCancellation:
    def __init__(self, terminator, pid_file, require_exit):
        self.terminator = terminator
        self.pid_file = pid_file
        self.require_exit = require_exit
        self.begin = time.monotonic()
    def is_cancelled(self):
        p = self.terminator.process
        return p is not None and self.pid_file.exists() and time.monotonic() - self.begin >= .35 and (not self.require_exit or p.poll() is not None)

record('identity', expected_head=HEAD, platform=sys.platform, python=sys.version, origins={m.__name__:m.__file__ for m in (commands,config,contracts,local_ports)})
assert all(Path(m.__file__).resolve().parent == TREE / 'src' for m in (commands,config,contracts,local_ports))
registry = ContractRegistry(TREE / 'schemas/v1')
source_settings = load_project_settings(TREE, load_installation_record(TREE))
with tempfile.TemporaryDirectory(prefix='TASK006-c2-R1-') as temp:
    project = Path(temp).resolve()
    worktree = project / '.worktrees/task'
    control = project / '.worktrees/control'
    worktree.mkdir(parents=True)
    control.mkdir(parents=True)
    settings = dataclasses.replace(source_settings, project_root=project)
    roots = CommandRootBindings(LocalProjectBinding('project',project), LocalWorktreeBinding('project','WT-R1C2',worktree), LocalControlBinding('project','CONTROL-R1C2',control))
    environment = {'PATH':str(Path(sys.executable).parent)}
    if os.name == 'nt':
        environment['SystemRoot'] = os.environ['SystemRoot']
    store = FileCommandLogStore(project, 'logs')
    ids = Ids()
    def runner(**kw):
        values = dict(project_settings=settings, run_settings=RunSettings(), allowed_permissions=('local_execute',), id_factory=ids, clock=Clock(), log_store=store, base_environment=environment)
        values.update(kw)
        return LocalCommandRunner(**values)
    def request(code, *, argv=(), names=(), env=(), timeout=3, maximum=20000, cwd='.', rule='worktree', plan='PLAN-001'):
        d = CommandDefinition('r1.c2.probe',(sys.executable,'-c',code,*argv),rule,timeout,maximum,'local_execute',names,('linux','windows'),'exit_zero')
        return CommandRequest('project',plan,'RUN-R1C2','OP-R1C2',d,roots,cwd,env)
    def logs(evidence):
        registry.validate(wire(evidence))
        result = []
        for ref in (evidence.stdout_ref,evidence.stderr_ref):
            assert ref is not None
            data = (project / ref.path).read_bytes()
            assert hashlib.sha256(data).hexdigest() == ref.sha256.value
            result.append(data)
        return result
    def status(e):
        return dict(status=e.status.value, exit_code=e.exit_code, error_category=e.error_category, output_truncated=e.output_truncated, redactions_applied=e.redactions_applied)

    # Exact original process shapes plus active cancellation; no fixture killer
    # runs until execute has returned and all assertions have observed the child.
    for shape in ('inherited_parent_exit','detached_parent_alive'):
        for mode in ('timeout','cancellation'):
            pid_file = worktree / (shape + '-' + mode + '.pid')
            detached = shape == 'detached_parent_alive'
            parent = (
                "import os,pathlib,subprocess,sys,time; "
                "detached=sys.argv[1]=='yes'; "
                "flags=(subprocess.CREATE_NEW_PROCESS_GROUP|subprocess.DETACHED_PROCESS) if os.name=='nt' and detached else 0; "
                "p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(12)'],stdout=subprocess.DEVNULL if detached else None,stderr=subprocess.DEVNULL if detached else None,creationflags=flags,start_new_session=detached and os.name!='nt'); "
                "pathlib.Path(os.environ['PID_FILE']).write_text(str(p.pid)); "
                "time.sleep(12) if detached else None"
            )
            terminator = ObservingTerminator()
            cancellation = ReadyCancellation(terminator,pid_file,not detached) if mode == 'cancellation' else None
            started = time.monotonic()
            try:
                e = runner(tree_terminator=terminator,cancellation=cancellation).execute(request(parent,argv=('yes' if detached else 'no',),names=('PID_FILE',),env=(EnvironmentBinding('PID_FILE',str(pid_file),False),),timeout=1 if mode=='timeout' else 8))
                elapsed = time.monotonic() - started
                pid = int(pid_file.read_text())
                child_live = alive(pid)
                contents = logs(e)
                record(shape + '_' + mode, elapsed_seconds=round(elapsed,3), **status(e), root_pid=terminator.observation.root_pid, launch_pgid=terminator.observation.posix_process_group, cleanup_claim=terminator.confirmed, child_pid=pid, child_alive_after_return=child_live, child_pgid=os.getpgid(pid) if child_live and os.name!='nt' else None, log_bytes=list(map(len,contents)), external_intervention_before_return=False)
                assert elapsed < 4
                if os.name == 'nt' and detached:
                    assert e.status.value == ('timed_out' if mode=='timeout' else 'cancelled') and not child_live
                else:
                    assert e.status.value == 'unknown' and e.exit_code is None and e.error_category == 'ambiguous_side_effect'
                    assert child_live == (os.name=='nt' or detached)
                if not detached:
                    assert e.output_truncated == (os.name=='nt')
            finally:
                if pid_file.exists():
                    cleanup(int(pid_file.read_text()))
                if terminator.process is not None and terminator.process.poll() is None:
                    cleanup(terminator.process.pid)
                    terminator.process.wait(timeout=5)

    # An escaped pipe holder writes sensitive data before and after freeze.
    pid_file = worktree / 'late-pipe.pid'
    late_file = worktree / 'late-written'
    token = 'R1C2-Synthetic-Token-8192'
    child = "import os,pathlib,time; t=os.environ['TOKEN'].encode(); os.write(1,b'x'*8191+t+b'y'*9000); time.sleep(1.8); os.write(1,t+b'L'*9000); pathlib.Path(os.environ['LATE_FILE']).touch(); time.sleep(12)"
    parent = "import os,pathlib,subprocess,sys; p=subprocess.Popen([sys.executable,'-c',sys.argv[1]],start_new_session=os.name!='nt'); pathlib.Path(os.environ['PID_FILE']).write_text(str(p.pid))"
    try:
        start = time.monotonic()
        e = runner().execute(request(parent,argv=(child,),names=('PID_FILE','LATE_FILE','TOKEN'),env=(EnvironmentBinding('PID_FILE',str(pid_file),False),EnvironmentBinding('LATE_FILE',str(late_file),False),EnvironmentBinding('TOKEN',token)),timeout=1))
        elapsed = time.monotonic()-start
        before = logs(e)
        assert e.status.value=='unknown' and e.output_truncated and e.redactions_applied and elapsed<4
        assert sum(map(len,before))<=20000 and token.encode() not in b''.join(before)
        deadline = time.monotonic()+3
        while not late_file.exists() and time.monotonic()<deadline:
            time.sleep(.05)
        assert late_file.exists()
        assert logs(e)==before
        record('incomplete_capture_freeze_with_late_secret',elapsed_seconds=round(elapsed,3),**status(e),log_bytes=list(map(len,before)),late_write_observed=True,durable_refs_unchanged=True,child_alive=alive(int(pid_file.read_text())))
    finally:
        if pid_file.exists():
            cleanup(int(pid_file.read_text()))

    # Natural inherited EOF before the deadline is a complete ordinary exit.
    pid_file = worktree / 'natural.pid'
    parent = "import os,pathlib,subprocess,sys; p=subprocess.Popen([sys.executable,'-c',\"import time; time.sleep(.25); print('descendant-complete')\"]); pathlib.Path(os.environ['PID_FILE']).write_text(str(p.pid))"
    try:
        e = runner().execute(request(parent,names=('PID_FILE',),env=(EnvironmentBinding('PID_FILE',str(pid_file),False),)))
        assert e.status.value=='exited' and e.exit_code==0 and not e.output_truncated
        assert logs(e)[0].strip()==b'descendant-complete'
        record('natural_inherited_eof',**status(e))
    finally:
        if pid_file.exists():
            cleanup(int(pid_file.read_text()))

    assert isinstance(runner(),CommandRunner)
    try:
        runner().execute({})
        raise AssertionError('mapping API accepted')
    except TypeError:
        pass
    args = ('  leading','trailing  ','line\nnext','tab\tvalue','; literal $() &','repeat','repeat')
    e=runner().execute(request('import json,sys; print(json.dumps(sys.argv[1:]))',argv=args,rule='project',plan=None))
    assert json.loads(logs(e)[0])==list(args) and e.argv_redacted[-len(args):]==args
    for rule, expected in [('project',project),('worktree',worktree),('control',control)]:
        e=runner().execute(request('from pathlib import Path; print(Path.cwd())',rule=rule))
        assert Path(logs(e)[0].decode().strip())==expected
    record('typed_api_literal_argv_zero_plan_and_cwd',result='PASS',argument_count=len(args),cwd_rules=3)

    sentinel='R1C2_AMBIENT_SENTINEL'
    old=os.environ.get(sentinel)
    os.environ[sentinel]='must-be-absent'
    try:
        e=runner().execute(request("import os,json; print(json.dumps([os.environ.get('EMPTY'),os.environ.get('R1C2_AMBIENT_SENTINEL')]))",names=('EMPTY',),env=(EnvironmentBinding('EMPTY',''),)))
        assert json.loads(logs(e)[0])==['',None]
    finally:
        if old is None: os.environ.pop(sentinel,None)
        else: os.environ[sentinel]=old
    for overrides, category in [(dict(allowed_permissions=()),'policy_denied'),(dict(run_settings=RunSettings(required_sandbox=True)),'unsupported_capability')]:
        e=runner(**overrides).execute(request('raise SystemExit(98)'))
        logs(e)
        assert e.status.value=='launch_failed' and e.error_category==category
    record('explicit_environment_permission_sandbox',result='PASS',empty_sensitive_preserved=True,ambient_absent=True)

    if os.name!='nt':
        (worktree/'alias').symlink_to(project,target_is_directory=True)
        e=runner().execute(request('raise SystemExit(98)',cwd='alias'))
        logs(e)
        assert e.status.value=='launch_failed' and e.error_category=='invalid_input'
        record('real_cwd_symlink_refusal',result='PASS')
    else:
        record('real_cwd_symlink_refusal',result='SKIP; actual symlink exercised on Linux')

    token='R1C2-Encoded-Secret-012345'
    code="import os; t=os.environ['TOKEN']; os.write(1,b'x'*8191+t.encode('utf-16-le')); os.write(2,t.encode('utf-16-be')+t.encode())"
    e=runner().execute(request(code,names=('TOKEN',),env=(EnvironmentBinding('TOKEN',token),),maximum=8199))
    data=logs(e)
    assert sum(map(len,data))<=8199 and e.output_truncated and e.redactions_applied
    assert all(token.encode(enc) not in stream for enc in ('utf-8','utf-16-le','utf-16-be') for stream in data)
    record('encoded_split_read_shared_byte_cap',**status(e),bytes=list(map(len,data)))

    first=store.write(EntityId('REUSE-C2'),'stdout',b'first')
    second=store.write(EntityId('REUSE-C2'),'stdout',b'second')
    assert first!=second and first==store.write(EntityId('REUSE-C2'),'stdout',b'first')
    (project/first.path).write_bytes(b'corrupted')
    try:
        store.write(EntityId('REUSE-C2'),'stdout',b'first')
        raise AssertionError('corrupt log accepted')
    except OSError:
        assert (project/first.path).read_bytes()==b'corrupted'
    record('immutable_log_identity_and_corruption_refusal',result='PASS')
    class StoreFailure:
        def write(self,*args): raise OSError('synthetic unavailable storage')
    e=runner(log_store=StoreFailure()).execute(request("print('output')"))
    registry.validate(wire(e))
    assert e.status.value=='unknown' and e.exit_code is None and e.stdout_ref is None and e.stderr_ref is None and e.error_category=='internal_error'
    record('unavailable_durable_store',**status(e))
    start=datetime(2026,9,8,12,tzinfo=timezone.utc)
    class BackwardClock:
        samples=iter((start,start-timedelta(seconds=2)))
        def now(self): return next(self.samples)
    e=runner(clock=BackwardClock()).execute(request("print('clock-evidence-retained')"))
    data=logs(e)
    assert e.started_at==start and e.finished_at is None and e.exit_code is None and e.status.value=='unknown' and e.error_category=='clock_regression' and data[0].strip()==b'clock-evidence-retained'
    record('backward_clock_observation',evidence=wire(e))
    deadline=time.monotonic()+3
    while any(t.name in ('command-stdout','command-stderr') for t in threading.enumerate()) and time.monotonic()<deadline:
        time.sleep(.05)
    remaining=[t.name for t in threading.enumerate() if t.name in ('command-stdout','command-stderr')]
    assert not remaining
    record('drain_threads_settled_after_fixture_cleanup',remaining=remaining)
record('completion',result='PASS',expected_head=HEAD)
