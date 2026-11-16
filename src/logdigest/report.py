"""Render a ``summarize()`` result as human-readable text."""

from __future__ import annotations

from typing import TypedDict


class Summary(TypedDict):
    """Holds the :func:`logdigest.cli.summarize`'s return value.

    Avoid a circular import on cli when importing the renderer.
    """

    total: int
    errors: int
    filtered: int
    worst_buckets: list[tuple[str, int]]
    worst_paths: list[tuple[str, int]]
    statuses: dict[int, int]
    skipped: dict[str, int]


BAR_WIDTH = 32


def _table(rows: list[tuple[str, int]], *, bar: bool = False) -> list[str]:
    """Format ``(label, count)`` rows as fixed-width lines."""
    if not rows:
        return ["   (none)"]

    width = max(len(label) for label, _ in rows)
    peak = max(count for _, count in rows)
    lines: list[str] = []
    for label, count in rows:
        line = f"   {label:<{width}}  {count:>4}"
        if bar:
            filled = max(1, round(count / peak * BAR_WIDTH))
            line += "  " + "\u2588" * filled
        lines.append(line)
    return lines


def render_tables(summary: Summary, *, threshold: int) -> str:
    """Print a human-readable report."""
    skipped = summary["skipped"]
    skip_total = sum(skipped.values())
    errors = summary["errors"]

    lines = [f"{summary['total']} parsed"]
    if summary["filtered"]:
        lines[0] += f" - {summary['filtered']} filtered (--since)"
    lines[0] += f" - {skip_total} skipped - {errors} errors (>={threshold})"

    if skipped:
        detail = ", ".join(
            f"{n} {reason}" for reason, n in sorted(skipped.items())
        )
        lines.append(f"  skipped: {detail}")

    statuses = summary["statuses"]
    if statuses:
        detail = ", ".join(f"{code} ({n})" for code, n in statuses.items())
        lines.append(f"  statuses: {detail}")

    lines += ["", "errors per bucket (UTC)"]
    lines += _table(summary["worst_buckets"], bar=True)

    lines += ["", "top error paths"]
    lines += _table(summary["worst_paths"])

    return "\n".join(lines)
