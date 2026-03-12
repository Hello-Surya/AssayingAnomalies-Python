"""Tests for the bivariate portfolio sort functionality.

These tests verify that the ``make_double_sort_ind`` and
``run_double_sort`` functions behave sensibly on simple synthetic
datasets.  They mirror the style of the univariate sort tests and
ensure that the basic aggregation and high–low calculations work as
expected.  The synthetic dataset is constructed to have a monotonic
relation between the two signals and returns, allowing for easy
validation of the high minus low spreads.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from aa.asset_pricing.double_sorts import (
    DoubleSortConfig,
    make_double_sort_ind,
    run_double_sort,
)


def _make_synthetic_data():
    # Construct a simple dataset with two dates and ten securities.
    dates = [pd.Timestamp("2020-01-31"), pd.Timestamp("2020-02-29")]
    records = []
    # Define two signals: signal1 increases with i, signal2 decreases with i.
    signal1_vals = np.linspace(-1, 1, 10)
    signal2_vals = np.linspace(1, -1, 10)
    for date in dates:
        for i, (s1, s2) in enumerate(zip(signal1_vals, signal2_vals)):
            # Returns are positively related to the first signal and
            # negatively related to the second signal.
            ret = 0.02 + 0.1 * s1 - 0.05 * s2
            me = 100 + 10 * i
            exch = 1  # treat all as NYSE for simplicity
            records.append((date, i, s1, s2, ret, me, exch))
    df = pd.DataFrame(
        records,
        columns=["date", "permno", "signal1", "signal2", "ret", "me", "exchcd"],
    )
    returns = df[["date", "permno", "ret"]].copy()
    signal1 = df[["date", "permno", "signal1"]].rename(columns={"signal1": "signal"})
    signal2 = df[["date", "permno", "signal2"]].rename(columns={"signal2": "signal"})
    size = df[["date", "permno", "me"]].copy()
    exch = df[["date", "permno", "exchcd"]].copy()
    return returns, signal1, signal2, size, exch


def test_make_double_sort_ind_basic():
    returns, s1, s2, size, exch = _make_synthetic_data()
    config = DoubleSortConfig(n_bins_1=2, n_bins_2=3, nyse_breaks=False, min_obs=1, conditional=False)
    ind = make_double_sort_ind(returns=returns, signal_1=s1, signal_2=s2, size=size, exch=exch, config=config)
    # All rows should have bin assignments
    assert not ind.empty
    assert {"date", "permno", "bin1", "bin2"}.issubset(ind.columns)
    # There should be as many rows as the number of returns
    assert len(ind) == len(returns)


def test_run_double_sort_high_low():
    returns, s1, s2, size, exch = _make_synthetic_data()
    config = DoubleSortConfig(n_bins_1=2, n_bins_2=2, nyse_breaks=False, min_obs=1, conditional=False)
    res = run_double_sort(returns=returns, signal_1=s1, signal_2=s2, size=size, exch=exch, config=config)
    ts = res["time_series"]
    summary = res["summary"]
    hl1 = res["hl_dim1"]
    hl2 = res["hl_dim2"]
    # Check the summary shape: number of unique portfolios should be n_bins_1 * n_bins_2
    assert len(summary) == config.n_bins_1 * config.n_bins_2
    # Compute high minus low along dimension 1 using the summary
    pivot = summary.pivot(index="bin1", columns="bin2", values="ret_ew")
    # Highest minus lowest bin along bin1 for each bin2
    hl1_from_summary = (pivot.loc[config.n_bins_1] - pivot.loc[1]).mean()
    # The average of hl_ew in hl1 should equal the above
    assert np.isclose(hl1["hl_ew"].mean(), hl1_from_summary, atol=1e-12)
    # Similarly for dimension 2
    pivot2 = summary.pivot(index="bin2", columns="bin1", values="ret_ew")
    hl2_from_summary = (pivot2.loc[config.n_bins_2] - pivot2.loc[1]).mean()
    assert np.isclose(hl2["hl_ew"].mean(), hl2_from_summary, atol=1e-12)