"""Slugs, YAML frontmatter and Markdown section editing."""
import re
import unicodedata

import yaml

from .results import VerbError

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
