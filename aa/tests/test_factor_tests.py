"""Tests for factor regression utilities.

These tests verify that the OLS regression functions in
``aa.asset_pricing.factor_tests`` produce sensible parameter
estimates on synthetic data.  The synthetic example constructs a
portfolio return series as a known linear function of a market
factor.  The regression should recover the true alpha and beta up to
numerical precision.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from aa.asset_pricing.factor_tests import regress_against_factors, regress_portfolios


def _make_synthetic_regression_data():
    # Create ten monthly observations
    dates = pd.date_range("2020-01-31", periods=10, freq="M")
    # Generate a market factor with mean zero
    rng = np.random.default_rng(seed=42)
    mkt = rng.normal(0.0, 0.05, size=len(dates))
    # True alpha and beta
    alpha_true = 0.01
    beta_true = 1.5
    # Portfolio returns as alpha + beta * market
    portfolio = alpha_true + beta_true * mkt
    # Assemble DataFrames
    returns = pd.DataFrame({"date": dates, "A": portfolio})
    factors = pd.DataFrame({"date": dates, "mkt": mkt})
    return returns, factors, alpha_true, beta_true


def test_regress_against_factors_single():
    returns, factors, alpha_true, beta_true = _make_synthetic_regression_data()
    # Use the single series version
    res = regress_against_factors(returns.set_index("date")["A"], factors)
    assert np.isclose(res["alpha"], alpha_true, atol=1e-6)
    # Beta is stored in a Series under key 'mkt'
    est_beta = res["betas"].get("mkt")
    assert est_beta is not None
    assert np.isclose(est_beta, beta_true, atol=1e-6)


def test_regress_portfolios_multiple():
    returns, factors, alpha_true, beta_true = _make_synthetic_regression_data()
    # Duplicate the portfolio into two columns with different names
    returns = returns.assign(B=returns["A"])  # identical series
    res = regress_portfolios(returns, factors)
    # Expect both A and B to have the same alpha and beta
    for p in ["A", "B"]:
        assert p in res.index
        assert np.isclose(res.loc[p, "alpha"], alpha_true, atol=1e-6)
        assert np.isclose(res.loc[p, "beta_mkt"], beta_true, atol=1e-6)
