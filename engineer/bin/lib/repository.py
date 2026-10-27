"""Pin provider operations to the current checkout's origin identity."""
import re
from urllib.parse import urlparse
from .core import Failure, root, run


def identity():
    value = run(["git", "remote", "get-url", "origin"], root()).stdout.strip()
    match = re.fullmatch(r"(?:[^@]+@)?([^/:]+):([^/]+/[^/]+?)(?:\.git)?", value) if "://" not in value else None
    if match:
        hostname, path = match.groups()
    else:
        parsed = urlparse(value)
        hostname, path = parsed.hostname, parsed.path.strip("/").removesuffix(".git")
    if not hostname or not re.fullmatch(r"[^/]+/[^/]+", path):
        raise Failure("unsupported-origin", "Provider operations require an origin repository URL")
    owner, name = path.split("/")
    return {"hostname": hostname.lower(), "owner": owner, "repository": name,
            "slug": hostname.lower()+"/"+owner+"/"+name}


def require_url(value, kind):
    expected = identity()
    parsed = urlparse(value)
    match = re.fullmatch(r"/([^/]+)/([^/]+)/"+kind+r"/(\d+)", parsed.path)
    if parsed.scheme != "https" or not match or parsed.hostname != expected["hostname"] or (match[1], match[2]) != (expected["owner"], expected["repository"]):
        raise Failure("provider-repository-mismatch", "Provider URL does not match origin", url=value)
    return int(match[3])
