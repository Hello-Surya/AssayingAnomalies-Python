"""Tests for anomaly performance metrics.

These tests check the correctness of the basic metrics implemented in
``aa.analysis.anomaly_metrics``.  They use small synthetic series to
verify that mean returns, t‑statistics, Sharpe ratios and drawdowns
are computed as expected.  The turnover function is also tested on a
simple assignment matrix.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from aa.analysis.anomaly_metrics import (
    mean_return,
    t_statistic,
    sharpe_ratio,
    max_drawdown,
    compute_turnover,
)


def test_basic_metrics():
    # Define a simple return series
    ser = pd.Series([0.10, -0.05, 0.10, 0.20, -0.10])
    # Mean return should equal numpy mean
    assert np.isclose(mean_return(ser), ser.mean(), atol=1e-12)
    # T‑statistic under IID assumptions
    expected_t = ser.mean() / (ser.std(ddof=1) / np.sqrt(len(ser)))
    assert np.isclose(t_statistic(ser), expected_t, atol=1e-12)
    # Annualised Sharpe ratio with monthly data (periods_per_year=12)
    expected_sharpe = ser.mean() / ser.std(ddof=1) * np.sqrt(12)
    assert np.isclose(sharpe_ratio(ser), expected_sharpe, atol=1e-12)
    # Maximum drawdown should be negative
    dd = max_drawdown(ser)
    assert dd <= 0.0
    # For a strictly increasing series, drawdown should be zero
    inc_ser = pd.Series([0.01, 0.02, 0.03, 0.04])
    assert max_drawdown(inc_ser) == 0.0


def test_turnover():
    # Build a small assignment DataFrame with two dates and three assets
    df = pd.DataFrame(
        {
            "date": [
                pd.Timestamp("2020-01-31"),
                pd.Timestamp("2020-01-31"),
                pd.Timestamp("2020-01-31"),
                pd.Timestamp("2020-02-29"),
                pd.Timestamp("2020-02-29"),
                pd.Timestamp("2020-02-29"),
            ],
            "permno": [1, 2, 3, 1, 2, 3],
            "bin1": [1, 1, 2, 1, 2, 2],
            "bin2": [1, 2, 3, 1, 2, 3],
        }
    )
    # Only the second asset moves from bin1=1 to bin1=2; turnover should be 1/3
    expected_turnover = 1 / 3
    assert np.isclose(compute_turnover(df), expected_turnover, atol=1e-12)
