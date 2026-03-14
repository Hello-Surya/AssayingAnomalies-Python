"""
Stability and robustness reporting utilities.
"""

from __future__ import annotations

from typing import Any, Callable

import pandas as pd

__all__ = ["stability_table", "robustness_table", "null_distribution_summary"]


def stability_table(
    results_by_regime: dict[str, Any],
    metric_fn: Callable[[Any], float],
) -> pd.DataFrame:
    """Create a simple stability table across regimes.

    Parameters
    ----------
    results_by_regime : dict
        Mapping from regime name to a result object.
    metric_fn : callable
        Function that takes one result object and returns a scalar metric.

    Returns
    -------
    DataFrame
        DataFrame with columns ``regime`` and ``metric``.
    """
    rows: list[dict[str, Any]] = []
    for regime, result in results_by_regime.items():
        rows.append({"regime": regime, "metric": metric_fn(result)})
    return pd.DataFrame(rows)


def robustness_table(
    results_by_spec: dict[str, Any],
    metric_fn: Callable[[Any], float],
) -> pd.DataFrame:
    """Create a simple robustness table across specifications."""
    rows: list[dict[str, Any]] = []
    for spec, result in results_by_spec.items():
        rows.append({"specification": spec, "metric": metric_fn(result)})
    return pd.DataFrame(rows)


def null_distribution_summary(values: pd.Series | list[float]) -> pd.DataFrame:
    """Summarize a null distribution with standard descriptive stats."""
    s = pd.Series(values, dtype=float)
    return pd.DataFrame(
        {
            "mean": [float(s.mean())],
            "std": [float(s.std(ddof=1))],
            "min": [float(s.min())],
            "median": [float(s.median())],
            "max": [float(s.max())],
        }
    )
