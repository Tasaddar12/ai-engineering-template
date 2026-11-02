"""Durable quick-batch DAG scheduling and evidence-bound item completion."""
from copy import deepcopy
import hashlib
import json
import re
import shlex
import sys
import uuid
from pathlib import Path
from . import config, records
from .core import Args, Failure, input_json, load_json, now, planning_lock, read, root, run, slug, write, write_json
from .text import join_frontmatter, split_frontmatter

TERMINAL = {'complete','failed','human_needed','cancelled'}
ACTIVE = {'running','executing','verifying'}
STATUSES = {'pending','planned','ready','blocked','merged', *ACTIVE, *TERMINAL}
ALIASES = {'depends_on':'dependsOn','files_modified':'plannedFiles','planned_files':'plannedFiles',
           'files_deleted':'deletedFiles','failure_reason':'failureReason', 'dispatched_worktree':'dispatchedWorktree',
           'dispatched_branch':'dispatchedBranch','dispatched_base':'dispatchedBase','quick_id':'quickId'}
MUTABLE = {'dependsOn','plannedFiles','deletedFiles','status','failureReason','dispatchedWorktree','dispatchedBranch',
           'dispatchedBase','agentId','researchStatus','researchPath','researchWarning','plannerStatus','checkerStatus',
           'verificationStatus','verificationPath','verificationRevision','mergeCommit','commit','notes','retryReason'}


def integer(value, name, minimum=1):
    if isinstance(value,bool) or not re.fullmatch(r'\d+',str(value)) or int(value) < minimum:
        raise Failure('invalid-concurrency' if name in ('jobs','capacity','task-count','in-flight') else 'invalid-integer', name+' must be an integer >= '+str(minimum), 2)
    return int(value)


def capacity(args=None):
    return integer(config.lookup(config.load(),'quick_batch.capacity',3),'capacity')


def batch_path(identifier):
    if not isinstance(identifier,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,119}',identifier) or '..' in identifier:
        raise Failure('invalid-batch-id',str(identifier),2)
    from .planning import safe
    current = safe(records.planning()/'quick-batches'/identifier/'BATCH.json')
    previous = safe(records.planning()/'quick/batches'/(identifier+'.json'))
    if current.exists() and previous.exists():
        raise Failure('ambiguous-batch-storage',identifier)
    return previous if previous.exists() else current


def batch(args):
    identifier = args.arg(0,args.get('batch',args.get('id')))
    path = batch_path(identifier)
    data = load_json(path)
    if not isinstance(data,dict) or data.get('id',data.get('batchId')) != identifier or not isinstance(data.get('items'),list):
        raise Failure('batch-not-found' if data is None else 'invalid-batch-manifest',str(identifier))
    identities = [str(item.get('quickId')) for item in data['items']]
    if len(identities) != len(set(identities)) or any(v in ('None','') for v in identities):
        raise Failure('invalid-batch-identities',str(identifier))
    for item in data['items']:
        if item.get('status') not in STATUSES:
            raise Failure('invalid-item-status',str(item.get('status')))
        item['dependsOn'] = ids(item.get('dependsOn',[]),'dependsOn')
        item['plannedFiles'] = paths(item.get('plannedFiles',[]))
        item['deletedFiles'] = paths(item.get('deletedFiles',[]))
        from .planning import safe
        directory = safe(item.get('directory',''))
        if directory.parent != records.planning()/'quick' or not directory.name.startswith(str(item['quickId'])+'-'):
            raise Failure('invalid-batch-item-directory',str(directory))
    validate_graph({str(v['quickId']):v['dependsOn'] for v in data['items']})
    return path,data


def json_array(args,key):
    value = input_json(args.get(key+'-file')) if args.has(key+'-file') else args.json(key,[])
    if not isinstance(value,list):
        raise Failure('invalid-array','--'+key+' must be a JSON array',2)
    return value


def ids(value,name):
    if not isinstance(value,list) or any(not isinstance(v,str) or not v for v in value) or len(set(value)) != len(value):
        raise Failure('invalid-id-array',name,2)
    return value


def parse(args):
    raw = sys.stdin.read() if args.has('stdin') else args.arg(0,'')
    try:
        lexer = shlex.shlex(raw,posix=True,punctuation_chars=False)
        lexer.whitespace_split,lexer.commenters = True,''
        tokens = list(lexer)
    except ValueError as exc:
        raise Failure('invalid-batch-arguments',str(exc),2) from exc
    result = {'tasks':[],'jobs':'auto','validate':False,'research':False,'resume':None,'file':None}
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token in ('--validate','--research'):
            result[token[2:]] = True
        elif token in ('--jobs','--resume','--file'):
            index += 1
            if index == len(tokens) or tokens[index].startswith('--'):
                raise Failure('missing-option-value',token,2)
            result[token[2:]] = tokens[index]
        elif token.startswith('--'):
            raise Failure('unknown-option',token,2)
        else:
            result['tasks'].append(token)
        index += 1
    if result['jobs'] != 'auto':
        result['jobs'] = integer(result['jobs'],'jobs')
    if result['resume'] and (result['file'] or result['tasks']):
        raise Failure('resume-task-conflict','Resume cannot replace the original task list',2)
    if result['file'] and result['tasks']:
        raise Failure('task-input-conflict','Choose a file or inline task list',2)
    result['inlineTaskList'] = ' '.join(result['tasks'])
    result['taskFile'] = result['file']
    return result


def source_tasks(args):
    if args.has('tasks'):
        tasks = args.json('tasks')
    elif args.has('file'):
        path = Path(str(args.get('file'))).expanduser()
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 10*1024*1024:
            raise Failure('invalid-task-file','Expected a bounded regular task file',2)
        text = path.read_text(encoding='utf-8-sig')
        try:
            tasks = json.loads(text)
        except ValueError:
            lines = [line for line in text.splitlines() if line.strip() and not line.lstrip().startswith('#')]
            if any(not re.match(r'^\s*(?:[-*+]\s+|\d+[.)]\s+)\S',line) for line in lines):
                raise Failure('invalid-task-list','Use a JSON array or a bulleted/numbered list',2)
            tasks = [re.sub(r'^\s*(?:[-*+]\s+|\d+[.)]\s+)','',line).strip() for line in lines]
    else:
        raise Failure('missing-task-input','Supply --file or --tasks JSON',2)
    if isinstance(tasks,dict):
        if set(tasks)-{'tasks'}:
            raise Failure('unknown-task-list-fields',str(sorted(set(tasks)-{'tasks'})),2)
        tasks = tasks.get('tasks')
    if not isinstance(tasks,list) or len(tasks) < 2:
        raise Failure('invalid-tasks','A quick batch requires at least two items',2)
    result = []
    for index,value in enumerate(tasks):
        value = {'description':value} if isinstance(value,str) else value
        if not isinstance(value,dict) or set(value)-{'id','description','title','dependsOn','depends_on','plannedFiles','files_modified','files_deleted','deletedFiles'}:
            raise Failure('invalid-task-fields',str(index),2)
        title = value.get('description',value.get('title'))
        if not isinstance(title,str) or not title.strip() or '\x00' in title:
            raise Failure('invalid-task-description',str(index),2)
        key = str(value.get('id',index+1))
        result.append({'sourceId':key,'description':title.strip(),
            'dependsOn':ids(value.get('dependsOn',value.get('depends_on',[])),'dependsOn'),
            'plannedFiles':paths(value.get('plannedFiles',value.get('files_modified',[]))),
            'deletedFiles':paths(value.get('deletedFiles',value.get('files_deleted',[])))})
    if len({v['sourceId'] for v in result}) != len(result):
        raise Failure('duplicate-task-id','Input task IDs must be unique',2)
    graph = {v['sourceId']:v['dependsOn'] for v in result}
    validate_graph(graph)
    return result


def paths(value):
    if not isinstance(value,list) or any(not isinstance(v,str) or not v or v == '.' or '\x00' in v for v in value):
        raise Failure('invalid-planned-files','Expected a path array',2)
    from .worktrees import scope_path
    return list(dict.fromkeys(scope_path(v) for v in value))


def validate_graph(graph):
    visited,active = set(),set()
    def visit(key):
        if key in active:
            raise Failure('batch-dependency-cycle',key,2)
        if key in visited:
            return
        active.add(key)
        for dependency in graph[key]:
            if dependency not in graph or dependency == key:
                raise Failure('invalid-batch-dependency',key+' -> '+dependency,2)
            visit(dependency)
        active.remove(key)
        visited.add(key)
    for key in graph:
        visit(key)


def overlap(first,second):
    return any(a == b or a.startswith(b.rstrip('/')+'/') or b.startswith(a.rstrip('/')+'/') for a in first for b in second)


def waves(data):
    graph = {str(item['quickId']):item.get('dependsOn',[]) for item in data['items']}
    validate_graph(graph)
    assigned,remaining = {},list(data['items'])
    while remaining:
        for item in list(remaining):
            identifier = str(item['quickId'])
            if not all(v in assigned for v in graph[identifier]):
                continue
            wave = max((assigned[v]+1 for v in graph[identifier]),default=0)
            files = item.get('plannedFiles',[])+item.get('deletedFiles',[])
            while any(other.get('wave') == wave and overlap(files,other.get('plannedFiles',[])+other.get('deletedFiles',[])) for other in data['items'] if str(other['quickId']) in assigned):
                wave += 1
            item['wave'],assigned[identifier] = wave,wave
            remaining.remove(item)


def packet(data,path,**extra):
    return {**data,'batchId':data.get('id',data.get('batchId')),'manifest':data,'path':str(path),**extra}


def create(args):
    tasks = source_tasks(args)
    identifier = args.get('id',now().replace(':','').replace('+','-')+'-'+uuid.uuid4().hex[:8])
    path = batch_path(identifier)
    source_hash = hashlib.sha256(json.dumps(tasks,sort_keys=True).encode()).hexdigest()
    revision = args.get('base-revision') or run(['git','rev-parse','HEAD'],root(),timeout=30).stdout.strip()
    canonical = run(['git','rev-parse','--verify',revision+'^{commit}'],root(),timeout=30).stdout.strip()
    with planning_lock():
        data = load_json(path)
        if data and (data.get('source_hash') != source_hash or data.get('base_revision') != canonical):
            raise Failure('batch-exists','The selected ID belongs to a different task list or base')
        if data and data.get('status') != 'initializing':
            return packet(data,path,reused=True)
        if not data:
            data = {'schema':2,'id':identifier,'created':now(),'status':'initializing','base_revision':canonical,
                'source_hash':source_hash,'source_root':str(root()),'validate':args.has('validate'),'research':args.has('research'),
                'items':[],'history':[]}
            write_json(path,data)
        for task in tasks:
            if any(v.get('sourceId') == task['sourceId'] for v in data['items']):
                continue
            source = {'batch':identifier,'task':task['sourceId'],'source_hash':source_hash}
            recovered = []
            from .planning import safe
            for record in (records.planning()/'quick').glob('*/QUICK.md'):
                metadata,_ = split_frontmatter(read(safe(record)))
                if metadata.get('source') == source:
                    recovered.append({**metadata,'quick_id':metadata['id'],'directory':str(record.parent)})
            if len(recovered) > 1:
                raise Failure('ambiguous-quick-allocation',task['sourceId'])
            quick = recovered[0] if recovered else records.quick_create(task['description'],{'source':source})
            data['items'].append({**task,'quickId':str(quick['quick_id']),'directory':quick['directory'],'status':'pending','wave':0,
                                  'created':now(),'history':[]})
            write_json(path,data)
        mapping = {v['sourceId']:v['quickId'] for v in data['items']}
        for item,task in zip(data['items'],tasks):
            item['dependsOn'] = [mapping[v] for v in task['dependsOn']]
        waves(data)
        data['status'],data['updated'] = 'pending',now()
        write_json(path,data)
    return packet(data,path)


def commit_exists(value):
    if not isinstance(value,str) or not re.fullmatch(r'[0-9a-fA-F]{7,64}',value):
        raise Failure('invalid-completion-commit',str(value),2)
    resolved = run(['git','rev-parse','--verify',value+'^{commit}'],root(),timeout=30).stdout.strip()
    if run(['git','merge-base','--is-ancestor',resolved,'HEAD'],root(),check=False,timeout=30).returncode:
        raise Failure('completion-commit-not-integrated',resolved)
    return resolved


def evidence(item,data,commit=None,require_verification=True):
    from .planning import safe
    directory = safe(item['directory'])
    expected = records.planning()/'quick'
    if directory.parent != expected:
        raise Failure('invalid-item-directory',str(directory))
    summary = safe(directory/(item['quickId']+'-SUMMARY.md'))
    metadata,body = split_frontmatter(read(summary))
    if not summary.is_file() or metadata.get('status') != 'complete' or not body.strip():
        raise Failure('batch-summary-incomplete',str(summary))
    revision = commit_exists(commit or item.get('mergeCommit') or item.get('commit'))
    if data.get('base_revision') and run(['git','merge-base','--is-ancestor',data['base_revision'],revision],root(),check=False,timeout=30).returncode:
        raise Failure('batch-commit-base-mismatch',revision)
    if revision == data.get('base_revision'):
        raise Failure('batch-no-implementation-commit',revision)
    # Require source changes in this attempt, rather than accepting an arbitrary old ancestor.
    changed = run(['git','diff','--name-only',data['base_revision'],revision],root(),check=False,timeout=30)
    actual = [p for p in changed.stdout.splitlines() if not p.startswith('.planning/')]
    if changed.returncode or not actual:
        raise Failure('batch-no-source-evidence',revision)
    plan = safe(directory/(item['quickId']+'-PLAN.md'))
    plan_metadata,_ = split_frontmatter(read(plan))
    if not plan.is_file() or not isinstance(plan_metadata.get('files_modified'),list):
        raise Failure('batch-plan-scope-missing',str(plan))
    scope = paths(plan_metadata['files_modified'])+paths(plan_metadata.get('files_deleted',[]))
    if not scope or not overlap(actual,scope):
        raise Failure('batch-no-item-source-evidence','The completion revision has no changes in this item plan scope')
    from .planning import section
    commits_section = section(body,'## Task Commits')
    citations = re.findall(r'(?<![A-Za-z0-9])[0-9a-fA-F]{7,64}(?![A-Za-z0-9])',body[commits_section[1]:commits_section[2]]) if commits_section else []
    declared = metadata.get('task_commits',metadata.get('commits',[]))
    if isinstance(declared,list):
        citations += [v for v in declared if isinstance(v,str)]
    if not citations:
        raise Failure('batch-task-commits-missing','SUMMARY must cite actual task commits')
    supported = False
    for citation in set(citations):
        resolved = commit_exists(citation)
        if run(['git','merge-base','--is-ancestor',resolved,revision],root(),check=False,timeout=30).returncode:
            raise Failure('batch-task-commit-not-integrated',citation)
        if run(['git','merge-base','--is-ancestor',resolved,data['base_revision']],root(),check=False,timeout=30).returncode == 0:
            raise Failure('batch-task-commit-predates-attempt',citation)
        touched = run(['git','diff-tree','--no-commit-id','--name-only','-r','--root',resolved],root(),timeout=30).stdout.splitlines()
        supported = supported or overlap(touched,scope)
    if not supported:
        raise Failure('batch-task-commits-outside-scope','No cited task commit changes the declared item scope')
    if require_verification and data.get('validate'):
        verification = safe(directory/(item['quickId']+'-VERIFICATION.md'))
        meta,_ = split_frontmatter(read(verification))
        captured = meta.get('revision',meta.get('verified_revision',meta.get('head')))
        if meta.get('status') != 'passed' or not captured or commit_exists(str(captured)) != revision:
            raise Failure('batch-verification-missing-or-stale',str(verification))
    return revision,summary


def apply_updates(data,updates):
    if not isinstance(updates,list) or not updates:
        raise Failure('invalid-batch-updates','Supply a nonempty array',2)
    indexed = {str(v['quickId']):v for v in data['items']}
    seen = set()
    for update in updates:
        if not isinstance(update,dict):
            raise Failure('invalid-item-update','Expected objects',2)
        normalized = {}
        for key,value in update.items():
            name = ALIASES.get(key,key)
            if name in normalized:
                raise Failure('duplicate-update-field',name,2)
            normalized[name] = value
        identifier = str(normalized.pop('quickId',None))
        if identifier not in indexed or identifier in seen:
            raise Failure('unknown-or-duplicate-batch-item',identifier,2)
        seen.add(identifier)
        if set(normalized)-MUTABLE:
            raise Failure('immutable-or-unknown-batch-field',','.join(sorted(set(normalized)-MUTABLE)),2)
        item = indexed[identifier]
        if item.get('completionTransaction') and any(item.get(k) != v for k, v in normalized.items()):
            raise Failure('completion-recovery-required', 'Resume the recorded completion before changing the item')
        if item['status'] in ACTIVE | {'merged','complete'} and any(key in normalized and item.get(key) != normalized[key] for key in ('dependsOn','plannedFiles','deletedFiles')):
            raise Failure('executing-item-scope-immutable',identifier)
        if item['status'] == 'complete' and any(item.get(k) != v for k,v in normalized.items()):
            raise Failure('completed-item-immutable',identifier)
        for key in ('dependsOn','plannedFiles','deletedFiles'):
            if key in normalized:
                normalized[key] = ids(normalized[key],key) if key == 'dependsOn' else paths(normalized[key])
        status = normalized.get('status',item['status'])
        if status not in STATUSES or status == 'complete' and item['status'] != 'complete':
            raise Failure('invalid-item-transition','Use complete with real evidence for completion',2)
        if status in ('failed','human_needed','cancelled') and not normalized.get('failureReason',item.get('failureReason')):
            raise Failure('missing-terminal-rationale',identifier,2)
        if item['status'] in TERMINAL and status not in TERMINAL and not normalized.get('retryReason'):
            raise Failure('retry-reason-required',identifier,2)
        candidate = {**item,**normalized}
        for key in ('dispatchedWorktree','dispatchedBranch','dispatchedBase'):
            if key in normalized and normalized[key] is not None and (not isinstance(normalized[key],str) or not normalized[key]):
                raise Failure('invalid-dispatch-metadata',key,2)
        if candidate.get('dispatchedWorktree'):
            from .worktrees import identity
            identity(candidate['dispatchedWorktree'],candidate.get('dispatchedBranch'))
            if not candidate.get('dispatchedBranch') or not candidate.get('dispatchedBase'):
                raise Failure('incomplete-dispatch-identity',identifier,2)
        for key in ('researchStatus','plannerStatus','checkerStatus'):
            if key in normalized and normalized[key] not in ('pending','running','complete','passed','failed','warning','skipped','human_needed'):
                raise Failure('invalid-lifecycle-status',key,2)
        for key in ('researchPath','verificationPath'):
            if candidate.get(key):
                from .planning import safe
                if not safe(candidate[key]).is_relative_to(safe(candidate['directory'])):
                    raise Failure('item-artifact-outside-directory',key,2)
        if status == 'merged':
            evidence(candidate,data,require_verification=False)
        if any(item.get(k) != v for k,v in normalized.items()):
            item.setdefault('history',[]).append({'at':now(),'changes':normalized,'previous':{k:item.get(k) for k in normalized}})
            item.update(normalized)
            item['updated'] = now()
    waves(data)


def reconcile(data):
    transitions = []
    indexed = {v['quickId']:v for v in data['items']}
    for _ in data['items']:
        changed = False
        for item in data['items']:
            failed = [v for v in item.get('dependsOn',[]) if indexed[v]['status'] in ('failed','cancelled','human_needed') or indexed[v].get('dependencyBlocked')]
            if failed and item['status'] in ('pending','planned','ready','blocked'):
                if item['status'] != 'blocked' or item.get('blockedBy') != failed:
                    transitions.append({'quickId':item['quickId'],'from':item['status'],'to':'blocked','dependencies':failed})
                    item.update(status='blocked',dependencyBlocked=True,blockedBy=failed)
                    changed = True
            elif not failed and item.get('dependencyBlocked'):
                transitions.append({'quickId':item['quickId'],'from':'blocked','to':'pending'})
                item.update(status='pending',dependencyBlocked=False,blockedBy=[])
                changed = True
        if not changed:
            break
    return transitions


def recover_completions(data):
    """Replay durable batch completion intents against authoritative QUICK.md records."""
    transitions = []
    for item in data['items']:
        transaction = item.get('completionTransaction')
        if item['status'] in TERMINAL or not transaction:
            continue
        revision, _ = evidence(item, data, transaction['commit'])
        records.quick(Args([item['quickId'], '--status', 'complete', '--commit', revision]), 'update')
        transitions.append({'quickId': item['quickId'], 'from': item['status'], 'to': 'complete',
                            'reason': 'recovered durable completion transaction', 'commit': revision})
        item.update(status='complete', commit=revision, completed=transaction['at'])
        item.pop('completionTransaction')
    return transitions


def complete(args,path,data):
    identifier = str(args.get('quick-id',args.arg(1,'')))
    matches = [v for v in data['items'] if v['quickId'] == identifier]
    if len(matches) != 1:
        raise Failure('unknown-batch-item',identifier,2)
    item = matches[0]
    if item['status'] == 'complete':
        return packet(data,path,already_complete=True,quickId=identifier)
    if item['status'] in ('failed','human_needed','cancelled','blocked'):
        raise Failure('item-not-completable',item['status'])
    for option,key in (('description','description'),('directory','directory')):
        if args.has(option) and str(args.get(option)) != str(item[key]):
            raise Failure('batch-identity-mismatch',option)
    revision,summary = evidence(item,data,args.get('commit'))
    if any(next(v for v in data['items'] if v['quickId'] == dep)['status'] != 'complete' for dep in item.get('dependsOn',[])):
        raise Failure('batch-dependencies-incomplete',identifier)
    date = args.get('date', now()[:10])
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', str(date)):
        raise Failure('invalid-completion-date', str(date), 2)
    transaction = item.get('completionTransaction')
    if transaction and transaction['commit'] != revision:
        raise Failure('quick-completion-conflict', identifier)
    item['completionTransaction'] = transaction or {'commit': revision, 'at': now()}
    write_json(path, data)
    records.quick(Args([identifier, '--status', 'complete', '--commit', revision]), 'update')
    item.pop('completionTransaction')
    item.setdefault('history',[]).append({'at':now(),'from':item['status'],'to':'complete','commit':revision,'summary':str(summary)})
    item.update(status='complete',commit=revision,completed=now())
    data['status'] = 'complete' if all(v['status'] in TERMINAL for v in data['items']) else 'pending'
    if data['status'] == 'complete':
        data['completed'] = now()
    data['updated'] = now()
    write_json(path,data)
    return packet(data,path,quickId=identifier,commit=revision)


def command(args,action):
    options = {
        'parse-args':{'stdin'}, 'effective-concurrency':{'jobs','capacity','task-count','isolation','mutating'},
        'filter-executed':{'eligible','executed','eligible-file','executed-file'},
        'merge-eligible':{'ready','wave-order','ready-file','wave-order-file'},
        'spawn-plan':{'in-flight','capacity','eligible','eligible-file'},
        'merge-routing':{'kind','detail'}, 'verification-routing':{'status'},
        'cleanup-entry':{'agent-id','worktree-path','branch','expected-base','allowed-bases','allowed-bases-file','plan-content','quick-id'},
        'create':{'file','tasks','id','base-revision','validate','research'},
        'resume':{'batch','id','current-base-revision'}, 'get':{'batch','id'}, 'list':set(),
        'update':{'batch','id','updates','updates-file'},
        'complete':{'batch','id','quick-id','description','date','commit','directory'},
    }
    if action not in options:
        raise Failure('unknown-batch-action',action,2)
    unknown = set(args.opts)-options[action]-{'raw','json','pick','ws'}
    if unknown:
        raise Failure('unknown-batch-options',','.join(sorted(unknown)),2)
    if action == 'parse-args':
        return parse(args)
    if action == 'effective-concurrency':
        cap = integer(args.get('capacity',capacity()),'capacity')
        requested = args.get('jobs','auto')
        jobs = cap if requested == 'auto' else integer(requested,'jobs')
        count = integer(args.get('task-count',1),'task-count',0)
        isolation = args.get('isolation','worktree')
        if isolation not in ('none','worktree','worktree-required','harness-worktree','orchestrator-worktree'):
            raise Failure('invalid-isolation',str(isolation),2)
        value = min(jobs,count,cap)
        if args.has('mutating') and isolation == 'none':
            value = min(value,1)
        return {'concurrency':value,'effective_concurrency':value,'capacity':cap,'requested':requested}
    if action in ('filter-executed','merge-eligible','spawn-plan'):
        if action == 'filter-executed':
            executed = set(ids(json_array(args,'executed'),'executed'))
            eligible = ids(json_array(args,'eligible'),'eligible')
            return {'spawnEligible':[v for v in eligible if v not in executed],'alreadyExecuted':[v for v in eligible if v in executed]}
        if action == 'merge-eligible':
            ready = set(ids(json_array(args,'ready'),'ready'))
            result = []
            for value in ids(json_array(args,'wave-order'),'wave-order'):
                if value not in ready:
                    break
                result.append(value)
            return {'mergeable':result}
        inflight = args.json('in-flight',[])
        count = len(ids(inflight,'in-flight')) if isinstance(inflight,list) else integer(inflight,'in-flight',0)
        available = max(0,integer(args.get('capacity',capacity()),'capacity')-count)
        eligible = ids(json_array(args,'eligible'),'eligible')
        return {'spawn':eligible[:available],'pending':eligible[available:],'available':available}
    if action == 'merge-routing':
        kind = args.get('kind')
        if kind not in ('merge_failed','conflict','scope_violation'):
            raise Failure('invalid-merge-kind',str(kind),2)
        return {'action':'retry' if kind == 'merge_failed' else 'block','retryable':kind == 'merge_failed','message':args.get('detail',kind),'preserveWorktree':True}
    if action == 'verification-routing':
        status = args.get('status')
        if status not in ('passed','human_needed','gaps_found','missing','stale','unparseable','phase_dir_not_found','failed','blocked'):
            raise Failure('invalid-verification-status',str(status),2)
        action = 'complete' if status == 'passed' else 'human_needed' if status == 'human_needed' else 'fail'
        return {'action':action,'route':action,'status':status,'failureReason':None if action == 'complete' else 'Verification: '+status}
    if action == 'cleanup-entry':
        from . import worktrees
        metadata,_ = split_frontmatter(str(args.get('plan-content','')))
        if not isinstance(metadata.get('files_modified'),list):
            raise Failure('missing-plan-scope','PLAN files_modified is required',2)
        path,branch,base = worktrees._canonical_entry({'worktree_path':args.get('worktree-path'),'branch':args.get('branch'),'expected_base':args.get('expected-base')})
        worktrees.identity(path,branch)
        owned = worktrees.owned(path)
        allowed = ids(json_array(args,'allowed-bases'),'allowed-bases')
        planned = paths(metadata['files_modified'])
        deleted = paths(metadata.get('files_deleted',[]))
        if owned.get('branch') != branch or owned.get('base') != base or base not in allowed or set(owned.get('files',[])) != set(planned) or set(owned.get('deletions',[])) != set(deleted):
            raise Failure('cleanup-entry-ownership-drift','Fresh PLAN scope must match the captured worktree ownership')
        if args.has('agent-id') and args.get('agent-id') != owned.get('agent_id'):
            raise Failure('cleanup-entry-agent-mismatch',str(args.get('agent-id')))
        return {**owned,'worktree_path':path,'path':path,'branch':branch,'expected_base':base,
                'allowed_bases':allowed,'plan_files':planned,'files_modified':planned,'files_deleted':deleted}
    if action == 'create':
        return create(args)
    if action not in ('resume','update','complete','list','get'):
        raise Failure('unknown-batch-action',action,2)
    if action == 'list':
        from .planning import safe
        paths_found = list((records.planning()/'quick-batches').glob('*/BATCH.json'))+list((records.planning()/'quick/batches').glob('*.json'))
        entries = [load_json(safe(p)) for p in sorted(paths_found)]
        return {'batches':entries,'count':len(entries)}
    with planning_lock():
        path,data = batch(args)
        if action == 'get':
            return packet(data,path)
        if data.get('status') == 'initializing':
            raise Failure('batch-initialization-incomplete','Repeat create with the same ID and original task input to recover')
        if action == 'complete':
            return complete(args,path,data)
        if action == 'update':
            candidate = deepcopy(data)
            apply_updates(candidate,json_array(args,'updates'))
            candidate['updated'] = now()
            write_json(path,candidate)
            return packet(candidate,path)
        current = args.get('current-base-revision') or run(['git','rev-parse','HEAD'],root(),timeout=30).stdout.strip()
        if run(['git','merge-base','--is-ancestor',data['base_revision'],current],root(),check=False,timeout=30).returncode:
            raise Failure('batch-base-diverged','The original base is not an ancestor of the current base')
        if data.get('source_root') and data['source_root'] != str(root()):
            raise Failure('batch-root-mismatch','Resume from the creating coordinator checkout')
        transitions = recover_completions(data)+reconcile(data)
        if transitions:
            data.setdefault('history',[]).extend({'at':now(),**v} for v in transitions)
            data['updated'] = now()
            if all(v['status'] in TERMINAL for v in data['items']):
                data['status'],data['completed'] = 'complete',now()
            write_json(path,data)
        indexed = {v['quickId']:v for v in data['items']}
        eligible = [v['quickId'] for v in data['items'] if v['status'] in ('pending','planned','ready') and all(indexed[d]['status'] == 'complete' for d in v.get('dependsOn',[]))]
        recovery = [{'quickId':v['quickId'],'worktree_path':v['dispatchedWorktree'],'branch':v.get('dispatchedBranch'),'expected_base':v.get('dispatchedBase')} for v in data['items'] if v.get('dispatchedWorktree')]
        return packet(data,path,eligible=eligible,transitions=transitions,in_flight=[v['quickId'] for v in data['items'] if v['status'] in ACTIVE],
                      done=[v['quickId'] for v in data['items'] if v['status'] in TERMINAL],base_drift=current != data['base_revision'],worktrees=recovery)
