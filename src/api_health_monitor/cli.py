"""Command-line interface for API Health Monitor."""

from __future__ import annotations

import argparse

from api_health_monitor.monitor import run_monitor, write_report


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""

    parser = argparse.ArgumentParser(
        prog="api-health-monitor",
        description="Check HTTP API endpoints and save a JSON health report.",
    )
    parser.add_argument(
        "urls",
        nargs="+",
        metavar="URL",
        help="one or more absolute HTTP or HTTPS endpoint URLs",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="request timeout in seconds (default: 5)",
    )
    parser.add_argument(
        "--output",
        default="health_report.json",
        help="JSON report destination (default: health_report.json)",
    )
    return parser


def main() -> int:
    """Run endpoint checks, save the report, and return a process exit code."""

    parser = build_parser()
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be greater than zero")

    results = run_monitor(args.urls, timeout=args.timeout)
    report_path = write_report(results, args.output)

    healthy = sum(result.is_available for result in results)
    total = len(results)
    print(f"Health check complete: {healthy}/{total} endpoints available.")
    print(f"JSON report saved to: {report_path}")
    return 0 if healthy == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
