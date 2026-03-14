"""
Anomaly ranking utilities.

This module provides functions to rank anomalies based on performance
metrics computed by the anomaly evaluation pipeline.  Rankings are
useful for identifying the most promising signals (e.g. those with
the highest mean return or t‑statistic) and for constructing
top‑decile lists.  The functions here are intended to mirror
functionality found in the MATLAB scripts ``makeAnomTop.m`` and
related ranking utilities, albeit in a simplified form suitable for
Python users.

The primary entry point is :func:`rank_anomalies`, which accepts a
dictionary of metric dictionaries and returns a DataFrame of ranks.
Additional helpers are provided to compute top‑decile subsets and
average ranks across multiple metrics.

Example
-------
>>> from aa.analysis.anomaly_ranking import rank_anomalies, top_decile
>>> metrics = {
...     'alpha': {'mean_ew': 0.02, 't_stat_ew': 1.5},
...     'beta': {'mean_ew': 0.05, 't_stat_ew': 2.0},
...     'gamma': {'mean_ew': -0.01, 't_stat_ew': -0.5},
... }
>>> ranks = rank_anomalies(metrics, metric='mean_ew')
>>> ranks.loc['beta', 'rank']
1.0

Notes
-----
* Rankings are assigned using ``pandas.Series.rank`` with method
  ``'min'``.  Missing metric values (NaN) are ranked at the bottom
  of the list (i.e. they receive the largest rank value).
* For metrics where lower values are better (e.g. maximum drawdown),
  set ``ascending=True`` when calling :func:`rank_anomalies` so that
  smaller values receive better (lower) ranks.
"""

from __future__ import annotations

from typing import Dict, Any, Iterable, List, Optional

import numpy as np
import pandas as pd

__all__ = ["rank_anomalies", "top_decile", "average_rank"]


def rank_anomalies(
    metrics: Dict[str, Dict[str, Any]],
    *,
    metric: str,
    ascending: bool = False,
) -> pd.DataFrame:
    """Rank anomalies by a chosen performance metric.

    Parameters
    ----------
    metrics : dict
        Mapping from anomaly identifiers to dictionaries of metric values.
    metric : str
        Name of the metric to rank on (must be a key in each inner
        dictionary).  Typically one of ``'mean_ew'``, ``'mean_vw'``,
        ``'t_stat_ew'``, ``'t_stat_vw'``, etc.
    ascending : bool, default False
        Whether to assign lower ranks to smaller metric values.
        For most performance metrics (mean return, t‑statistic,
        Sharpe ratio) higher values are better, so the default is
        ``False``.  For metrics like maximum drawdown (where a
        smaller negative number is preferable), set ``ascending=True``.

    Returns
    -------
    DataFrame
        DataFrame with index equal to anomaly identifiers and two
        columns: the selected metric and the rank (1 == best).  Rows
        are sorted by the selected metric according to ``ascending``.

    Examples
    --------
    >>> metrics = {
    ...     'a': {'mean_ew': 0.1},
    ...     'b': {'mean_ew': 0.05},
    ...     'c': {'mean_ew': np.nan},
    ... }
    >>> ranks = rank_anomalies(metrics, metric='mean_ew')
    >>> list(ranks['rank'])
    [1.0, 2.0, 3.0]
    """
    if not metrics:
        return pd.DataFrame(columns=[metric, "rank"])
    # Extract metric values into a Series
    data = {name: stats.get(metric, np.nan) for name, stats in metrics.items()}
    s = pd.Series(data, name=metric)
    # Compute ranks; NaN values will be assigned NaN rank at first
    # Replace NaN with +inf or -inf depending on ascending to push them to bottom
    s_for_rank = s.copy()
    if ascending:
        # For ascending rankings, NaN should be treated as +inf (worst)
        s_for_rank = s_for_rank.fillna(np.inf)
    else:
        # For descending rankings, NaN treated as -inf (worst) would invert; instead use -inf? Wait: we want NaN to be worst; bigger numbers are better; we set to -inf to ensure worst.
        s_for_rank = s_for_rank.fillna(-np.inf)
    ranks = s_for_rank.rank(ascending=ascending, method="min")
    # Combine into DataFrame and sort by metric
    df = pd.DataFrame({metric: s, "rank": ranks})
    df.sort_values(by=metric, ascending=ascending, inplace=True, na_position="last")
    return df


def top_decile(ranks: pd.DataFrame) -> pd.DataFrame:
    """Return the top decile of anomalies based on rank.

    Parameters
    ----------
    ranks : DataFrame
        DataFrame produced by :func:`rank_anomalies` containing a
        column ``'rank'``.  Must be sorted ascending by the ranking
        metric (i.e. best ranks first).

    Returns
    -------
    DataFrame
        The top 10% (rounded up) of the input DataFrame.  If the
        number of anomalies is less than 10, returns the first row.
    """
    if ranks is None or ranks.empty:
        return pd.DataFrame(columns=ranks.columns)
    n = len(ranks)
    top_n = max(1, int(np.ceil(n * 0.1)))
    return ranks.head(top_n).copy()


def average_rank(
    metrics: Dict[str, Dict[str, Any]],
    metric_names: Iterable[str],
    *,
    ascendings: Optional[Iterable[bool]] = None,
) -> pd.DataFrame:
    """Compute average ranks across multiple metrics.

    This helper ranks each anomaly separately for each metric in
    ``metric_names`` and then averages the ranks to produce a
    composite ranking.  The ordering (ascending/descending) for each
    metric can be specified via ``ascendings``; if not provided,
    metrics whose names begin with ``'max_dd'`` are ranked ascending
    (since smaller drawdowns are better) and all others are ranked
    descending.

    Parameters
    ----------
    metrics : dict
        Dictionary of metrics keyed by anomaly name.
    metric_names : iterable of str
        List of metric names to rank on.  Each must be present in
        every inner dictionary in ``metrics``.
    ascendings : iterable of bool, optional
        Sequence of booleans indicating whether each corresponding
        metric should be ranked ascending.  If not provided, a
        heuristic is applied based on the metric name: metrics
        starting with ``'max_dd'`` use ascending ranks, others use
        descending.

    Returns
    -------
    DataFrame
        DataFrame with a column for each metric containing the rank
        and a column ``'avg_rank'`` containing the average rank
        across all metrics.  Rows are sorted by ``avg_rank``.

    Examples
    --------
    >>> metrics = {
    ...     'a': {'mean_ew': 0.1, 't_stat_ew': 2.0},
    ...     'b': {'mean_ew': 0.05, 't_stat_ew': 3.0},
    ...     'c': {'mean_ew': 0.02, 't_stat_ew': 1.0},
    ... }
    >>> avg = average_rank(metrics, ['mean_ew', 't_stat_ew'])
    >>> avg.loc['b', 'avg_rank'] < avg.loc['a', 'avg_rank']
    True
    """
    metric_list = list(metric_names)
    if ascendings is None:
        ascendings = [(m.startswith("max_dd")) for m in metric_list]
    else:
        ascendings = list(ascendings)
    # Collect rank DataFrames for each metric
    rank_dfs: List[pd.DataFrame] = []
    for m, asc in zip(metric_list, ascendings):
        r = rank_anomalies(metrics, metric=m, ascending=asc)
        rank_dfs.append(r[["rank"]].rename(columns={"rank": f"rank_{m}"}))
    # Concatenate ranks on columns
    combined = pd.concat(rank_dfs, axis=1)
    # Compute average rank across metrics
    combined["avg_rank"] = combined.mean(axis=1)
    combined.sort_values(by="avg_rank", ascending=True, inplace=True)
    return combined
