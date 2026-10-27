"""Template-owned issue structure, excluding Markdown literal and HTML blocks."""
import re
from . import models
from .core import Failure, read

VARIANTS = ("Bug", "Enhancement", "Decision required", "Security risk", "UAT")
ACCEPTANCE = ("Status", "Reviewer", "Date", "Decision", "Evidence")


def visible_lines(body):
    result, fence, opaque = [], None, None
    for line in body.splitlines():
        stripped = line.lstrip(" ")
        indentation = len(line.expandtabs(4))-len(line.expandtabs(4).lstrip())
        if fence:
            if re.fullmatch(r" {0,3}"+re.escape(fence[0])+"{"+str(fence[1])+r",}\s*", line):
                fence = None
            result.append("")
            continue
        if opaque:
            if re.search(opaque, line, re.I):
                opaque = None
            result.append("")
            continue
        opening = re.match(r" {0,3}(`{3,}|~{3,})", line)
        if opening:
            fence = (opening[1][0], len(opening[1]))
            result.append("")
            continue
        if indentation >= 4:
            result.append("")
            continue
        html = re.match(r"<(pre|script|style|textarea|div|table)(?=[\s>]|$)", stripped, re.I)
        if html:
            closing = r"</"+html[1]+r"\s*>"
            opaque = None if re.search(closing, stripped, re.I) else closing
            result.append("")
            continue
        instruction = next(((start, end) for start, end in
                            (("<!--", "-->"), ("<?", "?>"), ("<![CDATA[", "]]>"), ("<!", ">"))
                            if stripped.startswith(start)), None)
        if instruction:
            start, end = instruction
            opaque = None if end in stripped[len(start):] else re.escape(end)
            result.append("")
            continue
        result.append(line)
    return result


def cells(line):
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def tables(lines, code):
    result, index = [], 0
    while index < len(lines):
        if not re.match(r"^ {0,3}\|", lines[index]):
            index += 1
            continue
        block = []
        while index < len(lines) and re.match(r"^ {0,3}\|", lines[index]):
            block.append(cells(lines[index]))
            index += 1
        if not block or block[0][0] != "Step":
            continue
        width = len(block[0])
        if width != 4 or any(not value for value in block[0]) or len(block) < 3:
            raise Failure(code, "UAT step table requires its four columns and numbered rows")
        if any(len(row) != width for row in block) or any(not re.fullmatch(r":?-{3,}:?", value) for value in block[1]):
            raise Failure(code, "Malformed UAT step table separator or row width")
        if [row[0] for row in block[2:]] != [str(number) for number in range(1, len(block)-1)]:
            raise Failure(code, "UAT steps must be consecutive unique numbers beginning at 1")
        result.append(block[0])
    return result


def schema(template=None):
    template = template or models.NAMESPACE/"engineer/templates/issue.md"
    text = read(template)
    catalog = text.split("## File Template", 1)
    if len(catalog) != 2:
        raise Failure("issue-schema", "Installed issue File Template catalog is absent")
    blocks = re.findall(r"(?ms)^### ([^\n]+)\n\s*```markdown\n(.*?)^```\s*$", catalog[1])
    result = {}
    for name, body in blocks:
        if name not in VARIANTS:
            continue
        if name in result:
            raise Failure("issue-schema", "Duplicate canonical issue variant: "+name)
        lines = visible_lines(body)
        headings = [match[1].strip() for line in lines if (match := re.match(r"^ {0,3}## (.+)$", line))]
        if not headings or len(headings) != len(set(headings)):
            raise Failure("issue-schema", "Canonical issue headings are missing or duplicated")
        expected_tables = tables(lines, "issue-schema") if name == "UAT" else []
        if name == "UAT" and not expected_tables:
            raise Failure("issue-schema", "Canonical UAT template lacks a numbered step table")
        if name == "UAT":
            for field in ACCEPTANCE:
                count = sum(bool(re.match(r"^ {0,3}(?:- )?"+field+r":\s*\S", line.replace("**", ""), re.I)) for line in lines)
                if count != 1:
                    raise Failure("issue-schema", "Canonical human acceptance field is missing or duplicated: "+field)
        result[name] = {"headings": headings, "tables": expected_tables}
    if set(result) != set(VARIANTS):
        raise Failure("issue-schema", "Installed issue catalog must retain every canonical variant")
    return {name: result[name] for name in VARIANTS}


def validate(body, variant, template=None):
    if not isinstance(variant, str) or variant not in VARIANTS:
        raise Failure("issue-variant", "Select an exact canonical issue variant")
    expected = schema(template)[variant]
    lines = visible_lines(body)
    actual = [match[1].strip() for line in lines if (match := re.match(r"^ {0,3}## (.+)$", line))]
    if actual != expected["headings"]:
        raise Failure("issue-format", "Issue sections must match their selected template in order", expected=expected["headings"], actual=actual)
    if variant == "UAT":
        if tables(lines, "issue-format") != expected["tables"]:
            raise Failure("issue-format", "Preserve the canonical UAT step table columns")
        for field in ACCEPTANCE:
            matches = [match[1].strip() for line in lines if
                       (match := re.match(r"^ {0,3}(?:- )?"+field+r":([^\n]*)$", line.replace("**", ""), re.I))]
            if len(matches) != 1 or not matches[0]:
                raise Failure("issue-format", "Human acceptance requires one nonempty "+field+" field")
    return {"valid": True, "variant": variant, "structuralOnly": True}
