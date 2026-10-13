"""Offline forge identity resolution. Provider calls never choose the target."""
import re
from urllib.parse import urlsplit

from . import config, gitops
from .results import VerbError, require


def _url(value):
    require(isinstance(value, str) and not any(c.isspace() or c in "\\?#" for c in value),
            "Invalid provider URL", "issue-repository")
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except (ValueError, TypeError):
        raise VerbError("Invalid provider URL", "issue-repository")
    require(parsed.hostname and (port is None or port > 0) and not parsed.query and not parsed.fragment
            and parsed.password is None, "Invalid provider URL", "issue-repository")
    return parsed, port


def _authority(parsed, port):
    host = parsed.hostname.lower()
    require(re.fullmatch(r"[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?", host)
            and ".." not in host,
            "Unsupported provider hostname", "issue-repository")
    return host + (":" + str(port) if port else "")


def resolve(workspace, cwd=None):
    """Return provider, host, project, remote, web_url and repository strings.

    GitLab host mappings are explicit HTTPS web bases. SSH ports are transport
    ports, independent of the mapped web/API port. Unknown origins fail offline.
    """
    origin = gitops.git(workspace, "remote", "get-url", "origin", check=False, cwd=cwd)
    require(origin.returncode == 0, "An origin is required", "issue-repository")
    remote = origin.stdout.strip()
    scp = re.fullmatch(r"git@([A-Za-z0-9.-]+):(.+)", remote)
    if scp:
        hostname, path = scp.groups()
        hostname, scheme, port = hostname.lower(), "ssh", None
    else:
        parsed, port = _url(remote)
        require(parsed.scheme in ("https", "ssh")
                and (parsed.username is None or
                     (parsed.scheme == "ssh" and parsed.username == "git")),
                "Only credential-free HTTPS or git SSH origins are supported",
                "issue-repository")
        hostname, scheme = parsed.hostname.lower(), parsed.scheme
        _authority(parsed, port)
        require(parsed.path.startswith("/"), "Invalid origin path", "issue-repository")
        path = parsed.path[1:]
    path = path.removesuffix("/").removesuffix(".git")
    parts = path.split("/")
    require(len(parts) >= 2 and all(re.fullmatch(r"[A-Za-z0-9_.-]+", part)
            and part not in (".", "..") for part in parts),
            "Invalid origin project path", "issue-repository")
    selected = config.get(workspace, "delivery.provider", "auto")
    require(selected in ("auto", "github", "gitlab"),
            "delivery.provider must be auto, github or gitlab", "bad-config")
    configured = config.get(workspace, "delivery.gitlab_hosts", {})
    require(isinstance(configured, dict), "delivery.gitlab_hosts must be a mapping", "bad-config")
    hosts = {"gitlab.com": "https://gitlab.com"}
    for key, base in configured.items():
        require(isinstance(key, str) and re.fullmatch(r"[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?", key)
                and ".." not in key and key != "github.com" and isinstance(base, str),
                "Invalid GitLab host mapping", "bad-config")
        web, web_port = _url(base)
        require(web.scheme == "https" and web.username is None and web.path in ("", "/"),
                "GitLab web base must be a credential-free HTTPS authority", "bad-config")
        hosts[key] = "https://" + _authority(web, web_port)
    provider = "github" if hostname == "github.com" else "gitlab"
    require(selected in ("auto", provider), "Provider does not match origin", "issue-repository")
    if provider == "github":
        require(len(parts) == 2 and port is None,
                "Only a GitHub HTTPS or SSH origin is supported", "issue-repository")
        base = "https://github.com"
    else:
        require(hostname in hosts, "Configure this GitLab origin host explicitly", "issue-repository")
        base = hosts[hostname]
        if scheme == "https":
            parsed, actual_port = _url(remote)
            require("https://" + _authority(parsed, actual_port) == base,
                    "HTTPS origin does not match configured GitLab web authority", "issue-repository")
    host = base[len("https://"):]
    return {"provider": provider, "host": host, "project": path, "remote": remote,
            "web_url": base + "/" + path, "repository": host + "/" + path}


def item_number(target, url, kind="issues"):
    """Validate a canonical repository-owned URL and return the local IID."""
    allowed = ("issues", "pull") if target["provider"] == "github" else ("issues", "merge_requests")
    require(kind in allowed and isinstance(url, str), "A verified item URL is required", "issue-url")
    separator = "/" if target["provider"] == "github" else "/-/"
    # GitHub historically accepts case-insensitive paths; GitLab paths are exact.
    flags = re.IGNORECASE if target["provider"] == "github" else 0
    match = re.fullmatch(re.escape(target["web_url"] + separator + kind + "/")
                         + r"([1-9][0-9]*)", url, flags)
    require(match is not None, "URL must identify an item in the origin repository", "issue-url")
    return int(match.group(1))
