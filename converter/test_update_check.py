"""Tests for update_check.py -- all network access is faked.

No test here touches the network: the opener is injected, so these run
offline on any platform.
"""

import io
import json
import urllib.error

import update_check
from update_check import check_for_update, format_result


class _FakeResponse:
    def __init__(self, payload: bytes):
        self._payload = payload

    def read(self):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _opener_with(payload_dict, url=None):
    def opener(request_url, timeout):
        assert request_url == update_check.RELEASES_LATEST_URL
        assert timeout == update_check.TIMEOUT_SECONDS
        return _FakeResponse(json.dumps(payload_dict).encode("utf-8"))

    return opener


def _opener_raising(exc):
    def opener(request_url, timeout):
        raise exc

    return opener


def test_newer_release_reports_update_available():
    result = check_for_update(
        "0.1.0",
        opener=_opener_with({"tag_name": "v0.2.0",
                            "html_url": "https://example.invalid/r/v0.2.0"}))
    assert result["status"] == "update-available"
    assert result["latest"] == "0.2.0"
    assert "0.2.0" in format_result(result)


def test_same_version_is_up_to_date():
    result = check_for_update(
        "0.1.0", opener=_opener_with({"tag_name": "v0.1.0"}))
    assert result["status"] == "up-to-date"
    assert format_result(result).startswith("up to date")


def test_older_release_is_up_to_date():
    result = check_for_update(
        "0.1.0", opener=_opener_with({"tag_name": "v0.0.9"}))
    assert result["status"] == "up-to-date"


def test_tag_without_v_prefix_compares():
    result = check_for_update(
        "0.1.0", opener=_opener_with({"tag_name": "1.0.0"}))
    assert result["status"] == "update-available"
    assert result["latest"] == "1.0.0"


def test_404_means_no_release_published():
    err = urllib.error.HTTPError(update_check.RELEASES_LATEST_URL, 404,
                                 "Not Found", {}, io.BytesIO(b""))
    result = check_for_update("0.1.0", opener=_opener_raising(err))
    assert result["status"] == "no-release"
    assert "no release published yet" in format_result(result)


def test_http_500_is_unavailable_not_raised():
    err = urllib.error.HTTPError(update_check.RELEASES_LATEST_URL, 500,
                                 "Server Error", {}, io.BytesIO(b""))
    result = check_for_update("0.1.0", opener=_opener_raising(err))
    assert result["status"] == "unavailable"


def test_network_error_is_unavailable_not_raised():
    result = check_for_update(
        "0.1.0",
        opener=_opener_raising(
            urllib.error.URLError("no network in this test")))
    assert result["status"] == "unavailable"


def test_non_numeric_tag_is_unavailable():
    result = check_for_update(
        "0.1.0", opener=_opener_with({"tag_name": "beta"}))
    assert result["status"] == "unavailable"


def test_missing_tag_is_unavailable():
    result = check_for_update("0.1.0", opener=_opener_with({}))
    assert result["status"] == "unavailable"


def test_malformed_json_is_unavailable():
    def opener(request_url, timeout):
        return _FakeResponse(b"not json{")

    result = check_for_update("0.1.0", opener=opener)
    assert result["status"] == "unavailable"


def test_cli_check_only_exits_zero_and_prints(capsys, monkeypatch):
    import bank_statement

    monkeypatch.setattr(
        update_check, "check_for_update",
        lambda current, opener=None: {
            "status": "update-available", "current": current,
            "latest": "0.2.0",
            "url": "https://example.invalid/r/v0.2.0"})
    assert bank_statement.main(["--check-update"]) == 0
    out = capsys.readouterr().out
    assert "update available: 0.2.0" in out
