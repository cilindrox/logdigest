from __future__ import annotations

import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

# 10.0.0.5 - - [13/Nov/2026:13:55:36 +0000] "GET /api/v1/jobs HTTP/1.1" 500 232
LOG_PATTERN = re.compile(
    r"(?P<ip>\S+)\s+\S+\s+\S+\s+"
    r"\[(?P<ts>[^\]]+)\]\s+"
    r'"(?P<method>[A-Z]+)\s+(?P<path>\S+)(?:\s+HTTP/[\d.]+)?"\s+'
    r"(?P<status>\d{3})\s+"
    r"(?P<size>\d+|-)\s+"
    r"\"(?P<referer>[^\"]*)\"\s"
    r"\"(?P<ua>[^\"]*)\"$"
)
TIMESTAMP_FORMAT = "%d/%b/%Y:%H:%M:%S %z"

class Skip(Enum):
    UNKNOWN_FORMAT = "unknown_format"
    MALFORMED = "malformed"


@dataclass(frozen=True, slots=True)
class LogEntry:
    ip: str
    method: str
    path: str
    referer: str
    size: int
    status: int
    ts: datetime
    ua: str


def parse_line(line: str) -> LogEntry | Skip:
    """Return a LogEntry or None if the line doesn't match. Never raises."""
    m = LOG_PATTERN.match(line)
    if m is None:
        return Skip.UNKNOWN_FORMAT
    try:
        ts = datetime.strptime(m["ts"], TIMESTAMP_FORMAT)
    except ValueError:
        return Skip.MALFORMED

    raw_size = m["size"]
    return LogEntry(
        ip=m["ip"],
        method=m["method"],
        path=m["path"],
        referer=m["referer"],
        size=0 if raw_size == "-" else int(raw_size),
        status=int(m["status"]),
        ts=ts,
        ua=m["ua"],
    )


def read_entries(lines: Iterable[str]) -> Iterator[tuple[int, LogEntry | Skip]]:
    """Stream (line_number, result) pairs."""
    for line_num, line in enumerate(lines, start=1):
        yield line_num, parse_line(line.rstrip("\r\n"))
