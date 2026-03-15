"""
Integration test for the Assaying Anomalies pipeline.

This test exercises the full workflow on a synthetic dataset.  It
generates a panel of returns and characteristics, runs a univariate
portfolio sort and performs a Fama–MacBeth regression.  The test
verifies that the outputs have the expected structure and contain
non‑trivial results.  By relying solely on synthetic data, the test
can run in any environment without access to WRDS.
"""

from __future__ import annotations


from aa.data.synthetic_generator import generate_synthetic_panel
from aa.asset_pricing import SortConfig, univariate_sort, fama_macbeth_full


def test_full_pipeline() -> None:
    """Run the anomaly pipeline on synthetic data and assert basic sanity."""
    # Generate a modest‑sized dataset for quick testing
    panel = generate_synthetic_panel(n_periods=24, n_stocks=50, seed=42)
    # Split into inputs required by univariate_sort
    returns_df = panel[["date", "permno", "ret"]].copy()
    signal_df = panel[["date", "permno", "signal"]].copy()
    size_df = panel[["date", "permno", "me"]].copy()
    exch_df = panel[["date", "permno", "exchcd"]].copy()
    # Configure a quintile sort with a reasonable minimum observation count
    config = SortConfig(n_bins=5, nyse_breaks=False, min_obs=20)
    sort_result = univariate_sort(
        returns=returns_df, signal=signal_df, size=size_df, exch=exch_df, config=config
    )
    # Ensure the result contains the expected keys
    assert (
        "time_series" in sort_result
    ), "univariate_sort must return a 'time_series' key"
    assert "summary" in sort_result, "univariate_sort must return a 'summary' key"
    time_series = sort_result["time_series"]
    summary = sort_result["summary"]
    # The time‑series and summary should not be empty
    assert not time_series.empty, "time_series DataFrame is unexpectedly empty"
    assert not summary.empty, "summary DataFrame is unexpectedly empty"
    # Construct a time identifier for Fama–MacBeth (YYYYMM)
    panel_with_time = panel.copy()
    panel_with_time["yyyymm"] = (
        panel_with_time["date"].dt.year * 100 + panel_with_time["date"].dt.month
    )
    # Run a two‑pass regression on the synthetic signal
    fm_result = fama_macbeth_full(
        panel_with_time, y="ret", xcols=["signal"], time_col="yyyymm"
    )
    # Check that the full result dictionary contains all expected keys
    for key in ["lambdas", "lambda_ts", "se", "tstat", "n_obs"]:
        assert key in fm_result, f"Missing key '{key}' in Fama–MacBeth output"
    # The lambdas and t‑statistics should contain at least one non‑NaN value
    assert fm_result["lambdas"].notna().any(), "All Fama–MacBeth coefficients are NaN"
    assert fm_result["tstat"].notna().any(), "All Fama–MacBeth t‑stats are NaN"
