from pathlib import Path

import pytest

from logdigest.parse import LogEntry, Skip, parse_line, read_entries

FIXTURE = Path(__file__).parent / "fixtures" / "access.log"

BAD_TS = ('10.0.1.22 - - [13/Nov/2026:13:99:00 +0000] '
          '"GET / HTTP/1.1" 200 0 "-" "curl/8.5.0"')
GOOD = ('10.0.0.5 - - [13/Nov/2026:13:54:02 +0000] '
        '"GET /healthz HTTP/1.1" 200 2 "-" "kube-probe/1.29"')

def test_bad_timestamp_is_malformed():
    assert parse_line(BAD_TS) is Skip.MALFORMED

def test_bad_line_does_not_poison_next_line():
    results = [r for _, r in read_entries([BAD_TS, GOOD])]
    assert results[0] is Skip.MALFORMED
    assert isinstance(results[1], LogEntry)
    assert results[1].ts.minute == 54  # value from GOOD

def test_parses_combined_format():
    e = parse_line(GOOD)
    assert isinstance(e, LogEntry)
    assert e.status == 200
    assert e.path == "/healthz"
    assert e.size == 2

def test_ipv6_is_parsed():
    entry = parse_line(GOOD.replace("10.0.0.5", "2001:db8::1"))
    assert isinstance(entry, LogEntry)

def test_fixture_counts():
    with FIXTURE.open(encoding="utf-8") as fh:
        results = list(read_entries(fh))
    entries = [r for _, r in results if isinstance(r, LogEntry)]
    malformed = [r for _, r in results if r is Skip.MALFORMED]
    assert len(entries) == 26
    assert len(malformed) == 1  # 13:99:00

@pytest.mark.parametrize(
    "line", ["", "garbage", GOOD.replace("200", "5xx"), "-- comment"]
)
def test_malformed_lines_return_unknown_format(line):
    assert parse_line(line) is Skip.UNKNOWN_FORMAT

def test_dash_size_is_zero():
    entry = parse_line(GOOD.replace('" 200 2 "', '" 200 - "'))
    assert isinstance(entry, LogEntry)
    assert entry.size == 0
    assert entry.status == 200
