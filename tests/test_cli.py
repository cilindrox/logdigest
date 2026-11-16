import argparse
import json
from datetime import UTC, datetime
from io import StringIO
from pathlib import Path

import pytest

from logdigest.cli import _iso8601, main, summarize
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


def test_error_count_and_distinct_buckets():
    result = summarize(
        load(), since=None, bucket="minute", top=5, threshold=500
    )
    assert result["total"] == 26
    assert result["errors"] == 11
    assert result["filtered"] == 0
    assert result["worst_buckets"] == [
        ("2026-11-13 13:56", 6),
        ("2026-11-13 13:55", 5),
    ]


def test_summarise_counts_skips_and_status_zero():
    results = list(
        read_entries(
            [
                GOOD,
                BAD_TS,
                GOOD.replace(" 200 2 ", " 000 2 "),
            ]
        )
    )

    out = summarize(results, since=None, bucket="minute", top=5, threshold=500)

    assert out["total"] == 2
    assert out["statuses"] == {0: 1, 200: 1}
    assert out["skipped"] == {"malformed": 1}
    assert out["errors"] == 0


def test_top_path_is_deterministic():
    result = summarize(
        load(),
        since=None,
        bucket="minute",
        top=1,
        threshold=500,
    )
    assert result["worst_paths"] == [("/api/v1/jobs", 7)]


def test_since_excludes_earlier_minutes():
    since = datetime(2026, 11, 13, 13, 56, tzinfo=UTC)
    result = summarize(
        load(),
        since=since,
        bucket="minute",
        top=5,
        threshold=500,
    )
    assert result["total"] == 13
    assert result["filtered"] == 13
    assert result["errors"] == 6


def test_bucket_hour_collapses_minutes():
    result = summarize(load(), since=None, bucket="hour", top=5, threshold=500)
    assert result["worst_buckets"] == [("2026-11-13 13:00", 11)]


def test_default_output_is_the_table_report(capsys):
    assert main([str(FIXTURE)]) == 0
    captured = capsys.readouterr()
    assert captured.out.startswith("26 parsed - 4 skipped - 11 errors (>=500)")
    assert "1 malformed" in captured.out
    assert "3 unknown_format" in captured.out
    assert "errors per bucket (UTC)" in captured.out
    assert "top error paths" in captured.out
    assert captured.err == ""


def test_json_output_is_parseable(capsys):
    assert main([str(FIXTURE), "--json", "--top", "1"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["total"] == 26
    assert data["errors"] == 11
    assert data["statuses"]["500"] == 7
    assert data["worst_paths"] == [["/api/v1/jobs", 7]]
    assert data["skipped"] == {"malformed": 1, "unknown_format": 3}


def test_since_is_reported_as_filtered(capsys):
    assert main([str(FIXTURE), "--since", "2026-11-13T13:56:00Z"]) == 0
    out = capsys.readouterr().out
    assert "13 parsed" in out
    assert "13 filtered (--since)" in out


@pytest.mark.parametrize("kind", ["missing", "directory"])
def test_io_failures_exit_2(kind, tmp_path, capsys):
    path = tmp_path / "absent.log" if kind == "missing" else tmp_path

    assert main([str(path)]) == 2

    captured = capsys.readouterr()
    assert captured.out == ""
    assert f"ERROR: {path}" in captured.err
    assert "Traceback" not in captured.err


def test_wrong_format_exits_1_and_prints_nothing(tmp_path, capsys):
    p = tmp_path / "wrong.log"
    p.write_text('{"level":"info"}\n' * 5, encoding="utf-8")

    assert main([str(p)]) == 1

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "parsed 0 of 5 lines" in captured.err


def test_empty_file_exits_0(tmp_path, capsys):
    p = tmp_path / "empty.log"
    p.write_text("", encoding="utf-8")

    assert main([str(p)]) == 0

    out = capsys.readouterr().out
    assert out.startswith("0 parsed - 0 skipped - 0 errors (>=500)")
    assert out.count("(none)") == 2


@pytest.fixture
def no_dup2(monkeypatch):
    """Keep _silence_stdout from dup2-ing pytest's real capture fd."""
    monkeypatch.setattr("logdigest.cli._silence_stdout", lambda: None)


def test_write_side_broken_pipe_exits_0(monkeypatch, no_dup2):
    class Boom:
        def write(self, _):
            raise BrokenPipeError

        def flush(self):
            pass

    monkeypatch.setattr("sys.stdout", Boom())
    monkeypatch.setattr("sys.stdin", StringIO(GOOD + "\n"))
    assert main(["-"]) == 0


def test_read_side_broken_pipe_exits_0(monkeypatch, no_dup2):
    class Boom:
        def __iter__(self):
            raise BrokenPipeError

    monkeypatch.setattr("sys.stdin", Boom())
    assert main(["-"]) == 0


def test_iso8601_raises_on_invalid_format():
    with pytest.raises(argparse.ArgumentTypeError, match="ISO-8601"):
        _iso8601("FOOBAR")


def test_iso8601_assumes_utc_for_naive_input():
    assert _iso8601("2026-11-14").tzinfo is UTC
    assert _iso8601("2026-11-14T00:00:05Z").tzinfo is not None
