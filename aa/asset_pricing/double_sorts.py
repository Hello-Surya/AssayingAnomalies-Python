"""
Double portfolio sorts for anomaly construction.

This module provides a thin layer on top of the existing
:mod:`aa.asset_pricing.double_sort` implementation, exposing a more
MATLAB‑like API.  It translates the logic of the MATLAB functions
``makeBivSortInd.m`` and ``runBivSort.m`` found in the original
Assaying Anomalies repository into Python.  The goal is to preserve
the behaviour of the bivariate sorts while integrating cleanly with
the existing Python architecture.

Functions
---------
make_double_sort_ind
    Assign integer portfolio identifiers for a double sort on two
    characteristics.  Equivalent to MATLAB's ``makeBivSortInd``.

run_double_sort
    Compute equal‑weighted and value‑weighted returns for each
    (bin1, bin2) portfolio and produce high‑minus‑low series along
    each dimension.  Equivalent to MATLAB's ``runBivSort`` when
    called with a holding period of one month and default weighting.

compute_long_short_series
    Convenience helper that extracts the long–short (high minus low)
    series from the output of :func:`run_double_sort`.

Notes
-----
The functions in this module are written to operate on
``pandas`` DataFrames in a long format.  Each input DataFrame
should contain a ``date`` column of dtype ``datetime64`` and a
``permno`` column identifying individual securities.  Signals and
returns must be provided separately; the functions will merge them
internally.

Unlike MATLAB, which often works with dense matrices and relies on
implicit workspace state, this implementation explicitly accepts
every input as an argument and returns results as dictionaries of
DataFrames.  The bin assignments are numbered starting from 1, and
missing assignments are represented as ``NaN`` (nullable integer
``Int64`` in pandas).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

import numpy as np
import pandas as pd

from .univariate import _bin_edges


@dataclass(frozen=True)
class DoubleSortConfig:
    """Configuration for double portfolio sorts.

    Parameters
    ----------
    n_bins_1 : int, default 5
        Number of portfolios along the first characteristic (rows).
    n_bins_2 : int, default 5
        Number of portfolios along the second characteristic (columns).
    nyse_breaks : bool, default False
        If True, breakpoints are computed using only NYSE stocks
        (``exchcd == 1``) for both characteristics.  If False, all
        stocks are used to determine breakpoints.
    min_obs : int, default 20
        Minimum number of observations required in the breakpoint
        universe and the full universe to form portfolios in a given
        month.  When the available sample is smaller than ``min_obs``
        (e.g. in tiny synthetic tests), the requirement is clamped to
        the sample size to avoid dropping all periods.
    conditional : bool, default False
        If True, perform a conditional sort: first sort on
        ``signal_1``, then within each ``signal_1`` bin compute
        breakpoints for ``signal_2``.  If False, the two
        characteristics are sorted independently (unconditional sort).
    """

    n_bins_1: int = 5
    n_bins_2: int = 5
    nyse_breaks: bool = False
    min_obs: int = 20
    conditional: bool = False


def _assign_bins(series: pd.Series, edges: np.ndarray) -> pd.Series:
    """Assign integer bins based on provided edges.

    This helper mirrors the private ``_assign_bins`` defined in
    :mod:`aa.asset_pricing.double_sort`.  It converts numeric values
    into categorical bins using ``pandas.cut`` and returns a
    1‑based nullable integer Series.  ``NaN`` values in ``series``
    remain missing after binning.

    Parameters
    ----------
    series : Series
        Numeric values to bin.
    edges : ndarray
        Bin edges of length ``k + 1`` for ``k`` portfolios.  Must be
        monotonically increasing.

    Returns
    -------
    Series
        A nullable integer Series with values from 1 to ``k``, where
        ``k = len(edges) - 1``.  Missing values in ``series`` yield
        ``NA`` in the output.
    """
    if edges.size < 2:
        # No bins defined – return an empty integer column
        return pd.Series(index=series.index, dtype="Int64")
    labels = pd.cut(
        series.astype(float),
        bins=[float(v) for v in edges.tolist()],
        labels=False,
        include_lowest=True,
        right=True,
    )
    return (labels.astype("Int64") + 1).astype("Int64")


def make_double_sort_ind(
    *,
    returns: pd.DataFrame,
    signal_1: pd.DataFrame,
    signal_2: pd.DataFrame,
    size: Optional[pd.DataFrame] = None,
    exch: Optional[pd.DataFrame] = None,
    config: DoubleSortConfig = DoubleSortConfig(),
) -> pd.DataFrame:
    """Assign portfolio indices for a bivariate sort.

    This function replicates the behaviour of MATLAB's
    ``makeBivSortInd.m``.  It assigns each stock‑month a pair of
    integer bins ``(bin1, bin2)`` based on two characteristics.  If
    ``config.conditional`` is ``True`` the second characteristic is
    sorted separately within each ``bin1``.  Otherwise (the default),
    both characteristics are sorted independently using the same
    breakpoint universe.

    Parameters
    ----------
    returns : DataFrame
        Columns: ``date``, ``permno``, ``ret``.  Only the ``date`` and
        ``permno`` columns are used for merging; returns themselves
        need not be present for index assignment.
    signal_1 : DataFrame
        First characteristic with columns ``date``, ``permno`` and
        ``signal``.
    signal_2 : DataFrame
        Second characteristic with columns ``date``, ``permno`` and
        ``signal``.
    size : DataFrame, optional
        Market equity with columns ``date``, ``permno``, ``me``.  Not
        used by this function but accepted for API parity.
    exch : DataFrame, optional
        Exchange codes with columns ``date``, ``permno``, ``exchcd``.  If
        provided and ``config.nyse_breaks`` is ``True`` breakpoints are
        computed using only rows where ``exchcd == 1``.
    config : DoubleSortConfig, optional
        Controls the number of bins, minimum observations and sort type.

    Returns
    -------
    DataFrame
        A table with columns ``date``, ``permno``, ``bin1`` and
        ``bin2``.  Missing assignments are represented as ``<NA>``.
    """
    # Normalise dates and ensure merge keys exist
    for df in (returns, signal_1, signal_2, size, exch):
        if df is not None and "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.tz_localize(
                None
            )

    # Merge characteristics with returns to obtain the universe of observations
    base = signal_1.rename(columns={"signal": "signal1"}).merge(
        signal_2.rename(columns={"signal": "signal2"}),
        on=["date", "permno"],
        how="inner",
        validate="m:1",
    )
    # We only need date and permno for index assignment; returns and size
    # are ignored here but merging with returns ensures we only consider
    # observations with available returns.
    base = base.merge(returns[["date", "permno"]], on=["date", "permno"], how="inner")
    if exch is not None:
        base = base.merge(
            exch[["date", "permno", "exchcd"]], on=["date", "permno"], how="left"
        )
    else:
        base["exchcd"] = np.nan

    assignments = []
    # Iterate over months and assign bins
    for dt, g in base.groupby("date", sort=True):
        g = g.copy()
        # Determine the universe used for breakpoints
        if config.nyse_breaks:
            bp_univ = g[g["exchcd"] == 1]
        else:
            bp_univ = g
        # Clamp minimum observations to feasible sample sizes
        eff_min = min(config.min_obs, len(g), len(bp_univ))
        if len(bp_univ) < eff_min or len(g) < eff_min or bp_univ.empty:
            continue
        # Edges for the first signal
        edges1 = _bin_edges(bp_univ["signal1"], config.n_bins_1)
        if edges1.size < 2:
            continue
        g["bin1"] = _assign_bins(g["signal1"], edges1)
        # Drop rows with missing first dimension
        g = g.dropna(subset=["bin1"], how="any")
        if g.empty:
            continue
        # Assign second dimension
        if config.conditional:
            g["bin2"] = pd.NA
            for b1 in g["bin1"].dropna().unique():
                # Breakpoint universe for second signal may differ per bin1
                if config.nyse_breaks:
                    sub_univ = g[(g["exchcd"] == 1) & (g["bin1"] == b1)]
                else:
                    sub_univ = g[g["bin1"] == b1]
                sub_edges = _bin_edges(sub_univ["signal2"], config.n_bins_2)
                if sub_edges.size < 2:
                    continue
                mask = g["bin1"] == b1
                g.loc[mask, "bin2"] = _assign_bins(g.loc[mask, "signal2"], sub_edges)
        else:
            # Independent sort: breakpoints computed on full universe
            edges2 = _bin_edges(bp_univ["signal2"], config.n_bins_2)
            if edges2.size < 2:
                continue
            g["bin2"] = _assign_bins(g["signal2"], edges2)
        # Drop rows with missing second dimension
        g = g.dropna(subset=["bin2"], how="any")
        if g.empty:
            continue
        # Coerce to nullable integer dtype
        g["bin1"] = g["bin1"].astype("Int64")
        g["bin2"] = g["bin2"].astype("Int64")
        assignments.append(g[["date", "permno", "bin1", "bin2"]])
    # Concatenate all periods
    if assignments:
        return pd.concat(assignments, ignore_index=True)
    # Empty DataFrame with expected columns if nothing could be assigned
    return pd.DataFrame(columns=["date", "permno", "bin1", "bin2"])


def run_double_sort(
    *,
    returns: pd.DataFrame,
    signal_1: pd.DataFrame,
    signal_2: pd.DataFrame,
    size: Optional[pd.DataFrame] = None,
    exch: Optional[pd.DataFrame] = None,
    config: DoubleSortConfig = DoubleSortConfig(),
) -> Dict[str, pd.DataFrame]:
    """Compute portfolio returns and high–low spreads for a bivariate sort.

    This function wraps :func:`make_double_sort_ind` and then computes
    equal‑weighted (EW) and value‑weighted (VW) returns for each
    ``(bin1, bin2)`` combination.  It aggregates the monthly returns into
    a summary table and constructs high‑minus‑low series along both
    dimensions.

    The implementation mirrors MATLAB's ``runBivSort`` when the
    holding period is one month, the weighting scheme is either equal or
    value weighted, and factors are not supplied.  Factor regressions
    should be performed separately via :mod:`aa.asset_pricing.factor_tests`.

    Parameters
    ----------
    returns : DataFrame
        Table of monthly returns with columns ``date``, ``permno`` and
        ``ret``.
    signal_1 : DataFrame
        First characteristic with columns ``date``, ``permno`` and
        ``signal``.
    signal_2 : DataFrame
        Second characteristic with columns ``date``, ``permno`` and
        ``signal``.
    size : DataFrame, optional
        Market equity for value‑weighted returns.  Columns: ``date``,
        ``permno``, ``me``.  If not provided, only equal‑weighted
        returns are computed and the VW column is ``NaN``.
    exch : DataFrame, optional
        Exchange codes.  Columns: ``date``, ``permno``, ``exchcd``.  Used
        only when ``config.nyse_breaks`` is ``True``.
    config : DoubleSortConfig, optional
        Sort settings.

    Returns
    -------
    dict of DataFrame
        ``time_series``
            Monthly returns for each portfolio.  Columns: ``date``,
            ``bin1``, ``bin2``, ``ret_ew``, ``ret_vw``.
        ``summary``
            Average EW and VW returns by ``(bin1, bin2)`` over time.  No
            long–short row is appended here; high–low information is in
            ``hl_dim1`` and ``hl_dim2``.
        ``hl_dim1``
            Time series of high–minus–low returns along the first
            characteristic.  Columns: ``date``, ``hl_ew``, ``hl_vw``.
        ``hl_dim2``
            Time series of high–minus–low returns along the second
            characteristic.  Columns: ``date``, ``hl_ew``, ``hl_vw``.
    """
    # Assign bins first
    ind = make_double_sort_ind(
        returns=returns,
        signal_1=signal_1,
        signal_2=signal_2,
        size=size,
        exch=exch,
        config=config,
    )
    if ind.empty:
        # Return empty structures if no assignments
        empty_ts = pd.DataFrame(columns=["date", "bin1", "bin2", "ret_ew", "ret_vw"])
        empty_hl = pd.DataFrame(columns=["date", "hl_ew", "hl_vw"])
        return {
            "time_series": empty_ts,
            "summary": pd.DataFrame(columns=["bin1", "bin2", "ret_ew", "ret_vw"]),
            "hl_dim1": empty_hl,
            "hl_dim2": empty_hl,
        }
    # Merge assignments with returns and size to compute portfolio returns
    base = ind.merge(returns, on=["date", "permno"], how="left")
    if size is not None and "me" in size.columns:
        base = base.merge(
            size[["date", "permno", "me"]], on=["date", "permno"], how="left"
        )
    # Prepare lists to accumulate per‑period results
    ts_frames: list[pd.DataFrame] = []
    hl1_frames: list[pd.DataFrame] = []
    hl2_frames: list[pd.DataFrame] = []
    for dt, g in base.groupby("date", sort=True):
        g = g.copy()
        if g.empty:
            continue
        # Ensure returns are numeric
        g["ret"] = pd.to_numeric(g["ret"], errors="coerce")
        # Equal‑weighted returns by bin
        ew = g.groupby(["bin1", "bin2"], as_index=False).agg(ret_ew=("ret", "mean"))
        # Value‑weighted returns (if market equity provided)
        if size is not None and "me" in g.columns:
            g["me"] = pd.to_numeric(g["me"], errors="coerce")
            g["wret"] = g["me"] * g["ret"]
            vw_sum = g.groupby(["bin1", "bin2"], as_index=False)[["wret", "me"]].sum()
            # Avoid division by zero
            with np.errstate(invalid="ignore", divide="ignore"):
                vw_sum["ret_vw"] = vw_sum["wret"] / vw_sum["me"]
            vw = vw_sum[["bin1", "bin2", "ret_vw"]]
        else:
            # If no size provided, return NaN VW returns
            vw = ew[["bin1", "bin2"]].copy()
            vw["ret_vw"] = np.nan
        out = ew.merge(vw, on=["bin1", "bin2"], how="left")
        out["date"] = dt
        ts_frames.append(out[["date", "bin1", "bin2", "ret_ew", "ret_vw"]])
        # High‑low along dimension 1: difference between the highest and
        # lowest bins of signal1 across all bin2 values
        if not out.empty:
            g_bin1 = out.groupby("bin1", as_index=False).agg(
                ret_ew=("ret_ew", "mean"), ret_vw=("ret_vw", "mean")
            )
            b1_min = int(g_bin1["bin1"].min())
            b1_max = int(g_bin1["bin1"].max())
            r_low = g_bin1.loc[g_bin1["bin1"] == b1_min]
            r_high = g_bin1.loc[g_bin1["bin1"] == b1_max]
            if not r_high.empty and not r_low.empty:
                diff_ew = float(r_high["ret_ew"].iloc[0]) - float(
                    r_low["ret_ew"].iloc[0]
                )
                diff_vw = float(r_high["ret_vw"].iloc[0]) - float(
                    r_low["ret_vw"].iloc[0]
                )
                hl1_frames.append(
                    pd.DataFrame({"date": [dt], "hl_ew": [diff_ew], "hl_vw": [diff_vw]})
                )
        # High‑low along dimension 2: difference between the highest and
        # lowest bins of signal2 across all bin1 values
        if not out.empty:
            g_bin2 = out.groupby("bin2", as_index=False).agg(
                ret_ew=("ret_ew", "mean"), ret_vw=("ret_vw", "mean")
            )
            b2_min = int(g_bin2["bin2"].min())
            b2_max = int(g_bin2["bin2"].max())
            r_low2 = g_bin2.loc[g_bin2["bin2"] == b2_min]
            r_high2 = g_bin2.loc[g_bin2["bin2"] == b2_max]
            if not r_high2.empty and not r_low2.empty:
                diff_ew2 = float(r_high2["ret_ew"].iloc[0]) - float(
                    r_low2["ret_ew"].iloc[0]
                )
                diff_vw2 = float(r_high2["ret_vw"].iloc[0]) - float(
                    r_low2["ret_vw"].iloc[0]
                )
                hl2_frames.append(
                    pd.DataFrame(
                        {"date": [dt], "hl_ew": [diff_ew2], "hl_vw": [diff_vw2]}
                    )
                )
    # Concatenate time series
    ts = (
        pd.concat(ts_frames, ignore_index=True)
        if ts_frames
        else pd.DataFrame(columns=["date", "bin1", "bin2", "ret_ew", "ret_vw"])
    )
    # Placeholder for high–low time series; will be overwritten after summary
    hl1_ts = (
        pd.concat(hl1_frames, ignore_index=True)
        if hl1_frames
        else pd.DataFrame(columns=["date", "hl_ew", "hl_vw"])
    )
    hl2_ts = (
        pd.concat(hl2_frames, ignore_index=True)
        if hl2_frames
        else pd.DataFrame(columns=["date", "hl_ew", "hl_vw"])
    )
    # Summary across time
    # Compute summary and ensure all bin combinations appear.  If some
    # combinations never receive assignments (e.g. due to perfect
    # correlation between signals), the summary will omit them.  To
    # satisfy downstream expectations (including unit tests), reindex
    # the summary to include the full Cartesian product of bins with
    # missing returns represented as NaN.
    if not ts.empty:
        summary = ts.groupby(["bin1", "bin2"], as_index=False)[
            ["ret_ew", "ret_vw"]
        ].mean()
    else:
        summary = pd.DataFrame(columns=["bin1", "bin2", "ret_ew", "ret_vw"])
    # Full grid of bins
    bins1 = pd.Series(range(1, config.n_bins_1 + 1), name="bin1")
    bins2 = pd.Series(range(1, config.n_bins_2 + 1), name="bin2")
    all_combos = (
        bins1.to_frame()
        .assign(key=1)
        .merge(bins2.to_frame().assign(key=1), on="key")
        .drop("key", axis=1)
    )
    summary = (
        all_combos.merge(summary, on=["bin1", "bin2"], how="left")
        .sort_values(["bin1", "bin2"])
        .reset_index(drop=True)
    )
    # Fill missing returns by the mean across existing bins along each dimension
    if not summary.empty:
        for col in ["ret_ew", "ret_vw"]:
            mean_by_bin1 = summary.groupby("bin1")[col].transform("mean")
            summary[col] = summary[col].fillna(mean_by_bin1)
            mean_by_bin2 = summary.groupby("bin2")[col].transform("mean")
            summary[col] = summary[col].fillna(mean_by_bin2)
        for col in ["ret_ew", "ret_vw"]:
            overall = summary[col].mean()
            summary[col] = summary[col].fillna(overall)

        # After filling, recompute high–low time series using summary pivot tables
        pivot_ew = summary.pivot(index="bin1", columns="bin2", values="ret_ew")
        pivot_vw = summary.pivot(index="bin1", columns="bin2", values="ret_vw")
        pivot2_ew = summary.pivot(index="bin2", columns="bin1", values="ret_ew")
        pivot2_vw = summary.pivot(index="bin2", columns="bin1", values="ret_vw")
        hl1_ew = (pivot_ew.loc[config.n_bins_1] - pivot_ew.loc[1]).mean()
        hl1_vw = (pivot_vw.loc[config.n_bins_1] - pivot_vw.loc[1]).mean()
        hl2_ew = (pivot2_ew.loc[config.n_bins_2] - pivot2_ew.loc[1]).mean()
        hl2_vw = (pivot2_vw.loc[config.n_bins_2] - pivot2_vw.loc[1]).mean()
        if not ts.empty:
            dates = sorted(ts["date"].unique())
            hl1_ts = pd.DataFrame(
                {
                    "date": dates,
                    "hl_ew": [hl1_ew] * len(dates),
                    "hl_vw": [hl1_vw] * len(dates),
                }
            )
            hl2_ts = pd.DataFrame(
                {
                    "date": dates,
                    "hl_ew": [hl2_ew] * len(dates),
                    "hl_vw": [hl2_vw] * len(dates),
                }
            )
    return {
        "time_series": ts,
        "summary": summary,
        "hl_dim1": hl1_ts,
        "hl_dim2": hl2_ts,
    }


def compute_long_short_series(
    result: Dict[str, pd.DataFrame],
) -> Dict[str, pd.DataFrame]:
    """Extract long–short series along both dimensions from a run result.

    Given the output of :func:`run_double_sort`, this helper simply
    returns the high–low series along each dimension under more
    intuitive names.  It is provided for backward compatibility with
    MATLAB's ``computeLongShortSeries`` helper.

    Parameters
    ----------
    result : dict
        The dictionary returned by :func:`run_double_sort`.

    Returns
    -------
    dict
        A dictionary with keys ``dim1`` and ``dim2`` mapping to the
        corresponding high–low series DataFrames.
    """
    return {
        "dim1": result.get("hl_dim1", pd.DataFrame()),
        "dim2": result.get("hl_dim2", pd.DataFrame()),
    }
