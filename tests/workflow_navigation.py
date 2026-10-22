"""Small Markdown navigation audit shared by contribution tests (no project writes)."""
import html
from pathlib import Path
import posixpath
import re
import unicodedata
from urllib.parse import unquote, urlsplit


def without_fences(text, inline=True):
    lines, fence, list_context = [], None, False
    for line in text.splitlines():
        if re.match(r'^\s*(?:[-*+] |\d+[.)] )', line):
            list_context = True
        elif line.strip() and not line[0].isspace():
            list_context = False
        match = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if match:
            mark, tail = match.groups()
            if fence is None:
                fence = mark
            elif mark[0] == fence[0] and len(mark) >= len(fence) and not tail.strip():
                fence = None
            lines.append("")
        elif fence or (not list_context and (line.startswith("    ") or line.startswith("\t"))):
            lines.append("")
        else:
            lines.append(line)
    text = "\n".join(lines)
    if inline:
        text = re.sub(r"(`+)(.*?)\1", lambda match: "" if re.search(
            r"\]\s*[([]", match[2]) else match[2], text)
    return text


def links(text):
    """Yield inline and resolved reference links outside code/comments."""
    text = re.sub(r"<!--.*?-->", "", without_fences(text), flags=re.S)
    definitions = dict((m[1].strip().casefold(), m[2] or m[3]) for m in re.finditer(
        r'^ {0,3}\[([^]\n]+)\]:\s*(?:<([^>]+)>|(\S+))', text, re.M))
    yield from definitions.values()
    for match in re.finditer(r'\[[^]\n]+\]\(\s*(?:<([^>\n]+)>|((?:[^\s()]|\([^()]*\))+))(?:\s+"[^"\n]*")?\s*\)', text):
        yield html.unescape(match[1] or match[2])
    for match in re.finditer(r'(?<!!)\[([^]\n]+)\]\[([^]\n]*)\]', text):
        key = (match[2] or match[1]).strip().casefold()
        yield html.unescape(definitions.get(key, 'unresolved-reference:' + key))


def anchors(text):
    text = re.sub(r"<!--.*?-->", "", without_fences(text, inline=False), flags=re.S)
    result, used = set(), set()
    for match in re.finditer(r'<(?:a|h[1-6])\b[^>]*\b(?:id|name)=["\']([^"\']+)["\']', text, re.I):
        result.add(html.unescape(match[1]))
    lines = text.splitlines()
    for index, line in enumerate(lines):
        match = re.match(r'^ {0,3}#{1,6}\s+(.+?)(?:\s+#+\s*)?$', line)
        title = match[1] if match else None
        if title is None and index + 1 < len(lines) and line.strip() and re.fullmatch(r' {0,3}(?:=+|-+)\s*', lines[index + 1]):
            title = line.strip()
        if title is None:
            continue
        title = re.sub(r'!?\[([^]]*)\]\([^)]*\)', r'\1', title)
        title = html.unescape(re.sub(r'<[^>]+>', '', title)).lower().replace('`', '')
        slug = ''.join(c for c in title if c in '_- ' or unicodedata.category(c)[0] in 'LN').replace(' ', '-')
        candidate, number = slug, 0
        while candidate in used:
            number += 1
            candidate = slug + '-' + str(number)
        used.add(candidate)
        result.add(candidate)
    return result


def audit(source, root):
    text = source.read_text(encoding='utf-8-sig')
    # Exact destinations only: an annotation never exempts neighboring links.
    placeholders = set(re.findall(r'<!-- guidance-placeholder:\s*(\S+)\s+\|\s*[^\n]+?-->', text))
    failures = []
    for target in links(text):
        if target in placeholders:
            continue
        parsed = urlsplit(target)
        if parsed.scheme or parsed.netloc:
            if target.startswith('unresolved-reference:'):
                failures.append(target + ' (missing reference definition)')
            continue
        relative = posixpath.normpath(source.parent.relative_to(root).as_posix() + '/' + unquote(parsed.path)) if parsed.path else source.relative_to(root).as_posix()
        destination = root / relative
        if not destination.resolve().is_relative_to(root.resolve()) or not destination.exists():
            failures.append(target + ' (missing or outside repository)')
            continue
        cursor = root
        for part in Path(relative).parts:
            if part not in {child.name for child in cursor.iterdir()}:
                failures.append(target + ' (case does not match tracked path)')
                break
            cursor /= part
        if parsed.fragment and destination.is_file() and destination.suffix.lower() == '.md':
            if unquote(parsed.fragment) not in anchors(destination.read_text(encoding='utf-8-sig')):
                failures.append(target + ' (missing heading anchor)')
    return failures
