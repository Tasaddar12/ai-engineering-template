"""Small Markdown navigation audit shared by contribution tests (no project writes)."""
import html
from pathlib import Path
import posixpath
import re
import unicodedata
from urllib.parse import unquote, urlsplit


def without_inline_code(text, preserve_labels=False):
    """Match whole backtick runs across lines; unmatched runs remain prose."""
    runs = list(re.finditer(r"`+", text))
    parts, cursor, index = [], 0, 0
    while index < len(runs):
        opening = runs[index]
        closing_index = next((candidate for candidate in range(index + 1, len(runs))
                              if runs[candidate][0] == opening[0]), None)
        if closing_index is None:
            index += 1
            continue
        closing = runs[closing_index]
        content = text[opening.end():closing.start()]
        parts.append(text[cursor:opening.start()])
        if preserve_labels and not re.search(r"\]\s*[([]", content):
            parts.append(content)  # Retain labels such as [`verb`](guide.md).
        cursor = closing.end()
        index = closing_index + 1
    parts.append(text[cursor:])
    return "".join(parts)


def without_fences(text, inline=True):
    lines, fence, containers = [], None, []
    fence_indent = 0
    for line in text.expandtabs(4).splitlines():
        indent = len(line) - len(line.lstrip())
        if fence:
            closing = re.match(r"^\s*(`{3,}|~{3,})(.*)$", line)
            if (closing and indent <= fence_indent + 3
                    and closing[1][0] == fence[0] and len(closing[1]) >= len(fence)
                    and not closing[2].strip()):
                fence = None
            lines.append("")
            continue
        if line.strip():
            while containers and indent < containers[-1]:
                containers.pop()
        marker = re.match(r"^( *)(?:[-*+]|\d+[.)])([ ]+)(.*)$", line)
        container = containers[-1] if containers else 0
        candidate = line[container:]
        if marker and indent <= container + 3:
            # A list item introduces a content column. Indented fences are
            # interpreted relative to that column, not the document margin.
            content_column = len(line) - len(marker[3])
            containers.append(content_column)
            candidate = marker[3]
            container = content_column
        match = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", candidate)
        if match:
            fence, fence_indent = match[1], container
            lines.append("")
        elif indent >= container + 4:
            lines.append("")  # Indented literal block outside list content.
        else:
            lines.append(line)
    text = "\n".join(lines)
    if inline:
        text = without_inline_code(text, preserve_labels=True)
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
    comments = without_fences(text, inline=False)
    comments = without_inline_code(comments)
    placeholders = set()
    for comment in re.findall(r'<!--(.*?)-->', comments, re.S):
        annotation = re.fullmatch(r'\s*guidance-placeholder:\s*(\S+)\s+\|([^\n]*)', comment)
        if annotation and annotation[2].strip():
            placeholders.add(annotation[1])
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
