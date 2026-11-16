import argparse
import json
import logging
import sys
from collections import Counter
from collections.abc import Iterator
from contextlib import nullcontext
from datetime import UTC, datetime
from typing import TextIO

from .parse import LogEntry, Skip, read_entries

BUCKETS = {
    "minute": "%Y-%m-%d %H:%M",
    "hour": "%Y-%m-%d %H:00",
    "day": "%Y-%m-%d"
}

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logdigest",
        description="Summarize HTTP access logs: error counts over time, noisiest paths.",
        epilog="Example: journalctl -u api --no-pager | logdigest - -n 5 --status 500",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default="-",
        help="log file, or '-' for stdin (default: -)",
    )
    parser.add_argument(
        "-n", "--top", type=int, default=10, help="rows per table (default: 10)"
    )
    parser.add_argument(
        "--status",
        type=int,
        default=500,
        help="count status >= N as errors (default: 500)",
    )
    parser.add_argument(
        "--since",
        type=_iso8601,
        metavar="ISO8601",
        help="ignore entries before this time (naive times are read as UTC)",
    )
    parser.add_argument(
        "--bucket",
        choices=tuple(BUCKETS),
        default="minute",
        help="time bucket (default: minute)",
    )
    parser.add_argument(
        "--json", action="store_true", help="emit JSON instead of tables"
    )
    parser.add_argument(
        "--verbose", help="increase log-level verbosity"
    )
    return parser


def _iso8601(value: str) -> datetime:
    try:
        dt = datetime.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"not an ISO-8601 timestamp: {value!r}") from exc
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def _open(path: str) -> TextIO:
    if path == "-":
        return sys.stdin
    return open(path, encoding="utf-8", errors="replace")


def summarize(
    results: Iterable[LogEntry | Skip],
    *,
    since: datetime | None,
    bucket: str,
    top: int,
    threshold: int,
) -> dict[str, object]:
    fmt = BUCKETS[bucket]
    errors: Counter[str] = Counter()
    paths: Counter[str] = Counter()
    statuses: Counter[int] = Counter()
    skips: Counter[str] = Counter()
    total = 0

    for line_num, item in enumerate(results, start=1):
        if isinstance(item, Skip):
            skips[item.value] += 1
            logger.debug('L%d: %s', line_num, item.value)
            continue

        if since is not None and item.ts < since:
            continue

        total +=1
        statuses[item.status] += 1
        if item.status >= threshold:
            errors[item.ts.strftime(fmt)] += 1
            paths[item.path] += 1
    return {
        "total": total,
        "errors": sum(errors.values()),
        "worst_buckets": errors.most_common(top),
        "worst_paths": paths.most_common(top),
        "statuses": dict(sorted(statuses.items())),
        "skipped": dict(skips),
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    ctx = nullcontext(sys.stdin) if args.path == "-" else _open(args.path)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(levelname)s: %(message)s",
        stream=sys.stderr,
        force=True,
    )

    try:
        with ctx as fh:
            result = summarize(
                read_entries(fh),
                since=args.since,
                bucket=args.bucket,
                top=args.top,
                threshold=args.status)
    except FileNotFoundError:
        logger.error("%s: no such file", args.path)
        return 2
    except BrokenPipeError:
        return 0

    if args.json:
        json.dump(result, sys.stdout, indent=2)
        print()
        return 0

    return 0
