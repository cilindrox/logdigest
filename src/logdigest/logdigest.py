import logging
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import TypedDict

logFile = Path('/home/cx/github/cilindrox/logdigest/tests/fixtures/access.log')
log_pattern = re.compile(
        r"(?P<ip>\b\d{1,3}(?:\.\d{1,3}){3}\b)"
        r"(?:\s\-){1,2}\s"
        r"\[(?P<timestamp>[^\]]+)\]"
        r"\s\"(?P<method>[A-Z]{3,7})\s"
        r"(?P<path>[^\"\s]+)\s"
        r"(?:HTTP/[123](?:\.[01]))\""
        r"\s(?P<code>000|[1-5][0-9][0-9])\s"
        r"(?P<size>\d+|-)\s"
        r"\"(?P<referer>[^\"]*)\"\s"
        r"\"(?P<ua>[^\"]*)\"$"
)

# 13/Nov/2026:13:54:02 +0000
TIMESTAMP_FORMAT = '%d/%b/%Y:%H:%M:%S %z'

class LogEntry(TypedDict):
    code: str
    ip: str
    method: str
    path: str
    referer: str
    size: int | None
    timestamp: datetime
    ua: str

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

parsed_logs = []
rejected_lines = 0

# TODO: abort if rejected exceeds threshold

with open(logFile, encoding='utf-8') as file:
    for line_num, line in enumerate(file, start=1):
        match = log_pattern.search(line.strip())
        if not match:
            logging.debug("Line %d didn't match :: %s", line_num, line.strip())
            rejected_lines += 1
            continue

        parsed_logs.append(match.groupdict())

logging.info("Total matches: %d", len(parsed_logs))

ips = []
for line_num, logs in enumerate(parsed_logs, start=1):
    try:
        ts = datetime.strptime(logs.get('timestamp'), TIMESTAMP_FORMAT)
    except ValueError as err:
        logging.error("Line %d skipped: %s", line_num, err)

    ips.append(logs.get('ip'))

    logging.info(
            'time: %s, method: %s, code: %s, path: %s, source: %s, referer: %s, size: %s, ua: %s',
            logs.get('timestamp'),
            logs.get('method'),
            logs.get('code'),
            logs.get('path'),
            logs.get('ip'),
            logs.get('referer'),
            logs.get('size'),
            logs.get('ua'),
            )

top_ips = Counter(ips).most_common(5)
logging.info('Top IPs: %s', top_ips)
logging.info(
        "Total matches: %d (%d rejected)",
        len(parsed_logs),
        rejected_lines
        )
