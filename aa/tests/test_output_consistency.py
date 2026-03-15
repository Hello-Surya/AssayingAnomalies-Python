"""
Tests for output consistency utilities.

These tests verify that the comparison functions correctly identify
matching and mismatching outputs across a range of data structures.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from aa.validation.output_consistency import (
    check_anomaly_ranking_stability,
    check_fama_macbeth_consistency,
    check_portfolio_returns_reproducibility,
    check_summary_table_consistency,
)


def test_check_portfolio_returns_reproducibility() -> None:
    df1 = pd.DataFrame({"a": [1.0, 2.0, np.nan], "b": [0.5, -1.0, 3.0]})
    df2 = df1.copy()
    assert check_portfolio_returns_reproducibility(df1, df2)

    df3 = pd.DataFrame({"a": [1.0, 2.1, np.nan], "b": [0.5, -1.0, 3.0]})
    assert not check_portfolio_returns_reproducibility(df1, df3)


def test_check_anomaly_ranking_stability() -> None:
    r1 = pd.Series(["size", "value", "momentum"], name="anomaly")
    r2 = pd.Series(["size", "value", "momentum"], name="anomaly")
    assert check_anomaly_ranking_stability(r1, r2)

    r3 = pd.Series(["value", "size", "momentum"], name="anomaly")
    assert not check_anomaly_ranking_stability(r1, r3)


def test_check_summary_table_consistency() -> None:
    t1 = pd.DataFrame(
        [[0.1, 2.0], [0.2, -1.0]],
        columns=["mean", "t_stat"],
        index=["a", "b"],
    )
    t2 = t1.copy()
    assert check_summary_table_consistency(t1, t2)

    t3 = pd.DataFrame(
        [[0.1, 2.0], [0.2, -1.1]],
        columns=["mean", "t_stat"],
        index=["a", "b"],
    )
    assert not check_summary_table_consistency(t1, t3)


def test_check_fama_macbeth_consistency() -> None:
    res1 = {
        "coefficients": pd.DataFrame(
            [[0.5, 1.0], [0.1, -0.2]],
            columns=["beta1", "beta2"],
            index=["signal1", "signal2"],
        ),
        "t_stats": pd.Series([2.5, -1.1], index=["beta1", "beta2"]),
        "sigma": np.array([0.1, 0.2]),
    }

    res2 = {
        "coefficients": res1["coefficients"].copy(),
        "t_stats": res1["t_stats"].copy(),
        "sigma": np.array([0.1, 0.2]),
    }
    assert check_fama_macbeth_consistency(res1, res2)

    res3 = {
        "coefficients": res1["coefficients"].copy(),
        "t_stats": res1["t_stats"].copy(),
        "sigma": np.array([0.1, 0.25]),
    }
    assert not check_fama_macbeth_consistency(res1, res3)
