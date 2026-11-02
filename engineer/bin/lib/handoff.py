"""Role-aware, source-bound continuation packets and measured context limits."""
import hashlib
import json
import re
from . import config, records
from .core import Failure, input_json, load_json, now, planning_lock, read, root, run, write_json


def limits(args=None):
    settings = config.load()
    window = settings.get('context_window', 200000)
    percent = config.lookup(settings, 'handoff.context_percent', 60)
    ceiling = config.lookup(settings, 'handoff.context_tokens', 250000)
    if isinstance(window,bool) or not isinstance(window,int) or window < 1 or isinstance(ceiling,bool) or not isinstance(ceiling,int) or ceiling < 1 or isinstance(percent,bool) or not isinstance(percent,(int,float)) or not 0 < percent <= 100:
        raise Failure('invalid-handoff-limits', 'Expected positive token limits and a percentage in (0,100]', 2)
    threshold = min(int(window*percent/100), ceiling)
    result = {'enabled': config.lookup(settings,'handoff.enabled',True), 'context_window': window,
        'context_percent': percent, 'context_tokens': ceiling, 'threshold_percent': percent, 'token_ceiling': ceiling,
        'binding': 'percent' if window*percent/100 <= ceiling else 'ceiling', 'threshold_tokens': threshold,
        'measurement_available': False, 'automatic_stop': False}
    if args and (args.has('used-tokens') or args.has('remaining-tokens')):
        try:
            used = int(args.get('used-tokens')) if args.has('used-tokens') else window-int(args.get('remaining-tokens'))
        except (ValueError,TypeError) as exc:
            raise Failure('invalid-token-measurement', 'Supply an integer observed token count', 2) from exc
        if not 0 <= used <= window:
            raise Failure('invalid-token-measurement', 'Observed tokens must fit the configured context window', 2)
        result.update(measurement_available=True, used_tokens=used, remaining_tokens=window-used,
                      threshold_reached=bool(result['enabled']) and used >= threshold, measurement_source='caller')
    return result


def path_for(identifier):
    identifier = str(identifier or '').removesuffix('.json')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,119}', identifier) or '..' in identifier:
        raise Failure('invalid-handoff-id', identifier, 2)
    from .planning import safe
    return safe(records.planning()/'handoffs'/(identifier+'.json'))


def fingerprint(entry):
    return hashlib.sha256(json.dumps({k:v for k,v in entry.items() if k not in ('packet_hash','path','continuation','binding_valid','binding_issues')}, sort_keys=True, separators=(',',':'),ensure_ascii=False).encode()).hexdigest()


def identity():
    revision = run(['git','rev-parse','HEAD'], root(), timeout=30).stdout.strip()
    branch = run(['git','symbolic-ref','--quiet','--short','HEAD'],root(),check=False,timeout=30).stdout.strip() or None
    common = run(['git','rev-parse','--path-format=absolute','--git-common-dir'], root(),timeout=30).stdout.strip()
    return {'root': str(root()), 'branch': branch, 'revision': revision, 'git_common_dir': common}


def verify(entry):
    if not isinstance(entry,dict) or not entry.get('id') or not entry.get('reason'):
        raise Failure('invalid-handoff-packet', 'Missing identity or reason')
    if entry.get('packet_hash') and entry['packet_hash'] != fingerprint(entry):
        raise Failure('handoff-tampered', entry['id'])
    captured = entry.get('source', {'root':entry.get('worktree'),'revision':entry.get('revision')})
    current = identity()
    issues = []
    for key in ('root','git_common_dir','branch'):
        if key in captured and captured[key] != current[key]:
            issues.append(key+' changed')
    revision = captured.get('revision')
    if not revision or run(['git','merge-base','--is-ancestor',revision,current['revision']],root(),check=False,timeout=30).returncode:
        issues.append('captured revision is unavailable or not an ancestor')
    return issues


def packet(entry, path):
    issues = verify(entry)
    continuation = 'Resume role '+str(entry.get('role','unassigned'))+' in '+str(entry.get('source',{}).get('root',entry.get('worktree',root())))+'.\n'
    continuation += 'Read these rules and records before continuing: '+', '.join(entry.get('read_rules',[]))+'.\n'
    continuation += '\n'.join(key+': '+(json.dumps(entry[key],ensure_ascii=False) if isinstance(entry[key],(dict,list)) else str(entry[key]))
                              for key in ('scope','phase','plan','reason','completed','remaining','next','blockers','notes') if entry.get(key))
    return {**entry, 'path':str(path), 'continuation':continuation, 'binding_valid':not issues, 'binding_issues':issues,
            'execution_authorized':False}


FIELDS = {'reason','scope','phase','plan','agent','role','completed','remaining','next','blockers','notes','read_rules'}


def command(args, action):
    if action == 'limits':
        return limits(args)
    if action not in ('list','write','read','consume'):
        raise Failure('unknown-handoff-action', action, 2)
    directory = records.planning()/'handoffs'
    if action == 'list':
        result, invalid = [], []
        for path in sorted(directory.glob('*.json')):
            if path.name.startswith('.'):
                continue
            try:
                path = path_for(path.stem)
                entry = load_json(path)
                if not entry.get('consumed'):
                    result.append(packet(entry,path))
            except (Failure,ValueError,OSError,TypeError,AttributeError) as exc:
                invalid.append({'id':path.stem,'error':str(exc)})
        return {'handoffs':result,'count':len(result),'invalid':invalid}
    identifier = args.arg(0,args.get('id'))
    path = path_for(identifier)
    with planning_lock():
        entry = load_json(path)
        from .planning import safe
        consumed_path = safe(directory/'consumed'/path.name)
        if entry is None and consumed_path.exists():
            consumed = load_json(consumed_path)
            issues = verify(consumed)
            if action == 'consume':
                if issues:
                    raise Failure('handoff-source-mismatch','; '.join(issues))
                if args.has('packet-hash') and args.get('packet-hash') not in (consumed.get('packet_hash'),consumed.get('consumed_from_hash')):
                    raise Failure('handoff-changed','The supplied packet hash does not match the archived packet')
                return {'consumed':True,'already_consumed':True,'id':path.stem,'path':str(consumed_path),'execution_authorized':False}
            if action == 'write':
                raise Failure('handoff-consumed','Use a new ID for a new continuation packet')
        if action == 'write':
            fields = input_json(args.get('file')) if args.has('file') else args.json('fields',{})
            if not isinstance(fields,dict) or set(fields)-FIELDS:
                raise Failure('invalid-handoff-fields', 'Only declared continuation fields are accepted', 2)
            for key in FIELDS:
                option = key.replace('_','-')
                if args.has(option):
                    fields[key] = args.get(option)
            if entry:
                issues = verify(entry)
                if issues:
                    raise Failure('handoff-source-mismatch', '; '.join(issues))
                if entry.get('consumed'):
                    raise Failure('handoff-consumed', path.stem)
            else:
                from .planning import safe
                canonical = ['AGENTS.md','CLAUDE.md','agents/AGENT.md','.planning/PROJECT.md','.planning/STATE.md']
                entry = {'schema':2,'id':path.stem,'created':now(),'history':[],
                    'scope':None,'phase':None,'plan':None,'role':None,'agent':None,
                    'completed':[],'remaining':[],'next':[],'blockers':[],'notes':[],
                    'read_rules':[p for p in canonical if safe(root()/p).is_file()]}
            if fields.get('role') is not None and fields['role'] not in config.ROLES:
                raise Failure('unsupported-handoff-role', str(fields['role']), 2)
            for key,value in fields.items():
                if key == 'read_rules':
                    if isinstance(value,str):
                        try:
                            value = json.loads(value)
                        except ValueError:
                            value = [value]
                    if not isinstance(value,list) or any(not isinstance(p,str) for p in value):
                        raise Failure('invalid-read-rules', 'Expected repository paths', 2)
                    from .planning import safe
                    value = [safe(root()/p).relative_to(root()).as_posix() for p in value]
                elif not isinstance(value,(str,list,dict)) or isinstance(value,bool):
                    raise Failure('invalid-handoff-field', key, 2)
                if key in entry and entry[key] != value:
                    entry.setdefault('history',[]).append({'at':now(),'field':key,'previous':entry[key],'replacement':value})
                entry[key] = value
            if not isinstance(entry.get('reason'),str) or not entry['reason'].strip():
                raise Failure('missing-handoff-reason', 'A new packet requires a nonempty reason', 2)
            if entry.get('role'):
                from .planning import safe
                role_path = 'agents/'+entry['role']+'.md'
                if safe(root()/role_path).is_file() and role_path not in entry['read_rules']:
                    entry['read_rules'].append(role_path)
            entry.update(updated=now(),consumed=False,source=identity(),execution_authorized=False)
            entry['revision'], entry['worktree'] = entry['source']['revision'],entry['source']['root']
            entry['packet_hash'] = fingerprint(entry)
            write_json(path,entry)
            return packet(entry,path)
        if not entry or entry.get('consumed'):
            raise Failure('handoff-not-found', path.stem)
        result = packet(entry,path)
        if action == 'read':
            return result
        if not result['binding_valid']:
            raise Failure('handoff-source-mismatch','; '.join(result['binding_issues']))
        if args.has('packet-hash') and args.get('packet-hash') != entry.get('packet_hash'):
            raise Failure('handoff-changed','Read the current packet before consuming it')
        entry.update(consumed=True,consumed_at=now(),consumed_from_hash=entry.get('packet_hash'))
        entry['packet_hash'] = fingerprint(entry)
        from .planning import safe
        destination = safe(directory/'consumed'/path.name)
        if destination.exists():
            archived = load_json(destination)
            verify(archived)
            old = {k:v for k,v in archived.items() if k not in ('consumed_at','packet_hash')}
            current = {k:v for k,v in entry.items() if k not in ('consumed_at','packet_hash')}
            if old != current:
                raise Failure('handoff-archive-conflict',str(destination))
            entry = archived
        write_json(destination,entry)
        path.unlink()
        return {'consumed':True,'id':entry['id'],'path':str(destination),'packet_hash':entry['packet_hash'],'execution_authorized':False}
