"""Read-only UI planning gate, bound to independent checker and source inputs."""
import hashlib
import json
import re
from . import config, records
from .core import Failure, read, root, run
from .text import split_frontmatter

# Only coordinator approval metadata may change after independent review.
# The COMPLETE body (including Checker Sign-Off) and all other metadata bind.
APPROVAL_FIELDS = frozenset({"status", "approved", "reviewed_at", "ui_checker"})
UI_WORDS = re.compile(r"\b(?:UI|user interface|frontend|front-end|visual design)\b", re.I)
NO_UI = re.compile(r"\b(?:no|without|exclude[ds]?|out of scope[: ]*)[ -]*(?:product )?(?:UI|user interface|frontend|front-end|screens?)\b|\b(?:UI|frontend|front-end)\s*(?:scope)?\s*:\s*(?:none|false|no)\b", re.I)


def text_digest(text):
    """SHA-256 of UTF-8 decoded text with LF line endings, as read by core.read."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def contract_digest(content):
    metadata, body = split_frontmatter(content)
    payload = {"metadata": {k: v for k, v in metadata.items() if k not in APPROVAL_FIELDS},
               "body": body}
    return text_digest(json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")))


def _scope_context(text):
    text = re.sub(r"(?ms)^## (?:Deferred Ideas|Out of Scope)\b.*?(?=^## |\Z)", "", text)
    return re.sub(r"(?is)<deferred[^>]*>.*?</deferred[^>]*>", "", text)


def _marked(text):
    # Negation applies only to its sentence/line, not a later positive UI outcome.
    return any(UI_WORDS.search(part) and not NO_UI.search(part)
               for part in re.split(r"[\n.!?;]+", text))


def _blob(revision, path):
    return run(["git", "show", f"{revision}:{path}"], root()).stdout


def _evidence_error(evidence, phase, spec_path, context_path, spec, context, roadmap):
    if not isinstance(evidence, dict):
        return "Missing independent ui-checker evidence"
    required = {"role": "ui-checker", "verdict": "APPROVED", "phase": phase,
                "spec_path": spec_path, "context_path": context_path,
                "spec_digest": contract_digest(spec), "context_digest": text_digest(context),
                "roadmap_digest": text_digest(roadmap)}
    for key, value in required.items():
        if evidence.get(key) != value:
            return f"UI checker evidence has missing, stale or mismatched {key}"
    if not all(isinstance(evidence.get(key), str) and evidence[key].strip()
               for key in ("checker_id", "author_id", "session", "reviewed_at")):
        return "UI checker provenance requires actual checker/author/session/time identities"
    if evidence["checker_id"] == evidence["author_id"]:
        return "UI checker must be independent of the specification author"
    if evidence.get("unexamined") != []:
        return "UI checker coverage is incomplete"
    dimensions = evidence.get("dimensions")
    if not isinstance(dimensions, list) or len(dimensions) != 7:
        return "UI checker must return all seven dimensions"
    seen = set()
    for item in dimensions:
        if not isinstance(item, dict):
            return "Malformed UI checker dimension"
        identity = item.get("dimension")
        if type(identity) is not int or identity not in range(1, 8) or identity in seen:
            return "UI checker dimensions must have unique IDs 1 through 7"
        seen.add(identity)
        if item.get("verdict") not in ("PASS", "FLAG"):
            return "UI checker has a blocking or missing dimension verdict"
        if not isinstance(item.get("evidence"), str) or not item["evidence"].strip():
            return "UI checker dimensions require cited evidence"
    revision = evidence.get("reviewed_revision", "")
    if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{40}", revision):
        return "UI checker requires the full captured Git revision"
    if run(["git", "merge-base", "--is-ancestor", revision, "HEAD"], root(), check=False).returncode:
        return "UI checker revision is missing or outside current source history"
    try:
        if contract_digest(_blob(revision, spec_path)) != required["spec_digest"]:
            return "Reviewed revision does not contain the checked UI contract"
        if text_digest(_blob(revision, context_path)) != required["context_digest"]:
            return "Reviewed revision does not contain the checked CONTEXT decisions"
        if text_digest(_blob(revision, ".planning/ROADMAP.md")) != required["roadmap_digest"]:
            return "Reviewed revision does not contain the checked ROADMAP"
        # Current tree equality alone misses a changed-and-restored source. Inspect
        # EVERY intervening commit, allowing only this spec's approval metadata.
        commits = run(["git", "rev-list", "--reverse", f"{revision}..HEAD"], root()).stdout.splitlines()
        for commit in commits:
            parents = run(["git", "rev-list", "--parents", "-n", "1", commit], root()).stdout.split()
            if len(parents) != 2:
                return "UI checker currentness cannot cross a merge commit"
            changed = run(["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "--no-renames", commit], root()).stdout.splitlines()
            if changed != [spec_path]:
                return "Source or phase inputs changed after UI review"
            for point in (parents[1], commit):
                if contract_digest(_blob(point, spec_path)) != required["spec_digest"]:
                    return "UI contract changed after review, including an intervening restored version"
    except Failure:
        return "UI checker revision/input provenance is unavailable"
    return None


def plan_gate(args):
    directory = records.phase_dir(args.arg(0, args.get("phase")))
    phase = records.roadmap_phase(directory.name)
    contexts = sorted(directory.glob("*-CONTEXT.md"))
    context = "\n".join(read(path) for path in contexts)
    # A recorded scope decision is authoritative; examples or deferred mentions
    # must not manufacture product screens for a CLI/backend phase.
    explicit_scope = None
    if len(contexts) == 1:
        metadata, _ = split_frontmatter(context)
        explicit_scope = metadata.get("ui_scope")
        if explicit_scope is not None and type(explicit_scope) is not bool:
            return {"blocked": True, "required": True, "reason": "CONTEXT ui_scope must be boolean"}, 1
    marked = explicit_scope if explicit_scope is not None else _marked(phase["name"] + "\n" + phase["body"] + "\n" + _scope_context(context))
    mode = config.lookup(config.load(), "workflow.ui_phase", "auto")
    if type(mode) is not bool and mode != "auto":
        return {"blocked": True, "required": bool(marked), "reason": "workflow.ui_phase must be auto, true or false"}, 1
    if not marked or mode is False:
        return {"blocked": False, "required": False, "reason": "disabled" if mode is False else "no-ui-scope"}, 0
    result = {"blocked": True, "required": True}
    if len(contexts) != 1 or not context.strip():
        return {**result, "reason": "UI planning requires one recorded CONTEXT decision artifact"}, 1
    paths = sorted(directory.glob("*-UI-SPEC.md"))
    if len(paths) != 1:
        return {**result, "reason": "UI planning requires exactly one UI-SPEC"}, 1
    path = paths[0]
    spec = read(path)
    metadata, _ = split_frontmatter(spec)
    if metadata.get("status") != "approved":
        return {**result, "reason": "UI specification requires evidenced coordinator approval"}, 1
    if run(["git", "status", "--porcelain", "--untracked-files=all"], root()).stdout.strip():
        return {**result, "reason": "Commit phase/source inputs and approval before the UI gate"}, 1
    spec_path = path.relative_to(root()).as_posix()
    context_path = contexts[0].relative_to(root()).as_posix()
    error = _evidence_error(metadata.get("ui_checker"), phase["number"], spec_path,
                            context_path, spec, context, read(records.planning()/"ROADMAP.md"))
    return {"blocked": bool(error), "required": True, "reason": error,
            "spec_path": spec_path, "spec_digest": contract_digest(spec)}, int(bool(error))
