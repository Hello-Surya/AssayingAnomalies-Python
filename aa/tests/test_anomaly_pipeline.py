import os
import sys
import numpy as np
import pandas as pd

# Ensure the aa package is importable when running tests directly.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from aa.analysis import evaluate_signals


def test_evaluate_signals_basic():
    # Synthetic two‑period dataset with two signals
    panel = pd.DataFrame(
        {
            "date": ["2020-01-31", "2020-01-31", "2020-02-28", "2020-02-28"],
            "permno": [1, 2, 1, 2],
            "ret": [0.01, 0.02, -0.005, 0.015],
            "me": [100, 200, 105, 210],
            "exchcd": [1, 1, 1, 1],
            "size": [10, 20, 11, 22],
            "value": [0.5, 0.4, 0.55, 0.45],
        }
    )
    results = evaluate_signals(panel, signals=["size", "value"], bins=2, min_obs=2)
    # Check that both signals are present
    assert set(results.keys()) == {"size", "value"}
    for sig, res in results.items():
        metrics = res["metrics"]
        expected_keys = {
            "mean_ew",
            "t_stat_ew",
            "sharpe_ew",
            "max_dd_ew",
            "mean_vw",
            "t_stat_vw",
            "sharpe_vw",
            "max_dd_vw",
        }
        assert expected_keys.issubset(metrics.keys())
        # ensure time_series and summary are DataFrames with expected columns
        ts = res["time_series"]
        summ = res["summary"]
        hl = res["hl_ts"]
        assert isinstance(ts, pd.DataFrame)
        assert isinstance(summ, pd.DataFrame)
        assert isinstance(hl, pd.DataFrame)
        # Each should have correct columns
        assert {"date", "bin", "ret_ew"}.issubset(ts.columns)
        # Metrics should be finite or NaN
        for mval in metrics.values():
            assert mval is np.nan or isinstance(mval, (float, int))
    # Verify approximate values for mean_ew
    size_metrics = results["size"]["metrics"]
    value_metrics = results["value"]["metrics"]
    # Size high‑low returns: [0.01, 0.02] -> mean 0.015, t‑stat ≈ 3.0, Sharpe ≈ 7.348 (annualised with 12 periods)
    assert abs(size_metrics["mean_ew"] - 0.015) < 1e-6
    assert abs(size_metrics["t_stat_ew"] - 3.0) < 1e-8
    assert abs(size_metrics["sharpe_ew"] - 7.3484692283495345) < 1e-6
    # Value high‑low returns: [-0.01, -0.02] -> mean -0.015, t‑stat ≈ -3.0, Sharpe ≈ -7.348 (annualised)
    assert abs(value_metrics["mean_ew"] + 0.015) < 1e-6
    assert abs(value_metrics["t_stat_ew"] + 3.0) < 1e-8
    assert abs(value_metrics["sharpe_ew"] + 7.3484692283495345) < 1e-6
