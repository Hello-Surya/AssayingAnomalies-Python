"""
Large-scale anomaly evaluation pipeline.

This module contains functions to evaluate many anomaly signals
simultaneously.  Given a panel of returns and firm-level
characteristics, the pipeline performs univariate portfolio sorts for
each signal, constructs high-minus-low series and computes a suite
of performance metrics (mean return, t-statistic, Sharpe ratio and
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
...     "date": ["2020-01-31", "2020-01-31", "2020-02-28", "2020-02-28"],
...     "permno": [1, 2, 1, 2],
...     "ret": [0.01, 0.02, -0.005, 0.015],
...     "me": [100, 200, 105, 210],
...     "exchcd": [1, 1, 1, 1],
...     "size": [10, 20, 11, 22],
...     "value": [0.5, 0.4, 0.55, 0.45],
... })
>>> results = evaluate_signals(panel, signals=["size", "value"])
>>> results["size"]["metrics"]["mean_ew"]
0.0
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from aa.analysis.anomaly_metrics import evaluate_anomaly
from aa.asset_pricing import SortConfig, univariate_sort

__all__ = ["evaluate_signals"]


def _identify_signals(
    panel: pd.DataFrame,
    *,
    returns_col: str,
    size_col: str,
    exch_col: str,
    provided: list[str] | None = None,
) -> list[str]:
    """Identify signal columns in a panel DataFrame."""
    if provided is not None:
        return provided
    drop_cols = {"date", "permno", returns_col, size_col, exch_col}
    candidates = [c for c in panel.columns if c not in drop_cols]
    signals = [c for c in candidates if pd.api.types.is_numeric_dtype(panel[c])]
    return signals


def _compute_high_low(ts: pd.DataFrame) -> pd.DataFrame:
    """Compute high-minus-low series from a time-series of bin returns."""
    if ts.empty:
        return pd.DataFrame(columns=["date", "hl_ew", "hl_vw"])

    ew_wide = ts.pivot(index="date", columns="bin", values="ret_ew")
    numeric_bins = [b for b in ew_wide.columns if isinstance(b, (int, np.integer))]
    if not numeric_bins:
        return pd.DataFrame(columns=["date", "hl_ew", "hl_vw"])

    hi_bin = max(numeric_bins)
    lo_bin = min(numeric_bins)

    ew_hi = (
        ew_wide[hi_bin]
        if hi_bin in ew_wide.columns
        else pd.Series(np.nan, index=ew_wide.index)
    )
    ew_lo = (
        ew_wide[lo_bin]
        if lo_bin in ew_wide.columns
        else pd.Series(np.nan, index=ew_wide.index)
    )
    hl_ew = ew_hi - ew_lo

    vw_wide = ts.pivot(index="date", columns="bin", values="ret_vw")
    vw_hi = (
        vw_wide[hi_bin]
        if hi_bin in vw_wide.columns
        else pd.Series(np.nan, index=vw_wide.index)
    )
    vw_lo = (
        vw_wide[lo_bin]
        if lo_bin in vw_wide.columns
        else pd.Series(np.nan, index=vw_wide.index)
    )
    hl_vw = vw_hi - vw_lo

    hl = pd.DataFrame(
        {"date": hl_ew.index, "hl_ew": hl_ew.values, "hl_vw": hl_vw.values}
    )
    return hl


def evaluate_signals(
    panel: pd.DataFrame,
    *,
    signals: list[str] | None = None,
    returns_col: str = "ret",
    size_col: str = "me",
    exch_col: str = "exchcd",
    bins: int = 5,
    nyse_breaks: bool = False,
    min_obs: int = 20,
) -> dict[str, dict[str, Any]]:
    """Evaluate multiple anomaly signals on a common panel of data."""
    panel = panel.copy()

    sigs = _identify_signals(
        panel,
        returns_col=returns_col,
        size_col=size_col,
        exch_col=exch_col,
        provided=signals,
    )

    results: dict[str, dict[str, Any]] = {}

    returns_df = panel[["date", "permno", returns_col]].rename(
        columns={returns_col: "ret"}
    )

    size_df: pd.DataFrame | None = None
    if size_col in panel.columns:
        size_df = panel[["date", "permno", size_col]].rename(columns={size_col: "me"})

    exch_df: pd.DataFrame | None = None
    if exch_col in panel.columns:
        exch_df = panel[["date", "permno", exch_col]].rename(
            columns={exch_col: "exchcd"}
        )

    for sig in sigs:
        sig_df = panel[["date", "permno", sig]].rename(columns={sig: "signal"})

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

        metrics: dict[str, Any] = {}
        if not hl_ts.empty:
            m_ew = evaluate_anomaly(hl_ts["hl_ew"])
            for k, v in m_ew.items():
                metrics[f"{k}_ew"] = v

            m_vw = evaluate_anomaly(hl_ts["hl_vw"])
            for k, v in m_vw.items():
                metrics[f"{k}_vw"] = v
        else:
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
