"""Fresh R1 probes, with bounded cleanup of only fixture-owned processes."""
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
import traceback

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[5]
TREE = ROOT / '.worktrees/TASK-006-a1'
sys.path.insert(0, str(TREE / 'src'))
from commands import LocalCommandRunner, FileCommandLogStore
from config import load_installation_record, load_project_settings
from contracts import ContractRegistry
from domain_values import EntityId, PlanId, Revision, Sha256Digest
from local_ports import (CommandDefinition, CommandRequest, CommandRootBindings,
                        LocalProjectBinding, LocalWorktreeBinding, EnvironmentBinding,
                        CommandRunner, ContentRef)

RESULTS = []
PLATFORM = 'windows' if os.name == 'nt' else 'linux'
OUT = Path(__file__).with_name('TASK-006-a1-c1-R1-probes-' + PLATFORM + '.txt')
registry = ContractRegistry(TREE / 'schemas/v1')
settings = load_project_settings(TREE, load_installation_record(TREE))

def wire(value):
    if isinstance(value, (EntityId, PlanId, Revision, Sha256Digest)):
        return value.value
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if dataclasses.is_dataclass(value):
        return {f.name: wire(getattr(value, f.name)) for f in dataclasses.fields(value)}
    if isinstance(value, tuple):
        return [wire(v) for v in value]
    return value

def record(case, **facts):
    RESULTS.append({'case':case, **facts})
    OUT.write_text(json.dumps(RESULTS, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(RESULTS[-1]), flush=True)

class Ids:
    def new(self, kind, plan_id=None):
        return EntityId('R1-EVIDENCE')

class Clock:
    def now(self):
        return datetime.now(timezone.utc)

def alive(pid):
    if os.name == 'nt':
        import ctypes
        handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
        if not handle:
            return False
        code = ctypes.c_ulong()
        try:
            return bool(ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(code))) and code.value == 259
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False

def kill_owned(pid):
    if alive(pid):
        if os.name == 'nt':
            subprocess.run(['taskkill','/PID',str(pid),'/T','/F'],check=False,capture_output=True,timeout=5)
        else:
            os.kill(pid, 9)
    deadline = time.monotonic() + 3
    while alive(pid) and time.monotonic() < deadline:
        time.sleep(.05)
    return not alive(pid)

with tempfile.TemporaryDirectory(prefix='task006-r1-') as temp:
    project = Path(temp).resolve()
    worktree = project / '.worktrees/task'
    worktree.mkdir(parents=True)
    bound_settings = dataclasses.replace(settings, project_root=project)
    roots = CommandRootBindings(LocalProjectBinding('project', project), LocalWorktreeBinding('project','WT-R1',worktree))
    base_env = {'PATH': str(Path(sys.executable).parent)}
    if os.name == 'nt':
        base_env['SystemRoot'] = os.environ['SystemRoot']
    store = FileCommandLogStore(project, 'logs')
    def runner(**kw):
        values = dict(project_settings=bound_settings, run_settings=bound_settings.resolve_run(),
                      allowed_permissions=('local_execute',), id_factory=Ids(), clock=Clock(),
                      log_store=store, base_environment=base_env)
        values.update(kw)
        return LocalCommandRunner(**values)
    def request(code, *, names=(), env=(), timeout=2, maximum=10000, cwd='.'):
        definition = CommandDefinition('r1.probe',(sys.executable,'-c',code),'worktree',timeout,maximum,'local_execute',names,('linux','windows'),'exit_zero')
        return CommandRequest('project',PlanId('PLAN-001'),'RUN-R1','OP-R1',definition,roots,cwd,env)
    def logs(evidence):
        registry.validate(wire(evidence))
        result=[]
        for ref in (evidence.stdout_ref,evidence.stderr_ref):
            data=(project/ref.path).read_bytes()
            assert hashlib.sha256(data).hexdigest() == ref.sha256.value
            result.append(data)
        return result

    assert isinstance(runner(), CommandRunner)
    try:
        runner().execute({})
        raise AssertionError('dict accepted')
    except TypeError:
        record('typed_api', result='PASS; actual Protocol instance; dict rejected')

    if os.name != 'nt':
        (worktree/'alias').symlink_to(project,target_is_directory=True)
        e = runner().execute(request('raise SystemExit(98)',cwd='alias'))
        logs(e)
        assert e.status.value == 'launch_failed' and e.error_category == 'invalid_input'
        record('cwd_symlink', result='PASS', status=e.status.value)
    else:
        record('cwd_symlink', result='SKIP; exercised on Linux without Windows symlink privilege assumption')

    token='R1-Token-0123456789'
    code="import os; t=os.environ['TOKEN']; os.write(1,b'x'*8191+t.encode('utf-16-le')); os.write(2,t.encode('utf-16-be')+t.encode('utf-8'))"
    e=runner().execute(request(code,names=('TOKEN',),env=(EnvironmentBinding('TOKEN',token),),maximum=8199))
    contents=logs(e)
    assert sum(map(len,contents)) <= 8199 and e.redactions_applied and e.output_truncated
    assert all(token.encode(enc) not in b for b in contents for enc in ('utf-8','utf-16-le','utf-16-be'))
    record('encoded_streaming_redaction_and_shared_budget', result='PASS', bytes=list(map(len,contents)),redacted=e.redactions_applied,truncated=e.output_truncated)

    reference=store.write(EntityId('CORRUPT-R1'),'stdout',b'original')
    (project/reference.path).write_bytes(b'corruption')
    try:
        store.write(EntityId('CORRUPT-R1'),'stdout',b'original')
        raise AssertionError('corrupt content accepted')
    except OSError:
        assert (project/reference.path).read_bytes()==b'corruption'
        record('existing_content_corruption',result='PASS; rejected mismatched immutable destination without overwrite')

    start=datetime(2026,9,8,12,tzinfo=timezone.utc)
    class BackwardClock:
        samples=iter((start,start-timedelta(seconds=1)))
        def now(self): return next(self.samples)
    e=runner(clock=BackwardClock()).execute(request("print('retained')"))
    contents=logs(e)
    assert e.status.value=='unknown' and e.finished_at is None and e.exit_code is None and e.started_at==start and contents[0].strip()==b'retained'
    record('clock_regression',result='PASS',evidence=wire(e))

    if os.name != 'nt':
        pid_file=worktree/'detached.pid'
        parent=("import os,subprocess,sys,time,pathlib; "
                "p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)'],start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); "
                "pathlib.Path(os.environ['PID_FILE']).write_text(str(p.pid)); time.sleep(30)")
        e=runner().execute(request(parent,names=('PID_FILE',),env=(EnvironmentBinding('PID_FILE',str(pid_file),False),),timeout=1))
        pid=int(pid_file.read_text())
        try:
            child_alive=alive(pid)
            pgid=os.getpgid(pid) if child_alive else None
            logs(e)
            record('detached_descendant_timeout',result='DEFECT' if e.status.value=='timed_out' and child_alive else 'OBSERVATION',status=e.status.value,exit_code=e.exit_code,error_category=e.error_category,child_pid=pid,child_pgid=pgid,child_alive_after_return=child_alive)
        finally:
            record('detached_descendant_fixture_cleanup',pid=pid,confirmed_gone=kill_owned(pid))
    else:
        record('detached_descendant_timeout',result='SKIP; POSIX setsid/group-specific probe')

    pid_file=worktree/'pipe-holder.pid'
    parent=("import os,subprocess,sys,pathlib; "
            "p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)']); "
            "pathlib.Path(os.environ['PID_FILE']).write_text(str(p.pid))")
    main_ident=threading.get_ident()
    observation={}
    def intervene():
        pid=int(pid_file.read_text())
        observation.update(child_pid=pid,child_alive=alive(pid),main_stack=traceback.format_stack(sys._current_frames()[main_ident]))
        observation['fixture_cleanup_confirmed']=kill_owned(pid)
    timer=threading.Timer(7,intervene)
    timer.start()
    begin=time.monotonic()
    try:
        e=runner().execute(request(parent,names=('PID_FILE',),env=(EnvironmentBinding('PID_FILE',str(pid_file),False),),timeout=1))
        elapsed=time.monotonic()-begin
        logs(e)
    finally:
        timer.join(timeout=10)
        if pid_file.exists():
            kill_owned(int(pid_file.read_text()))
    record('parent_exits_descendant_keeps_pipes',result='DEFECT' if elapsed>=6.8 and any('pipe.close()' in line for line in observation.get('main_stack',[])) else 'OBSERVATION',elapsed_seconds=round(elapsed,3),configured_timeout=1,status=e.status.value,error_category=e.error_category,watchdog_at_seconds=7,observation=observation)

record('probe_completion', result='COMPLETE', platform=sys.platform, source=str(TREE/'src/commands.py'))
