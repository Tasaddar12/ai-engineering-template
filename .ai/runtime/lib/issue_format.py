"""Structural issue validation from the templates beside this runtime.

This deliberately checks shape, not facts, safe content, working links or human
acceptance. Direct provider edits do not pass through this gate.
"""
import re
from pathlib import Path

from .paths import read_text
from .results import VerbError, require


def template_path():
    # Source .ai and installed .codex/.claude share this runtime/templates layout.
    return Path(__file__).resolve().parents[2] / "templates" / "issue.md"


def visible_lines(content):
    """Ignore literal code/raw HTML blocks, comments and block quotes."""
    content = re.sub(r"<!--.*?(?:-->|\Z)", "", content, flags=re.S)
    fence = None
    raw_tag = None
    lines = []
    for line in content.splitlines():
        if raw_tag:
            if re.search(r"</" + raw_tag + r"\s*>", line, re.I):
                raw_tag = None
            lines.append("")
            continue
        indentation = re.match(r"^[ \t]*", line).group()
        if not fence and (len(indentation.expandtabs(4)) >= 4
                          or line.lstrip().startswith(">")):
            lines.append("")
            continue
        raw_start = re.match(r"^ {0,3}<(pre|script|style|textarea)(?=[\s>])", line, re.I)
        if not fence and raw_start:
            tag = raw_start.group(1).lower()
            raw_tag = None if re.search(r"</" + tag + r"\s*>", line, re.I) else tag
            lines.append("")
            continue
        match = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if match:
            mark, tail = match.groups()
            if fence is None:
                fence = mark
            elif mark[0] == fence[0] and len(mark) >= len(fence) and not tail.strip():
                fence = None
            lines.append("")
        elif fence:
            lines.append("")
        else:
            lines.append(line)
    return lines


def headings(lines):
    return [(index, match.group(1).strip()) for index, line in enumerate(lines)
            if (match := re.fullmatch(r" {0,3}##\s+(.+?)\s*", line))]


def cells(line):
    if not line.strip().startswith("|") or not line.strip().endswith("|"):
        return None
    return [cell.strip() for cell in re.split(r"(?<!\\)\|", line.strip()[1:-1])]


def separator(row):
    return row is not None and all(re.fullmatch(r":?-{3,}:?", cell) for cell in row)


def schema(path=None):
    try:
        text = read_text(path or template_path())
    except (VerbError, OSError, UnicodeError):
        raise VerbError("Issue template schema cannot be read", "issue-schema")
    registry = re.search(r"^\| Variant \|.*?\n(.*?)(?=\n\n)", text, re.M | re.S)
    require(registry is not None, "Issue variant registry missing", "issue-schema")
    rows = [cells(line) for line in registry.group(1).splitlines()]
    require(rows and separator(rows[0]) and all(row and len(row) == 3 for row in rows),
            "Malformed issue variant registry", "issue-schema")
    names = [row[0] for row in rows[1:]]
    require(names and len(set(names)) == len(names) and all(names),
            "Invalid issue variants", "issue-schema")
    blocks = re.findall(r"^### ([^\n]+)\n\n```markdown\n(.*?)\n```(?=\n|$)", text, re.M | re.S)
    require([name for name, _ in blocks] == names,
            "Missing or malformed issue variant templates", "issue-schema")
    result = {}
    for name, block in blocks:
        lines = visible_lines(block)
        entries = headings(lines)
        titles = [title for _, title in entries]
        require(titles and len(set(titles)) == len(titles),
                "Invalid issue template headings", "issue-schema")
        shape = {"headings": titles}
        if name == "UAT":
            tables = [(index, cells(line)) for index, line in enumerate(lines)
                      if cells(line) is not None]
            require(len(tables) >= 3 and separator(tables[1][1])
                    and len(tables[0][1]) == 4
                    and all(tables[0][1])
                    and all(len(row) == 4 for _, row in tables)
                    and [index for index, _ in tables] == list(range(tables[0][0], tables[0][0] + len(tables)))
                    and all(row[0] == str(n) for n, (_, row) in enumerate(tables[2:], 1)),
                    "Malformed UAT template table", "issue-schema")
            owner = next((title for index, title in reversed(entries) if index < tables[0][0]), None)
            fields = re.findall(r"^([A-Za-z][A-Za-z ]*):\s*.+$", "\n".join(lines[entries[-1][0] + 1:]), re.M)
            require(owner and len(fields) == 5 and len(set(fields)) == len(fields),
                    "Malformed UAT acceptance schema", "issue-schema")
            shape.update(table=tables[0][1], table_heading=owner,
                         acceptance_heading=titles[-1], fields=fields)
        result[name] = shape
    return result


def validate(content, variant, schema_path=None):
    shapes = schema(schema_path)
    require(isinstance(variant, str) and variant in shapes,
            "Select a canonical issue variant: " + ", ".join(shapes), "issue-variant")
    shape = shapes[variant]
    lines = visible_lines(content)
    entries = headings(lines)
    require([title for _, title in entries] == shape["headings"],
            "Issue headings must match the selected template exactly in order", "issue-format")
    if "table" in shape:
        sections = {title: lines[index + 1:(entries[n + 1][0] if n + 1 < len(entries) else len(lines))]
                    for n, (index, title) in enumerate(entries)}
        section = sections[shape["table_heading"]]
        tables = [(index, cells(line)) for index, line in enumerate(section) if cells(line) is not None]
        require(len(tables) >= 3 and tables[0][1] == shape["table"]
                and len(tables[1][1]) == len(shape["table"]) and separator(tables[1][1])
                and [index for index, _ in tables] == list(range(tables[0][0], tables[0][0] + len(tables)))
                and all(len(row) == len(shape["table"]) and all(row)
                        and row[0] == str(n) for n, (_, row) in enumerate(tables[2:], 1)),
                "UAT requires the canonical table and sequential numbered action rows", "issue-format")
        fields = re.findall(r"^([A-Za-z][A-Za-z ]*):\s*(.*)$",
                            "\n".join(sections[shape["acceptance_heading"]]), re.M)
        require([key for key, _ in fields] == shape["fields"] and all(value.strip() for _, value in fields),
                "UAT requires every Human acceptance field in template order", "issue-format")
    return {"variant": variant, "valid": True, "structuralOnly": True}


def validate_file(body_file, variant):
    require(isinstance(body_file, str) and body_file.strip(),
            "A public body file is required", "issue-review")
    try:
        content = read_text(body_file)
    except (VerbError, OSError, UnicodeError):
        raise VerbError("Public body file cannot be read", "issue-review")
    return validate(content, variant)
