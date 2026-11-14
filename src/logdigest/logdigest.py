from pathlib import Path
import re
import logging

logFile = Path('/home/cx/github/cilindrox/logdigest/tests/fixtures/access.log')
log_pattern = re.compile(
        r"(?P<ip>\b\d{1,3}(?:\.\d{1,3}){3}\b)"
        r"(?:\s\-){1,2}\s"
        r"\[(?P<timestamp>.*)\]"
        r"\s\"(?P<method>[A-Z]{3,7})\s"
        r"(?P<path>.*)"
        r"(?:HTTP/1\.1)\""
        r"\s(?P<code>[1-5][0-9][0-9])\s"
        r"(?:\d*)\s"
        r"(?:\"\-\")\s"
        r"\"(?P<ua>.*)\"$"
)

# logging.basicConfig()

parsed_logs = []

with open(logFile, 'r', encoding='utf-8') as file:
    for line in file:
        match = log_pattern.search(line.strip())
        if match:
            parsed_logs.append(match.groupdict())

# ips = [ip for ip in parsed_logs if ip]
for match in parsed_logs:
    print(f"{match.get('method')} | {match.get('path')} | {match.get('code')} | {match.get('ip')} | {match.get('timestamp')} by {match.get('ua')}")
    # logging.info(match.get('method'))
