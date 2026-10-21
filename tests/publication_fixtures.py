"""Valid publication content derived from the installed source templates."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHA = "a" * 40


def issue_body(variant="Bug"):
    source = (ROOT / ".ai/templates/issue.md").read_text(encoding="utf-8")
    block = re.search(r"^### " + re.escape(variant) + r"\n\n```markdown\n(.*?)\n```",
                      source, re.M | re.S)[1]
    filled = re.sub(r"\[(?![ xX]\])[^\]\n]+\]", "Safe fixture detail", block)
    if variant == "Bug":
        filled = filled.replace("## Problem\nSafe fixture detail", "## Problem\nBlank search fails for signed-in users.")
    return filled


def pr_body(reference=None, stack=False):
    source = (ROOT / ".ai/templates/pull-request.md").read_text(encoding="utf-8")
    block = re.search(r"^## File Template\n\n```markdown\n(.*?)\n```", source, re.M | re.S)[1]
    block = re.sub(r"## Requirements or Issues\n.*?(?=\n## Verification)",
                   "## Requirements or Issues\n\nREFERENCE_SENTINEL\n" if reference else "",
                   block, flags=re.S)
    block = re.sub(r"## Risks or rollback\n.*?(?=\n## Stack)",
                   "## Risks or rollback\n\n- Risks: Fixture-only change.\n"
                   "- Rollback: Revert this fixture.\n\nNone identified: fixture scope.\n",
                   block, flags=re.S)
    if not stack:
        block = block.split("\n## Stack", 1)[0]
    block = block.replace("[one full current head SHA]", SHA)
    block = block.replace("[one full tested SHA, or Pending until verified]", "Pending: fixture check")
    filled = re.sub(r"\[[^\]\n]+\]", "Safe fixture detail", block)
    return filled.replace("REFERENCE_SENTINEL", reference or "").strip() + "\n"
