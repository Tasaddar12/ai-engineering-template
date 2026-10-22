"""Publication format validation from the templates beside this runtime.

This deliberately checks shape, not facts, safe content, working links or human
acceptance. Direct provider edits do not pass through this gate.
"""
import re
from pathlib import Path

from .paths import read_text
from .results import VerbError, require

TEMPLATES = {
    "Bug": "bug.md",
    "Enhancement": "enhancement.md",
    "Decision required": "decision-required.md",
    "Security risk": "security-risk.md",
    "UAT": "uat.md",
}


def template_path():
    # Source .ai and installed .codex/.claude share this runtime/templates layout.
    return Path(__file__).resolve().parents[2] / "templates" / "issues"


def visible_lines(content):
    """Ignore literal code/raw HTML blocks, comments and block quotes."""
    fence = None
    raw_end = None
    html_block = False
    lines = []
    for line in content.splitlines():
        if raw_end:
            if re.search(raw_end, line, re.I):
                raw_end = None
            lines.append("")
            continue
        if html_block:
            if not line.strip():
                html_block = False
            lines.append("")
            continue
        indentation = re.match(r"^[ \t]*", line).group()
        if not fence and (len(indentation.expandtabs(4)) >= 4
                          or line.lstrip().startswith(">")):
            lines.append("")
            continue
        raw_start = re.match(r"^ {0,3}<(pre|script|style|textarea)(?=[\s>]|$)", line, re.I)
        if not fence:
            end = None
            if raw_start:
                end = r"</" + raw_start.group(1) + r"\s*>"
            else:
                for opening, closing in ((r"<!--", r"-->"), (r"<\?", r"\?>"),
                                         (r"<!\[CDATA\[", r"\]\]>"), (r"<![A-Z]", r">")):
                    if re.match(r"^ {0,3}" + opening, line):
                        end = closing
                        break
            if end:
                raw_end = None if re.search(end, line, re.I) else end
                lines.append("")
                continue
            # Conservatively exclude line-start HTML tag blocks through the
            # next blank line; their raw rows cannot supply Markdown structure.
            if re.match(r"^ {0,3}</?[A-Za-z][A-Za-z0-9-]*(?=[\s/>]|$)", line):
                html_block = True
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


def _body_lines(content, issue_marker=False):
    # This marker is appended by reviewed TODO publication, not author content.
    if issue_marker:
        content = re.sub(r"(?m)^<!-- todo-id: [^\n]+ -->\s*$", "", content)
    return content.splitlines()


def _sections(content, expected, code, optional=(), risk_entries=False, issue_marker=False):
    raw = _body_lines(content, issue_marker)
    entries = headings(visible_lines("\n".join(raw)))
    titles = [title for _, title in entries]
    require(titles == [title for title in expected if title not in optional or title in titles],
            "Sections must match the publication template in order", code)
    require(entries and not any(line.strip() for line in raw[:entries[0][0]]),
            "Content before the first template section is not allowed", code)
    result = {}
    for n, (index, title) in enumerate(entries):
        section = raw[index + 1:entries[n + 1][0] if n + 1 < len(entries) else len(raw)]
        require(any(line.strip() for line in visible_lines("\n".join(section))),
                "Empty template section: " + title, code)
        for line in section:
            match = re.match(r"^ {0,3}(#{1,6})\s+(.+)", line)
            if match:
                require(risk_entries and title == "Risk assessment and lifecycle"
                        and len(match[1]) == 3,
                        "Unexpected heading inside template section: " + title, code)
            require(not re.match(r"^\s*(?:`{3,}|~{3,}|>|<!|<\?|</?[A-Za-z][A-Za-z0-9-]*(?=[\s/>]))", line),
                    "Literal or quoted blocks are not fields in this publication template", code)
            require(not re.fullmatch(r" {0,3}(?:=+|-+)\s*", line),
                    "Setext headings and thematic breaks are not template fields", code)
        result[title] = section
    return result


def _blocks(lines, field_lines=False):
    result = []
    for line, visible in zip(lines, visible_lines("\n".join(lines))):
        if not line.strip():
            if result:
                result[-1][2] = True
            continue
        # Keep raw prose/list continuations, but only rendered Markdown rows
        # can supply required table structure. cells() intentionally strips
        # whitespace for cell values and is not a visibility check.
        kind = ("table" if cells(visible) is not None else
                "bullets" if re.match(r"^ {0,3}[-*+]\s+", line) else
                "ordered" if re.match(r"^ {0,3}\d+\.\s+", line) else
                "fields" if field_lines and not re.match(r"^[A-Za-z][A-Za-z0-9+.-]*://", line)
                and re.match(r"^[A-Za-z][A-Za-z /-]*:\s*", line) else
                "paragraph")
        if result and kind == "paragraph" and result[-1][0] == "fields" and not result[-1][2]:
            result[-1][1][-1] += "\n" + line
        elif (result and kind == "paragraph" and line.startswith("  ")
                and result[-1][0] in ("bullets", "ordered")):
            result[-1][1].append(line)
        elif result and result[-1][0] == kind and not result[-1][2]:
            result[-1][1].append(line)
        else:
            result.append([kind, [line], False])
    return [(kind, rows) for kind, rows, _ in result]


def _check_blocks(actual, source, code, title):
    fields = bool(re.search(r"(?m)^[A-Za-z][A-Za-z /-]*:\s*", "\n".join(source)))
    wanted, found = _blocks(source, fields), _blocks(actual, fields)
    require([kind for kind, _ in found] == [kind for kind, _ in wanted],
            "Unexpected content blocks in template section: " + title, code)
    for (kind, rows), (_, model) in zip(found, wanted):
        if kind == "table":
            values, sample = [cells(row) for row in rows], [cells(row) for row in model]
            require(len(values) >= 3 and values[0] == sample[0] and separator(values[1])
                    and all(len(row) == len(sample[0]) and all(row) for row in values),
                    "Malformed template table in " + title, code)
        elif kind in ("bullets", "ordered"):
            pattern = r"^ {0,3}[-*+]\s+(.+)" if kind == "bullets" else r"^ {0,3}(\d+)\.\s+(.+)"
            items = [re.match(pattern, row) for row in rows if re.match(pattern, row)]
            require(items and all(item[item.lastindex].strip() for item in items),
                    "Empty template list item in " + title, code)
            if kind == "ordered":
                require([int(item[1]) for item in items] == list(range(1, len(items) + 1)),
                        "Numbered template actions must be sequential", code)
                continue
            sample_items = [re.match(pattern, row)[1] for row in model if re.match(pattern, row)]
            minimum = sum(not re.search(r"optional|if needed|if applicable", item, re.I) for item in sample_items)
            maximum = 4 if title == "Acceptance checklist" else len(sample_items)
            require(minimum <= len(items) <= maximum,
                    "Template list item count differs in " + title, code)
            labels = [re.match(r"^([^\[\]:]+):\s*(.+)$", value) for value in sample_items]
            expected_labels = [match[1] for match in labels if match]
            actual_labels = [match[1] for item in items
                             if (match := re.match(r"^([^\[\]:]+):\s*(.+)$", item[1]))]
            require(not expected_labels or actual_labels == expected_labels,
                    "Required template field labels differ in " + title, code)
        elif kind == "fields":
            labels = lambda values: [row.split(":", 1)[0] for row in values]
            require(labels(rows) == labels(model) and all(row.split(":", 1)[1].strip() for row in rows),
                    "Required template fields differ in " + title, code)


def _risk_entry_sections(lines, source, code):
    require(all(not raw.strip() or visible.strip()
                for raw, visible in zip(lines, visible_lines("\n".join(lines)))),
            "Literal blocks cannot supply consolidated risk rows or tasks", code)
    entries = [(i, match[1].strip()) for i, line in enumerate(lines)
               if (match := re.fullmatch(r" {0,3}###\s+(.+)", line))]
    model_entries = [(i, match[1].strip()) for i, line in enumerate(source)
                     if (match := re.fullmatch(r" {0,3}###\s+(.+)", line))]
    require(len(model_entries) == 1, "Consolidated template requires one task model", "issue-schema")
    model_index = model_entries[0][0]
    _check_blocks(lines[:entries[0][0]] if entries else lines,
                  source[:model_index], code, "Risk assessment and lifecycle")
    rows = [cells(line) for line in lines[:entries[0][0]] if cells(line) is not None] if entries else []
    identities = [row[0] for row in rows[2:]]
    require(entries and len(set(identities)) == len(identities)
            and [name for _, name in entries] == identities,
            "Consolidated risks require unique row IDs and matching task headings in order", code)
    model_task = [line.strip() for line in source[model_index + 1:] if line.strip()]
    require(len(model_task) == 1 and re.fullmatch(r"- \[[ xX]\] .+", model_task[0]),
            "Consolidated template requires one checkbox task", "issue-schema")
    label = model_task[0][6:]
    for n, (index, name) in enumerate(entries):
        value = lines[index + 1:entries[n + 1][0] if n + 1 < len(entries) else len(lines)]
        task = [line.strip() for line in value if line.strip()]
        require(len(task) == 1 and re.fullmatch(r"- \[[ xX]\] " + re.escape(label), task[0]),
                "Each consolidated risk requires its canonical checkbox: " + name, code)


def schema(path=None):
    directory = Path(path) if path is not None else template_path()
    try:
        sources = [(name, read_text(directory / filename))
                   for name, filename in list(TEMPLATES.items()) +
                   [("consolidated", "security-risk-consolidated.md")]]
    except (VerbError, OSError, UnicodeError):
        raise VerbError("Issue template schema cannot be read", "issue-schema")
    blocks = []
    for name, text in sources:
        matches = re.findall(r"^## File Template\n\n```markdown\n(.*?)\n```(?=\n|$)",
                             text, re.M | re.S)
        require(len(matches) == 1, "Missing or malformed issue variant templates", "issue-schema")
        blocks.append((name, matches[0]))
    result = {}
    for name, block in blocks:
        lines = visible_lines(block)
        entries = headings(lines)
        titles = [title for _, title in entries]
        require(titles and len(set(titles)) == len(titles),
                "Invalid issue template headings", "issue-schema")
        shape = {"headings": titles, "sections": {
            title: block.splitlines()[index + 1:entries[n + 1][0] if n + 1 < len(entries) else len(lines)]
            for n, (index, title) in enumerate(entries)}}
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
    consolidated = result.pop("consolidated")
    risk_source = consolidated["sections"].get("Risk assessment and lifecycle", [])
    table = [cells(line) for line in risk_source if cells(line) is not None]
    require(len(table) == 3 and len(table[0]) == 7 and all(table[0])
            and len(set(table[0])) == 7 and separator(table[1])
            and all(len(row) == 7 and all(row) for row in table),
            "Malformed consolidated risk template table", "issue-schema")
    _risk_entry_sections(risk_source, risk_source, "issue-schema")
    result["Security risk"]["consolidated"] = consolidated
    return result


def validate(content, variant, schema_path=None):
    require(isinstance(content, str), "A composed issue body is required", "issue-format")
    shapes = schema(schema_path)
    require(isinstance(variant, str) and variant in shapes,
            "Select a canonical issue variant: " + ", ".join(shapes), "issue-variant")
    shape = shapes[variant]
    consolidated = variant == "Security risk" and any(cells(line) is not None for line in visible_lines(content))
    if consolidated:
        shape = shape["consolidated"]
    lines = visible_lines(content)
    entries = headings(lines)
    require([title for _, title in entries] == shape["headings"],
            "Issue headings must match the selected template exactly in order", "issue-format")
    sections = _sections(content, shape["headings"], "issue-format",
                         risk_entries=consolidated, issue_marker=True)
    for title, section in sections.items():
        if consolidated and title == "Risk assessment and lifecycle":
            _risk_entry_sections(section, shape["sections"][title], "issue-format")
        else:
            _check_blocks(section, shape["sections"][title], "issue-format", title)
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
        fields = [row.split(":", 1)
                  for kind, rows in _blocks(sections[shape["acceptance_heading"]], True)
                  if kind == "fields" for row in rows]
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


def validate_pr(content, template=None):
    require(isinstance(content, str), "A composed PR body is required", "pr-format")
    path = (Path(template) if template is not None else
            Path(__file__).resolve().parents[2] / "templates" / "pull-request.md")
    try:
        source = read_text(path)
    except (VerbError, OSError, UnicodeError):
        raise VerbError("PR template cannot be read", "pr-schema") from None
    blocks = re.findall(r"^## File Template\n\n```markdown\n(.*?)\n```", source, re.M | re.S)
    require(len(blocks) == 1, "Exactly one PR File Template is required", "pr-schema")
    block = blocks[0]
    entries = headings(block.splitlines())
    titles = [title for _, title in entries]
    require(titles and len(set(titles)) == len(titles)
            and {"Verification", "Risks or rollback"}.issubset(titles),
            "PR template is missing required unique sections", "pr-schema")
    samples = {title: block.splitlines()[index + 1:entries[n + 1][0] if n + 1 < len(entries) else len(block.splitlines())]
               for n, (index, title) in enumerate(entries)}
    verification_schema = _blocks(samples["Verification"])
    require([kind for kind, _ in verification_schema] == ["table", "table"],
            "PR template requires revision and check tables", "pr-schema")
    revision_model = [cells(row) for row in verification_schema[0][1]]
    check_model = [cells(row) for row in verification_schema[1][1]]
    require(len(revision_model) == 4 and all(len(row) == 2 for row in revision_model)
            and separator(revision_model[1])
            and [row[0] for row in revision_model[2:]] == ["Candidate", "Tested"]
            and len(check_model) >= 3 and all(len(row) == 3 for row in check_model)
            and separator(check_model[1]),
            "Malformed PR revision or check table schema", "pr-schema")
    sections = _sections(content, titles, "pr-format", optional=("Requirements or Issues", "Stack"))
    for title, section in sections.items():
        sample = samples[title]
        if title == "Risks or rollback":
            # The template explicitly permits None identified with inspected scope.
            sentinel = [i for i, line in enumerate(sample) if line.startswith("[Use None identified")]
            require(len(sentinel) == 1, "PR risk omission instruction is missing", "pr-schema")
            sample = sample[:sentinel[0]]
            values = _blocks(section)
            if len(values) == 2 and values[1][0] == "paragraph":
                require(" ".join(values[1][1]).startswith("None identified:")
                        and bool(" ".join(values[1][1]).partition(":")[2].strip()),
                        "Use None identified with the inspected risk scope", "pr-format")
                table_start = next((i for i, line in enumerate(sample) if cells(line) is not None), None)
                require(table_start is not None, "PR risk table is missing", "pr-schema")
                sample = sample[:table_start]
                _check_blocks(values[0][1], sample, "pr-format", title)
                continue
        _check_blocks(section, sample, "pr-format", title)
    verification = _blocks(sections["Verification"])
    rows = [cells(row) for row in verification[0][1]]
    require([row[0] for row in rows[2:]] == ["Candidate", "Tested"],
            "PR revision table requires Candidate and Tested", "pr-format")
    require(re.fullmatch(r"[0-9a-fA-F]{40}|[0-9a-fA-F]{64}", rows[2][1].strip("`"))
            and (re.fullmatch(r"[0-9a-fA-F]{40}|[0-9a-fA-F]{64}", rows[3][1].strip("`"))
                 or rows[3][1].startswith("Pending")),
            "PR revisions require full SHAs or Pending tested evidence", "pr-format")
    return {"valid": True, "structuralOnly": True, "template": "pull-request.md"}


def validate_pr_file(body_file):
    require(isinstance(body_file, str) and body_file.strip(), "A PR body file is required", "pr-review")
    try:
        content = read_text(body_file)
    except (VerbError, OSError, UnicodeError):
        raise VerbError("PR body file cannot be read", "pr-review") from None
    return validate_pr(content)
