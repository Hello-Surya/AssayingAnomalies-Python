"""
    Factor comparison utilities for anomaly returns.

    This module provides simple time‑series regressions of portfolio
    returns on benchmark factor models.  It is a direct translation of
    the functionality found in MATLAB utilities such as
    ``runBivSort.m`` (for alphas and loadings) and ``calcGenAlpha.m``.
    The functions here are intentionally minimal: they accept return
    series and factor returns, fit ordinary least squares regressions
    with an intercept, and report parameter estimates and t‑statistics.
    Users seeking cross‑sectional regressions or Newey–West correction
    should refer to :mod:`aa.asset_pricing.fama_macbeth`.

    Functions
    ---------
    regress_against_factors
        Regress a single portfolio return series on a set of factor
        returns.

    regress_portfolios
        Regress multiple portfolio return series on factors and
        assemble the results into a tidy DataFrame.

    Notes
    -----
    All inputs must be indexed by the same date frequency.  Missing
    observations are dropped before estimation.  Factors should be
    provided without an intercept; one will be added internally.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, Iterable, List

import numpy as np
import pandas as pd
import statsmodels.api as sm


def regress_against_factors(
    returns: pd.Series,
    factors: pd.DataFrame,
    *,
    add_intercept: bool = True,
) -> Dict[str, Any]:
    """Regress a single portfolio return series on benchmark factors.

    Parameters
    ----------
    returns : Series
        Portfolio excess returns with a ``date`` index or column.  If
        ``returns`` has a ``name`` attribute, it will be used in the
        output dictionary.
    factors : DataFrame
        DataFrame of factor returns with matching date index or
        ``date`` column.  The factors should not include a column for
        the intercept.
    add_intercept : bool, default True
        If True, an intercept term will be added to the regression
        regressors.  This corresponds to estimating alpha.

    Returns
    -------
    dict
        Dictionary containing the regression coefficients, t‑values,
        adjusted R‑squared and the number of observations.  The keys
        are: ``alpha``, ``t_alpha``, ``betas``, ``t_betas``, ``r2`` and
        ``nobs``.
    """
    # Align returns and factors on their index or date column
    if "date" in returns.index.names:
        series = returns.copy()
    elif "date" in returns.index or "date" in returns.columns:
        series = returns.copy()
        if "date" in series.columns:
            series = series.set_index("date")
    else:
        series = returns.copy()
    y = pd.to_numeric(series, errors="coerce").dropna()
    # Align factors
    if "date" in factors.columns:
        X = factors.copy().set_index("date")
    else:
        X = factors.copy()
    # Join on the index and drop missing
    df = pd.concat([y, X], axis=1, join="inner").dropna()
    if df.empty:
        return {"alpha": np.nan, "t_alpha": np.nan, "betas": pd.Series(dtype=float), "t_betas": pd.Series(dtype=float), "r2": np.nan, "nobs": 0}
    y_aligned = df.iloc[:, 0]
    X_aligned = df.iloc[:, 1:]
    if add_intercept:
        X_aligned = sm.add_constant(X_aligned, has_constant="add")
    model = sm.OLS(y_aligned, X_aligned)
    results = model.fit()
    params = results.params
    tvalues = results.tvalues
    # Identify the intercept (const) if present
    alpha = params.get("const") if "const" in params.index else np.nan
    t_alpha = tvalues.get("const") if "const" in tvalues.index else np.nan
    # Betas exclude the intercept
    betas = params.drop("const", errors="ignore")
    t_betas = tvalues.drop("const", errors="ignore")
    return {
        "alpha": float(alpha) if alpha is not np.nan else np.nan,
        "t_alpha": float(t_alpha) if t_alpha is not np.nan else np.nan,
        "betas": betas.astype(float),
        "t_betas": t_betas.astype(float),
        "r2": float(results.rsquared_adj),
        "nobs": int(results.nobs),
    }


def regress_portfolios(
    returns: pd.DataFrame,
    factors: pd.DataFrame,
    *,
    add_intercept: bool = True,
) -> pd.DataFrame:
    """Regress multiple portfolio return series on factors.

    Parameters
    ----------
    returns : DataFrame
        Wide DataFrame of portfolio returns with a ``date`` column and
        one column per portfolio.  The column names will be used as
        index labels in the output.
    factors : DataFrame
        DataFrame of factor returns with a ``date`` column and one
        column per factor.  Must align with ``returns`` on the date.
    add_intercept : bool, default True
        If True, include an intercept in each regression to estimate
        alpha.

    Returns
    -------
    DataFrame
        Tidy summary of the regression results.  The index consists
        of portfolio names, and the columns include ``alpha``,
        ``t_alpha``, one column per beta and its t‑statistic, and
        ``r2``.  The column order is deterministic: parameters are
        listed before t‑values.
    """
    if "date" not in returns.columns:
        raise KeyError("returns must contain a 'date' column")
    if "date" not in factors.columns:
        raise KeyError("factors must contain a 'date' column")
    portfolios = [c for c in returns.columns if c != "date"]
    summaries: List[Dict[str, Any]] = []
    index: List[str] = []
    for p in portfolios:
        res_dict = regress_against_factors(
            returns.set_index("date")[p], factors, add_intercept=add_intercept
        )
        index.append(p)
        summary = {
            "alpha": res_dict["alpha"],
            "t_alpha": res_dict["t_alpha"],
        }
        # Add betas and t_betas with deterministic ordering
        for beta_name, beta_val in res_dict["betas"].items():
            summary[f"beta_{beta_name}"] = beta_val
        for beta_name, t_val in res_dict["t_betas"].items():
            summary[f"t_beta_{beta_name}"] = t_val
        summary["r2"] = res_dict["r2"]
        summaries.append(summary)
    out = pd.DataFrame(summaries, index=index)
    return out