import argparse
import json
from pathlib import Path
import sys

from orchestrate import Blocked, git, json_section, relative_path, require, validate


def compile_snapshot(repository, manifest, source_ref='HEAD', config_path='.ai/config.yaml'):
    try:
        import yaml
    except ImportError as exc:
        raise Blocked('Snapshot preparation requires PyYAML; install .ai/runtime/requirements-prepare.txt') from exc
    root = Path(repository).resolve()
    require(Path(git(root, 'rev-parse', '--show-toplevel')).resolve() == root, 'Use the exact checkout root')
    revision = git(root, 'rev-parse', '--verify', source_ref + '^{commit}')
    for name in (manifest, config_path):
        relative_path(name)
    try:
        config = yaml.safe_load(git(root, 'show', f'{revision}:{config_path}'))
    except yaml.YAMLError as exc:
        raise Blocked('Configuration is not valid YAML') from exc
    schedule = json_section(git(root, 'show', f'{revision}:{manifest}'), 'Execution schedule')
    require(isinstance(config, dict) and isinstance(schedule, dict), 'Configuration and schedule must be objects')
    allowed = {'run_id', 'remote', 'github_repo', 'worker_command', 'readiness_worker_command', 'tracks',
               'worker_timeout_seconds', 'check_timeout_seconds', 'github_timeout_seconds'}
    require(not (set(schedule) - allowed), 'Execution schedule duplicates configuration or contains unsupported fields: ' +
            ', '.join(sorted(set(schedule) - allowed)))
    orchestration = config['orchestration']
    require(orchestration['dispatch'] == 'background', 'Snapshot compiler requires background dispatch')
    require(orchestration['review']['max_rounds'] == 2 and orchestration['documentation']['max_review_rounds'] == 2,
            'Runtime requires exactly two code and two documentation review rounds')
    fixed_paths = {'plans': '.ai/plans', 'fixes': '.ai/fixes', 'specs': '.ai/specs',
                   'decisions': '.ai/decisions', 'amendments': '.ai/decisions/amendments',
                   'orchestration': '.ai/state/orchestration', 'research': '.ai/research'}
    require(all(config['paths'].get(key) == value for key, value in fixed_paths.items()),
            'Runtime requires the fixed record paths')
    fixed_ids = {'plan': 'PLAN-{nnn}-{slug}', 'fix': 'FIX-{nnn}-{slug}', 'intake': 'INTAKE-{nnn}-{slug}',
                 'spec': 'SPEC-{nnn}-{slug}', 'decision': 'ADR-{nnnn}-{slug}', 'amendment': 'AMD-{nnn}-{slug}'}
    require(all(config['ids'].get(key) == value for key, value in fixed_ids.items()),
            'Runtime requires the fixed record ID formats')
    primary = git(root, 'worktree', 'list', '--porcelain').splitlines()[0].removeprefix('worktree ')
    snapshot = {**schedule, 'protocol_version': 3, 'repository': str(Path(primary).resolve()),
                'done_partition': config['lifecycle']['done_partition'],
                'required_commands': config['verification']['commands'],
                'documentation_model': orchestration['documentation']['model'],
                'documentation_worker_command': orchestration['documentation']['worker_command']}
    for key in ('base_branch', 'branch_prefix', 'max_parallel_tracks', 'worktree_root', 'max_process_attempts',
                'forge', 'merge_strategy', 'auto_merge', 'cleanup_on_merge', 'required_status_checks'):
        snapshot[key] = orchestration[key]
    snapshot['sources'] = {'revision': revision, **{key: {'path': path, 'blob': git(root, 'rev-parse', f'{revision}:{path}')}
                           for key, path in (('configuration', config_path), ('manifest', manifest))}}
    return validate(snapshot)


def main():
    parser = argparse.ArgumentParser(description='Compile a committed configuration and ORCH manifest into a JSON snapshot on stdout.')
    parser.add_argument('manifest')
    parser.add_argument('--repository', type=Path, default=Path.cwd())
    parser.add_argument('--ref', default='HEAD')
    parser.add_argument('--config', default='.ai/config.yaml')
    args = parser.parse_args()
    try:
        snapshot = compile_snapshot(args.repository, args.manifest, args.ref, args.config)
        print(json.dumps(snapshot, indent=2))
        return 0
    except (Blocked, KeyError, TypeError, ValueError, OSError) as exc:
        print(f'Blocked: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
