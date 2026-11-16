from pathlib import Path

import pytest

from logdigest.cli import main, summarize
from logdigest.parse import parse_line, read_entries

# 30 lines, 4 unparseable
FIXTURE = Path(__file__).parent / "fixtures" / "access.log"


def load():
    with FIXTURE.open(encoding="utf-8") as fh:
        return list(read_entries(fh))


def test_fixture_totals():
    entries = load()
    assert len(entries) == 30


def test_error_count_and_distinct_buckets():
    result = summarize(
            iter(load()),
            since=None,
            bucket="minute",
            top=5, 
            threshold=500)
    assert result["total"] == 26
    assert result["errors"] == 11
    assert result["worst_buckets"] == [
        ("2026-11-13 13:56", 6),
        ("2026-11-13 13:55", 5),
    ]


def test_summarise_counts_skips_and_status_zero():
    bad_ts = (
        "10.0.1.22 - - [13/Nov/2026:13:99:00 +0000] "
        '"GET / HTTP/1.1" 200 0 "-" "curl/8.5.0"'
    )
    good = (
        "10.0.0.5 - - [13/Nov/2026:13:54:02 +0000] "
        '"GET /healthz HTTP/1.1" 200 2 "-" "kube-probe/1.29"'
    )

    results = list(read_entries([
        good,
        bad_ts,
        good.replace(" 200 2 ", " 000 2 "),
    ]))

    out = summarize(results, since=None, bucket="minute", top=5, threshold=500)

    assert out["total"] == 2
    assert out["statuses"] == {0: 1, 200: 1}
    assert out["skipped"] == {"malformed": 1}
    assert out["errors"] == 0
