"""
Paper‑style tables for anomaly evaluation results.

This module extends the basic reporting utilities in
``aa.reporting.library_tables`` to produce tables that mirror those in the
original MATLAB Assaying Anomalies toolkit.  The functions here
assemble summary statistics, ranking information and long–short return
statistics into tidy ``pandas`` DataFrames.  Optional helpers are
provided to convert these tables into Markdown or LaTeX using
``aa.reporting.anomaly_tables``.

The primary entry points are:

* :func:`performance_summary` – build a table of mean returns,
  t‑statistics, Sharpe ratios and drawdowns for each anomaly.
* :func:`long_short_stats` – compute statistics on the high‑minus‑low
  (long–short) return series for each anomaly directly from the
  results of :func:`aa.analysis.anomaly_pipeline.evaluate_signals`.
* :func:`ranking_table` – produce a DataFrame ranking anomalies by
  a chosen metric.
* :func:`t_statistics_table` and :func:`sharpe_ratio_table` – extract
  t‑statistics and Sharpe ratios into dedicated tables.

These tables are intended for inclusion in academic papers.  They
preserve the structure and logic of the MATLAB outputs without
introducing any new modelling assumptions.  All inputs are expected to
be dictionaries produced by the existing Python pipeline.  Users can
choose to include an optional average row in the summary tables.
"""

from __future__ import annotations

from typing import Dict, Any, Optional, List

import pandas as pd

from . import anomaly_tables
from .library_tables import performance_table  # reuse lower‑level summary

from aa.analysis.anomaly_metrics import (
    mean_return,
    t_statistic,
    sharpe_ratio,
    max_drawdown,
)

__all__ = [
    "performance_summary",
    "long_short_stats",
    "ranking_table",
    "t_statistics_table",
    "sharpe_ratio_table",
    "to_markdown",
    "to_latex",
]


def performance_summary(
    metrics: Dict[str, Dict[str, Any]],
    *,
    average: bool = False,
    include: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Assemble a summary table of anomaly performance metrics.

    Given a dictionary mapping anomaly names to performance metrics
    (returned under the ``'metrics'`` key of
    :func:`aa.analysis.anomaly_pipeline.evaluate_signals`), this
    function constructs a tidy ``pandas`` DataFrame with one row per
    anomaly.  All numeric metrics present in the first entry of
    ``metrics`` are included by default.  Users may optionally pass
    ``include`` to specify a subset of columns to retain.

    Parameters
    ----------
    metrics : dict
        Mapping from anomaly identifiers to dictionaries of scalar
        metrics (e.g. ``mean_ew``, ``t_stat_ew``, ``sharpe_ew``,
        ``max_dd_ew``, ``mean_vw``, etc.).  Metrics are assumed to be
        scalars and are not modified here.
    average : bool, default False
        If True, an additional row labelled ``"Average"`` will be
        appended that contains the cross‑sectional mean of each numeric
        column.
    include : list of str, optional
        List of metric names to retain.  If provided, the returned
        DataFrame will contain only these columns, in the order given.

    Returns
    -------
    DataFrame
        A DataFrame with anomalies on the index and metrics as
        columns.  If ``average`` is True, an extra row labelled
        ``"Average"`` is appended.
    """
    # Build the full summary table via the lower‑level helper
    df = performance_table(metrics)
    # Restrict to specified columns if requested
    if include is not None:
        missing = [c for c in include if c not in df.columns]
        if missing:
            raise KeyError(f"Requested columns not found in metrics: {missing}")
        df = df[include]
    # Append average row if needed
    if average and not df.empty:
        numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        avg_row = df[numeric_cols].mean(axis=0)
        # Insert NaN for non‑numeric columns
        non_num = [c for c in df.columns if c not in numeric_cols]
        for c in non_num:
            avg_row[c] = float("nan")
        avg_row.name = "Average"
        df = pd.concat([df, avg_row.to_frame().T])
    return df


def long_short_stats(
    results: Dict[str, Dict[str, Any]],
    *,
    value_weighted: bool = False,
) -> pd.DataFrame:
    """Compute long–short (high‑minus‑low) return statistics for each anomaly.

    This function derives statistics directly from the per‑period
    high‑minus‑low series contained under the ``'hl_ts'`` key of the
    results returned by :func:`aa.analysis.anomaly_pipeline.evaluate_signals`.
    It computes the mean return, t‑statistic, Sharpe ratio and maximum
    drawdown for each anomaly.  These statistics correspond to the
    long–short portfolio and replicate the summary tables in the
    MATLAB toolkit.

    Parameters
    ----------
    results : dict
        Nested dictionary keyed by anomaly name.  Each entry must
        contain a ``'hl_ts'`` DataFrame with columns ``'hl_ew'`` and
        ``'hl_vw'``.
    value_weighted : bool, default False
        If True, use the value‑weighted spreads (``hl_vw``);
        otherwise use equal‑weighted spreads (``hl_ew``).

    Returns
    -------
    DataFrame
        A table with one row per anomaly and columns ``'mean'``,
        ``'t_stat'``, ``'sharpe'`` and ``'max_dd'`` summarising the
        long–short series.
    """
    stats: Dict[str, Dict[str, float]] = {}
    col = "hl_vw" if value_weighted else "hl_ew"
    for name, out in results.items():
        hl_ts = out.get("hl_ts")
        if hl_ts is None or col not in hl_ts.columns:
            continue  # skip anomalies with missing series
        series = pd.to_numeric(hl_ts[col], errors="coerce").dropna()
        # Use the basic metrics to compute summary statistics
        stats[name] = {
            "mean": mean_return(series),
            "t_stat": t_statistic(series),
            "sharpe": sharpe_ratio(series),
            "max_dd": max_drawdown(series),
        }
    return pd.DataFrame.from_dict(stats, orient="index")


def ranking_table(
    metrics: Dict[str, Dict[str, Any]],
    *,
    metric: str = "mean_ew",
    ascending: bool = False,
) -> pd.DataFrame:
    """Rank anomalies by a specified performance metric.

    Parameters
    ----------
    metrics : dict
        Mapping from anomaly names to metric dictionaries.  Each
        dictionary must contain the key given by ``metric``.
    metric : str, default ``"mean_ew"``
        The name of the metric to rank anomalies by.  Larger values
        receive a better (lower) rank when ``ascending`` is False.
    ascending : bool, default False
        Whether lower metric values correspond to better ranks.  If
        False (the default), higher values rank better (rank 1).

    Returns
    -------
    DataFrame
        A DataFrame with columns ``metric`` and ``rank`` where ``metric``
        contains the raw metric values and ``rank`` contains their
        ranks using dense ranking.
    """
    # Extract the chosen metric into a Series
    values = {name: stats.get(metric, float("nan")) for name, stats in metrics.items()}
    series = pd.Series(values, name=metric)
    # Compute dense ranks (ties receive the same rank)
    # When ascending=False, higher values get smaller rank numbers
    ranks = series.rank(method="dense", ascending=ascending).astype(int)
    # Assemble DataFrame
    df = pd.DataFrame({metric: series, "rank": ranks})
    # Sort by rank
    df = df.sort_values("rank")
    return df


def t_statistics_table(metrics: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
    """Extract t‑statistics into a dedicated table.

    Parameters
    ----------
    metrics : dict
        Dictionary mapping anomaly names to metric dictionaries.  Each
        dictionary should contain ``'t_stat_ew'`` and ``'t_stat_vw'``.

    Returns
    -------
    DataFrame
        A DataFrame with two columns, ``'t_stat_ew'`` and
        ``'t_stat_vw'``, containing the t‑statistics for equal‑weighted
        and value‑weighted high‑minus‑low returns, respectively.
    """
    rows: Dict[str, Dict[str, float]] = {}
    for name, stats in metrics.items():
        rows[name] = {
            "t_stat_ew": stats.get("t_stat_ew", float("nan")),
            "t_stat_vw": stats.get("t_stat_vw", float("nan")),
        }
    return pd.DataFrame.from_dict(rows, orient="index")


def sharpe_ratio_table(metrics: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
    """Extract Sharpe ratios into a dedicated table.

    Parameters
    ----------
    metrics : dict
        Dictionary mapping anomaly names to metric dictionaries.  Each
        dictionary should contain ``'sharpe_ew'`` and ``'sharpe_vw'``.

    Returns
    -------
    DataFrame
        A DataFrame with two columns, ``'sharpe_ew'`` and
        ``'sharpe_vw'``, containing the Sharpe ratios for equal‑weighted
        and value‑weighted high‑minus‑low returns, respectively.
    """
    rows: Dict[str, Dict[str, float]] = {}
    for name, stats in metrics.items():
        rows[name] = {
            "sharpe_ew": stats.get("sharpe_ew", float("nan")),
            "sharpe_vw": stats.get("sharpe_vw", float("nan")),
        }
    return pd.DataFrame.from_dict(rows, orient="index")


def to_markdown(df: pd.DataFrame, *, index: bool = True) -> str:
    """Render a DataFrame as a Markdown table.

    This is a thin wrapper around :func:`aa.reporting.anomaly_tables.to_markdown`.

    Parameters
    ----------
    df : DataFrame
        The table to render.
    index : bool, default True
        Whether to include the index in the output.

    Returns
    -------
    str
        A Markdown representation of the DataFrame.
    """
    return anomaly_tables.to_markdown(df, index=index)


def to_latex(df: pd.DataFrame, *, index: bool = True) -> str:
    """Render a DataFrame as a LaTeX table.

    This is a thin wrapper around :func:`aa.reporting.anomaly_tables.to_latex`.

    Parameters
    ----------
    df : DataFrame
        The table to render.
    index : bool, default True
        Whether to include the index in the output.

    Returns
    -------
    str
        A LaTeX representation of the DataFrame.
    """
    return anomaly_tables.to_latex(df, index=index)
