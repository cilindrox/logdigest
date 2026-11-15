from pathlib import Path
import pytest

from logdigest.parse import parse_line, read_entries

FIXTURE = Path(__file__).parent / "fixtures" / "access.log"

GOOD = '10.0.0.5 - - [13/Nov/2026:13:55:36 +0000] "GET /api/v1/jobs HTTP/1.1" 500 232'

def test_parses_combined_format():
    e = parse_line(GOOD)
    assert e is not None and e.status == 500 and e.path == "/api/v1/jobs"

@pytest.mark.parametrize("line", ["", "garbage", GOOD.replace("500", "5xx"), "-- comment"])
def test_malformed_lines_return_none(line):
    assert parse_line(line) is None

def test_dash_size_is_zero():
    assert parse_line(GOOD.replace("232", "-")).size == 0

def test_reader_is_lazy():
    consumed = []
    def lines():
        for i in range(5):
            consumed.append(i)
            yield GOOD
    it = read_entries(lines())
    # nothing read until asked
    assert consumed == []
    next(it)
    assert consumed == [0]

def test_generator_streams_without_loading_file(tmp_path):
    p = tmp_path / "access.log"
    p.write_text(GOOD + "\n" * 10_000)
    with p.open(encoding="utf-8") as fh:
        assert sum(1 for _ in read_entries(fh)) == 10_001
