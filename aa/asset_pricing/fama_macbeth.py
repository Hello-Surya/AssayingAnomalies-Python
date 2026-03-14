"""
Fama–MacBeth two‑pass regression estimators.

This module provides implementations of the cross‑sectional regression
procedures commonly used in asset pricing.  The basic estimator,
known as the Fama–MacBeth (1973) two‑pass method, fits a cross‑
sectional regression in each time period and then averages the
resulting series of coefficients.  Newey–West heteroskedasticity
and autocorrelation consistent (HAC) standard errors are used to
account for serial correlation in the estimated risk prices.

Two functions are provided:

``fama_macbeth``
    Replicates the original behaviour from earlier milestones.  It
    returns average coefficients, the full time series of
    period‑by‑period coefficients and their Newey–West standard errors.

``fama_macbeth_full``
    Extends the basic estimator to include t‑statistics and the
    number of cross‑sectional observation periods used for each
    coefficient.  This function is the recommended interface when
    reporting results in tables.
"""

from __future__ import annotations

from typing import Sequence, Tuple, Dict

import numpy as np
import pandas as pd
import statsmodels.api as sm

__all__ = ["fama_macbeth", "fama_macbeth_full"]


def _long_run_variance(series: np.ndarray, lags: int) -> float:
    """Compute the Newey–West long‑run variance for a 1‑D array.

    Parameters
    ----------
    series : ndarray
        One‑dimensional array of demeaned observations.
    lags : int
        Number of lags to include in the HAC estimator.  A lag of zero
        yields the usual sample variance.

    Returns
    -------
    float
        Estimate of the long‑run variance.  Returns ``nan`` if the
        series is empty.
    """
    n = len(series)
    if n == 0:
        return np.nan
    # Gamma_0
    gamma0 = float(np.dot(series, series)) / n
    if lags == 0:
        return gamma0
    var = gamma0
    for k in range(1, lags + 1):
        if k >= n:
            break
        cov = float(np.dot(series[k:], series[:-k])) / n
        weight = 1.0 - k / (lags + 1)
        var += 2.0 * weight * cov
    return var


def fama_macbeth(
    panel: pd.DataFrame,
    y: str = "ret",
    xcols: Sequence[str] | None = None,
    *,
    time_col: str = "yyyymm",
    nw_lags: int | None = None,
) -> Tuple[pd.Series, pd.DataFrame, pd.Series]:
    """Estimate Fama–MacBeth risk prices and Newey–West standard errors.

    Parameters
    ----------
    panel : DataFrame
        Long format panel of returns and characteristics.  Must
        contain columns ``time_col``, ``y`` and each name in ``xcols``.
        Each row corresponds to an asset–period observation.
    y : str, default "ret"
        Column name of the dependent variable (e.g. one‑month ahead
        returns).
    xcols : sequence of str, optional
        Names of characteristic columns used as regressors.  If None,
        no regressors are used and only an intercept is estimated.
    time_col : str, default "yyyymm"
        Name of the column identifying time periods.  Each unique value
        of this column is treated as a separate cross‑section.
    nw_lags : int, optional
        Number of Newey–West lags for the second‑pass standard errors.
        If None, an automatic lag length is chosen based on the number
        of periods.

    Returns
    -------
    lambdas : Series
        The average risk prices across all periods.  Index includes
        the intercept ``const`` and each regressor.
    lambda_ts : DataFrame
        Period‑by‑period coefficients.  Rows correspond to periods.
    se : Series
        Newey–West standard errors of the average coefficients.
    """
    if xcols is None:
        xcols = []
    # Input validation
    if time_col not in panel.columns:
        raise KeyError(f"panel must contain time column '{time_col}'")
    if y not in panel.columns:
        raise KeyError(f"panel must contain dependent variable '{y}'")
    for col in xcols:
        if col not in panel.columns:
            raise KeyError(f"panel is missing regressor column '{col}'")
    coeffs: list[pd.Series] = []
    # Loop over periods and run cross‑sectional regressions
    for period, grp in panel.groupby(time_col):
        # Require no missing values in y or regressors
        mask = grp[y].notna()
        for col in xcols:
            mask &= grp[col].notna()
        grp_valid = grp.loc[mask]
        # If no regressors, simply compute mean return (intercept)
        if not xcols:
            if grp_valid.empty:
                coeffs.append(pd.Series({"const": np.nan}, name=period))
                continue
            coeffs.append(pd.Series({"const": float(grp_valid[y].mean())}, name=period))
            continue
        # With regressors, run OLS with intercept
        if grp_valid.empty:
            coeff = pd.Series(
                {"const": np.nan, **{c: np.nan for c in xcols}}, name=period
            )
            coeffs.append(coeff)
            continue
        yv = grp_valid[y]
        X = grp_valid[list(xcols)]
        X = sm.add_constant(X, has_constant="add")
        try:
            model = sm.OLS(yv, X)
            res = model.fit()
            coeff = res.params.rename(period)
        except Exception:
            # On failure, return NaNs for all coefficients
            coeff = pd.Series({col: np.nan for col in X.columns}, name=period)
        # Ensure all expected columns are present
        for col in ["const"] + list(xcols):
            if col not in coeff.index:
                coeff.loc[col] = np.nan
        coeffs.append(coeff)
    lambda_ts = pd.DataFrame(coeffs).sort_index()
    # Align columns order
    lambda_ts = lambda_ts.reindex(columns=lambda_ts.columns, fill_value=np.nan)
    lambdas = lambda_ts.mean(axis=0, skipna=True)
    T = lambda_ts.shape[0]
    # Automatic lag length if not specified: 4*(T/100)^(2/9) (Newey & West 1994)
    if nw_lags is None:
        nw_lags = int(np.floor(4 * (T / 100.0) ** (2.0 / 9.0)))
    se_vals = {}
    for col in lambda_ts.columns:
        # Demean coefficient series
        series = lambda_ts[col].dropna().to_numpy(dtype=float)
        demeaned = series - np.nanmean(series)
        var = _long_run_variance(demeaned, nw_lags)
        se_vals[col] = np.sqrt(var / len(series)) if len(series) > 0 else np.nan
    se = pd.Series(se_vals)
    se.index.name = None
    return lambdas, lambda_ts, se


ddef fama_macbeth_full(
    panel: pd.DataFrame,
    y: str = "ret",
    xcols: Sequence[str] | None = None,
    *,
    time_col: str = "yyyymm",
    nw_lags: int | None = None,
) -> Dict[str, pd.DataFrame | pd.Series]:
    """Full Fama–MacBeth regression with t-statistics and counts.

    This function runs the two-pass procedure and returns the
    average risk prices, their Newey–West standard errors, t-values and
    the number of periods used for each coefficient.

    Parameters
    ----------
    panel, y, xcols, time_col, nw_lags
        See :func:`fama_macbeth` for definitions.

    Returns
    -------
    dict
        Dictionary containing both the legacy keys expected by the test
        suite and the newer alias keys used elsewhere in the codebase.

        Legacy keys:
        ``"lambdas"``, ``"lambda_ts"``, ``"se"``, ``"tstat"``, ``"n_obs"``

        Alias keys:
        ``"lambda"``, ``"t"``, ``"n"``
    """
    lambdas, lambda_ts, se = fama_macbeth(
        panel, y=y, xcols=xcols, time_col=time_col, nw_lags=nw_lags
    )
    t_vals = lambdas / se
    n_counts = lambda_ts.count()

    return {
        # legacy keys expected by tests
        "lambdas": lambdas,
        "lambda_ts": lambda_ts,
        "se": se,
        "tstat": t_vals,
        "n_obs": n_counts,
        # backward-compatible aliases
        "lambda": lambdas,
        "t": t_vals,
        "n": n_counts,
    }