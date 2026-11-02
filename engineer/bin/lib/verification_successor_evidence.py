"""Schema-2 adapter for prospective, read-only report-successor evidence."""
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import stat
import subprocess
import sys

from . import verification_successors as successors
from .core import Failure

STORE = '.planning/verification-receipts'
SCHEMA = 2


def bad(message):
    raise Failure('invalid-successor-evidence', message, 2)


def inventory(root):
    raw = successors.git(root, 'ls-files', '--cached', '--others', '--exclude-standard', '-z')
    return sorted({os.fsdecode(name) for name in raw.split(b'\0') if name
                   and os.fsdecode(name) != STORE and not os.fsdecode(name).startswith(STORE + '/')})


def source_paths(root, sources=None):
    if not sources:
        return inventory(root)
    result = set()
    for name in sources:
        path = successors.safe_path(root, name)
        if path.is_dir():
            for child in path.rglob('*'):
                relative = child.relative_to(root).as_posix()
                successors.safe_path(root, relative)
                if '.git' in child.relative_to(root).parts or relative.startswith(STORE + '/'):
                    continue
                if not child.is_dir():
                    result.add(relative)
        else:
            result.add(name)
    return sorted(result)


def file_fingerprint(root, paths, guarded=False):
    rows = successors.manifest(root, paths)
    if guarded:
        metadata = []
        for name in sorted(set(paths)):
            path = successors.safe_path(root, name)
            try:
                info = path.lstat()
                metadata.append([name, info.st_mtime_ns, info.st_ctime_ns, info.st_ino])
            except FileNotFoundError:
                metadata.append([name, 'missing'])
        return successors.digest([rows, metadata])
    return successors.digest(rows)


def directory_inputs(root, sources=None, guarded=False):
    """Bind declared root kinds and all descendant directories, including empty ones.

    File membership/content retains its independent pure-helper manifest. Times
    and inode identities guard only the current capture/execution/proof window;
    report publication is allowed to change ancestor-directory timestamps.
    """
    roots = sorted(set(sources or []))
    entries, metadata = {}, {}

    def excluded(name):
        return '.git' in name.split('/') or name == STORE or name.startswith(STORE + '/')

    def identity(info):
        return [stat.S_IMODE(info.st_mode), info.st_mtime_ns, info.st_ctime_ns, info.st_ino]

    def visit(name, declared=False):
        if excluded(name):
            if declared:
                raise ValueError('administrative storage is not a declared directory input')
            return
        path = successors.safe_path(root, name)
        try:
            info = path.lstat()
        except FileNotFoundError:
            entries[name] = [name, 'missing']
            metadata[name] = [name, 'missing']
            return
        if stat.S_ISDIR(info.st_mode):
            entries[name] = [name, 'directory', stat.S_IMODE(info.st_mode)]
            metadata[name] = [name, *identity(info)]
            for child in sorted(path.iterdir(), key=lambda value: value.name):
                relative = child.relative_to(root).as_posix()
                if excluded(relative):
                    continue
                child = successors.safe_path(root, relative)
                child_info = child.lstat()
                if stat.S_ISDIR(child_info.st_mode):
                    visit(relative)
                elif not stat.S_ISREG(child_info.st_mode):
                    raise ValueError('unsupported directory member: ' + relative)
            if identity(path.lstat()) != identity(info):
                raise ValueError('directory changed while capturing topology: ' + name)
        elif stat.S_ISREG(info.st_mode):
            if declared:
                entries[name] = [name, 'file', stat.S_IMODE(info.st_mode)]
                metadata[name] = [name, *identity(info)]
        else:
            raise ValueError('unsupported declared input kind: ' + name)

    for name in roots:
        visit(name, declared=True)
    # Cover overlapping roots and mutation after an earlier subtree was walked.
    for name, expected in sorted(metadata.items()):
        path = successors.safe_path(root, name)
        try:
            actual = [name, *identity(path.lstat())]
        except FileNotFoundError:
            actual = [name, 'missing']
        if actual != expected:
            raise ValueError('directory input moved while capturing topology: ' + name)
    rows = [entries[name] for name in sorted(entries)]
    result = {'schema': 1, 'roots': roots, 'entries': rows,
              'sha256': successors.digest([roots, rows])}
    if guarded:
        result['metadata'] = [metadata[name] for name in sorted(metadata)]
    return result


def safe_directory_inputs(root, sources=None):
    try:
        return directory_inputs(root, sources)
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def validate_directory_inputs(value):
    if (not isinstance(value, dict) or set(value) != {'schema','roots','entries','sha256'}
            or type(value.get('schema')) is not int or value['schema'] != 1
            or not isinstance(value.get('roots'), list) or not isinstance(value.get('entries'), list)):
        raise FreshRequired('no valid prospective directory topology')
    roots, names = value['roots'], []
    for name in roots:
        successors.literal_path(name)
    if roots != sorted(set(roots)):
        raise ValueError('unordered directory topology roots')
    for row in value['entries']:
        if not isinstance(row, list) or len(row) not in (2,3):
            raise ValueError('invalid directory topology row')
        name = successors.literal_path(row[0]); names.append(name)
        if not any(name == declared or name.startswith(declared + '/') for declared in roots):
            raise ValueError('directory topology row outside declared roots')
        if (row[1] == 'missing' and len(row) == 2):
            continue
        if (len(row) != 3 or row[1] not in ('file','directory')
                or type(row[2]) is not int or not 0 <= row[2] <= 0o7777):
            raise ValueError('invalid directory topology mode or kind')
    if names != sorted(set(names)) or not set(roots) <= set(names):
        raise ValueError('incomplete or unordered directory topology')
    if value['sha256'] != successors.digest([roots,value['entries']]):
        raise ValueError('directory topology hash mismatch')


def safe_snapshot(root, sources=None, guarded=False):
    try:
        files = file_fingerprint(root, source_paths(root, sources), guarded)
        return successors.digest([files,directory_inputs(root,sources,guarded=True)]) if guarded else files
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def runtime_paths():
    directory = Path(__file__).parent
    return sorted(directory.glob('*.py')) + [directory.parent / 'engineer.py']


def runtime_identity():
    return {'python': sys.version, 'executable': sys.executable, 'platform': platform.platform(),
            'schema': SCHEMA, 'implementation': successors.digest(
                [[path.name, file_digest(path)] for path in runtime_paths()])}


def capture_inputs(root, commands, configuration, revision, environment):
    from . import verification
    runtime = runtime_identity()
    order = successors.digest(commands)
    protected_paths = None
    protected_roots = sorted({name for item in commands for name in item.get('sources',[])})
    protected_directories = safe_directory_inputs(root,protected_roots)
    if any('successor_independence' in item for item in commands):
        try:
            protected_paths = set(inventory(root))
            for item in commands:
                protected_paths.update(source_paths(root, item.get('sources')))
        except (OSError, ValueError, subprocess.SubprocessError):
            protected_paths = None
    result = []
    for index, item in enumerate(commands):
        effective, env_key = verification._environment(item, environment)
        # Receipt metadata records identities, never the raw environment mapping
        # or potentially secret command arguments.
        specification = {key: value for key, value in item.items() if key not in ('argv', 'environment')}
        specification.update(argv_sha256=successors.digest(item['argv']),
                             environment_declaration_sha256=successors.digest(item.get('environment')))
        inputs = {'command_sha256': successors.digest(item['argv']),
                  'configuration': successors.digest(configuration), 'specification': specification,
                  'source': safe_snapshot(root, item.get('sources')), 'environment': env_key['digest'],
                  'runtime': runtime, 'tool': tool_identity(root / item['cwd'], item['argv'], effective),
                  'root': str(root), 'timeout': item['timeout'], 'index': index, 'order': order}
        inputs['directory_inputs'] = safe_directory_inputs(root,item.get('sources'))
        if item.get('revision'):
            inputs['revision'] = revision
        if 'successor_independence' in item:
            try:
                if protected_paths is None:
                    raise ValueError('complete configured dependency inventory unavailable')
                inputs['successor'] = successors.capture_bundle(
                    root, revision, item['successor_independence'], protected_paths,
                    source_paths(root, item.get('sources')), successors.digest(configuration), order, index)
                inputs['protected_directory_inputs'] = protected_directories
            except (OSError, ValueError, subprocess.SubprocessError):
                inputs['successor'] = None
        result.append(inputs)
    return result


def authentic_result(root, row):
    from . import verification
    if not isinstance(row, dict):
        raise ValueError('invalid check result')
    reference = row.get('receipt')
    if (not isinstance(reference, str) or not reference.startswith(STORE + '/')
            or len(reference.split('/')) != 3 or not reference.endswith('.json')):
        raise ValueError('invalid receipt reference')
    path = successors.safe_path(root, reference)
    stored = strict_json(path.read_text(encoding='utf-8'))
    if (not isinstance(stored, dict) or type(stored.get('schema')) is not int
            or stored['schema'] != SCHEMA or not verification._valid_receipt(stored, path)):
        raise ValueError('invalid immutable schema-2 receipt')
    presentation = {'reused', 'reusable', 'path'}
    if (successors.digest({k: v for k, v in row.items() if k not in presentation})
            != successors.digest({k: v for k, v in stored.items() if k not in presentation})
            or row.get('reused') is not False or stored.get('status') != 'passed'
            or type(stored.get('exit_code')) is not int or stored['exit_code'] != 0
            or stored.get('snapshot_valid') is not True
            or not isinstance(stored.get('stdout'), str) or not isinstance(stored.get('stderr'), str)):
        raise ValueError('original fresh passing stored result required')
    inputs = stored.get('inputs')
    if (not isinstance(inputs, dict) or type(inputs.get('index')) is not int
            or type(stored.get('full_index')) is not int or stored['full_index'] != inputs['index']):
        raise ValueError('missing prospective input/order binding')
    return inputs

def file_digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()

def tool_identity(root, command, environment):
    executable = command[0]
    if os.path.dirname(executable):
        executable = str((root / executable).resolve())
    else:
        executable = shutil.which(executable, path=environment.get("PATH"))
    if not executable:
        return None
    try:
        path = Path(executable)
        if os.name == "nt" and os.path.normcase(str(path)) == os.path.normcase(sys.executable):
            # A Windows Store execution alias is not readable. Ask the OS for
            # this running interpreter's loaded executable, rather than guessing
            # a different installation or treating an unknown tool as reusable.
            import ctypes
            buffer = ctypes.create_unicode_buffer(32768)
            size = ctypes.windll.kernel32.GetModuleFileNameW(None, buffer, len(buffer))
            if not size or size >= len(buffer):
                return None
            path = Path(buffer.value)
        path = path.resolve(strict=True)
        return {"path": str(path), "sha256": file_digest(path)}
    except OSError:
        return None

def selected_indices(only_checks, count):
    if only_checks is None:
        return list(range(count))
    if not isinstance(only_checks, list) or not only_checks:
        bad("only-checks requires nonempty zero-based indices")
    result = []
    for value in only_checks:
        if isinstance(value, bool) or not str(value).isascii() or not str(value).isdigit():
            bad("only-checks requires zero-based integer indices")
        index = int(value)
        if index >= count or index in result:
            bad("only-checks has duplicate or out-of-range indices")
        result.append(index)
    if result != sorted(result):
        bad("only-checks indices must follow configuration order")
    return result

def strict_json(content):
    def object_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON field: " + key)
            result[key] = value
        return result
    def invalid_constant(value):
        raise ValueError("invalid JSON constant: " + value)
    return json.loads(content, object_pairs_hook=object_pairs, parse_constant=invalid_constant)

def read_evidence(path):
    """Read external JSON without following links or treating it as authority."""
    path = Path(path).absolute()
    successors.safe_path(Path(path.anchor), path.relative_to(path.anchor).as_posix())
    with path.open(encoding="utf-8-sig") as handle:
        value = strict_json(handle.read())
    if not isinstance(value, dict):
        raise ValueError("evidence must be an object")
    return value

def equivalent_current_inputs(original, current):
    # Only the explicit dependency contract can subsequently bridge these fields.
    ignored = {"source", "revision", "successor", "directory_inputs", "protected_directory_inputs"}
    return (successors.digest({k: v for k, v in original.items() if k not in ignored})
            == successors.digest({k: v for k, v in current.items() if k not in ignored})
            and original.get("source") is not None and current.get("source") is not None
            and original.get("tool") is not None and current.get("tool") is not None)

class FreshRequired(ValueError):
    """An uncovered command needs a genuine replacement, not an inferred pass."""

def independent_successor(root, tested, original, current, approved):
    bundle = original.get("successor")
    contract = current["specification"].get("successor_independence")
    if not contract or not isinstance(bundle, dict) or current.get("successor") is None:
        raise FreshRequired("no original prospective independence/input contract")
    if not set(approved) <= set(contract["report_paths"]):
        raise FreshRequired("report not covered by this check's original independence contract")
    for field in ('directory_inputs','protected_directory_inputs'):
        old, new = original.get(field), current.get(field)
        validate_directory_inputs(old); validate_directory_inputs(new)
        # Exact generated report files may appear/change, but their already
        # existing owner directories retain stable kinds and modes.
        old_rows = [row for row in old['entries'] if row[0] not in contract['report_paths']]
        new_rows = [row for row in new['entries'] if row[0] not in contract['report_paths']]
        if old['roots'] != new['roots'] or old_rows != new_rows:
            raise ValueError('directory input topology changed: ' + field)
    expected = {"schema", "contract", "source_manifest", "protected_manifest", "reports",
                "configuration_sha256", "order_sha256", "index", "source_sha256", "protected_sha256"}
    if (set(bundle) != expected or type(bundle["schema"]) is not int or bundle["schema"] != 1
            or bundle["contract"] != contract or bundle["index"] != original["index"]
            or type(bundle["index"]) is not int
            or bundle["configuration_sha256"] != current["configuration"]
            or bundle["order_sha256"] != current["order"]
            or bundle["source_sha256"] != successors.digest(bundle["source_manifest"])
            or bundle["source_sha256"] != original["source"]
            or bundle["protected_sha256"] != successors.digest(bundle["protected_manifest"])):
        raise ValueError("baseline input manifest binding is invalid")
    successors.validate_manifest(root, tested, bundle["source_manifest"])
    successors.validate_manifest(root, tested, bundle["protected_manifest"])
    reports = {name: successors.tree_entry(root, tested, name) for name in contract["report_paths"]}
    if bundle["reports"] != reports:
        raise ValueError("baseline report blobs/modes changed")
    if bundle["protected_manifest"] != current["successor"]["protected_manifest"]:
        raise ValueError("protected inputs changed")
    # Current source membership/content must match, allowing only these original
    # declared reports. The full protected inventory also covers undeclared code.
    report_set = set(contract["report_paths"])
    old = [row for row in bundle["source_manifest"] if row[0] not in report_set]
    new = [row for row in current["successor"]["source_manifest"] if row[0] not in report_set]
    if old != new:
        raise ValueError("declared source inputs changed")
    if "revision" in original and original["revision"] != tested:
        raise ValueError("original revision provenance mismatch")


def validate_successor(evidence, approved_paths, expected_head, fresh_evidence=None):
    """Authenticate schema-2 evidence and attest H without changing R receipts."""
    from . import config, verification
    root = verification.root().resolve()
    commands = verification.configured_checks()
    configuration = config.load()["verification"]
    count = len(commands)
    tested = evidence.get("tested_revision") if isinstance(evidence, dict) else None
    result = {"qualified": False, "tested_revision": tested, "qualified_revision": expected_head,
              "approved_paths": approved_paths, "checked_commits": [], "checks": [],
              "original_receipts": [], "qualifications": [], "fresh_required": list(range(count))}
    try:
        guard = safe_snapshot(root, guarded=True)
        if guard is None:
            raise ValueError("current source proof unavailable")
        if (not count or not isinstance(evidence, dict)
                or evidence.get("ok", True) is not True
                or evidence.get("configured") is not True or evidence.get("passed") is not True
                or evidence.get("snapshot_valid") is not True or evidence.get("partial", False) is not False
                or not isinstance(evidence.get("checks"), list) or len(evidence["checks"]) != count):
            raise ValueError("complete passing original baseline aggregate required")
        source_guards = [safe_snapshot(root, (item if isinstance(item, dict) else {}).get("sources"), guarded=True)
                         for item in commands]
        if any(value is None for value in source_guards):
            raise ValueError("declared source guard unavailable")
        identity_guard = runtime_identity()
        implementation_paths = runtime_paths()
        runtime_guards = [(str(p), p.stat().st_mtime_ns, p.stat().st_ctime_ns, p.stat().st_ino) for p in implementation_paths]
        evidence_paths = []
        for document in (evidence, fresh_evidence):
            if document is not None:
                if not isinstance(document.get("checks"), list):
                    raise ValueError("invalid check list")
                for row in document["checks"]:
                    for field in ("receipt",):
                        name = row[field]
                        if not isinstance(name, str) or not name.startswith(STORE + "/"):
                            raise ValueError("invalid evidence storage reference")
                        successors.safe_path(root, name)
                        evidence_paths.append(name)
        evidence_guard = file_fingerprint(root, sorted(set(evidence_paths)), guarded=True)
        original_inputs = [authentic_result(root, row) for row in evidence["checks"]]
        history = successors.prove_report_only_successor(root, tested, expected_head, approved_paths)
        result["checked_commits"] = history["checked_commits"]
        if history["qualified"] is not True:
            raise ValueError(history["reason"])
        specs = commands
        current_inputs = capture_inputs(root, commands, configuration, expected_head, os.environ.copy())
        for index, (row, current, original) in enumerate(zip(evidence["checks"], current_inputs, original_inputs)):
            if (row.get("revision") != tested or row.get("full_index") != index
                    or not equivalent_current_inputs(original, current)):
                raise ValueError("original check order/configuration/current input identity mismatch")
        # An invalid baseline is never selectively rehabilitated with fresh rows.
        result["original_receipts"] = [row["receipt"] for row in evidence["checks"]]
        result["checks"] = list(evidence["checks"])
        required = []
        for index, (original, current) in enumerate(zip(original_inputs, current_inputs)):
            try:
                independent_successor(root, tested, original, current, approved_paths)
                reason, qualified = "original receipt independently covers successor", True
            except FreshRequired as exc:
                reason, qualified = str(exc), False
                required.append(index)
            result["qualifications"].append({"index": index, "qualified": qualified,
                                              "reason": reason, "evidence_revision": tested})
        result["fresh_required"] = list(required)
        if fresh_evidence is not None:
            if (not isinstance(fresh_evidence, dict)
                    or fresh_evidence.get("ok", True) is not True
                    or fresh_evidence.get("configured") is not True
                    or fresh_evidence.get("snapshot_valid") is not True
                    or fresh_evidence.get("tested_revision") != expected_head
                    or fresh_evidence.get("selected_indices") != required
                    or any(type(v) is not int for v in fresh_evidence.get("selected_indices", []))
                    or fresh_evidence.get("full_configuration_sha256") != successors.digest(configuration)
                    or fresh_evidence.get("full_order_sha256") != successors.digest(specs)
                    or fresh_evidence.get("selected_passed") is not True
                    or fresh_evidence.get("partial") is not (len(required) != count)
                    or fresh_evidence.get("passed") is not (len(required) == count)
                    or not isinstance(fresh_evidence.get("checks"), list)
                    or len(fresh_evidence["checks"]) != len(required) or not required):
                raise ValueError("fresh evidence must exactly account for ordered fresh-required indices")
            for index, row in zip(required, fresh_evidence["checks"]):
                actual = authentic_result(root, row)
                if (row.get("revision") != expected_head or row.get("full_index") != index
                        or successors.digest(actual) != successors.digest(dict(current_inputs[index], fresh_execution_revision=expected_head))):
                    raise ValueError("fresh receipt is not the exact current-H configured check")
                result["checks"][index] = row
                result["qualifications"][index] = {"index": index, "qualified": True,
                    "reason": "genuine fresh current-H evidence", "evidence_revision": expected_head}
            result["fresh_required"] = []
        # Repeat both source and Git guards after receipt/log and fresh validation.
        if (safe_snapshot(root, guarded=True) != guard or runtime_identity() != identity_guard
                or [(str(p), p.stat().st_mtime_ns, p.stat().st_ctime_ns, p.stat().st_ino)
                    for p in implementation_paths] != runtime_guards
                or file_fingerprint(root, sorted(set(evidence_paths)), guarded=True) != evidence_guard
                or any(safe_snapshot(root, spec.get("sources"), guarded=True) != source_guard
                       for spec, source_guard in zip(specs, source_guards))
                or any(tool_identity(root / spec["cwd"], spec["argv"], verification._environment(spec)[0]) != current["tool"]
                       for spec, current in zip(specs, current_inputs))):
            raise ValueError("inputs moved during qualification")
        again = successors.prove_report_only_successor(root, tested, expected_head, approved_paths)
        if again != history:
            raise ValueError("history/worktree changed during qualification")
        result["qualified"] = not result["fresh_required"]
        result["reason"] = "complete ordered evidence covers H" if result["qualified"] else "fresh checks required"
    except (OSError, ValueError, KeyError, TypeError, AttributeError, RecursionError, subprocess.SubprocessError, Failure) as exc:
        result.update(qualified=False, fresh_required=list(range(count)), reason=str(exc))
    return result
