"""Owned Linux subreaper / Windows Job process execution and terminal evidence."""
import ctypes
import hashlib
import json
import math
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from .core import Failure


def _encoded(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()


def _identity(pid):
    if sys.platform != 'linux':
        return {'pid':pid,'start_ticks':None}
    try:
        fields = Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()
        return {'pid':pid,'start_ticks':int(fields[19])}
    except FileNotFoundError:
        return None


def _new(path,data):
    path = Path(path)
    temporary = path.with_name('.'+path.name+'.writing-'+uuid.uuid4().hex)
    try:
        fd = os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,'O_NOFOLLOW',0),0o600)
        with os.fdopen(fd,'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if os.name == 'nt':
            os.rename(temporary,path)  # Windows rename refuses an existing target.
        else:
            os.link(temporary,path)  # Atomic publish without overwriting evidence.
    finally:
        if temporary.exists():
            temporary.unlink()


def terminal(ownership):
    """Validate durable receipt identity; never infer termination from a dead PID."""
    directory = Path(ownership['directory'])
    for candidate in (directory,*directory.parents):
        if candidate.is_symlink() or candidate.exists() and getattr(candidate.lstat(),'st_file_attributes',0) & 0x400:
            raise Failure('process-ownership-unsafe',str(candidate))
    request_path,receipt_path = directory/'request.json',directory/'terminal.json'
    for path in (request_path,receipt_path):
        if path.is_symlink() or not path.is_file():
            raise Failure('process-terminal-unavailable','Retain this attempt until its supervisor supplies terminal proof',ownership=ownership)
        if os.name != 'nt' and (path.stat().st_uid != os.getuid() or path.stat().st_mode & 0o077):
            raise Failure('process-ownership-unsafe',str(path))
    request = json.loads(request_path.read_bytes())
    proof = json.loads(receipt_path.read_bytes())
    if request.get('directory') != str(directory):
        raise Failure('process-terminal-mismatch','private attempt directory')
    if request.get('request_hash') != hashlib.sha256(_encoded({k:v for k,v in request.items() if k != 'request_hash'})).hexdigest():
        raise Failure('process-request-changed',str(request_path))
    if proof.get('receipt_hash') != hashlib.sha256(_encoded({k:v for k,v in proof.items() if k != 'receipt_hash'})).hexdigest():
        raise Failure('process-terminal-changed',str(receipt_path))
    for key in ('token','request_hash','owner'):
        if proof.get(key) != ownership.get(key) or request.get(key) != ownership.get(key):
            raise Failure('process-terminal-mismatch',key)
    if request.get('prompt_hash') is not None:
        prompt = directory/'prompt.bin'
        if prompt.is_symlink() or not prompt.is_file() or hashlib.sha256(prompt.read_bytes()).hexdigest() != request['prompt_hash']:
            raise Failure('process-prompt-changed',str(prompt))
    if ownership.get('supervisor') and not proof.get('windows_job'):
        if any((proof.get('supervisor') or {}).get(k) != ownership['supervisor'].get(k) for k in ('pid','start_ticks')):
            raise Failure('process-terminal-mismatch','supervisor identity')
    if proof.get('terminal') is not True or proof.get('tree_stopped') is not True or type(proof.get('exit_code')) is not int:
        raise Failure('process-tree-uncertain','Subtree termination is not confirmed',ownership=ownership)
    return proof


class _WindowsJob:
    """Kill every assigned descendant when this runner's job handle closes."""
    def __init__(self):
        self.handle = None
        if os.name != "nt":
            return
        from ctypes import wintypes as w

        class Basic(ctypes.Structure):
            _fields_ = [("process_time", ctypes.c_longlong), ("job_time", ctypes.c_longlong),
                        ("flags", w.DWORD), ("minimum", ctypes.c_size_t), ("maximum", ctypes.c_size_t),
                        ("active", w.DWORD), ("affinity", ctypes.c_size_t),
                        ("priority", w.DWORD), ("scheduling", w.DWORD)]

        class IO(ctypes.Structure):
            _fields_ = [(name, ctypes.c_ulonglong) for name in
                        ("read_ops", "write_ops", "other_ops", "read_bytes", "write_bytes", "other_bytes")]

        class Extended(ctypes.Structure):
            _fields_ = [("basic", Basic), ("io", IO), ("process_memory", ctypes.c_size_t),
                        ("job_memory", ctypes.c_size_t), ("peak_process", ctypes.c_size_t),
                        ("peak_job", ctypes.c_size_t)]

        self.api = ctypes.WinDLL("kernel32", use_last_error=True)
        self.api.CreateJobObjectW.restype = w.HANDLE
        self.handle = self.api.CreateJobObjectW(None, None)
        limits = Extended()
        limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE; no breakaway.
        if not self.handle or not self.api.SetInformationJobObject(
                w.HANDLE(self.handle), 9, ctypes.byref(limits), ctypes.sizeof(limits)):
            self.close()
            raise Failure("pipeline-job", "Cannot establish Windows process-tree ownership")

    def assign(self, process):
        if self.handle and not self.api.AssignProcessToJobObject(
                ctypes.c_void_p(self.handle), ctypes.c_void_p(int(process._handle))):
            raise Failure("pipeline-job", "Cannot assign host to the owned Windows job")

    def resume(self, process):
        """Resume the suspended primary thread only after its job owns it."""
        from ctypes import wintypes as w

        class ThreadEntry(ctypes.Structure):
            _fields_ = [("size", w.DWORD), ("usage", w.DWORD), ("thread", w.DWORD),
                        ("owner", w.DWORD), ("priority", w.LONG), ("delta", w.LONG), ("flags", w.DWORD)]

        self.api.CreateToolhelp32Snapshot.argtypes = [w.DWORD, w.DWORD]
        self.api.CreateToolhelp32Snapshot.restype = w.HANDLE
        self.api.Thread32First.argtypes = [w.HANDLE, ctypes.POINTER(ThreadEntry)]
        self.api.Thread32Next.argtypes = [w.HANDLE, ctypes.POINTER(ThreadEntry)]
        self.api.OpenThread.argtypes = [w.DWORD, w.BOOL, w.DWORD]
        self.api.OpenThread.restype = w.HANDLE
        self.api.ResumeThread.argtypes = [w.HANDLE]
        self.api.ResumeThread.restype = w.DWORD
        snapshot = self.api.CreateToolhelp32Snapshot(0x4, 0)
        if not snapshot or snapshot == ctypes.c_void_p(-1).value:
            raise Failure("pipeline-job", "Cannot locate suspended host thread")
        try:
            entry = ThreadEntry()
            entry.size = ctypes.sizeof(entry)
            present = self.api.Thread32First(w.HANDLE(snapshot), ctypes.byref(entry))
            while present:
                if entry.owner == process.pid:
                    thread = self.api.OpenThread(0x2, False, entry.thread)
                    if not thread:
                        raise Failure("pipeline-job", "Cannot open suspended host thread")
                    try:
                        if self.api.ResumeThread(w.HANDLE(thread)) != 1:
                            raise Failure("pipeline-job", "Host thread did not resume from its initial suspension")
                        return
                    finally:
                        self.api.CloseHandle(w.HANDLE(thread))
                present = self.api.Thread32Next(w.HANDLE(snapshot), ctypes.byref(entry))
            raise Failure("pipeline-job", "Suspended host thread was not found")
        finally:
            self.api.CloseHandle(w.HANDLE(snapshot))

    def stop(self):
        if self.handle:
            if not self.api.TerminateJobObject(ctypes.c_void_p(self.handle), 1):
                raise Failure("pipeline-job", "Cannot terminate the owned Windows process tree")
            # Query JobObjectBasicAccountingInformation until ActiveProcesses is zero.
            buffer = ctypes.create_string_buffer(48)
            deadline = time.monotonic() + 30
            while True:
                if not self.api.QueryInformationJobObject(ctypes.c_void_p(self.handle), 1, buffer, 48, None):
                    raise Failure("pipeline-job", "Cannot establish process-tree termination")
                if int.from_bytes(buffer.raw[40:44], "little") == 0:
                    break
                if time.monotonic() >= deadline:
                    raise Failure("pipeline-job", "Owned process tree did not terminate")
                time.sleep(0.1)

    def close(self):
        if self.handle:
            self.api.CloseHandle(ctypes.c_void_p(self.handle))
            self.handle = None


class OwnedProcess:
    """A live attempt whose return code requires confirmed descendant termination."""
    def __init__(self,argv,cwd,env=None,stdin=None,stdout=None,stderr=None,input=None,timeout=300,output_limit=None,on_prepare=None):
        if os.name != 'nt' and sys.platform != 'linux':
            raise Failure('process-supervision-unavailable','Owned descendant supervision requires Linux /proc or Windows Jobs',69)
        if sys.platform == 'linux' and not Path('/proc/self/task').is_dir():
            raise Failure('process-supervision-unavailable','Linux /proc child ownership is unavailable',69)
        if not isinstance(argv,(list,tuple)) or not argv or any(not isinstance(v,str) or '\x00' in v for v in argv):
            raise Failure('invalid-process-argv','Supply exact executable argv',2)
        if isinstance(timeout,bool) or not isinstance(timeout,(int,float)) or not math.isfinite(timeout) or timeout <= 0:
            raise Failure('invalid-process-timeout','Supply a finite positive seconds budget',2)
        if output_limit is not None and (type(output_limit) is not int or output_limit < 1):
            raise Failure('invalid-output-limit','Output limit must be a positive byte count',2)
        self.started,self.deadline = time.monotonic(),time.monotonic()+timeout
        self.directory = Path(tempfile.mkdtemp(prefix='engineer-process-'))
        os.chmod(self.directory,0o700)
        self.returncode,self.proof,self.process = None,None,None
        self.job,self.assigned,self.streams = None,False,[]
        self._threads,self._stream_errors,self._limit_event = [],[],threading.Event()
        self._closed = False
        self._input = None
        owner = _identity(os.getpid())
        environment = dict(os.environ if env is None else env)
        if any(not isinstance(k,str) or not isinstance(v,str) or '\x00' in k+v for k,v in environment.items()):
            raise Failure('invalid-process-environment','Environment must contain exact string pairs',2)
        prompt_hash = None
        if input is not None:
            if stdin is not None:
                raise Failure('ambiguous-process-input','Select supplied stdin or explicit input bytes',2)
            content = input.encode('utf-8') if isinstance(input,str) else bytes(input)
            prompt_hash = hashlib.sha256(content).hexdigest()
            _new(self.directory/'prompt.bin',content)
            self._input = (self.directory/'prompt.bin').open('rb')
            stdin = self._input
        request = {'schema':1,'directory':str(self.directory),'token':uuid.uuid4().hex,'owner':owner,
            'uid':os.getuid() if os.name != 'nt' else None,'argv':list(argv),'cwd':str(Path(cwd).resolve()),
            'environment':environment,'deadline':self.deadline,'output_limit':output_limit,'prompt_hash':prompt_hash}
        request['request_hash'] = hashlib.sha256(_encoded(request)).hexdigest()
        _new(self.directory/'request.json',_encoded(request))
        self.ownership = {k:request[k] for k in ('directory','token','request_hash','owner')}
        try:
            if on_prepare is not None:
                on_prepare(dict(self.ownership))
            if os.name == 'nt':
                self.job = _WindowsJob()
                options = {'creationflags':subprocess.CREATE_NEW_PROCESS_GROUP|subprocess.CREATE_NO_WINDOW|0x4}
                self.process = subprocess.Popen(argv,cwd=request['cwd'],env=environment,stdin=stdin,
                    stdout=subprocess.PIPE if output_limit else stdout,stderr=subprocess.PIPE if output_limit else stderr,shell=False,**options)
                self.job.assign(self.process)
                self.assigned = True
                self.pid = self.process.pid
                self.job.resume(self.process)
                if output_limit:
                    def pump(source,destination):
                        count = 0
                        try:
                            destination = destination if destination is not None else sys.stdout.buffer if source is self.process.stdout else sys.stderr.buffer
                            while True:
                                chunk = source.read(65536)
                                if not chunk:
                                    break
                                available = max(0,output_limit-count)
                                if available:
                                    destination.write(chunk[:available])
                                    destination.flush()
                                count += len(chunk)
                                if count > output_limit:
                                    self._limit_event.set()
                        except BaseException as exc:
                            self._stream_errors.append(str(exc))
                            self._limit_event.set()
                        finally:
                            source.close()
                    for source,destination in ((self.process.stdout,stdout),(self.process.stderr,stderr)):
                        thread = threading.Thread(target=pump,args=(source,destination),daemon=True)
                        thread.start()
                        self._threads.append(thread)
            else:
                supervisor = Path(__file__).resolve().parents[1]/'process_supervisor.py'
                self.process = subprocess.Popen([sys.executable,'-I',str(supervisor),str(self.directory/'request.json')],
                    cwd=request['cwd'],stdin=stdin,stdout=stdout,stderr=stderr,start_new_session=True,shell=False)
                self.pid = self.process.pid
            self.ownership['supervisor'] = _identity(self.pid)
        except BaseException as exc:
            if self.process is not None:
                if os.name == 'nt' and not self.assigned:
                    self.process.kill()
                    self.process.wait(timeout=30)
                elif os.name == 'nt':
                    self.job.stop()
                    self.process.wait(timeout=30)
                else:
                    self.stop('startup-failed')
            if self.job:
                self.job.close()
            if isinstance(exc,Failure):
                exc.details.setdefault('ownership',self.ownership)
            raise
        finally:
            if self._input:
                self._input.close()

    def _windows_terminal(self,reason=None):
        actual = self.process.poll()
        self.job.stop()
        self.process.wait(timeout=30)
        for thread in self._threads:
            thread.join(timeout=5)
        if any(thread.is_alive() for thread in self._threads):
            raise Failure('process-tree-uncertain','Owned output threads have not stopped',ownership=self.ownership)
        if self._stream_errors:
            reason = reason or 'stream-error'
        code = 124 if reason == 'timeout' else actual if actual is not None else self.process.returncode
        if reason and code == 0:
            code = 125
        request = json.loads((self.directory/'request.json').read_bytes())
        proof = {'schema':1,**{k:request[k] for k in ('token','request_hash','owner')},'leader_pid':self.pid,
            'terminal':True,'tree_stopped':True,'exit_code':code,'reason':reason,'error':'; '.join(self._stream_errors) or None,
            'elapsed_seconds':time.monotonic()-self.started,'prompt_hash':request['prompt_hash'],'windows_job':True}
        proof['receipt_hash'] = hashlib.sha256(_encoded(proof)).hexdigest()
        _new(self.directory/'terminal.json',_encoded(proof))
        self.proof = terminal(self.ownership)
        self.returncode = self.proof['exit_code']
        return self.returncode

    def poll(self):
        if self.proof:
            return self.returncode
        if os.name == 'nt':
            reason = 'output-limit' if self._limit_event.is_set() else 'timeout' if time.monotonic() >= self.deadline else None
            if reason or self.process.poll() is not None:
                return self._windows_terminal(reason)
            return None
        if (self.directory/'terminal.json').exists():
            self.proof = terminal(self.ownership)
            self.returncode = self.proof['exit_code']
            return self.returncode
        if self.process.poll() is not None:
            if self.process.returncode == 69:
                raise Failure('process-supervision-unavailable','Supervisor could not establish Linux subreaper ownership',69,ownership=self.ownership)
            raise Failure('process-tree-uncertain','Supervisor exited without verified terminal proof',ownership=self.ownership)
        return None

    def wait(self,timeout=None):
        deadline = time.monotonic()+timeout if timeout is not None else self.deadline+45
        while self.poll() is None:
            if deadline is not None and time.monotonic() >= deadline:
                if timeout is None:
                    raise Failure('process-tree-uncertain','Pinned execution/cleanup budget expired without terminal proof',ownership=self.ownership)
                raise subprocess.TimeoutExpired(self.ownership,timeout)
            time.sleep(0.05)
        return self.returncode

    def stop(self,reason='cancelled'):
        if self.poll() is not None:
            return True
        if os.name == 'nt':
            self._windows_terminal(reason)
            return True
        expected = self.ownership.get('supervisor')
        current = _identity(self.pid)
        if not expected or current != expected:
            raise Failure('process-tree-uncertain','Supervisor identity changed before cancellation',ownership=self.ownership)
        cancellation = self.directory/'cancel.json'
        if not cancellation.exists():
            _new(cancellation,_encoded({'token':self.ownership['token'],'request_hash':self.ownership['request_hash'],
                                       'reason':reason if reason in ('timeout','cancelled','output-limit') else 'runner-error'}))
        # The supervisor polls this authenticated, atomically published request.
        # SIGTERM could otherwise kill it before its Python handlers are ready,
        # losing the only authority that can reap descendants and attest stop.
        try:
            self.wait(timeout=40)
        except subprocess.TimeoutExpired as exc:
            raise Failure('process-tree-uncertain','Supervisor retained because subtree stop is not confirmed',ownership=self.ownership) from exc
        return True

    def close(self):
        if self._closed:
            return
        self.proof = terminal(self.ownership)
        self.process.wait(timeout=5)
        if self.job:
            self.job.close()
        # Keep hashed ownership and terminal evidence for crash recovery; remove
        # the private request's raw environment/prompt only when explicitly released.
        self._closed = True

    def cleanup(self):
        self.close()
        for name in ('prompt.bin','request.json','terminal.json','cancel.json'):
            path = self.directory/name
            if path.exists():
                path.unlink()
        self.directory.rmdir()


def start_owned(argv,cwd,**kwargs):
    return OwnedProcess(argv,cwd,**kwargs)


def stop(process,job=None):
    if isinstance(process,OwnedProcess):
        return process.stop()
    if os.name == 'nt' and job and job.handle:
        job.stop()
        process.wait(timeout=30)
        return True
    raise Failure('process-supervision-required','A bare PID/process group cannot prove descendant termination',69)


def run_owned(argv,cwd,**kwargs):
    process = start_owned(argv,cwd,**kwargs)
    try:
        process.wait()
        return {'returncode':process.returncode,'proof':process.proof,'ownership':process.ownership,'pid':process.pid}
    except BaseException:
        process.stop()
        raise
    finally:
        process.close()
