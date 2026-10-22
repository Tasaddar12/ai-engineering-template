"""Read-only provider gate. Run only from the trusted workflow revision.

No event body or head files are read. Diagnostics deliberately exclude provider
response text, body content and exception messages, which can contain secrets.
"""
import json
import os
from pathlib import Path
import re
import sys
from urllib import error, parse, request

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".ai/runtime"))
from lib.issue_format import validate_pr
from lib.results import VerbError

MAX_RESPONSE = 1024 * 1024


class GateError(Exception):
    """Fixed, safe diagnostic only; never include provider data."""


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Never forward the authorization header to a redirected origin.
        return None


def configuration(env):
    repo = env.get("PHASE_PR_REPOSITORY", "")
    number = env.get("PHASE_PR_NUMBER", "")
    api = env.get("PHASE_PR_API_URL", "")
    token = env.get("PHASE_PR_TOKEN", "")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
        raise GateError("Invalid repository identity.")
    if any(part in (".", "..") for part in repo.split("/")):
        raise GateError("Invalid repository identity.")
    if not re.fullmatch(r"[1-9][0-9]{0,9}", number):
        raise GateError("Invalid pull request number.")
    parts = parse.urlsplit(api)
    if (parts.scheme != "https" or not parts.hostname or parts.username
            or parts.password or parts.query or parts.fragment
            or parts.path not in ("", "/", "/api/v3", "/api/v3/")):
        raise GateError("Invalid provider API URL.")
    if not token or any(c.isspace() for c in token):
        raise GateError("Missing or invalid provider token.")
    return api.rstrip("/") + "/repos/" + repo + "/pulls/" + number, repo, int(number), token


def fetch(url, token):
    req = request.Request(url, headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "phase-saved-pr-validator",
        "Cache-Control": "no-cache",
    }, method="GET")
    try:
        with request.build_opener(NoRedirect).open(req, timeout=20) as response:
            data = response.read(MAX_RESPONSE + 1)
        if len(data) > MAX_RESPONSE:
            raise GateError("Provider response exceeds size limit.")
        result = json.loads(data)
    except (error.URLError, OSError, ValueError, UnicodeError):
        raise GateError("Provider read failed; validation is unverified.") from None
    return result


def snapshot(payload, repo, number):
    """Bind saved body to PR identity and both revisions, including ref movement."""
    try:
        if type(payload["number"]) is not int or payload["number"] != number:
            raise ValueError
        if payload["base"]["repo"]["full_name"].casefold() != repo.casefold():
            raise ValueError
        body = payload["body"]
        if body is None:
            body = ""
        if not isinstance(body, str):
            raise ValueError
        revisions = []
        for side in ("head", "base"):
            revision = payload[side]
            sha = revision["sha"]
            ref = revision["ref"]
            repository_id = revision["repo"]["id"]
            if (not isinstance(sha, str) or not re.fullmatch(r"[a-fA-F0-9]{40}|[a-fA-F0-9]{64}", sha)
                    or not isinstance(ref, str) or not ref
                    or type(repository_id) is not int or repository_id <= 0):
                raise ValueError
            revisions.append((sha, ref, repository_id))
        updated = payload["updated_at"]
        if not isinstance(updated, str) or not updated:
            raise ValueError
        return body, tuple(revisions), updated
    except (KeyError, TypeError, ValueError, AttributeError):
        raise GateError("Provider returned an invalid PR snapshot.") from None


def validate_saved(env, reader=fetch):
    url, repo, number, token = configuration(env)
    before = snapshot(reader(url, token), repo, number)
    valid = True
    try:
        validate_pr(before[0])
    except VerbError:
        valid = False
    after = snapshot(reader(url, token), repo, number)
    if before != after:
        raise GateError("PR changed during validation; rerun against the saved state.")
    if not valid:
        raise GateError("Saved PR body fails canonical structural validation.")
    return "Saved PR body passes canonical structural validation (structural only)."


def main():
    try:
        message = validate_saved(os.environ)
    except GateError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except Exception:
        # Do not surface an unexpected exception with credential/body-bearing locals.
        print("Saved PR validation failed unexpectedly; validation is unverified.", file=sys.stderr)
        return 1
    print(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
