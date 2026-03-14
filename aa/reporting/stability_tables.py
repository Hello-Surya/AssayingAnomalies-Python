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
    results_by_spec: dict[str, Any],
    metric_fn: Callable[[Any], float],
) -> dict[str, str]:
    """Create a formatted robustness table across specifications."""
    rows: list[dict[str, Any]] = []
    for spec, result in results_by_spec.items():
        rows.append({"specification": spec, "metric": metric_fn(result)})
    df = pd.DataFrame(rows)
    return _format_table(df)


def null_distribution_summary(values: pd.Series | list[float]) -> dict[str, str]:
    """Summarize a null distribution and return formatted output."""
    s = pd.Series(values, dtype=float)
    df = pd.DataFrame(
        {
            "mean": [float(s.mean())],
            "std": [float(s.std(ddof=1))],
            "min": [float(s.min())],
            "median": [float(s.median())],
            "max": [float(s.max())],
        }
    )
    return _format_table(df)
