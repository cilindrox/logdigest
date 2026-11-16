# logdigest

A lightweight Python CLI utility to digest HTTP access logs into error rates per
time bucket and highlight your noisiest endpoints.

Features:
- **Time-Bucketed Error Rates:** Aggregates HTTP status codes across
  configurable time intervals to spot traffic anomalies and spikes.
- **Noisiest Endpoints:** Ranks the paths producing the most errors, to help
  see where failures concentrate.

## Installation

Ensure you have Python installed (see `.python-version`), then install the
package:

```bash
git clone https://github.com/cilindrox/logdigest.git
cd logdigest
pip install .
```

> **NOTE**: For development and running tests, install with dev dependencies:
> `pip install -e '.[dev]'`

Alternatively, you can build and run the container directly using Docker or
Docker Buildx Bake:

```bash
make bake
```

## Usage

Pass an access log file or pipe `stdin` directly into `logdigest`:

```bash
logdigest /var/log/nginx/access.log [OPTIONS]
```

Run `logdigest` with no path, or with `-`, to read stdin.

The following options are supported:

| Flag            | Description                                        |
| ---             | ---                                                |
| `-b, --bucket`  | Time bucket unit. One of `minute`, `hour` or `day` |
| `-n, --top`     | Rows per table (default: `10`)                     |
| `--status`      | Count status >= N as errors (default: `500`)       |
| `--since`       | Ignore entries before this ISO-8601 time           |
| `--json`        | Print a JSON-formatted report                      |
| `-v, --verbose` | Print skip reasons to stderr                       |

### Example

```bash
logdigest --bucket minute --top 5 < access.log
```

**Sample Output:**

```text
26 parsed - 4 skipped - 11 errors (>=500)
  skipped: 1 malformed, 3 unknown_format
  statuses: 200 (10), 201 (1), 301 (1), 304 (1), 404 (1), 429 (1), 500 (7), 502 (2), 503 (1), 504 (1)

errors per bucket (UTC)
   2026-11-13 13:56     6  ████████████████████████████████
   2026-11-13 13:55     5  ███████████████████████████

top error paths
   /api/v1/jobs               7
   /api/v1/jobs/8412/run      1
   /api/v1/backtests/2291     1
   /api/v1/jobs/8412          1
   /api/v1/backtests          1
```

## Development

This repository includes a `Makefile` to streamline common development tasks.
Run `make help` for details.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file
for details.
