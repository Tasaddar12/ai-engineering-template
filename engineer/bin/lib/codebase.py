"""Source-bound map stamps and advisory, measured drift reports."""
import hashlib
import re
from pathlib import Path
from . import config, records
from .core import Failure, digest, load_json, now, planning_lock, read, root, run, write, write_json
from .text import split_frontmatter


def git(*values, check=True):
    return run(['git', *values], root(), check=check, timeout=60)


def unavailable(reason, message=None):
    return ({'skipped': True, 'reason': reason, 'message': message or reason,
             'action_required': False, 'spawn_mapper': False, 'available': False}, 69)


def source_paths(prefixes=()):
    names = git('ls-files', '-co', '--exclude-standard', '-z').stdout.split('\0')
    result = []
    for name in sorted(set(names)):
        if not name or name.startswith(('.planning/', '.git/')):
            continue
        if prefixes and not any(name == p or name.startswith(p.rstrip('/')+'/') for p in prefixes):
            continue
        from .planning import safe
        path = safe(root()/name)
        if path.is_file():
            result.append(path)
    return result


def inputs(prefixes=()):
    prefixes = [p for p in prefixes if p != '.']
    paths = source_paths(prefixes)
    return {'digest': digest(paths, root()), 'paths': [p.relative_to(root()).as_posix() for p in paths]}


def prefixes(args):
    values = args.all('paths')
    if len(values) == 1:
        values = values[0].split(',')
    from .planning import safe
    result = []
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise Failure('invalid-map-path', str(value), 2)
        result.append(safe(root()/value).relative_to(root()).as_posix())
    return result


def map_hash(content):
    # Machine stamps are excluded; every other byte remains part of the map identity.
    return hashlib.sha256(re.sub(r'(?m)^(last_mapped_commit|last_mapped_at|map_input_hash):[^\n]*\n?', '', content).encode()).hexdigest()


def stamp(args):
    try:
        revision = git('rev-parse', 'HEAD').stdout.strip()
        directory = records.planning()/'codebase'
        names = args.all('files') or args.all('maps') or args.pos
        if len(names) == 1:
            names = names[0].split(',')
        if not names:
            names = [p.name for p in directory.glob('*.md')]
        if not names:
            return {'skipped': True, 'reason': 'no-map-documents', 'stamped': [], 'failed': []}
        from .planning import safe
        paths = []
        for name in names:
            name = name.strip()
            if not re.fullmatch(r'[A-Za-z0-9_-]+(?:\.md)?', name):
                raise Failure('invalid-map-name', name, 2)
            path = safe(directory/(name if name.endswith('.md') else name+'.md'))
            if not path.is_file():
                raise Failure('map-not-found', str(path), 2)
            paths.append(path)
        with planning_lock():
            selected = prefixes(args)
            captured = inputs(selected)
            manifest = load_json(safe(directory/'.freshness.json'), {'schema': 2, 'maps': {}})
            if not isinstance(manifest, dict) or not isinstance(manifest.get('maps'), dict):
                raise Failure('invalid-map-stamp', str(directory), 2)
            for path in paths:
                content = read(path)
                values = {'last_mapped_commit': revision, 'last_mapped_at': now(), 'map_input_hash': captured['digest']}
                if content.startswith('---\n') or content.startswith('---\r\n'):
                    match = re.match(r'\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)', content, re.S)
                    if not match:
                        raise Failure('invalid-map-frontmatter', str(path), 2)
                    head = match.group(1)
                    for key, value in values.items():
                        line = key+': '+value
                        head = re.sub(r'(?m)^'+key+r':[^\n]*', line, head) if re.search(r'(?m)^'+key+':', head) else head+'\n'+line
                    updated = '---\n'+head+'\n---\n'+content[match.end():]
                else:
                    updated = '---\n'+''.join(k+': '+v+'\n' for k,v in values.items())+'---\n'+content
                write(path, updated)
                manifest['maps'][path.name] = {'revision': revision, 'created': now(), 'paths': selected,
                    'input_hash': captured['digest'], 'input_paths': captured['paths'], 'map_hash': map_hash(updated)}
            manifest['schema'] = 2
            if git('rev-parse','HEAD').stdout.strip() != revision or inputs(selected)['digest'] != captured['digest']:
                raise Failure('map-source-changed-during-stamp','Source changed; refresh the map before stamping again',69)
            write_json(safe(directory/'.freshness.json'), manifest)
        return {'stamped': [p.name for p in paths], 'recorded': [p.name for p in paths], 'commit': revision, 'revision': revision, 'failed': [], 'input_hash': captured['digest']}
    except (Failure, OSError, ValueError) as exc:
        return unavailable('stamp-unavailable', str(exc))


def changed(revision):
    if git('merge-base', '--is-ancestor', revision, 'HEAD', check=False).returncode:
        raise Failure('map-source-not-ancestor', revision, 69)
    values = {}
    for argv in [('diff','--name-status','--no-renames',revision,'HEAD','-z'), ('diff','--name-status','--no-renames','HEAD','-z')]:
        fields = git(*argv).stdout.split('\0')
        for index in range(0, len(fields)-1, 2):
            values[fields[index+1]] = fields[index]
    for name in git('ls-files','--others','--exclude-standard','-z').stdout.split('\0'):
        if name:
            values[name] = 'A'
    return {p:s for p,s in values.items() if not p.startswith(('.planning/', '.git/'))}


def drift(args):
    try:
        directory = records.planning()/'codebase'
        if not (directory/'STRUCTURE.md').is_file():
            return {'skipped': True, 'reason': 'no-structure-map', 'action_required': False, 'spawn_mapper': False}
        data = load_json(directory/'.freshness.json', {'maps': {}})
        entry = data.get('maps', {}).get('STRUCTURE.md') or data.get('maps', {}).get('STRUCTURE')
        if not entry or not entry.get('input_hash'):
            return unavailable('missing-map-input-baseline', 'Run stamp-codebase-map after refreshing the map.')
        from .planning import safe
        structure = safe(directory/'STRUCTURE.md')
        if map_hash(read(structure)) != entry.get('map_hash'):
            return unavailable('map-edited-since-stamp', 'The map changed after its source baseline was captured.')
        revision = entry['revision']
        changes = changed(revision)
        selected = entry.get('paths', [])
        changes = {p:s for p,s in changes.items() if not selected or any(p == v or p.startswith(v.rstrip('/')+'/') for v in selected)}
        old_names = set(git('ls-tree','-r','--name-only',revision).stdout.splitlines())
        old_dirs = {str(parent).replace('\\','/') for name in old_names for parent in Path(name).parents if str(parent) != '.'}
        elements = {'new_directories': [], 'new_barrel_exports': [], 'new_migrations': [], 'new_route_modules': [], 'modified_files': [], 'deleted_files': []}
        for path, status in changes.items():
            candidate = Path(path)
            if status == 'D':
                elements['deleted_files'].append(path)
            elif status.startswith('A') or path not in old_names:
                elements['new_directories'].extend(str(p).replace('\\','/') for p in candidate.parents if str(p) != '.' and str(p).replace('\\','/') not in old_dirs)
                if candidate.stem in ('index', '__init__', 'mod', 'lib'):
                    elements['new_barrel_exports'].append(path)
                if 'migration' in path.lower():
                    elements['new_migrations'].append(path)
                if any(v in ('routes','route','pages','app') for v in candidate.parts[:-1]):
                    elements['new_route_modules'].append(path)
                # New ordinary files are also measurable structural additions.
                elements.setdefault('new_files', []).append(path)
            else:
                elements['modified_files'].append(path)
        elements = {k:sorted(set(v)) for k,v in elements.items()}
        settings = config.load()
        threshold = config.lookup(settings, 'workflow.drift_threshold', 3)
        action = config.lookup(settings, 'workflow.drift_action', 'warn')
        if isinstance(threshold, bool) or not isinstance(threshold, int) or threshold < 1 or action not in ('warn','auto-remap'):
            raise Failure('invalid-drift-config', 'Expected positive threshold and warn/auto-remap action', 69)
        count = sum(len(v) for v in elements.values())
        affected = sorted({str(Path(p).parent).replace('\\','/') for p in changes})
        allowed = [p for p in affected if re.fullmatch(r'[A-Za-z0-9_./-]+', p) and '..' not in p.split('/')]
        input_changed = inputs(selected)['digest'] != entry['input_hash']
        required = count >= threshold
        message = 'Codebase drift detected: '+str(count)+' structural element(s) since last mapping.\n'
        message += '\n'.join(k.replace('_',' ').capitalize()+':\n'+''.join('  - '+p+'\n' for p in v) for k,v in elements.items() if v)
        if len(allowed) != len(affected):
            message += '\n'+str(len(affected)-len(allowed))+' path(s) withheld from mapper hints.'
        message += '\nRun /map-codebase --paths '+','.join(allowed)+' to refresh planning context.'
        return {'skipped': False, 'available': True, 'reason': None, 'action_required': required, 'directive': action,
            'spawn_mapper': required and action == 'auto-remap' and bool(allowed), 'affected_paths': allowed,
            'elements': elements, 'element_count': count, 'threshold': threshold, 'action': action,
            'last_mapped_commit': revision, 'input_changed': input_changed, 'message': message if required else '',
            'source_revision': git('rev-parse','HEAD').stdout.strip(), 'fresh': not input_changed}
    except (Failure, OSError, ValueError, KeyError, TypeError) as exc:
        return unavailable('drift-unavailable', str(exc))


def context_drift(args):
    try:
        directory = records.phase_dir(args.need())
        context = directory/(directory.name.split('-')[0]+'-CONTEXT.md')
        if not context.is_file():
            matches = list(directory.glob('*CONTEXT.md'))
            context = matches[0] if len(matches) == 1 else context
        if not context.is_file():
            return {'skipped': True, 'reason': 'no-phase-context', 'stale_artifacts': [], 'block': False}
        from .planning import safe
        context = safe(context)
        metadata, _ = split_frontmatter(read(context))
        declared = args.all('paths') or metadata.get('source_paths', metadata.get('files', []))
        if isinstance(declared, str):
            declared = [declared]
        if not isinstance(declared, list) or any(not isinstance(p,str) for p in declared):
            raise Failure('invalid-context-paths', 'Declare a source_paths array', 69)
        declared = [safe(root()/p).relative_to(root()).as_posix() for p in declared]
        packet = {'context_hash': digest([context],root()), 'source_hash': inputs(declared)['digest'] if declared else None,
                  'source_paths': declared, 'revision': git('rev-parse','HEAD').stdout.strip()}
        baseline_path = safe(directory/'.context-freshness.json')
        if args.has('record') or args.has('stamp'):
            with planning_lock():
                packet['artifacts'] = {p.name:digest([safe(p)],root()) for p in directory.glob('*.md') if p != context}
                write_json(baseline_path, packet)
            return {'recorded': True, **packet}
        baseline = load_json(baseline_path)
        if not baseline:
            return {'skipped': True, 'reason': 'no-context-source-baseline', 'stale_artifacts': [], 'block': False,
                    'source_paths': declared, 'semantic_assessment': False}
        changed(baseline['revision'])
        if not declared and baseline.get('source_paths'):
            packet['source_paths'] = baseline['source_paths']
            packet['source_hash'] = inputs(baseline['source_paths'])['digest']
        premise_changed = any(packet.get(k) != baseline.get(k) for k in ('context_hash','source_hash','source_paths'))
        stale = []
        for name, original_hash in baseline.get('artifacts',{}).items():
            if Path(name).name != name or not name.endswith('.md'):
                raise Failure('invalid-context-artifact', str(name), 69)
            path = safe(directory/name)
            if premise_changed and path.is_file() and digest([path],root()) == original_hash:
                stale.append(name)
        action = config.lookup(config.load(), 'workflow.context_drift_action','warn')
        if action not in ('warn','block'):
            raise Failure('invalid-context-drift-action', str(action), 69)
        return {'skipped': False, 'stale_artifacts': stale, 'block': bool(stale) and action == 'block',
                'context_changed': packet['context_hash'] != baseline['context_hash'], 'source_changed': packet['source_hash'] != baseline.get('source_hash'),
                'source_paths': packet['source_paths'], 'semantic_assessment': False,
                'message': ('Context/source inputs changed; unchanged artifacts need regeneration: '+', '.join(stale)+'. Run /plan-phase '+str(args.need())+'.') if stale else ''}
    except (Failure, OSError, ValueError, TypeError, KeyError) as exc:
        return unavailable('context-drift-unavailable', str(exc))


def command(args, action):
    if action in ('record','stamp'):
        return stamp(args)
    if action in ('drift','codebase-drift'):
        return drift(args)
    if action in ('context-drift','context_drift'):
        return context_drift(args)
    if action != 'status':
        raise Failure('unknown-codebase-action', action, 2)
    try:
        from .planning import safe
        directory = records.planning()/'codebase'
        data = load_json(safe(directory/'.freshness.json'), {'maps': {}})
        result = []
        for name,entry in data['maps'].items():
            if Path(name).name != name:
                raise Failure('invalid-map-name',str(name))
            path = safe(directory/(name if name.endswith('.md') else name+'.md'))
            try:
                files = changed(entry['revision'])
                selected = entry.get('paths',[])
                files = [p for p in files if not selected or any(p == v or p.startswith(v.rstrip('/')+'/') for v in selected)]
                count = int(git('rev-list','--count',entry['revision']+'..HEAD').stdout.strip())
                available = bool(entry.get('input_hash') and entry.get('map_hash'))
                stale = not available or not path.is_file() or inputs(selected)['digest'] != entry['input_hash'] or map_hash(read(path)) != entry['map_hash']
                result.append({'name':name,**entry,'stale':stale,'available':available,'commits_since':count,'changed_files':files})
            except (Failure,OSError,ValueError,KeyError) as exc:
                result.append({'name':name,**entry,'stale':True,'available':False,'commits_since':None,'changed_files':[],'reason':str(exc)})
        packet = {'maps':result,'fresh':bool(result) and all(not item['stale'] for item in result),
                  'revision':git('rev-parse','HEAD').stdout.strip(),'available':all(item['available'] for item in result)}
        return (packet,69) if any(not item['available'] for item in result) else packet
    except (Failure,OSError,ValueError,KeyError,TypeError) as exc:
        return unavailable('map-status-unavailable',str(exc))

