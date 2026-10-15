"""Scoped planning-record schema and authored-content integrity boundaries.

No historical migration: only changed canonical active records are commit gated.
Inspection uses read-only Git commands and never changes an index.
"""
import re
import subprocess
from collections import Counter
from pathlib import Path, PurePosixPath

import yaml

from . import phase_issues, phases
from .paths import read_text
from .results import VerbError, require
from .text import FRONTMATTER, split_frontmatter

CODE = 'planning-integrity'
REQUIRED = {
    'CONTEXT': {'phase': str, 'discussion': str, 'issue_refs': list},
    'PLAN': {'phase': str, 'plan': (str, int), 'type': str, 'wave': int,
             'depends_on': list, 'files_modified': list, 'autonomous': bool,
             'requirements': list, 'acceptance': list, 'documentation': list,
             'checks': list, 'must_haves': dict, 'issue_refs': list},
    'SUMMARY': {'phase': str, 'plan': (str, int), 'status': str,
                'requirements-completed': list, 'acceptance': list,
                'documentation': list, 'issue_refs': list},
}


def record_kind(path):
    parts = PurePosixPath(str(path).replace('\\', '/')).parts
    if len(parts) != 4 or parts[:2] != ('.planning', 'phases'):
        return None
    directory = phases.DIRECTORY.fullmatch(parts[2])
    if not directory:
        return None
    for kind, pattern in [('PLAN', phases.PLAN_FILE), ('SUMMARY', phases.SUMMARY_FILE)]:
        match = pattern.fullmatch(parts[3])
        if match and phases.as_number(match[1]) == phases.as_number(directory[1]):
            return kind
    if parts[3] == phases.pad(directory[1]) + '-CONTEXT.md':
        return 'CONTEXT'
    return None


class IntegrityLoader(yaml.SafeLoader):
    """Strict only at the current-record boundary; historical readers stay lenient."""

    def flatten_mapping(self, node):
        # Check each original mapping before SafeLoader expands inherited keys.
        # Its recursive calls also check anchored merge sources. Remember nodes
        # so their later construction cannot mistake flattened inherited keys
        # for duplicate explicit keys.
        checked = getattr(self, '_integrity_checked_mappings', None)
        if checked is None:
            checked = self._integrity_checked_mappings = set()
        if node not in checked:
            checked.add(node)
            seen = set()
            for key_node, _ in node.value:
                if key_node.tag in ('tag:yaml.org,2002:merge', 'tag:yaml.org,2002:value'):
                    key = key_node.value
                else:
                    key = self.construct_object(key_node, deep=False)
                try:
                    duplicate = key in seen
                except TypeError:
                    raise yaml.constructor.ConstructorError(
                        'while reading frontmatter', node.start_mark,
                        'mapping key must be hashable', key_node.start_mark) from None
                if duplicate:
                    raise yaml.constructor.ConstructorError(
                        'while reading frontmatter', node.start_mark,
                        'duplicate explicit key: ' + repr(key), key_node.start_mark)
                seen.add(key)
        return super().flatten_mapping(node)


def validate_record(path, content):
    kind = record_kind(path)
    if not kind:
        return None
    def need(condition, key, message):
        require(condition, str(path) + ': ' + key + ': ' + message, CODE)
    block = FRONTMATTER.match(content)
    need(block is not None, 'frontmatter', 'required YAML mapping is missing or unterminated')
    try:
        data = yaml.load(block[1], Loader=IntegrityLoader)
    except yaml.YAMLError as exc:
        raise VerbError(str(path) + ': frontmatter: ' + str(exc), CODE) from None
    need(isinstance(data, dict), 'frontmatter', 'must be a YAML mapping')
    for key, expected in REQUIRED[kind].items():
        need(key in data, key, 'required field is missing')
        value = data[key]
        need(isinstance(value, expected) and not (isinstance(value, bool) and expected != bool),
             key, 'wrong field type')
        if expected == str:
            need(bool(value.strip()), key, 'must be nonempty')
    for key in ('depends_on', 'files_modified', 'requirements', 'requirements-completed', 'acceptance', 'documentation'):
        if key in data:
            need(isinstance(data[key], list), key, 'must be a list')
            need(all(isinstance(item, str) and item.strip() for item in data[key]), key, 'entries must be nonempty strings')
    if kind == 'PLAN':
        need(data['wave'] > 0, 'wave', 'must be a positive integer')
        need(bool(data['requirements']), 'requirements', 'must not be empty')
        need(data['type'] in ('execute', 'tdd'), 'type', 'must be execute or tdd')
        for key in ('truths', 'artifacts', 'key_links'):
            need(isinstance(data['must_haves'].get(key), list), 'must_haves.' + key, 'must be a list')
        need(all(isinstance(check, list) and check and all(isinstance(arg, str) and arg for arg in check)
                 for check in data['checks']), 'checks', 'each command must be a nonempty argv list of strings')
    elif kind == 'SUMMARY':
        need(data['status'] in ('complete', 'blocked', 'halted'), 'status', 'must be complete, blocked or halted')
    else:
        need(data['discussion'] in ('pending', 'in-progress', 'complete'), 'discussion',
             'must be pending, in-progress or complete; this does not authorize implementation')
    try:
        phase_issues.entries(data, required=True)
    except VerbError as exc:
        raise VerbError(str(path) + ': issue_refs: ' + str(exc), CODE) from None
    return {'record': str(path), 'kind': kind, 'valid': True}


def git_read(cwd, *args):
    try:
        result = subprocess.run(['git', *args], cwd=str(cwd), capture_output=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise VerbError('Cannot inspect prospective planning commit: ' + str(exc), CODE) from None
    require(result.returncode == 0, 'Cannot inspect prospective planning commit: '
            + result.stderr.decode('utf-8', 'replace').strip(), CODE)
    return result.stdout


def names(cwd, *args):
    return [item.decode('utf-8') for item in git_read(cwd, *args).split(b'\0') if item]


def validate_index(cwd):
    paths = names(cwd, 'diff', '--cached', '--name-only', '--diff-filter=ACMRT', '-z')
    validated = []
    for path in paths:
        if record_kind(path):
            try:
                content = git_read(cwd, 'show', ':' + path).decode('utf-8-sig')
            except UnicodeError:
                raise VerbError(path + ': frontmatter: record must be UTF-8', CODE) from None
            validated.append(validate_record(path, content))
    return validated


def selected(workspace, paths):
    require(paths, 'Select explicit canonical record paths with --files', CODE)
    validated = []
    for name in paths:
        path = (workspace.root / name).resolve()
        require(path.is_relative_to(workspace.root) and record_kind(name),
                'Select an active canonical CONTEXT, PLAN or SUMMARY: ' + str(name), CODE)
        validated.append(validate_record(name, read_text(path)))
    return {'records': validated}


# Split at every heading, including unknown/deeper headings. A replacement of a
# known parent never grants permission to erase an unexpected child section.
HEADING = re.compile(r'^(#{1,6})[ \t]+(.+?)[ \t]*$', re.M)
FIELD = re.compile(r'^(?:Phase|Plan|Status|Last activity|Progress|Last session|Stopped at|Resume file):|^\*\*Current focus:\*\*')


def sections(content):
    _, body = split_frontmatter(content.replace('\r\n', '\n'))
    matches = list(HEADING.finditer(body))
    chunks = [('<preamble>', body[:matches[0].start()] if matches else body)]
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        chunks.append((match[1] + ' ' + match[2], body[match.end():end]))
    return chunks


def content_loss(before, after, record, verb='', allowed_sections=(), removed_phase=None):
    """Return structured evidence for authored lines lost outside owned fields.

    Exceptions are section/line specific. Unknown headings are never exempt.
    Frontmatter derivation and newline spelling are not authored body loss.
    """
    after_sections = sections(after)
    after_lines = {}
    for name, body in after_sections:
        after_lines.setdefault(name, Counter()).update(line.strip() for line in body.splitlines() if line.strip())
    after_heads = Counter(name for name, _ in after_sections)
    losses = []
    for name, body in sections(before):
        title = name.lstrip('# ').strip()
        if name != '<preamble>' and not after_heads[name]:
            # planning.repair may restore a heading, never remove an authored one.
            if not (removed_phase and re.match(r'Phase\s+' + re.escape(str(removed_phase)) + r'(?:\s|:)', title)):
                losses.append({'record': record, 'verb': verb, 'section': name, 'content': name})
        if after_heads[name]:
            after_heads[name] -= 1
        for line in body.splitlines():
            text = line.strip()
            if not text or text.lower().strip('*_') in {'none yet.', 'none.', 'none', 'n/a', '(none)', 'tbd', '- none yet.', '- none'}:
                continue
            if record.endswith('STATE.md') and ((title in ('Current Position', 'Session Continuity') and FIELD.match(text))
                                               or text.startswith('**Current focus:**')):
                continue
            if title in allowed_sections and (text.startswith(('- ', '* ', '|'))):
                continue
            if record.endswith('ROADMAP.md'):
                # Generated checklist/progress rows and specific phase fields.
                if ((title == 'Phases' and re.match(r'^- \[[ xX]\] \*\*Phase ', text))
                        or (title == 'Progress' and re.match(r'^\|(?:[- :|]+\|| Phase \|| \d+(?:\.\d+)?\. )', text))):
                    continue
                if removed_phase and re.match(r'Phase\s+' + re.escape(str(removed_phase)) + r'(?:\s|:)', title):
                    continue
            available = after_lines.get(name, Counter())
            if available[text]:
                available[text] -= 1
            else:
                losses.append({'record': record, 'verb': verb, 'section': name, 'content': text[:240]})
    for loss in losses:
        loss['message'] = 'Potential authored-content truncation; inspect the saved record (no rollback was attempted).'
    return losses


def require_preserved(before, after, record, allowed_sections=()):
    losses = content_loss(before, after, record, allowed_sections=allowed_sections)
    require(not losses, record + ': potential authored-content truncation in '
            + '; '.join(item['section'] + ': ' + item['content'] for item in losses[:4]), CODE)


def snapshot(workspace):
    return {name: read_text(workspace.root / name, '')
            for name in ('.planning/STATE.md', '.planning/ROADMAP.md')}


def mutation_warnings(workspace, before, verb, positionals, options, result=None):
    allowed = set()
    if verb in ('state.add-decision', 'state.add-roadmap-evolution'):
        allowed.add('Decisions' if verb.endswith('decision') else 'Roadmap Evolution')
    if verb == 'state.sync-todos' or verb.startswith('todo.'):
        allowed.add('Pending Todos')
    if verb in ('state.clear-blocker', 'state.clear-entry'):
        allowed.add('Blockers/Concerns' if verb.endswith('blocker') else str(positionals[0] if positionals else ''))
    warnings = []
    for name, original in before.items():
        current = read_text(workspace.root / name, '')
        if original and current != original:
            if name.endswith('STATE.md') and verb == 'planning.repair':
                # Use the repair owner's conservative heading-only proposal;
                # restored section boundaries are intended, authored lines stay.
                from . import planning_review
                original = planning_review._state_headings(split_frontmatter(original)[1])[0]
            if name.endswith('ROADMAP.md'):
                original = expected_roadmap(original, current, verb, positionals, options, result)
            warnings.extend(content_loss(original, current, name, verb,
                                         allowed_sections=allowed if name.endswith('STATE.md') else (),
                                         removed_phase=None))
    return warnings


def expected_roadmap(before, after, verb, positionals, options, result=None):
    """Normalize only the explicit operation's generated roadmap changes."""
    if verb == 'phase.remove' and positionals:
        # Remove only the expressly selected block before renumbering successors.
        number = phases.display_number(positionals[0])
        heading = re.search(r'^(#{3,4}) Phase ' + re.escape(number) + r'\s*:[^\n]*', before, re.M)
        if heading:
            following = re.search(r'^#{1,' + str(len(heading[1])) + r'} ', before[heading.end():], re.M)
            end = heading.end() + following.start() if following else len(before)
            before = before[:heading.start()] + before[end:]
    if verb == 'phase.remove' and isinstance(result, dict):
        # Renumbering is part of explicit removal; preserve successors' prose.
        for item in result.get('renumbered', []):
            before = phases.renumber_text(before, item['from'], item['to'])
    if positionals and verb in ('milestone.create', 'milestone.complete'):
        from . import milestones
        if verb == 'milestone.create':
            before = milestones.MILESTONE_LINE.sub(lambda match: milestones.demote(match, positionals[0]), before)
        elif isinstance(result, dict):
            version, date = positionals[0], result['date']
            before = milestones.MILESTONE_LINE.sub(lambda match: milestones.ship(match, version, date), before)
            before = re.sub(r'^###\s+' + re.escape(milestones.STATUS_EMOJI['in_progress'])
                            + r'\s+(' + re.escape(version) + r'[^\n]*?)\s*\(In Progress\)\s*$',
                            '### ' + milestones.STATUS_EMOJI['shipped'] + r' \g<1> (Shipped ' + date + ')',
                            before, flags=re.M)
    if not positionals:
        return before
    target = str(positionals[0]).split('-')[0]
    if verb not in ('phase.edit', 'roadmap.set-plans', 'phase.complete',
                    'state.advance-plan', 'roadmap.update-plan-progress'):
        return before
    def target_section(chunks):
        for name, body in chunks:
            match = re.match(r'#+ Phase (\d+(?:\.\d+)?)\s*:', name)
            if match and phases.as_number(match[1]) == phases.as_number(target):
                return name, body
        return None, ''
    old_name, old_body = target_section(sections(before))
    new_name, new_body = target_section(sections(after))
    if not old_name or not new_name:
        return before
    replacement = old_body
    if verb == 'phase.edit':
        for option, label in [('goal', 'Goal'), ('depends_on', 'Depends on'), ('requirements', 'Requirements')]:
            if options.get(option):
                pattern = r'^\*\*' + label + r'\*\*[^\n]*$'
                updated = re.search(pattern, new_body, re.M)
                if updated:
                    replacement = re.sub(pattern, lambda _: updated[0], replacement, flags=re.M)
    if verb == 'roadmap.set-plans':
        pattern = r'^\*\*Plans\*\*[^\n]*$'
        updated = re.search(pattern, new_body, re.M)
        if updated:
            replacement = re.sub(pattern, lambda _: updated[0], replacement, flags=re.M)
        # Explicit registration replaces precisely numbered plan checklist rows.
        replacement = re.sub(r'^- \[[ xX]\] \d+(?:\.\d+)?-\d+:.*\n?', '', replacement, flags=re.M)
    if verb in ('phase.complete', 'state.advance-plan', 'roadmap.update-plan-progress'):
        replacement = re.sub(r'(?m)^(- )\[[ xX]\]( \d+(?:\.\d+)?-\d+:)', r'\1[x]\2', replacement)
        after = re.sub(r'(?m)^(- )\[[ xX]\]( \d+(?:\.\d+)?-\d+:)', r'\1[x]\2', after)
        # The caller compares to actual after; keep only marker-neutral plan rows
        # that are present there, avoiding any exemption for lost descriptions.
        for line in old_body.splitlines():
            if re.match(r'^- \[[ xX]\] \d+(?:\.\d+)?-\d+:', line):
                neutral = re.sub(r'\[[ xX]\]', '[x]', line, count=1)
                if neutral in after:
                    replacement = replacement.replace(neutral, '')
    # Replace only this direct section's content, never unknown child headings.
    start = before.find(old_name) + len(old_name)
    normalized = before[:start] + replacement + before[start + len(old_body):]
    if verb == 'phase.edit' and options.get('name'):
        normalized = normalized.replace(old_name, new_name, 1)
    return normalized
