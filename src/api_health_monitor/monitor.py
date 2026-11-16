"""Core endpoint checks and JSON report generation."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

import requests


@dataclass(frozen=True, slots=True)
class EndpointResult:
    """Result of checking one HTTP endpoint."""

    url: str
    is_available: bool
    status_code: int | None
    response_time_ms: float
    checked_at: str
    error: str | None = None


def _utc_timestamp() -> str:
    """Return a timezone-aware UTC timestamp."""

    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _valid_http_url(url: str) -> bool:
    """Accept only absolute HTTP and HTTPS URLs with a host."""

    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def check_endpoint(url: str, timeout: float = 5.0) -> EndpointResult:
    """Check one endpoint and return its availability and timing information.

    HTTP 2xx and 3xx responses are considered available. HTTP 4xx and 5xx
    responses are recorded as unavailable. Request failures are captured in
    the result instead of terminating the entire monitoring run.
    """

    if timeout <= 0:
        raise ValueError("timeout must be greater than zero")

    if not _valid_http_url(url):
        return EndpointResult(
            url=url,
            is_available=False,
            status_code=None,
            response_time_ms=0.0,
            checked_at=_utc_timestamp(),
            error="Invalid URL. Provide an absolute http:// or https:// URL.",
        )

    started_at = time.perf_counter()
    try:
        response = requests.get(url, timeout=timeout)
        elapsed_ms = (time.perf_counter() - started_at) * 1000
        return EndpointResult(
            url=url,
            is_available=response.status_code < 400,
            status_code=response.status_code,
            response_time_ms=round(elapsed_ms, 2),
            checked_at=_utc_timestamp(),
            error=None if response.status_code < 400 else f"HTTP {response.status_code}",
        )
    except requests.RequestException as exc:
        elapsed_ms = (time.perf_counter() - started_at) * 1000
        return EndpointResult(
            url=url,
            is_available=False,
            status_code=None,
            response_time_ms=round(elapsed_ms, 2),
            checked_at=_utc_timestamp(),
            error=f"{type(exc).__name__}: {exc}",
        )


def run_monitor(urls: Iterable[str], timeout: float = 5.0) -> list[EndpointResult]:
    """Check each URL sequentially and return all results."""

    if timeout <= 0:
        raise ValueError("timeout must be greater than zero")
    return [check_endpoint(url, timeout=timeout) for url in urls]


def build_report(results: Iterable[EndpointResult]) -> dict[str, object]:
    """Build a JSON-serializable report with aggregate health statistics."""

    items = list(results)
    healthy = sum(item.is_available for item in items)
    total = len(items)
    return {
        "generated_at": _utc_timestamp(),
        "summary": {
            "total_endpoints": total,
            "healthy": healthy,
            "unhealthy": total - healthy,
        },
        "results": [asdict(item) for item in items],
    }


def write_report(results: Iterable[EndpointResult], output_path: str | Path) -> Path:
    """Write a formatted JSON report and return the output path."""

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    report = build_report(results)
    destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return destination
