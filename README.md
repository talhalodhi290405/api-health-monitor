# API Health Monitor

A lightweight Python command-line utility for checking HTTP API endpoint availability, measuring response times, handling request failures, and exporting structured JSON health reports.

## Features

- Check one or multiple HTTP/HTTPS endpoints in a single run.
- Measure each request's response time in milliseconds.
- Treat HTTP 2xx and 3xx responses as available, and HTTP 4xx/5xx responses as unavailable.
- Capture request exceptions and continue checking the remaining endpoints.
- Validate endpoint URLs before making a network request.
- Configure request timeouts.
- Generate a JSON report with per-endpoint results and aggregate health totals.
- Run from the command line or import the monitoring functions into another Python program.

## Requirements

- Python 3.10 or newer
- pip
- Internet access to reach the endpoints you choose to monitor

The project uses [Requests](https://requests.readthedocs.io/) for HTTP requests and [pytest](https://docs.pytest.org/) for development tests.

## Installation

Clone the repository and move into its directory:

```powershell
git clone https://github.com/talhalodhi290405/api-health-monitor.git
cd api-health-monitor
```

Create and activate a virtual environment on Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the project with its development dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

The editable installation makes the `api-health-monitor` command available in the active environment.

## Usage

Check one endpoint:

```powershell
api-health-monitor https://example.com/health
```

Check multiple endpoints and choose a timeout and report location:

```powershell
api-health-monitor https://example.com/health https://httpbin.org/status/503 --timeout 4 --output reports/health_report.json
```

Show available command-line options:

```powershell
api-health-monitor --help
```

### Command-line options

| Argument | Description | Default |
| --- | --- | --- |
| `URL` | One or more absolute HTTP/HTTPS endpoint URLs | Required |
| `--timeout` | Request timeout in seconds; must be greater than zero | `5` |
| `--output` | Destination path for the JSON report | `health_report.json` |

The monitor checks endpoints sequentially. A request failure is recorded in that endpoint's result and does not prevent later endpoints from being checked.

### Exit codes

- `0`: every checked endpoint was available.
- `1`: at least one endpoint was unavailable or a request failed.
- `2`: command-line arguments were invalid (for example, a non-positive timeout).

## Example JSON report

The following is an illustrative report. Actual timestamps, response times, status codes, and errors depend on the endpoints at runtime.

```json
{
  "generated_at": "2026-11-16T12:00:00+00:00",
  "summary": {
    "total_endpoints": 2,
    "healthy": 1,
    "unhealthy": 1
  },
  "results": [
    {
      "url": "https://example.com/health",
      "is_available": true,
      "status_code": 200,
      "response_time_ms": 124.52,
      "checked_at": "2026-11-16T12:00:00+00:00",
      "error": null
    },
    {
      "url": "https://httpbin.org/status/503",
      "is_available": false,
      "status_code": 503,
      "response_time_ms": 98.31,
      "checked_at": "2026-11-16T12:00:00+00:00",
      "error": "HTTP 503"
    }
  ]
}
```

The report's `summary` counts available and unavailable endpoints. If a URL is invalid or a request raises a Requests exception, `status_code` is `null` and `error` explains the failure.

## Run tests

Install the development dependencies as shown above, then run:

```powershell
python -m pytest -v
```

The tests use mocked HTTP responses and temporary files. They do not depend on live external APIs.

## Project structure

```text
api-health-monitor/
├── src/
│   └── api_health_monitor/
│       ├── __init__.py
│       ├── cli.py
│       └── monitor.py
├── tests/
│   └── test_monitor.py
├── .gitignore
├── LICENSE
├── README.md
└── pyproject.toml
```

## Architecture

1. **CLI layer (`cli.py`)** parses endpoint URLs, timeout, and output path.
2. **Monitoring layer (`monitor.py`)** validates each URL, sends an HTTP GET request, measures elapsed time, and converts request failures into result objects.
3. **Reporting layer (`monitor.py`)** aggregates endpoint results and writes a formatted JSON report.
4. **Test layer (`tests/test_monitor.py`)** validates monitoring and report behavior with mocked network calls.

## Current scope and limitations

This is a small, synchronous monitoring utility intended for local use and portfolio demonstration. It does not currently provide continuous background scheduling, retries, parallel checks, alerting, authentication configuration, a web dashboard, or persistent historical storage.

Only HTTP GET checks are implemented. Use endpoints you are authorized to access, and choose a timeout appropriate for the service being checked.

## License

This project is distributed under the MIT License. See [LICENSE](LICENSE) for details.
