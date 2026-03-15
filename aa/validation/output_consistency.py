"""
aa.validation.output_consistency
===============================

This module provides utility functions to verify that outputs from
multiple runs of the Assaying Anomalies pipeline are consistent with
each other.  Because the pipeline may involve stochastic elements
(bootstrapping, random draws), these functions perform robust
comparisons on `pandas` objects with configurable tolerances.  They
return boolean values indicating whether the inputs are considered
equal.

Functions
---------

``check_portfolio_returns_reproducibility(df1, df2, tol=1e-10)``
    Compare two DataFrames of portfolio returns and return ``True`` if
    they match elementwise within a tolerance.

``check_anomaly_ranking_stability(rank1, rank2)``
    Check that two ranking Series are identical (labels and order).

``check_fama_macbeth_consistency(res1, res2, tol=1e-8)``
    Compare two dictionaries of Fama–MacBeth regression results.

``check_summary_table_consistency(table1, table2, tol=1e-8)``
    Verify that two summary tables have the same shape, columns and
    numeric values within a tolerance.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Any, Dict


def check_portfolio_returns_reproducibility(
    df1: pd.DataFrame, df2: pd.DataFrame, tol: float = 1e-10
) -> bool:
    """Check that two DataFrames of portfolio returns are equal within a tolerance.

    Parameters
    ----------
    df1, df2 : pandas.DataFrame
        DataFrames containing portfolio returns.  They must have the
        same shape and index/columns ordering.
    tol : float, optional
        Absolute tolerance for floating point comparisons (default ``1e-10``).

    Returns
    -------
    bool
        ``True`` if the DataFrames match elementwise within the tolerance,
        otherwise ``False``.
    """
    # Ensure shape and labels are identical
    if df1.shape != df2.shape:
        return False
    if list(df1.index) != list(df2.index) or list(df1.columns) != list(df2.columns):
        return False
    return np.allclose(df1.values, df2.values, atol=tol, equal_nan=True)


def check_anomaly_ranking_stability(rank1: pd.Series, rank2: pd.Series) -> bool:
    """Determine whether two anomaly ranking series are exactly equal.

    The Series must have identical indices and values.  This function
    performs an exact equality check rather than a floating point
    comparison because ranks should be deterministic.

    Parameters
    ----------
    rank1, rank2 : pandas.Series
        Series containing anomaly names (or identifiers) in ranked
        order.  The index should represent the rank position.

    Returns
    -------
    bool
        ``True`` if the two Series are equal, otherwise ``False``.
    """
    return rank1.equals(rank2)


def _compare_ndarrays(arr1: Any, arr2: Any, tol: float) -> bool:
    """Helper to compare two numeric arrays or scalars within a tolerance."""
    try:
        return np.allclose(np.asarray(arr1), np.asarray(arr2), atol=tol, equal_nan=True)
    except Exception:
        return False


def check_fama_macbeth_consistency(
    res1: Dict[str, Any], res2: Dict[str, Any], tol: float = 1e-8
) -> bool:
    """Compare two dictionaries of Fama–MacBeth regression results.

    Each dictionary should contain comparable keys (e.g. ``'coefficients'``,
    ``'t_stats'``) whose values may be scalars, NumPy arrays, pandas
    Series or DataFrames.  The function returns ``True`` only if all
    corresponding values match within the specified tolerance.

    Parameters
    ----------
    res1, res2 : dict
        Dictionaries of regression outputs.
    tol : float, optional
        Absolute tolerance for numeric comparisons.

    Returns
    -------
    bool
        ``True`` if the dictionaries are consistent, ``False`` otherwise.
    """
    keys = set(res1.keys()).union(res2.keys())
    for key in keys:
        v1 = res1.get(key)
        v2 = res2.get(key)
        if v1 is None or v2 is None:
            return False
        # Compare pandas DataFrame
        if isinstance(v1, pd.DataFrame) and isinstance(v2, pd.DataFrame):
            if v1.shape != v2.shape:
                return False
            if list(v1.columns) != list(v2.columns) or list(v1.index) != list(v2.index):
                return False
            if not np.allclose(v1.values, v2.values, atol=tol, equal_nan=True):
                return False
        # Compare pandas Series
        elif isinstance(v1, pd.Series) and isinstance(v2, pd.Series):
            if not v1.equals(v2):
                return False
        else:
            # Fallback to numeric comparison
            if not _compare_ndarrays(v1, v2, tol=tol):
                return False
    return True


def check_summary_table_consistency(
    table1: pd.DataFrame, table2: pd.DataFrame, tol: float = 1e-8
) -> bool:
    """Check consistency between two summary tables.

    Parameters
    ----------
    table1, table2 : pandas.DataFrame
        DataFrames containing summary statistics such as mean returns,
        t‑statistics or Sharpe ratios.  They must have the same shape
        and matching columns.
    tol : float, optional
        Absolute tolerance for numeric comparisons.

    Returns
    -------
    bool
        ``True`` if the tables match elementwise within the tolerance,
        otherwise ``False``.
    """
    if table1.shape != table2.shape:
        return False
    if list(table1.columns) != list(table2.columns) or list(table1.index) != list(
        table2.index
    ):
        return False
    return np.allclose(table1.values, table2.values, atol=tol, equal_nan=True)


__all__ = [
    "check_portfolio_returns_reproducibility",
    "check_anomaly_ranking_stability",
    "check_fama_macbeth_consistency",
    "check_summary_table_consistency",
]
