"""
usage_walkthrough.py
====================

This script provides a step‑by‑step walkthrough of the basic workflow in
the Assaying Anomalies Python library.  It generates synthetic data,
computes anomaly signals, performs a univariate portfolio sort and runs
a Fama–MacBeth regression.  The results printed to the console have no
economic meaning – the random data are merely for illustration.

Running this script does not require any external data sources or
authentication.  Simply execute:

    python examples/usage_walkthrough.py

to follow along.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from aa.signals import (
    compute_size_signal,
    compute_book_to_market_signal,
    compute_momentum_signal,
    compute_investment_signal,
    compute_profitability_signal,
)
from aa.asset_pricing.univariate import SortConfig, univariate_sort
from aa.asset_pricing.fama_macbeth import fama_macbeth_full


def generate_synthetic_panel(n_firms: int = 50, n_months: int = 60) -> pd.DataFrame:
    """Generate a synthetic panel of returns and fundamentals.

    Parameters
    ----------
    n_firms : int
        Number of unique firms.
    n_months : int
        Number of monthly observations.

    Returns
    -------
    DataFrame
        A panel with columns `date`, `permno`, `ret`, `me`, `be`, `at`, `op`.
    """
    dates = pd.date_range("2010-01-31", periods=n_months, freq="M")
    firm_ids = np.arange(1, n_firms + 1)
    panel = pd.MultiIndex.from_product(
        [dates, firm_ids], names=["date", "permno"]
    ).to_frame(index=False)
    rng = np.random.default_rng(0)
    panel["ret"] = rng.normal(loc=0.01, scale=0.05, size=len(panel))
    panel["me"] = rng.lognormal(mean=7, sigma=1.0, size=len(panel))
    panel["be"] = rng.lognormal(mean=6.5, sigma=1.0, size=len(panel))
    panel["at"] = rng.lognormal(mean=8.0, sigma=1.0, size=len(panel))
    panel["op"] = rng.normal(loc=0.1, scale=0.05, size=len(panel)) * panel["be"]
    return panel


def main() -> None:
    # ------------------------------------------------------------------
    # 1. Generate synthetic data
    # ------------------------------------------------------------------
    print("Generating synthetic panel of returns and fundamentals...")
    panel = generate_synthetic_panel()
    print(
        f"Panel contains {panel['permno'].nunique()} firms and {panel['date'].nunique()} monthly observations."
    )

    # ------------------------------------------------------------------
    # 2. Compute anomaly signals
    # ------------------------------------------------------------------
    print("Computing anomaly signals...")
    size = compute_size_signal(panel[["date", "permno", "me"]])
    bm = compute_book_to_market_signal(
        panel[["date", "permno", "be"]], panel[["date", "permno", "me"]]
    )
    momentum = compute_momentum_signal(panel[["date", "permno", "ret"]])
    investment = compute_investment_signal(
        funda=panel[["date", "permno", "at"]],
        crsp=panel[["date", "permno", "me"]],
    )
    profitability = compute_profitability_signal(
        panel[["date", "permno", "op"]], panel[["date", "permno", "be"]]
    )

    # Merge signals into a single DataFrame
    signals = (
        size.rename(columns={"signal": "size"})
        .merge(bm.rename(columns={"signal": "bm"}), on=["date", "permno"])
        .merge(momentum.rename(columns={"signal": "momentum"}), on=["date", "permno"])
        .merge(
            investment.rename(columns={"signal": "investment"}), on=["date", "permno"]
        )
        .merge(
            profitability.rename(columns={"signal": "profitability"}),
            on=["date", "permno"],
        )
    )
    panel_signals = panel.merge(signals, on=["date", "permno"])
    print("Signals computed and merged with returns.")

    # ------------------------------------------------------------------
    # 3. Perform a univariate sort on size
    # ------------------------------------------------------------------
    print("Performing a univariate sort on the size signal...")
    sort_cfg = SortConfig(n_bins=5, nyse_breaks=False, min_obs=20)
    res = univariate_sort(
        returns=panel_signals[["date", "permno", "ret"]],
        signal=size,
        size=panel_signals[["date", "permno", "me"]],
        exch=None,
        config=sort_cfg,
    )
    summary_table = res["summary"]
    hl_series = res["hl"]
    print("Summary of equal‑weighted portfolio returns by quintile:")
    print(summary_table.head())
    print("\nFirst few high-minus-low observations:")
    print(hl_series.head())

    # ------------------------------------------------------------------
    # 4. Run a Fama–MacBeth regression
    # ------------------------------------------------------------------
    print("\nRunning a two-pass Fama–MacBeth regression on size and book–to–market...")
    panel_reg = panel_signals[["date", "permno", "ret", "size", "bm"]].dropna()
    reg_res = fama_macbeth_full(
        panel=panel_reg, y="ret", xcols=["size", "bm"], time_col="date", nw_lags=3
    )
    print("Average betas:")
    print(reg_res["average_beta"])
    print("\nNewey–West standard errors:")
    print(reg_res["se_beta"])


if __name__ == "__main__":
    main()
