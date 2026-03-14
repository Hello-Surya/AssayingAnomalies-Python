"""
Stability and robustness reporting utilities.
"""

from __future__ import annotations

from typing import Any, Callable

import pandas as pd

__all__ = ["stability_table", "robustness_table", "null_distribution_summary"]


def _format_table(df: pd.DataFrame) -> dict[str, str]:
    """Format a DataFrame into Markdown and LaTeX."""
    fmt_df = df.copy()

    # format floats nicely
    for col in fmt_df.columns:
        if pd.api.types.is_float_dtype(fmt_df[col]):
            fmt_df[col] = fmt_df[col].map(lambda x: f"{x:.3f}" if pd.notna(x) else "")

    try:
        markdown = fmt_df.to_markdown(index=False)
    except Exception:
        header = "| " + " | ".join(str(c) for c in fmt_df.columns) + " |"
        separator = "|" + "|".join("---" for _ in fmt_df.columns) + "|"
        rows = []
        for _, row in fmt_df.iterrows():
            rows.append("| " + " | ".join(str(v) for v in row.tolist()) + " |")
        markdown = "\n".join([header, separator] + rows)

    try:
        latex = fmt_df.to_latex(index=False, escape=False)
    except Exception:
        latex = ""

    return {"markdown": markdown, "latex": latex}


def stability_table(
    results_by_regime: dict[str, Any],
    metric_fn: Callable[[Any], float],
) -> dict[str, str]:
    """Create a formatted stability table across regimes."""
    rows: list[dict[str, Any]] = []
    for regime, result in results_by_regime.items():
        rows.append({"regime": regime, "metric": metric_fn(result)})

    df = pd.DataFrame(rows)
    return _format_table(df)


def robustness_table(
    results_by_spec: Any,
    metric_fn: Callable[[Any], float] | None = None,
) -> dict[str, str]:
    """Create a formatted robustness table."""

    # case 1: already a DataFrame
    if isinstance(results_by_spec, pd.DataFrame):
        return _format_table(results_by_spec.copy())

    # case 2: dict of results
    if metric_fn is None:
        raise TypeError("metric_fn must be provided when results_by_spec is a dict")

    rows: list[dict[str, Any]] = []
    for spec, result in results_by_spec.items():
        rows.append({"specification": spec, "metric": metric_fn(result)})

    df = pd.DataFrame(rows)
    return _format_table(df)


def null_distribution_summary(
    values: pd.Series | list[float],
    observed: float | None = None,
) -> dict[str, str]:
    """Summarize a null distribution and optionally compare to an observed value."""

    s = pd.Series(values, dtype=float)

    data: dict[str, list[float]] = {
        "mean": [float(s.mean())],
        "std": [float(s.std(ddof=1))],
        "min": [float(s.min())],
        "median": [float(s.median())],
        "max": [float(s.max())],
    }

    if observed is not None:
        data["observed"] = [float(observed)]
        data["p_left"] = [float((s <= observed).mean())]
        data["p_right"] = [float((s >= observed).mean())]
        data["p_two_sided"] = [float((s.abs() >= abs(observed)).mean())]

    df = pd.DataFrame(data)

    return _format_table(df)
