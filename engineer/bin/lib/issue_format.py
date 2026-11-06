"""Template-owned issue structure, excluding Markdown literal and HTML blocks."""
import re
import json
import textwrap
from pathlib import Path
from . import models
from .core import Failure, read, root

VARIANTS = ("Bug", "Enhancement", "Decision required", "Security risk", "UAT")
FORM_NAMES = dict(zip(VARIANTS, ("bug", "enhancement", "decision-required", "security-risk", "uat")))
ACCEPTANCE = ("Status", "Reviewer", "Date", "Decision", "Evidence")
FALLBACK_HEADINGS = {
    "Bug": ["Problem", "Expected behavior", "Actual behavior", "Reproduction", "Safe evidence", "Impact", "Acceptance", "Scope", "Related links"],
    "Enhancement": ["User need", "Proposed outcome", "Current limitation and evidence", "Impact", "Scope", "Acceptance", "Related links"],
    "Decision required": ["Decision question", "Context", "Options", "Evidence", "Recommendation", "Blocking dependency", "Scope", "Acceptance", "Related links"],
    "Security risk": ["Security concern", "Affected surface and behavior", "Impact", "Risk assessment and lifecycle", "Safe evidence", "Requested remediation", "Scope and acceptance", "Related links"],
    "UAT": ["Acceptance checklist", "Context", "Impact and scope", "Build and environment", "Steps and expected outcomes", "Related links", "Human acceptance"],
}


def fallback_schema():
    return {name: {"headings": list(headings), "tables": [["Step", "Action", "Expected outcome", "Actual outcome / evidence"]] if name == "UAT" else []}
            for name, headings in FALLBACK_HEADINGS.items()}


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


def github_directory():
    """Global assets belong to the runtime; local forms belong to the project."""
    installed = models.NAMESPACE/".github"
    return installed if installed.is_dir() else root()/".github"


def template_path(variant, directory=None):
    directory = Path(directory) if directory is not None else github_directory()/"ISSUE_TEMPLATE"
    return directory/(FORM_NAMES[variant]+".yml")


def form_body(path):
    """Read our literal Report default, not arbitrary YAML or executable tags.

    The forms deliberately retain the full Markdown body in one textarea. This
    keeps tables, human decisions and exact headings intact in the GitHub UI
    and lets the standard-library runtime consume the same canonical content.
    """
    text = read(path)
    name = re.search(r'^name: ("[^\n]+")$', text, re.M)
    report = re.search(r'(?m)^    id: report\n    attributes:\n      label: Report\n      description: [^\n]+\n      value: \|\n((?:(?:        [^\n]*)?\n)+)', text)
    if not name or not report:
        raise Failure("issue-schema", "Missing canonical Report default: "+str(path))
    try:
        variant = json.loads(name[1])
    except ValueError as exc:
        raise Failure("issue-schema", "Invalid canonical form name: "+str(path)) from exc
    return variant, textwrap.dedent(report[1])


def schema(template=None):
    result = {}
    for expected in VARIANTS:
        path = template_path(expected, template)
        name, body = form_body(path)
        if name != expected:
            raise Failure("issue-schema", "Canonical form name does not match its path: "+str(path))
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
