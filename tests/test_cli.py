import argparse
from pathlib import Path

import pytest

from logdigest.cli import _iso8601, _open_stream, main, summarize
from logdigest.parse import read_entries

FIXTURE = Path(__file__).parent / "fixtures" / "access.log"

BAD_TS = (
    "10.0.1.22 - - [13/Nov/2026:13:99:00 +0000] "
    '"GET / HTTP/1.1" 200 0 "-" "curl/8.5.0"'
)
GOOD = (
    "10.0.0.5 - - [13/Nov/2026:13:54:02 +0000] "
    '"GET /healthz HTTP/1.1" 200 2 "-" "kube-probe/1.29"'
)


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
    results = list(read_entries([
        GOOD,
        BAD_TS,
        GOOD.replace(" 200 2 ", " 000 2 "),
    ]))

    out = summarize(results, since=None, bucket="minute", top=5, threshold=500)

    assert out["total"] == 2
    assert out["statuses"] == {0: 1, 200: 1}
    assert out["skipped"] == {"malformed": 1}
    assert out["errors"] == 0


def test_top_path_is_deterministic():
    result = summarize(
            iter(load()),
            since=None,
            bucket="minute",
            top=1,
            threshold=500,
    )
    assert result["worst_paths"] == [("/api/v1/jobs", 7)]


def test_since_excludes_earlier_minutes():
    from datetime import UTC, datetime
    since = datetime(2026, 11, 13, 13, 56, tzinfo=UTC)
    result = summarize(
        iter(load()),
        since=since,
        bucket="minute",
        top=5,
        threshold=500,
    )
    assert result["total"] == 13
    assert result["errors"] == 6


def test_cli_exit_code_on_missing_file(capsys):
    assert main(["/nonexistent/access.log"]) == 2
    assert (
        'ERROR: /nonexistent/access.log: '
        'No such file or directory\n'
    ) in capsys.readouterr().err

def test_cli_reads_stdin(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", FIXTURE.open(encoding="utf-8"))
    assert main(["-", "--json", "--top", "1"]) == 0
    assert '"total": 26' in capsys.readouterr().out


def test_open_stream_does_not_close_stdin(monkeypatch, tmp_path):
    p = tmp_path / "a.log"
    p.write_text(GOOD + "\n", encoding="utf-8")
    fake = p.open(encoding="utf-8")
    monkeypatch.setattr("sys.stdin", fake)
    with _open_stream("-") as fh:
        assert fh.readline().startswith(GOOD[:10])
    assert not fake.closed


def test_iso8602_raises_on_invalid_format():
    with pytest.raises(argparse.ArgumentTypeError):
        _iso8601('FOOBAR')


def test_iso8602_parses_valid_ts():
    _iso8601('2026-11-14T00:00:05Z')


def test_iso8602_parses_simple_ts():
    _iso8601('2026-11-14')
