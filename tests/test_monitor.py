from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
import requests

from api_health_monitor.monitor import (
    EndpointResult,
    build_report,
    check_endpoint,
    run_monitor,
    write_report,
)


def test_check_endpoint_accepts_successful_response() -> None:
    response = type("Response", (), {"status_code": 200})()

    with patch("api_health_monitor.monitor.requests.get", return_value=response) as get:
        result = check_endpoint("https://example.com/health", timeout=2.0)

    assert result.is_available is True
    assert result.status_code == 200
    assert result.response_time_ms >= 0
    assert result.error is None
    get.assert_called_once_with("https://example.com/health", timeout=2.0)


def test_check_endpoint_marks_server_error_unavailable() -> None:
    response = type("Response", (), {"status_code": 503})()

    with patch("api_health_monitor.monitor.requests.get", return_value=response):
        result = check_endpoint("https://example.com/health")

    assert result.is_available is False
    assert result.status_code == 503
    assert result.error == "HTTP 503"


def test_check_endpoint_captures_request_timeout() -> None:
    with patch(
        "api_health_monitor.monitor.requests.get",
        side_effect=requests.Timeout("request timed out"),
    ):
        result = check_endpoint("https://example.com/health")

    assert result.is_available is False
    assert result.status_code is None
    assert result.error is not None
    assert result.error.startswith("Timeout:")


def test_check_endpoint_rejects_invalid_url_without_request() -> None:
    with patch("api_health_monitor.monitor.requests.get") as get:
        result = check_endpoint("not-a-valid-url")

    assert result.is_available is False
    assert result.status_code is None
    assert result.error is not None
    assert "Invalid URL" in result.error
    get.assert_not_called()


def test_check_endpoint_requires_positive_timeout() -> None:
    with pytest.raises(ValueError, match="timeout must be greater than zero"):
        check_endpoint("https://example.com/health", timeout=0)


def test_run_monitor_checks_all_urls() -> None:
    first = EndpointResult(
        url="https://one.example/health",
        is_available=True,
        status_code=200,
        response_time_ms=12.5,
        checked_at="2026-01-01T00:00:00+00:00",
    )
    second = EndpointResult(
        url="https://two.example/health",
        is_available=False,
        status_code=503,
        response_time_ms=8.0,
        checked_at="2026-01-01T00:00:00+00:00",
        error="HTTP 503",
    )

    with patch(
        "api_health_monitor.monitor.check_endpoint",
        side_effect=[first, second],
    ) as check:
        results = run_monitor([first.url, second.url], timeout=3.0)

    assert results == [first, second]
    assert check.call_count == 2
    check.assert_any_call(first.url, timeout=3.0)
    check.assert_any_call(second.url, timeout=3.0)


def test_write_report_creates_json_report_and_parent_directory(tmp_path: Path) -> None:
    result = EndpointResult(
        url="https://example.com/health",
        is_available=True,
        status_code=200,
        response_time_ms=15.25,
        checked_at="2026-01-01T00:00:00+00:00",
    )
    output_path = tmp_path / "reports" / "health_report.json"

    saved_path = write_report([result], output_path)
    report = json.loads(saved_path.read_text(encoding="utf-8"))

    assert saved_path == output_path
    assert report["summary"] == {
        "total_endpoints": 1,
        "healthy": 1,
        "unhealthy": 0,
    }
    assert report["results"][0]["url"] == result.url
    assert report["results"][0]["response_time_ms"] == 15.25


def test_build_report_handles_empty_results() -> None:
    report = build_report([])

    assert report["summary"] == {
        "total_endpoints": 0,
        "healthy": 0,
        "unhealthy": 0,
    }
    assert report["results"] == []
