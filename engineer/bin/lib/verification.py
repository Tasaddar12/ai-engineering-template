"""Revision-bound verification reports and argv-only command receipts."""
from pathlib import Path
import json
import re
import subprocess
import os
import hashlib
from . import config, records
from .core import Args, Failure, digest, load_json, now, planning_lock, read, root, run, safe_path, write, write_json
from .text import join_frontmatter, split_frontmatter


def configured_checks():
    configured = config.lookup(config.load(), "verification.commands", [])
    result = [config.normalize_check(original,index) for index,original in enumerate(configured)]
    names = [check["id"] for check in result]
    if len(names) != len(set(names)):
        raise Failure("duplicate-check-name", "Configured checks require unique names", 2)
    return result


def resolve_file(value):
    directory = records.phase_dir(value)
    matches = sorted(directory.glob("*-VERIFICATION.md"))
    if len(matches) > 1:
        raise Failure('ambiguous-verification-report',str(directory),2)
    return _safe(matches[0] if matches else directory/(directory.name.split("-")[0]+"-VERIFICATION.md"))


def status(args):
    value = args.arg(0, args.get("phase"))
    path = resolve_file(value)
    metadata, body = split_frontmatter(read(path))
    state = metadata.get("status", "not_started")
    phase = path.parent.name.split("-")[0]
    routes = {"passed": ("ship", "Publish verified work", f"/ship {phase}"),
              "gaps_found": ("fix", "Close verification gaps", f"/plan-phase {phase} --gaps"),
              "human_needed": ("human", "Complete human verification", f"/verify-work {phase}")}
    route, action, command = routes.get(state, ("verify", "Verify phase goal", f"/verify-work {phase}"))
    return {**metadata, "status": state, "path": str(path), "exists": path.exists(), "route": route,
            "next_action": action, "next_command": command}


def phase_fingerprint(directory, extra=()):
    report = resolve_file(directory)
    paths = list(directory.glob("*-PLAN.md"))+list(directory.glob("*-SUMMARY.md"))+list(directory.glob("*-CONTEXT.md"))
    if not isinstance(extra,(list,tuple)) or any(not isinstance(v,str) for v in extra):
        raise Failure('invalid-covered-files','Declare literal covered file paths',2)
    covered = list(extra)
    for path in list(paths):
        metadata, _ = split_frontmatter(read(_safe(path)))
        modified = metadata.get('files_modified',[])
        must = metadata.get('must_haves',{})
        if not isinstance(modified,list) or any(not isinstance(v,str) for v in modified) or not isinstance(must,dict) or not isinstance(must.get('artifacts',[]),list):
            raise Failure('invalid-phase-evidence-schema',str(path),2)
        covered.extend(modified)
        for artifact in must.get("artifacts", []):
            if isinstance(artifact, dict) and artifact.get("path"):
                covered.append(artifact["path"])
    paths.extend(_safe(p) for p in covered)
    phase = records.roadmap_phase(directory.name)
    ids = set(phase.get("requirements", []))
    requirement_lines = [re.sub(r"^\s*[-*]\s+\[[ xX]\]\s*", "", line) for line in read(records.planning()/"REQUIREMENTS.md").splitlines()
                         if not line.lstrip().startswith("|") and any(re.search(r"\b"+re.escape(identifier)+r"\b", line) for identifier in ids)]
    goal = json.dumps({"goal": phase.get("goal"), "depends_on": phase.get("depends_on"),
                       "requirements": sorted(ids), "wording": requirement_lines}, sort_keys=True)
    snapshot = _source_snapshot({'sources':[str(p) for p in paths if p != report]},excluded=(report,))
    return hashlib.sha256((snapshot['digest']+goal).encode()).hexdigest()


def current_evidence(value):
    directory = records.phase_dir(value)
    report = resolve_file(directory)
    metadata, body = split_frontmatter(read(report))
    head = run(["git", "rev-parse", "HEAD"], root()).stdout.strip()
    recorded = metadata.get("fingerprint")
    covered = metadata.get("covered_files", [])
    expected = phase_fingerprint(directory, covered)
    reasons = []
    if metadata.get("status") != "passed":
        reasons.append("verification has not passed")
    if not recorded or recorded != expected:
        reasons.append("verification fingerprint is absent or stale")
    revision = metadata.get("revision", metadata.get("verified_revision"))
    if not revision or run(["git", "merge-base", "--is-ancestor", str(revision), head], root(), check=False).returncode:
        reasons.append("verified revision is absent or outside current history")
    if revision and revision != head:
        commits = run(["git","rev-list",str(revision)+".."+head],root(),check=False)
        allowed = {report.relative_to(root()).as_posix()}
        stale = bool(commits.returncode)
        for commit in commits.stdout.splitlines():
            changed = run(["git","diff-tree","--root","--no-commit-id","--name-only","-r","-m",commit],root(),check=False)
            if changed.returncode or any(path and path not in allowed for path in changed.stdout.splitlines()):
                stale = True
        if stale:
            reasons.append("source changed since the frozen verification revision")
    if run(["git", "status", "--porcelain"], root()).stdout:
        reasons.append("working tree is dirty")
    settings = configured_checks()
    if settings:
        receipt_status = check_status(None)
        if receipt_status.get("passed") is not True:
            reasons.append("configured checks lack passing receipts at current HEAD")
    return {"current": not reasons, "reasons": reasons, "revision": head, "verified_revision": revision, "fingerprint": expected}


def fingerprint(args):
    directory = records.phase_dir(args.arg(0, args.get("phase")))
    report = resolve_file(directory)
    covered = args.all("files") + args.all("covered-files")
    with planning_lock():
        revision = _head()
        value = phase_fingerprint(directory, covered)
        metadata, body = split_frontmatter(read(report))
        metadata["fingerprint"] = value
        metadata.setdefault("status", "not_started")
        metadata["covered_files"] = covered
        if _head() != revision:
            raise Failure('revision-drift','HEAD changed while capturing phase evidence')
        metadata["revision"] = revision
        metadata.setdefault("phase", directory.name.split("-")[0])
        write(report, join_frontmatter(metadata, body))
    return {"fingerprint": value, "path": str(report)}


def append_audit(args):
    path = _safe(args.need())
    heading = str(args.get("heading", args.arg(1, "Audit")))
    block = str(args.get("body", args.get("content", args.arg(2, "")))).strip()
    if args.has("file"):
        block = read(_safe(args.get("file"))).strip()
    if not block:
        raise Failure("empty-audit", "Audit content cannot be empty", 2)
    section = "## "+heading+"\n\n"+block
    with planning_lock():
        content = read(path)
        sections = re.findall(r"(?ms)^## "+re.escape(heading)+r"\n(.*?)(?=^## |\Z)", content)
        if sections and sections[-1].strip() == block:
            return {"appended": False}
        write(path, content.rstrip()+"\n\n"+section+"\n")
    return {"appended": True, "path": str(path)}


def _safe(value):
    from .planning import safe
    return safe(root()/value)


def _hash(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()


def _head():
    return run(['git','rev-parse','HEAD'],root(),timeout=30).stdout.strip()


def _source_snapshot(check,excluded=()):
    """Expand literal inputs without following links or including receipt output."""
    declared = check.get('sources',check.get('inputs',[]))
    default = not declared
    if default:
        declared = run(['git','ls-files','--cached','--others','--exclude-standard','-z'],root(),timeout=30).stdout.split('\0')
    output = {}
    def collect(path):
        if path in excluded:
            return
        relative = path.relative_to(root()).as_posix()
        if relative == '.git' or relative.startswith('.git/'):
            raise Failure('check-git-input','Git administration is not a verification input',2)
        if relative.startswith(('.planning/verification-receipts/','.planning/verification/receipts/')) or relative in ('.planning/verification-receipts','.planning/verification/receipts'):
            return
        if default and (relative == '.planning' or relative.startswith('.planning/')):
            return
        path = _safe(relative)
        if path.is_dir():
            output[relative] = {'kind':'directory'}
            for child in sorted(path.iterdir(),key=lambda p:p.name):
                if child.name == '.git':
                    continue
                collect(child)
        elif path.is_file():
            output[relative] = {'kind':'file','sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
        elif path.exists():
            raise Failure('check-input-not-regular',relative,2)
        else:
            output[relative] = {'kind':'missing'}
    for value in declared:
        if value:
            collect(_safe(value))
    return {'digest':_hash(output),'entries':output}


def _environment(check,inherited=None):
    environment = dict(os.environ if inherited is None else inherited)
    environment['CI'] = 'true'
    declared = check.get('environment')
    if isinstance(declared,dict):
        environment.update(declared)
    names = sorted(declared if isinstance(declared,list) else environment)
    values = {key:environment.get(key) for key in names}
    return environment,{'names':names,'digest':_hash(values)}


def _binding(check,revision=None,inherited=None):
    revision = revision or _head()
    if not _safe(check.get('cwd','.')).is_dir():
        raise Failure('check-cwd-not-directory',check.get('id','check'),2)
    snapshot = _source_snapshot(check)
    environment,environment_key = _environment(check,inherited)
    spec = {k:v for k,v in check.items() if not k.startswith('_') and k != 'environment'}
    spec['environment'] = {'mode':'names' if isinstance(check.get('environment'),list) else 'mapping' if isinstance(check.get('environment'),dict) else 'inherited',
                           'declaration_hash':_hash(check.get('environment'))}
    specification_hash = _hash(spec)
    payload = {'specification_hash':specification_hash,'sources_hash':snapshot['digest'],'environment_hash':environment_key['digest'],
               'revision':revision if check.get('revision') else None}
    return {'fingerprint':_hash(payload),'specification_hash':specification_hash,'sources_hash':snapshot['digest'],
            'source_paths':sorted(snapshot['entries']),'environment_hash':environment_key['digest'],'environment_names':environment_key['names'],
            'environment':environment}


def check_fingerprint(check):
    return _binding(check)['fingerprint']


def _receipt_hash(receipt):
    return _hash({k:v for k,v in receipt.items() if k not in ('receipt_hash','reused','path','reusable')})


def _receipt_files():
    result = []
    def collect(directory):
        for child in directory.iterdir():
            child = _safe(child)
            if child.is_dir():
                collect(child)
            elif child.suffix == '.json' and child.name != 'current.json':
                result.append(child)
    for base in (records.planning()/'verification-receipts',records.planning()/'verification/receipts'):
        base = _safe(base)
        if base.exists():
            collect(base)
    return sorted(set(result))


def _valid_receipt(item,path):
    if not isinstance(item,dict) or item.get('schema') != 2 or item.get('receipt_id') != path.stem:
        return False
    if item.get('receipt_hash') != _receipt_hash(item) or item.get('status') not in ('passed','failed'):
        return False
    if not isinstance(item.get('exit_code'),int) or isinstance(item['exit_code'],bool) or (item['status'] == 'passed') != (item['exit_code'] == 0):
        return False
    if not isinstance(item.get('finished_ns'),int) or not isinstance(item.get('revision'),str):
        return False
    try:
        from . import processes
        proof = processes.terminal(item.get('process_ownership',{}))
        if proof != item.get('process_terminal') or proof['exit_code'] != item['exit_code']:
            return False
    except (Failure,OSError,ValueError,KeyError,TypeError):
        return False
    return all(isinstance(item.get(k),str) and re.fullmatch(r'[0-9a-f]{64}',item[k]) for k in ('fingerprint','specification_hash','sources_hash','environment_hash'))


def _compatible(item,check,binding,revision):
    if item.get('name') != check['id'] or item.get('fingerprint') != binding['fingerprint']:
        return False
    if any(item.get(k) != binding[k] for k in ('specification_hash','sources_hash','environment_hash')):
        return False
    if check.get('revision') or not check.get('reuse',True):
        return item['revision'] == revision
    return run(['git','merge-base','--is-ancestor',item['revision'],revision],root(),check=False,timeout=30).returncode == 0


def _load_receipts():
    valid,invalid = [],[]
    for path in _receipt_files():
        try:
            item = load_json(path)
            if not _valid_receipt(item,path):
                invalid.append(str(path))
            else:
                valid.append((item,path))
        except (OSError,ValueError,Failure):
            invalid.append(str(path))
    index_path = _safe(records.planning()/'verification-receipts/current.json')
    if not index_path.exists():
        # Orphan receipts from an interrupted publication never become current.
        return [],invalid
    try:
        index = load_json(index_path)
        if not isinstance(index,dict) or index.get('schema') != 2 or not isinstance(index.get('entries'),dict) or index.get('index_hash') != _hash({k:v for k,v in index.items() if k != 'index_hash'}):
            raise Failure('invalid-receipt-index',str(index_path))
        indexed = {item['receipt_id']:(item,path) for item,path in valid}
        current = []
        for name,entry in index['entries'].items():
            if not isinstance(entry,dict) or set(entry) != {'receipt_id','fingerprint'} or not isinstance(entry.get('receipt_id'),str):
                raise Failure('invalid-receipt-index',str(index_path))
            pair = indexed.get(entry['receipt_id'])
            if not pair or pair[0]['name'] != name or pair[0]['fingerprint'] != entry['fingerprint']:
                invalid.append('missing or modified current receipt: '+name)
            else:
                current.append(pair)
        return current,invalid
    except (ValueError,OSError,Failure):
        return [],[*invalid,str(index_path)]


def _selected(args,configured):
    values = args.all('checks') if args else []
    if args and args.has('checks') and not values:
        raise Failure('empty-check-selection','Name at least one configured check',2)
    if len(values) == 1 and values[0].startswith('['):
        values = args.json('checks')
    elif len(values) == 1 and ',' in values[0]:
        values = values[0].split(',')
    if not isinstance(values,list) or any(not isinstance(v,str) or not v for v in values) or len(values) != len(set(values)):
        raise Failure('invalid-check-selection','Use unique configured check names',2)
    unknown = set(values)-{v['id'] for v in configured}
    if unknown:
        raise Failure('unknown-check','Requested checks are not configured',2,checks=sorted(unknown))
    return [v for v in configured if not values or v['id'] in values]


def _current_damage(invalid):
    return any(value.startswith('missing or modified current receipt: ') or Path(value).name == 'current.json' for value in invalid)


def _redact(text,environment,declared=None):
    # Keep raw environment mappings out of receipts and redact echoed secret values.
    explicit = set(declared.values()) if isinstance(declared,dict) else {environment.get(key) for key in declared} if isinstance(declared,list) else set()
    values = sorted({value for key,value in environment.items() if value and (value in explicit or len(value) >= 4 or re.search(r'token|secret|password|credential|api.?key',key,re.I))},key=len,reverse=True)
    result = str(text)
    for value in values:
        result = result.replace(value,'[environment value]')
    return result


def _freeze_unchanged(checks,bindings,revision,settings):
    if _head() != revision:
        raise Failure('revision-drift','HEAD changed during the frozen verification run')
    current = config.load()['verification']
    if current != settings:
        raise Failure('verification-config-drift','Configured checks changed during the frozen run')
    for check in checks:
        if _binding(check,revision)['fingerprint'] != bindings[check['id']]['fingerprint']:
            raise Failure('verification-input-drift','Frozen check inputs or environment changed',check=check['id'])


def run_checks(args):
    from .locking import acquire
    args = args or Args([])
    common = run(['git','rev-parse','--path-format=absolute','--git-common-dir'],root(),timeout=30).stdout.strip()
    try:
        with acquire(Path(common)/'engineer/verification-run.lock',10):
            return _run_checks(args)
    except TimeoutError as exc:
        raise Failure('verification-run-owned','Another coordinator owns the frozen check run') from exc


def _run_checks(args):
    from concurrent.futures import ThreadPoolExecutor
    import time
    import uuid
    settings = config.load()['verification']
    checks = _selected(args,configured_checks())
    revision = _head()
    if not checks:
        return {'passed':None,'status':'not_configured','revision':revision,'checks':[],'count':0},69
    inherited = dict(os.environ)
    bindings = {check['id']:_binding(check,revision,inherited) for check in checks}
    _freeze_unchanged(checks,bindings,revision,settings)
    previous,invalid = _load_receipts()
    results = {}
    queued = []
    for check in checks:
        binding = bindings[check['id']]
        candidates = [item for item,path in previous if _compatible(item,check,binding,revision)]
        latest = max(candidates,key=lambda item:item['finished_ns'],default=None)
        if latest and latest['status'] == 'passed' and not _current_damage(invalid) and settings['reuse'] and check['reuse'] and not args.has('force'):
            results[check['id']] = {**latest,'reused':True,'reusable':True}
        else:
            queued.append(check)
    def execute(check):
        started = now()
        binding = bindings[check['id']]
        execution = {**check,'_execution_environment':binding['environment']}
        try:
            code,stdout,stderr = _execute_check(execution)
        except OSError as exc:
            code,stdout,stderr = 127,'',str(exc)
        except Failure as exc:
            if exc.code != 'command-timeout':
                raise
            code,stdout,stderr = 124,'',exc.message
        finished_ns = time.time_ns()
        receipt = {'schema':2,'receipt_id':str(finished_ns)+'-'+uuid.uuid4().hex,'name':check['id'],
            'argv':[_redact(v,binding['environment'],check.get('environment')) for v in check['argv']],
            'cwd':str(_safe(check['cwd']).relative_to(root())),'revision':revision,'fingerprint':binding['fingerprint'],
            'specification_hash':binding['specification_hash'],'sources_hash':binding['sources_hash'],
            'source_paths':binding['source_paths'],'environment_hash':binding['environment_hash'],'environment_names':binding['environment_names'],
            'started':started,'finished':now(),'finished_ns':finished_ns,'exit_code':code,'timed_out':code == 124,
            'stdout':_redact(stdout,binding['environment'],check.get('environment')),'stderr':_redact(stderr,binding['environment'],check.get('environment')),
            'status':'passed' if code == 0 else 'failed','required':check['required'],'independent':check['independent'],
            'resources':check['resources'],'exact_revision':check['revision'],'reuse_allowed':settings['reuse'] and check['reuse'],
            'process_ownership':execution.get('_process_ownership'),'process_terminal':execution.get('_process_terminal')}
        receipt['receipt_hash'] = _receipt_hash(receipt)
        return receipt
    # Consecutive independent checks may share a wave only with disjoint resources.
    cursor = 0
    with ThreadPoolExecutor(max_workers=settings['max_parallel']) as executor:
        while cursor < len(queued):
            _freeze_unchanged(checks,bindings,revision,settings)
            if not queued[cursor]['independent']:
                current = queued[cursor]
                results[current['id']] = execute(current)
                cursor += 1
                continue
            end = cursor
            while end < len(queued) and queued[end]['independent']:
                end += 1
            pending = list(queued[cursor:end])
            while pending:
                resources,wave = set(),[]
                for check in pending:
                    if len(wave) < settings['max_parallel'] and not resources.intersection(check['resources']):
                        wave.append(check)
                        resources.update(check['resources'])
                futures = [(check,executor.submit(execute,check)) for check in wave]
                # Wait for the entire wave, including failures, before any publication.
                errors = []
                for check,future in futures:
                    try:
                        results[check['id']] = future.result()
                    except BaseException as exc:
                        errors.append(exc)
                if errors:
                    raise errors[0]
                pending = [check for check in pending if check not in wave]
                _freeze_unchanged(checks,bindings,revision,settings)
            cursor = end
    _freeze_unchanged(checks,bindings,revision,settings)
    with planning_lock():
        _freeze_unchanged(checks,bindings,revision,settings)
        entries = {item['name']:{'receipt_id':item['receipt_id'],'fingerprint':item['fingerprint']} for item,path in previous}
        for check in checks:
            receipt = results[check['id']]
            if receipt.get('reused'):
                continue
            path = _safe(records.planning()/'verification-receipts'/(receipt['receipt_id']+'.json'))
            if path.exists():
                raise Failure('immutable-receipt-conflict',str(path))
            write_json(path,receipt)
        for check in checks:
            receipt = results[check['id']]
            entries[check['id']] = {'receipt_id':receipt['receipt_id'],'fingerprint':receipt['fingerprint']}
        index = {'schema':2,'revision':revision,'updated':now(),'entries':entries}
        index['index_hash'] = _hash(index)
        write_json(_safe(records.planning()/'verification-receipts/current.json'),index)
    ordered = [{**results[check['id']],'reused':results[check['id']].get('reused',False),
                'reusable':settings['reuse'] and check['reuse']} for check in checks]
    required = [v for v in ordered if v['required']] or ordered
    passed = all(v['status'] == 'passed' for v in required)
    return {'passed':passed,'status':'passed' if passed else 'failed','revision':revision,'checks':ordered,'count':len(ordered),
            'invalid_receipts':invalid,'frozen':True,'max_parallel':settings['max_parallel']},int(not passed)


def check_status(args):
    settings = config.load()['verification']
    checks = _selected(args,configured_checks())
    revision = _head()
    if not checks:
        return {'revision':revision,'receipts':[],'invalid_receipts':[],'configured':False,'passed':None,'status':'not_configured'}
    bindings = {check['id']:_binding(check,revision) for check in checks}
    previous,invalid = _load_receipts()
    selected,missing = [],[]
    for check in checks:
        candidates = [item for item,path in previous if _compatible(item,check,bindings[check['id']],revision) and
                      (settings['reuse'] or item['revision'] == revision)]
        latest = max(candidates,key=lambda item:item['finished_ns'],default=None)
        if latest:
            selected.append({**latest,'reusable':settings['reuse'] and check['reuse']})
        elif check['required']:
            missing.append(check['id'])
    _freeze_unchanged(checks,bindings,revision,settings)
    required = [check for check in checks if check['required']] or checks
    passing = {item['name'] for item in selected if item['status'] == 'passed'}
    passed = not _current_damage(invalid) and {check['id'] for check in required}.issubset(passing)
    return {'revision':revision,'receipts':selected,'invalid_receipts':invalid,'configured':True,'passed':passed,
            'status':'passed' if passed else 'missing_or_failed','missing_checks':missing,'current_receipts_intact':not _current_damage(invalid)}


def _execute_check(check):
    """Capture bounded output only after shared owned-subtree terminal proof."""
    import tempfile
    from . import processes
    process = None
    try:
        with tempfile.TemporaryFile() as output,tempfile.TemporaryFile() as errors:
            process = processes.start_owned(check['argv'],_safe(check.get('cwd','.')),
                env=check.get('_execution_environment') or _environment(check)[0],stdin=subprocess.DEVNULL,
                stdout=output,stderr=errors,timeout=check.get('timeout',300),output_limit=1024*1024)
            code = process.wait()
            check['_process_ownership'],check['_process_terminal'] = process.ownership,process.proof
            output.seek(0)
            errors.seek(0)
            return code,output.read(1024*1024).decode('utf-8',errors='replace'),errors.read(1024*1024).decode('utf-8',errors='replace')
    except BaseException:
        if process is not None:
            process.stop('runner-error')
        raise
    finally:
        if process is not None and process.proof:
            process.close()
