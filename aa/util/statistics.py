"""
Basic statistical helper functions.

This module contains small utility routines used throughout the
Assaying Anomalies Python port.  These helpers are analogous to
various small MATLAB functions (e.g. ``winsorize.m``, ``lag.m``)
and are written to operate on ``pandas`` objects.  They do not
introduce any new algorithms beyond standard practices.

Functions
---------
winsorize
    Cap extreme values of a Series or each column of a DataFrame at
    specified quantiles.

rank_series
    Compute fractional ranks of a Series, scaled to the unit
    interval.

lag
    Shift a Series or DataFrame by a specified number of periods.
"""

from __future__ import annotations

from typing import Optional, Tuple, Union

import numpy as np
import pandas as pd


def winsorize(
    x: Union[pd.Series, pd.DataFrame],
    *,
    limits: Tuple[float, float] = (0.01, 0.99),
    inclusive: bool = True,
) -> Union[pd.Series, pd.DataFrame]:
    """Winsorize a Series or DataFrame at specified quantiles.

    Parameters
    ----------
    x : Series or DataFrame
        The data to be winsorized.  If a DataFrame is provided, the
        operation is applied column‑wise.
    limits : tuple of float, default (0.01, 0.99)
        Lower and upper quantile boundaries.  Values below the lower
        quantile are set to the lower quantile, and values above the
        upper quantile are set to the upper quantile.
    inclusive : bool, default True
        Whether to include the quantile values themselves in the
        truncation range.  If False, the truncation thresholds are
        calculated using exclusive quantiles.

    Returns
    -------
    Series or DataFrame
        The winsorized data.
    """
    lower, upper = limits
    if isinstance(x, pd.DataFrame):
        return x.apply(lambda col: winsorize(col, limits=limits, inclusive=inclusive))
    series = pd.to_numeric(x, errors="coerce")
    # Compute quantile thresholds
    q_low = series.quantile(lower, interpolation="linear" if inclusive else "lower")
    q_high = series.quantile(upper, interpolation="linear" if inclusive else "higher")
    return series.clip(lower=q_low, upper=q_high)


def rank_series(series: pd.Series, *, ascending: bool = True) -> pd.Series:
    """Compute fractional ranks of a Series on the unit interval.

    The ranks are computed using the average ranking method (ties
    receive the average of the ranks they span) and scaled to lie in
    ``(0, 1]``.  Missing values are returned as ``NaN``.

    Parameters
    ----------
    series : Series
        Input data.
    ascending : bool, default True
        If True, the smallest value receives the smallest rank.  If
        False, the largest value receives the smallest rank.

    Returns
    -------
    Series
        Fractional ranks in ``(0, 1]`` with the same index as the input.
    """
    s = pd.to_numeric(series, errors="coerce")
    ranks = s.rank(method="average", ascending=ascending, na_option="keep")
    n = ranks.count()
    if n == 0:
        return ranks
    return ranks / n


def lag(
    x: Union[pd.Series, pd.DataFrame],
    periods: int = 1,
    fill_value: Optional[float] = np.nan,
) -> Union[pd.Series, pd.DataFrame]:
    """Shift a Series or DataFrame by a number of periods.

    Parameters
    ----------
    x : Series or DataFrame
        The data to lag.  If a DataFrame is provided, the lag is
        applied to each column independently.
    periods : int, default 1
        Number of periods by which to shift the data.  Positive values
        shift the data down (forward in time), introducing missing
        values at the beginning.
    fill_value : scalar, default NaN
        Value used to fill introduced missing values.  If None, a
        missing value is introduced (``NaN`` for floats, ``NaT`` for
        datetimes).

    Returns
    -------
    Series or DataFrame
        Lagged data with the same index.
    """
    if isinstance(x, pd.DataFrame):
        return x.shift(periods=periods).fillna(fill_value)
    return x.shift(periods=periods).fillna(fill_value)
