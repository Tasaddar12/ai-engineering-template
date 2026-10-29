#!/usr/bin/env python3
"""Private Linux subreaper for one exact, owned runtime process attempt."""
import ctypes
import hashlib
import json
import os
from pathlib import Path
import selectors
import signal
import stat
import subprocess
import sys
import time


def encoded(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()


def identity(pid):
    try:
        fields = Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()
        return {'pid':pid,'start_ticks':int(fields[19]),'state':fields[0]}
    except (FileNotFoundError,ProcessLookupError):
        return None


def children(pid):
    result = set()
    try:
        tasks = list(Path('/proc',str(pid),'task').iterdir())
    except FileNotFoundError:
        return result
    for task in tasks:
        try:
            result.update(int(v) for v in (task/'children').read_text().split())
        except FileNotFoundError:
            continue
    return result


def descendants():
    pending = list(children(os.getpid()))
    result = {}
    while pending:
        pid = pending.pop()
        if pid in result:
            continue
        entry = identity(pid)
        if entry:
            result[pid] = entry
            pending.extend(children(pid))
    return result


def private_json(path,value):
    raw = encoded(value)
    temporary = path.with_name('.'+path.name+'.writing-'+str(os.getpid()))
    try:
        fd = os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,'O_NOFOLLOW',0),0o600)
        with os.fdopen(fd,'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary,path)
    finally:
        if temporary.exists():
            temporary.unlink()


def cancellation_reason(path,request):
    """An unreadable or invalid optional envelope cannot stop a live attempt."""
    try:
        if path.is_symlink() or not path.is_file():
            return None
        packet = json.loads(path.read_bytes())
    except (OSError,UnicodeDecodeError,json.JSONDecodeError):
        return None
    if isinstance(packet,dict) and packet.get('token') == request['token'] and packet.get('request_hash') == request['request_hash'] and packet.get('reason') in ('timeout','cancelled','output-limit','runner-error'):
        return packet['reason']
    return None


def supervise(request_path):
    if sys.platform != 'linux' or not Path('/proc/self/task').is_dir():
        raise RuntimeError('Linux /proc and child subreaper support are required')
    path = Path(request_path)
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise RuntimeError('Private request ownership/mode is invalid')
    raw = path.read_bytes()
    request = json.loads(raw)
    if request.get('schema') != 1 or request.get('uid') != os.getuid() or request.get('directory') != str(path.parent):
        raise RuntimeError('Request identity does not match its private owner')
    expected = {k:v for k,v in request.items() if k != 'request_hash'}
    if request.get('request_hash') != hashlib.sha256(encoded(expected)).hexdigest():
        raise RuntimeError('Request hash does not match its contents')
    owner = request['owner']
    actual_owner = identity(owner['pid'])
    if os.getppid() != owner['pid'] or not actual_owner or actual_owner['start_ticks'] != owner['start_ticks']:
        raise RuntimeError('Request owner exited or its PID was reused')
    libc = ctypes.CDLL(None,use_errno=True)
    if libc.prctl(36,1,0,0,0) != 0:  # PR_SET_CHILD_SUBREAPER
        raise RuntimeError('Cannot establish child subreaper ownership')
    flag = ctypes.c_int()
    if libc.prctl(37,ctypes.byref(flag),0,0,0) != 0 or flag.value != 1:
        raise RuntimeError('Child subreaper ownership was not confirmed')
    cancelled = []
    signal.signal(signal.SIGTERM,lambda *_:cancelled.append('cancelled'))
    signal.signal(signal.SIGINT,lambda *_:cancelled.append('cancelled'))
    proof_path = path.parent/'terminal.json'
    started = time.monotonic()
    observed = {}
    process = None
    selector = selectors.DefaultSelector()
    limit = request.get('output_limit')
    counts = {1:0,2:0}
    reason = None
    uncertain = None
    owner_exited = False
    def reap():
        while True:
            try:
                pid,status = os.waitpid(-1,os.WNOHANG)
            except ChildProcessError:
                return True
            if pid == 0:
                return False
            if process is not None and pid == process.pid:
                process.returncode = os.waitstatus_to_exitcode(status)
    def drain(wait=0):
        nonlocal reason
        for key,_ in selector.select(wait):
            chunk = os.read(key.fd,65536)
            if not chunk:
                selector.unregister(key.fd)
                key.fileobj.close()
                continue
            destination = key.data
            available = max(0,limit-counts[destination])
            selected = chunk[:available]
            while selected:
                selected = selected[os.write(destination,selected):]
            counts[destination] += len(chunk)
            if counts[destination] > limit:
                reason = reason or 'output-limit'
    def stop_all():
        # Killing a parent adopts its setsid/double-fork descendants here. Repeat
        # until the kernel reports ECHILD, not merely an absent process group.
        deadline = time.monotonic()+30
        while time.monotonic() < deadline:
            current = descendants()
            observed.update({str(v['pid'])+':'+str(v['start_ticks']):v for v in current.values()})
            for entry in current.values():
                fresh = identity(entry['pid'])
                if fresh and fresh['start_ticks'] == entry['start_ticks']:
                    try:
                        os.kill(entry['pid'],signal.SIGKILL)
                    except ProcessLookupError:
                        pass
            no_children = reap()
            if limit is not None:
                drain(0)
            if no_children and not children(os.getpid()):
                return True
            time.sleep(0.02)
        return False
    try:
        options = {'stdout':subprocess.PIPE,'stderr':subprocess.PIPE} if limit is not None else {}
        process = subprocess.Popen(request['argv'],cwd=request['cwd'],env=request['environment'],stdin=None,shell=False,**options)
        if limit is not None:
            for source,destination in ((process.stdout,1),(process.stderr,2)):
                os.set_blocking(source.fileno(),False)
                selector.register(source,selectors.EVENT_READ,destination)
        while True:
            current = descendants()
            observed.update({str(v['pid'])+':'+str(v['start_ticks']):v for v in current.values()})
            reap()
            if process.returncode is not None:
                # Give already-finishing descendants a bounded opportunity to
                # flush their pipes before classifying them as leftover workers.
                finish_deadline = time.monotonic()+0.25
                while children(os.getpid()) and time.monotonic() < finish_deadline:
                    if limit is not None:
                        drain(0.02)
                    else:
                        time.sleep(0.02)
                    reap()
                if any(v['state'] != 'Z' for v in descendants().values()):
                    reason = reason or 'descendants-after-leader'
                break
            parent = identity(owner['pid'])
            if os.getppid() != owner['pid'] or not parent or parent['start_ticks'] != owner['start_ticks']:
                # A crashed caller does not abandon the healthy host. This private
                # supervisor keeps ownership until completion or its pinned budget.
                owner_exited = True
            if cancelled:
                reason = 'cancelled'
            # The durable request may precede this interpreter's signal setup.
            # Poll it independently so a caller never needs to signal bootstrap.
            requested_reason = cancellation_reason(path.parent/'cancel.json',request)
            if requested_reason:
                reason = requested_reason
            if not reason and time.monotonic() >= request['deadline']:
                reason = 'timeout'
            if reason:
                break
            if limit is not None:
                drain(0.05)
            else:
                time.sleep(0.05)
    except BaseException as exc:
        reason = reason or 'launch-or-supervision-error'
        uncertain = type(exc).__name__+': '+str(exc)
    stopped = False
    try:
        stopped = stop_all()
        if stopped and limit is not None:
            deadline = time.monotonic()+5
            while selector.get_map() and time.monotonic() < deadline:
                drain(0.02)
            if selector.get_map():
                stopped = False
                uncertain = 'Output streams did not close after descendant termination'
    except BaseException as exc:
        uncertain = type(exc).__name__+': '+str(exc)
    finally:
        selector.close()
    code = process.returncode if process is not None else 127
    if uncertain:
        reason = reason or 'supervision-error'
    if reason == 'timeout':
        code = 124
    elif reason and code == 0:
        code = 125
    proof = {'schema':1,'token':request['token'],'request_hash':request['request_hash'],'owner':owner,
        'supervisor':identity(os.getpid()),'leader_pid':process.pid if process else None,'terminal':stopped,'tree_stopped':stopped,
        'exit_code':code,'reason':reason,'error':uncertain,'observed':list(observed.values()),'elapsed_seconds':time.monotonic()-started,
        'output_bytes':counts,'prompt_hash':request.get('prompt_hash'),'owner_exited':owner_exited}
    proof['receipt_hash'] = hashlib.sha256(encoded(proof)).hexdigest()
    private_json(proof_path,proof)
    return 0 if stopped else 70


def main():
    try:
        return supervise(sys.argv[1])
    except BaseException as exc:
        # No receipt is preferable to a fabricated tree-stopped claim.
        print('process supervision unavailable: '+str(exc),file=sys.stderr)
        return 69


if __name__ == '__main__':
    raise SystemExit(main())
