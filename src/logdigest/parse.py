from __future__ import annotations

import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import datetime

# 10.0.0.5 - - [13/Nov/2026:13:55:36 +0000] "GET /api/v1/jobs HTTP/1.1" 500 232
LOG_PATTERN = re.compile(
    r'(?P<ip>\b\d{1,3}(?:\.\d{1,3}){3}\b)'
    r'(?:\s\-){1,2}\s'
    r'\[(?P<ts>[^\]]+)\]'
    r'\s\"(?P<method>[A-Z]{3,7})\s'
    r'(?P<path>[^\"\s]+)\s'
    r'(?:HTTP/[123](?:\.[01]))\"'
    r'\s(?P<status>000|[1-5][0-9][0-9])\s'
    r'(?P<size>\d+|-)\s'
    r'\"(?P<referer>[^\"]*)\"\s'
    r'\"(?P<ua>[^\"]*)\"$'
)
TIMESTAMP_FORMAT = '%d/%b/%Y:%H:%M:%S %z'

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

def parse_line(line: str) -> LogEntry | None:
    """ Return a LogEntry or None if the line doesn't match. Never raises."""
    m = LOG_PATTERN.match(line)
    if m is None:
        return None
    try:
        ts = datetime.strptime(m['ts'], TIMESTAMP_FORMAT)
    except ValueError as err:
        # TODO
        # logging.error(err)
        return None

    raw_size = m['size']
    return LogEntry(
        ip=m['ip'],
        method=m['method'],
        path=m['path'],
        referer=m['referer'],
        size=0 if raw_size == "-" else int(raw_size),
        status=int(m['status']),
        ts=ts,
        ua=m['ua'],
    )

def read_entries(lines: Iterable[str]) -> Iterator[LogEntry]:
    """ Stream entries. Skips unparseable lines instead of aborting."""
    for line_num, line in enumerate(lines, start=1):
        entry = parse_line(line)
        if entry is not None:
            # TODO
            # logging.debug("line %d didn't match :: %s", line_num, line.strip())
            yield entry
