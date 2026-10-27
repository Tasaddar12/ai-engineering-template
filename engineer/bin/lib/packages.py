"""Registry metadata checks are advisory and fail to UNKNOWN when offline."""
import datetime as dt
import difflib
import json
from urllib.parse import quote
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
from .core import Failure

POPULAR = {"npm": ["react", "express", "lodash", "typescript", "axios", "next"],
           "pypi": ["requests", "numpy", "pandas", "django", "flask", "pytest"],
           "crates": ["serde", "tokio", "clap", "anyhow", "rand"]}


def check(args):
    registry = args.get("registry", "pypi").lower()
    if registry not in POPULAR:
        raise Failure("unknown-registry", registry, 2)
    items = []
    for package in args.pos:
        encoded = quote(package, safe="")
        urls = {"npm": f"https://registry.npmjs.org/{encoded}", "pypi": f"https://pypi.org/pypi/{encoded}/json", "crates": f"https://crates.io/api/v1/crates/{encoded}"}
        try:
            with urlopen(urls[registry], timeout=10) as response:
                metadata = json.load(response)
            releases = metadata.get("releases", metadata.get("versions", []))
            created = metadata.get("time", {}).get("created") if registry == "npm" else metadata.get("crate", {}).get("created_at")
            if registry == "pypi":
                dates = [release.get("upload_time_iso_8601") for versions in metadata.get("releases", {}).values() for release in versions if release.get("upload_time_iso_8601")]
                created = min(dates) if dates else None
            age = (dt.datetime.now(dt.timezone.utc)-dt.datetime.fromisoformat(created.replace("Z", "+00:00"))).days if created else None
            similar = [name for name in POPULAR[registry] if package != name and difflib.SequenceMatcher(None, package, name).ratio() > 0.82]
            reasons = (["recent package"] if age is not None and age < 30 else []) + (["few releases"] if len(releases) < 2 else []) + (["similar to "+", ".join(similar)] if similar else [])
            items.append({"package": package, "registry": registry, "verdict": "SUS" if reasons else "OK", "age_days": age, "release_count": len(releases), "reasons": reasons})
        except HTTPError as exc:
            items.append({"package": package, "registry": registry, "verdict": "MISSING" if exc.code == 404 else "UNKNOWN", "reason": str(exc)})
        except (OSError, ValueError, TypeError, KeyError) as exc:
            items.append({"package": package, "registry": registry, "verdict": "UNKNOWN", "reason": str(exc)})
    return {"packages": items, "count": len(items)}
