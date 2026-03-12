"""
    Anomaly performance metrics and ranking utilities.

    This module implements common statistics used to evaluate the
    profitability and risk profile of anomaly strategies.  These
    functions are inspired by various MATLAB utilities in the
    Assaying Anomalies codebase (e.g. ``calcPerfStats.m`` and
    ``calcDrawdowns.m``) but are rewritten in Python to operate on
    ``pandas`` Series.  They do not introduce new models or research
    ideas; rather, they provide a clear and testable interface for
    computing basic metrics such as mean return, t‑statistics, Sharpe
    ratios, drawdowns and portfolio turnover.

    Functions
    ---------
    mean_return
        Compute the average return of a series, optionally annualising.

    t_statistic
        Compute the t‑statistic of the mean return under the IID
        assumption.

    sharpe_ratio
        Compute the (annualised) Sharpe ratio given a series of
        returns.

    max_drawdown
        Compute the maximum drawdown of a return series.

    compute_turnover
        Estimate the turnover of a strategy given portfolio
        assignments over time.

    evaluate_anomaly
        Convenience wrapper that returns a dictionary of common
        metrics for a given return series.

    Notes
    -----
    All functions accept a ``pandas`` Series of periodic returns.  The
    periodicity is inferred via the ``periods_per_year`` parameter
    (default ``12`` for monthly data).  Missing values are dropped
    prior to computation.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def mean_return(returns: pd.Series, *, annualize: bool = False, periods_per_year: int = 12) -> float:
    """Compute the average return of a series.

    Parameters
    ----------
    returns : Series
        Periodic returns expressed in decimal form (e.g. 0.01 for 1%).
    annualize : bool, default False
        If True, scale the mean by ``periods_per_year``.  This
        corresponds to an arithmetic annualisation, which is consistent
        with the conventions used in the MATLAB code.
    periods_per_year : int, default 12
        Number of periods per year.  Set to 12 for monthly data or 252
        for daily data.

    Returns
    -------
    float
        The mean return, annualised if requested.
    """
    series = pd.to_numeric(returns, errors="coerce").dropna()
    if series.empty:
        return float("nan")
    mean = float(series.mean())
    if annualize:
        mean *= periods_per_year
    return mean


def t_statistic(returns: pd.Series) -> float:
    """Compute the t‑statistic of the mean return under IID assumptions.

    The t‑statistic is defined as:

    .. math:: \frac{\bar{r}}{s / \sqrt{n}},

    where ``\bar{r}`` is the sample mean, ``s`` is the sample standard
    deviation (using Bessel's correction) and ``n`` is the number of
    non‑missing observations.  This implementation makes no attempt to
    correct for autocorrelation; users requiring Newey–West adjusted
    statistics should employ the functions in :mod:`aa.asset_pricing.fama_macbeth` or
    implement their own estimator.

    Parameters
    ----------
    returns : Series
        Periodic returns.

    Returns
    -------
    float
        The t‑statistic of the mean return.  Returns ``nan`` if the
        series is empty or constant.
    """
    series = pd.to_numeric(returns, errors="coerce").dropna()
    n = len(series)
    if n == 0:
        return float("nan")
    mean = float(series.mean())
    std = float(series.std(ddof=1))
    if std == 0:
        return float("nan")
    se = std / np.sqrt(n)
    if se == 0:
        return float("nan")
    return mean / se


def sharpe_ratio(
    returns: pd.Series,
    *,
    risk_free: float = 0.0,
    periods_per_year: int = 12,
) -> float:
    """Compute the annualised Sharpe ratio of a return series.

    The Sharpe ratio is defined as the excess mean return divided by
    the standard deviation of returns, scaled by the square root of
    periods per year.  It measures risk‑adjusted performance under
    the assumption of IID returns.  No correction for
    autocorrelation or heteroskedasticity is applied.

    Parameters
    ----------
    returns : Series
        Periodic returns.
    risk_free : float, default 0.0
        Risk‑free rate per period (expressed in the same units as
        ``returns``).  Subtracted from the series prior to
        computation.
    periods_per_year : int, default 12
        Number of periods per year (12 for monthly data, 252 for
        daily data).

    Returns
    -------
    float
        The annualised Sharpe ratio, or ``nan`` if the series is
        empty or has zero variance.
    """
    series = pd.to_numeric(returns, errors="coerce").dropna()
    if series.empty:
        return float("nan")
    excess = series - risk_free
    mean_excess = float(excess.mean())
    std = float(excess.std(ddof=1))
    if std == 0:
        return float("nan")
    sr = mean_excess / std * np.sqrt(periods_per_year)
    return sr


def max_drawdown(returns: pd.Series) -> float:
    """Compute the maximum drawdown of a return series.

    Maximum drawdown is defined as the largest peak‑to‑trough decline
    in the cumulative return trajectory.  It is computed on the
    assumption that returns are expressed in decimal form (e.g. 0.01
    for 1%).  Missing values are ignored.  If the series is empty
    the function returns ``0.0``.

    Parameters
    ----------
    returns : Series
        Periodic returns.

    Returns
    -------
    float
        The maximum drawdown, expressed as a negative number.  A
        value of −0.2 indicates a 20% loss from peak to trough.
    """
    series = pd.to_numeric(returns, errors="coerce").dropna()
    if series.empty:
        return 0.0
    # Convert returns into cumulative wealth index
    cumulative = (1 + series).cumprod()
    running_max = cumulative.cummax()
    drawdowns = (cumulative - running_max) / running_max
    return float(drawdowns.min())


def compute_turnover(assignments: pd.DataFrame) -> float:
    """Estimate the turnover of a strategy given portfolio assignments.

    Turnover measures the fraction of assets whose portfolio membership
    changes between consecutive periods.  It is calculated as one minus
    the ratio of the number of securities that remain in the same
    portfolio to the total number of securities present in either
    period.  The input DataFrame must contain ``date``, ``permno`` and
    at least one column representing the portfolio assignment (e.g.
    ``bin`` for univariate sorts or ``bin1``/``bin2`` for bivariate
    sorts).  Any number of additional assignment columns will be
    compared jointly.

    Parameters
    ----------
    assignments : DataFrame
        Table with columns ``date`` and ``permno`` plus one or more
        portfolio assignment columns.  The data need not be sorted.

    Returns
    -------
    float
        The average turnover across all adjacent periods.  Returns
        ``nan`` if fewer than two periods are present.
    """
    if assignments.empty:
        return float("nan")
    # Determine which columns define the portfolio assignment
    cols = [c for c in assignments.columns if c not in {"date", "permno"}]
    if not cols:
        raise ValueError("Assignments must include at least one portfolio column")
    # Sort by date to compare consecutive periods
    assignments = assignments.sort_values(["date", "permno"]).reset_index(drop=True)
    unique_dates = assignments["date"].drop_duplicates().sort_values().to_list()
    if len(unique_dates) < 2:
        return float("nan")
    turnover_rates = []
    # Loop over pairs of consecutive dates
    for i in range(1, len(unique_dates)):
        prev_date = unique_dates[i - 1]
        curr_date = unique_dates[i]
        prev_df = assignments[assignments["date"] == prev_date][["permno"] + cols]
        curr_df = assignments[assignments["date"] == curr_date][["permno"] + cols]
        # Merge to find overlapping securities
        merged = prev_df.merge(curr_df, on="permno", how="inner", suffixes=("_prev", "_curr"))
        if merged.empty:
            # No overlapping securities; turnover is 100%
            turnover_rates.append(1.0)
            continue
        # Determine assets whose assignments are unchanged across all portfolio columns
        unchanged = np.ones(len(merged), dtype=bool)
        for col in cols:
            unchanged &= merged[f"{col}_prev"].values == merged[f"{col}_curr"].values
        # Turnover is 1 - (# unchanged / # overlapping)
        rate = 1.0 - (unchanged.sum() / len(merged))
        turnover_rates.append(rate)
    return float(np.nanmean(turnover_rates))


def evaluate_anomaly(
    returns: pd.Series,
    *,
    risk_free: float = 0.0,
    periods_per_year: int = 12,
) -> dict:
    """Compute a bundle of performance metrics for a return series.

    This helper consolidates the statistics defined above into a single
    dictionary, facilitating the construction of summary tables.  It
    does not introduce any additional logic beyond calling the
    underlying functions.

    Parameters
    ----------
    returns : Series
        Periodic returns.
    risk_free : float, default 0.0
        Risk‑free rate per period.
    periods_per_year : int, default 12
        Number of periods per year.

    Returns
    -------
    dict
        Mapping of metric names to their numeric values: ``mean``,
        ``t_stat``, ``sharpe``, and ``max_dd``.
    """
    m = mean_return(returns, annualize=False)
    t = t_statistic(returns)
    s = sharpe_ratio(returns, risk_free=risk_free, periods_per_year=periods_per_year)
    dd = max_drawdown(returns)
    return {"mean": m, "t_stat": t, "sharpe": s, "max_dd": dd}