"""
Large‑scale anomaly evaluation pipeline.

This module contains functions to evaluate many anomaly signals
simultaneously.  Given a panel of returns and firm‑level
characteristics, the pipeline performs univariate portfolio sorts for
each signal, constructs high‑minus‑low series and computes a suite
of performance metrics (mean return, t‑statistic, Sharpe ratio and
drawdown).  The results are returned in a structured format
suitable for further analysis or conversion to tables.

The pipeline mirrors the MATLAB logic used in ``makeAnomStratResults.m``
and related scripts but adheres to Pythonic conventions.  It relies
on the univariate sort implementation in :mod:`aa.asset_pricing` and
the performance metrics defined in :mod:`aa.analysis.anomaly_metrics`.

Example
-------
>>> import pandas as pd
>>> from aa.analysis.anomaly_pipeline import evaluate_signals
>>> panel = pd.DataFrame({
...     'date': ['2020-01-31','2020-01-31','2020-02-28','2020-02-28'],
...     'permno': [1,2,1,2],
...     'ret': [0.01, 0.02, -0.005, 0.015],
...     'me': [100, 200, 105, 210],
...     'exchcd': [1, 1, 1, 1],
...     'size': [10, 20, 11, 22],
...     'value': [0.5, 0.4, 0.55, 0.45],
... })
>>> results = evaluate_signals(panel, signals=['size', 'value'])
>>> results['size']['metrics']['mean_ew']
0.0
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any

import numpy as np
import pandas as pd

from aa.asset_pricing import SortConfig, univariate_sort
from aa.analysis.anomaly_metrics import evaluate_anomaly

__all__ = ["evaluate_signals"]


def _identify_signals(
    panel: pd.DataFrame,
    *,
    returns_col: str,
    size_col: str,
    exch_col: str,
    provided: Optional[List[str]] = None,
) -> List[str]:
    """Identify signal columns in a panel DataFrame.

    This helper examines the DataFrame columns and returns a list of
    candidate signal names.  If ``provided`` is not None, it is
    returned directly.  Otherwise, the function drops a fixed set of
    non‑signal columns (date, permno, returns, size and exchange
    codes) and treats the remainder as signals.

    Parameters
    ----------
    panel : DataFrame
        Input panel containing returns and characteristics.
    returns_col : str
        Name of the return column.
    size_col : str
        Name of the size column (used for value‑weighted returns).
    exch_col : str
        Name of the exchange code column.
    provided : list[str], optional
        Explicit list of signals supplied by the caller.

    Returns
    -------
    list of str
        Names of columns to be treated as signals.
    """
    if provided is not None:
        return provided
    drop_cols = {"date", "permno", returns_col, size_col, exch_col}
    candidates = [c for c in panel.columns if c not in drop_cols]
    # Return only numeric columns
    signals = [c for c in candidates if pd.api.types.is_numeric_dtype(panel[c])]
    return signals


def _compute_high_low(ts: pd.DataFrame) -> pd.DataFrame:
    """Compute high‑minus‑low series from a time‑series of bin returns.

    Parameters
    ----------
    ts : DataFrame
        Output of :func:`aa.asset_pricing.univariate_sort` under key
        ``'time_series'``.  Must contain columns ``date``, ``bin``,
        ``ret_ew`` and ``ret_vw``.

    Returns
    -------
    DataFrame
        DataFrame with columns ``date``, ``hl_ew`` and ``hl_vw``
        containing the per‑period high‑minus‑low spreads.  Missing
        values indicate periods where either the high or low bin is
        missing.
    """
    if ts.empty:
        return pd.DataFrame(columns=["date", "hl_ew", "hl_vw"])
    # Pivot equal‑weighted returns by bin
    ew_wide = ts.pivot(index="date", columns="bin", values="ret_ew")
    # The highest bin is the maximum numeric bin
    numeric_bins = [b for b in ew_wide.columns if isinstance(b, (int, np.integer))]
    if not numeric_bins:
        return pd.DataFrame(columns=["date", "hl_ew", "hl_vw"])
    hi_bin = max(numeric_bins)
    lo_bin = min(numeric_bins)
    hl_ew = ew_wide.get(hi_bin) - ew_wide.get(lo_bin)
    # Pivot value‑weighted returns; may contain NaN if size not provided
    vw_wide = ts.pivot(index="date", columns="bin", values="ret_vw")
    hl_vw = vw_wide.get(hi_bin) - vw_wide.get(lo_bin)
    hl = pd.DataFrame(
        {"date": hl_ew.index, "hl_ew": hl_ew.values, "hl_vw": hl_vw.values}
    )
    return hl


def evaluate_signals(
    panel: pd.DataFrame,
    *,
    signals: Optional[List[str]] = None,
    returns_col: str = "ret",
    size_col: str = "me",
    exch_col: str = "exchcd",
    bins: int = 5,
    nyse_breaks: bool = False,
    min_obs: int = 20,
) -> Dict[str, Dict[str, Any]]:
    """Evaluate multiple anomaly signals on a common panel of data.

    Given a long‑format panel of returns and characteristics, this
    function iterates over each signal column, performs a univariate
    portfolio sort, constructs high‑minus‑low series and computes
    performance metrics.  The outputs are returned as a nested
    dictionary keyed by the signal name.

    Parameters
    ----------
    panel : DataFrame
        Long format panel with columns ``date``, ``permno``, a
        returns column (default ``ret``), an optional size column
        (default ``me``), an optional exchange code column (default
        ``exchcd``) and one or more signal columns.  Each row
        corresponds to a firm‑period observation.
    signals : list[str], optional
        Names of signal columns to evaluate.  If omitted, all
        columns other than the fixed identifiers (``date``, ``permno``,
        returns, size and exchange codes) are treated as signals.
    returns_col : str, default ``ret``
        Name of the returns column.
    size_col : str, default ``me``
        Name of the size column (used for value‑weighted returns).
    exch_col : str, default ``exchcd``
        Name of the exchange code column (NYSE == 1).  If the
        column is not present, all firms are treated as non‑NYSE.
    bins : int, default 5
        Number of portfolios to form in each period.
    nyse_breaks : bool, default False
        Whether to compute breakpoints using only NYSE stocks.
    min_obs : int, default 20
        Minimum number of observations required in both the
        breakpoint and full universes for a period to be sorted.

    Returns
    -------
    dict
        Nested dictionary where each key is a signal name and the
        value is another dictionary with the following entries:

        ``'metrics'`` – Dictionary of performance metrics for the
        high‑minus‑low series.  Keys are ``mean_ew``, ``t_stat_ew``,
        ``sharpe_ew``, ``max_dd_ew``, ``mean_vw``, ``t_stat_vw``,
        ``sharpe_vw``, and ``max_dd_vw``.

        ``'time_series'`` – DataFrame with columns ``date``, ``bin``,
        ``ret_ew`` and ``ret_vw``.

        ``'summary'`` – DataFrame summarising the mean returns per
        bin and the high‑minus‑low (L‑S) row.

        ``'hl_ts'`` – DataFrame with columns ``date``, ``hl_ew`` and
        ``hl_vw`` containing the high‑minus‑low spreads by period.
    """
    panel = panel.copy()
    # Identify signals if not provided
    sigs = _identify_signals(
        panel,
        returns_col=returns_col,
        size_col=size_col,
        exch_col=exch_col,
        provided=signals,
    )
    results: Dict[str, Dict[str, Any]] = {}
    # Pre‑extract returns, size and exchange codes for efficiency
    returns_df = panel[["date", "permno", returns_col]].rename(
        columns={returns_col: "ret"}
    )
    size_df = None
    if size_col in panel.columns:
        size_df = panel[["date", "permno", size_col]].rename(columns={size_col: "me"})
    exch_df = None
    if exch_col in panel.columns:
        exch_df = panel[["date", "permno", exch_col]].rename(
            columns={exch_col: "exchcd"}
        )
    # Evaluate each signal independently
    for sig in sigs:
        sig_df = panel[["date", "permno", sig]].rename(columns={sig: "signal"})
        # Perform univariate sort
        res = univariate_sort(
            returns=returns_df,
            signal=sig_df,
            size=size_df,
            exch=exch_df,
            config=SortConfig(n_bins=bins, nyse_breaks=nyse_breaks, min_obs=min_obs),
        )
        ts = res["time_series"]
        summ = res["summary"]
        hl_ts = _compute_high_low(ts)
        # Compute performance metrics for equal and value‑weighted high‑low series
        metrics: Dict[str, Any] = {}
        if not hl_ts.empty:
            # Equal‑weighted
            m_ew = evaluate_anomaly(hl_ts["hl_ew"])
            for k, v in m_ew.items():
                metrics[f"{k}_ew"] = v
            # Value‑weighted
            m_vw = evaluate_anomaly(hl_ts["hl_vw"])
            for k, v in m_vw.items():
                metrics[f"{k}_vw"] = v
        else:
            # Populate metrics with NaN if no data
            for suffix in ["_ew", "_vw"]:
                metrics.update(
                    {
                        f"mean{suffix}": np.nan,
                        f"t_stat{suffix}": np.nan,
                        f"sharpe{suffix}": np.nan,
                        f"max_dd{suffix}": np.nan,
                    }
                )
        results[sig] = {
            "metrics": metrics,
            "time_series": ts,
            "summary": summ,
            "hl_ts": hl_ts,
        }
    return results
