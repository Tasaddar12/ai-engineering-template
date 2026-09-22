"""Slugs, YAML frontmatter and Markdown section editing."""
import re
import unicodedata

import yaml

from .results import VerbError, require

FRONTMATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---[ \t]*\r?\n?", re.DOTALL)
STOPWORDS = {"a", "an", "the", "and", "or", "for", "to", "of", "in", "on", "with"}


def slugify(value, limit=5):
    """Lowercase hyphenated slug, first `limit` meaningful words."""
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = text.encode("ascii", "ignore").decode("ascii").lower()
    words = [w for w in re.split(r"[^a-z0-9]+", text) if w]
    meaningful = [w for w in words if w not in STOPWORDS] or words
    slug = "-".join(meaningful[:limit]) if limit else "-".join(meaningful)
    return slug or "untitled"


def split_frontmatter(content):
    """Return (frontmatter dict, body). Missing or unparsable block yields {}."""
    match = FRONTMATTER.match(content or "")
    if not match:
        return {}, content or ""
    try:
        data = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError as exc:
        raise VerbError(f"invalid frontmatter: {exc}", "bad-frontmatter")
    if not isinstance(data, dict):
        raise VerbError("frontmatter must be a mapping", "bad-frontmatter")
    return data, content[match.end():]


def join_frontmatter(data, body):
    if not data:
        return body
    rendered = yaml.safe_dump(data, sort_keys=False, allow_unicode=True,
                              default_flow_style=False).rstrip("\n")
    return f"---\n{rendered}\n---\n{body}"


def heading_pattern(name, level):
    marker = "#" * level
    return re.compile(rf"^{marker}\s+{re.escape(name)}\s*$", re.MULTILINE)


def find_section(content, name, level=2):
    """Return (start, body_start, end) offsets for a heading and its body."""
    match = heading_pattern(name, level).search(content or "")
    if not match:
        return None
    body_start = match.end()
    if body_start < len(content) and content[body_start] == "\n":
        body_start += 1
    following = re.compile(rf"^#{{1,{level}}}\s+", re.MULTILINE).search(content, body_start)
    end = following.start() if following else len(content)
    return match.start(), body_start, end


def section_body(content, name, level=2, default=""):
    found = find_section(content, name, level)
    if not found:
        return default
    _, body_start, end = found
    return content[body_start:end].strip("\n")


def replace_section(content, name, body, level=2, create=True):
    """Replace a heading's body wholesale. Appends the section when absent."""
    body = body.rstrip("\n")
    found = find_section(content, name, level)
    if not found:
        if not create:
            raise VerbError(f"section not found: {name}", "missing-section")
        prefix = content if content.endswith("\n") else content + "\n"
        return f"{prefix}\n{'#' * level} {name}\n\n{body}\n"
    _, body_start, end = found
    trailer = "\n\n" if end < len(content) else "\n"
    return content[:body_start] + body + trailer + content[end:]


def upsert_bullet(body, bullet):
    """Append a bullet to a section body, clearing placeholder text."""
    lines = [line for line in (body or "").splitlines()
             if line.strip() and not is_placeholder(line)]
    if bullet not in lines:
        lines.append(bullet)
    return "\n".join(lines)


def is_placeholder(line):
    stripped = line.strip().strip("*_")
    if not stripped:
        return True
    lowered = stripped.lower()
    return lowered in {"none yet.", "none.", "none", "n/a", "(none)", "*(none)*",
                       "tbd", "- none yet.", "- none"} or stripped.startswith("[")


def split_row(line):
    """Cells of a Markdown table row, or None when the line is not a row."""
    stripped = line.strip()
    if not stripped.startswith("|"):
        return None
    return [cell.strip() for cell in stripped.strip("|").split("|")]


def render_row(cells):
    return "| " + " | ".join(str(cell).strip() for cell in cells) + " |"


def is_divider_row(line):
    cells = split_row(line)
    return bool(cells) and all(re.fullmatch(r":?-{2,}:?", cell or "") for cell in cells)


def is_placeholder_row(cells):
    return all(is_placeholder(cell) for cell in cells)


def find_table(body):
    """Return (divider_index, first_row_index, end_index) for the first table."""
    lines = (body or "").splitlines()
    for index, line in enumerate(lines):
        if not is_divider_row(line) or index == 0 or split_row(lines[index - 1]) is None:
            continue
        end = index + 1
        while end < len(lines) and split_row(lines[end]) is not None:
            end += 1
        return index, index + 1, end
    return None


def upsert_table_row(body, cells, key_index=0):
    """Replace the row whose key cell matches, else append. Drops placeholders.

    Rows live inside the table block; anything after it (footers, notes) stays
    where the author put it.
    """
    found = find_table(body)
    require(found is not None, "section has no Markdown table", "no-table")
    _, first, end = found
    lines = (body or "").splitlines()
    width = len(split_row(lines[first - 1]))
    row = list(cells) + [""] * (width - len(cells))
    kept = []
    replaced = False
    for line in lines[first:end]:
        existing = split_row(line)
        if existing is None or is_placeholder_row(existing):
            continue
        if not replaced and existing[key_index].strip().lower() == str(row[key_index]).strip().lower():
            kept.append(render_row(row[:width]))
            replaced = True
            continue
        kept.append(line.rstrip())
    if not replaced:
        kept.append(render_row(row[:width]))
    return "\n".join(lines[:first] + kept + lines[end:])


def table_records(body, columns=None):
    """Every non-placeholder row of the first table, as dicts keyed by header."""
    found = find_table(body)
    if not found:
        return []
    divider, first, end = found
    lines = (body or "").splitlines()
    headers = columns or split_row(lines[divider - 1])
    records = []
    for line in lines[first:end]:
        cells = split_row(line)
        if cells is None or is_placeholder_row(cells):
            continue
        padded = cells + [""] * (len(headers) - len(cells))
        records.append({header: padded[index] for index, header in enumerate(headers)})
    return records
