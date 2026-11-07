"""Opt-in new-version check for the bank-statement converter.

Runs ONLY when the user explicitly asks (``--check-update``). It does one
plain GET to the GitHub API for the latest release tag of this repository
and compares the tag with the local ``__version__``.

What it does NOT do (deliberately):
- never downloads or installs anything;
- never runs at startup or on every conversion -- the converter is
  offline by default, and this check is the single exception;
- never sends any data except the GET itself (no account, no file names,
  no telemetry).

Any failure (no network, no release published yet, unexpected response)
is reported as a status string, never raised: the check is advisory and
must not break a conversion. Status values:

- ``update-available`` -- a newer release tag exists;
- ``up-to-date`` -- the local version is >= the latest release tag;
- ``no-release`` -- the repository has no release published yet
  (HTTP 404 from the releases endpoint), so there is nothing to compare;
- ``unavailable`` -- network error, unexpected response, or a tag that
  cannot be parsed as a version.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

RELEASES_LATEST_URL = (
    "https://api.github.com/repos/alapha888/bank-statement-presale"
    "/releases/latest"
)
TIMEOUT_SECONDS = 5


def _parse_version(tag: str) -> tuple[int, ...] | None:
    """Parse "v1.2.3" / "1.2.3" into (1, 2, 3); None if not numeric."""
    s = (tag or "").strip().lstrip("vV")
    if not s:
        return None
    parts: list[int] = []
    for piece in s.split("."):
        if not piece.isdigit():
            return None
        parts.append(int(piece))
    return tuple(parts) if parts else None


def check_for_update(current_version: str, opener=None) -> dict:
    """Check the latest release tag against ``current_version``.

    ``opener`` is an injectable ``urlopen``-compatible callable
    ``(url, timeout) -> context manager with .read() -> bytes``; it exists
    so tests can run without network. Defaults to ``urllib.request.urlopen``.
    """
    open_url = opener or urllib.request.urlopen
    result = {"current": current_version, "latest": None, "url": None}
    try:
        with open_url(RELEASES_LATEST_URL,
                       timeout=TIMEOUT_SECONDS) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            result.update(status="no-release",
                          detail="no release published yet")
        else:
            result.update(status="unavailable",
                          detail=f"GitHub API returned HTTP {exc.code}")
        return result
    except (urllib.error.URLError, OSError, ValueError) as exc:
        result.update(status="unavailable", detail=str(exc))
        return result

    tag = payload.get("tag_name") if isinstance(payload, dict) else None
    latest = _parse_version(tag) if isinstance(tag, str) else None
    current = _parse_version(current_version)
    if latest is None or current is None:
        result.update(status="unavailable",
                      detail="could not parse release tag "
                             f"{tag!r} as a version")
        return result
    result["latest"] = tag.lstrip("vV")
    result["url"] = payload.get("html_url")
    if latest > current:
        result["status"] = "update-available"
    else:
        result["status"] = "up-to-date"
    return result


def format_result(result: dict) -> str:
    """One human-readable line for the CLI."""
    status = result["status"]
    current = result["current"]
    if status == "update-available":
        line = (f"update available: {result['latest']} "
                f"(you have {current})")
        if result.get("url"):
            line += f" — {result['url']}"
        return line
    if status == "up-to-date":
        return f"up to date: {current} is the latest release"
    if status == "no-release":
        return (f"no release published yet (you have {current}) — "
                "nothing to compare against")
    return (f"update check unavailable: {result.get('detail', 'unknown')} "
            f"(you have {current})")
