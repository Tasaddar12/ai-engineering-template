"""Reject executable Node examples and retired JS runtime helpers in tracked Markdown.

Scan the Git index's complete filename inventory (including hidden directories and
case-insensitive Markdown suffixes). Prose about Node, graph nodes, package-manager
commands and JavaScript application source remain valid documentation.
"""
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
# A command token, including POSIX/Windows paths and quoted executable names.
NODE = re.compile(r'''(?<![\w./\\-])(?:["'][^"'\r\n]*[\\/]node(?:js)?(?:\.exe)?["']|(?:["']?(?:[A-Za-z]:[\\/]|/|\.\.?[\\/])?[^\s`"'|;()]*[\\/])?["']?node(?:js)?(?:\.exe)?["']?)\s+(?=--?[\w-]|-\s|["']?\$|["']?[^\s`|;()]+\.(?:[cm]?js|json)(?:[\s`"']|$)|<[^>]+>)''', re.I)
RETIRED = re.compile(r'''(?:\brequire\s*\([^\n]*(?:code-review-(?:flags|depth)|fallow-runner)|(?:\b(?:python3?|node(?:js)?)\b|\$\([^\n]*)[^\n]*\b(?:edge-probe|spec-section|ui-consideration-probe)\.cjs)''')


def executable_regions(text):
    """Yield (offset, text) for fences and inline code, without broad path exemptions."""
    lines = text.splitlines(keepends=True)
    offset, fence, body, start = 0, None, [], 0
    for line in lines:
        marker = re.match(r"^\s{0,3}(`{3,}|~{3,})(.*)$", line)
        if marker:
            if fence is None:
                fence, start, body = marker[1], offset+len(line), []
            elif marker[1][0] == fence[0] and len(marker[1]) >= len(fence):
                yield start, "".join(body)
                fence = None
            else:
                body.append(line)
        elif fence is not None:
            body.append(line)
        elif line.startswith(("    ", "\t")):
            yield offset, line
        else:
            for match in re.finditer(r"(`+)(.+?)\1", line):
                yield offset+match.start(2), match[2]
        offset += len(line)
    if fence is not None:
        yield start, "".join(body)


def findings(text):
    results = []
    for offset, region in executable_regions(text):
        region = re.sub(r"[\\`]\r?\n", lambda m: " "*len(m[0]), region)
        for pattern, reason in ((NODE, "executable Node command"), (RETIRED, "retired JavaScript helper")):
            for match in pattern.finditer(region):
                line_start = region.rfind("\n", 0, match.start())+1
                # Shell comments document semantics, rather than execute commands.
                if region[line_start:match.start()].lstrip().startswith("#"):
                    continue
                absolute = offset+match.start()
                results.append((text.count("\n", 0, absolute)+1, reason, match[0].strip()))
    return sorted(set(results))


def tracked_markdown(root=ROOT):
    output = subprocess.check_output(["git", "-C", str(root), "ls-files", "-z"])
    return [Path(name.decode("utf-8")) for name in output.split(b"\0") if name.lower().endswith((b".md", b".markdown"))]


def main():
    files = tracked_markdown()
    errors = []
    for file in files:
        for line, reason, command in findings((ROOT/file).read_text(encoding="utf-8-sig")):
            errors.append(f"{file.as_posix()}:{line}: {reason}: {command}")
    print("\n".join(errors)) if errors else None
    print(f"Scanned {len(files)} tracked Markdown files; {len(errors)} findings.")
    return int(bool(errors))


if __name__ == "__main__":
    sys.exit(main())
