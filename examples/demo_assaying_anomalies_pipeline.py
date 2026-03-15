# ruff: noqa: E402

"""
End-to-end demonstration of the Assaying Anomalies pipeline on synthetic data.

This script synthesises monthly CRSP-like returns, market equity and
fundamental data for a handful of stocks, computes five common anomaly
signals (size, value/book-to-market, momentum, investment and
profitability), performs univariate portfolio sorts on each signal
using the evaluation pipeline and runs a Fama–MacBeth regression with
all signals as regressors.  The results are printed to the console.

The synthetic dataset allows the script to run without access to WRDS
or proprietary data.  Because the inputs are random, the resulting
metrics have no economic interpretation; they merely illustrate how
to invoke the library.
"""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

from aa.analysis.anomaly_pipeline import evaluate_signals
from aa.asset_pricing.fama_macbeth import fama_macbeth_full
from aa.signals import (
    compute_book_to_market_signal,
    compute_investment_signal,
    compute_momentum_signal,
    compute_profitability_signal,
    compute_size_signal,
)


def main() -> None:
    np.random.seed(42)

    n_stocks = 10
    n_periods = 24
    permnos = np.arange(10000, 10000 + n_stocks)
    dates = pd.date_range("2019-01-31", periods=n_periods, freq="ME")

    crsp_records: list[dict[str, object]] = []
    for permno in permnos:
        me0 = np.abs(np.random.lognormal(mean=5.0, sigma=0.4))
        growth = np.random.normal(loc=1.0, scale=0.05, size=n_periods)
        me_series = me0 * np.cumprod(growth)
        for date, me in zip(dates, me_series):
            ret = np.random.normal(loc=0.01, scale=0.04)
            exchcd = 1 if np.random.rand() < 0.5 else 2
            crsp_records.append(
                {
                    "date": date,
                    "permno": int(permno),
                    "ret": float(ret),
                    "me": float(me),
                    "exchcd": int(exchcd),
                }
            )
    crsp = pd.DataFrame(crsp_records)

    fund_records: list[dict[str, object]] = []
    years = [2017, 2018, 2019, 2020, 2021]
    for permno in permnos:
        for year in years:
            datadate = pd.Timestamp(f"{year}-12-31")
            be = np.abs(np.random.lognormal(mean=4.0, sigma=0.4))
            at = np.abs(np.random.lognormal(mean=6.0, sigma=0.4))
            op = np.abs(np.random.lognormal(mean=2.0, sigma=0.4))
            fund_records.append(
                {
                    "permno": int(permno),
                    "datadate": datadate,
                    "be": float(be),
                    "at": float(at),
                    "op": float(op),
                }
            )
    fund = pd.DataFrame(fund_records)

    size_sig = compute_size_signal(crsp[["date", "permno", "me"]]).rename(
        columns={"signal": "size"}
    )
    momentum_sig = compute_momentum_signal(crsp[["date", "permno", "ret"]]).rename(
        columns={"signal": "momentum"}
    )
    bm_sig = compute_book_to_market_signal(
        crsp[["date", "permno", "me"]],
        fund[["permno", "datadate", "be"]],
    ).rename(columns={"signal": "value"})
    inv_sig = compute_investment_signal(
        crsp[["date", "permno"]],
        fund[["permno", "datadate", "at"]],
    ).rename(columns={"signal": "investment"})
    prof_sig = compute_profitability_signal(
        crsp[["date", "permno"]],
        fund[["permno", "datadate", "op", "be"]],
    ).rename(columns={"signal": "profitability"})

    panel = crsp.merge(size_sig, on=["date", "permno"], how="left")
    panel = panel.merge(momentum_sig, on=["date", "permno"], how="left")
    panel = panel.merge(bm_sig, on=["date", "permno"], how="left")
    panel = panel.merge(inv_sig, on=["date", "permno"], how="left")
    panel = panel.merge(prof_sig, on=["date", "permno"], how="left")

    results = evaluate_signals(
        panel.dropna(subset=["ret"]),
        signals=["size", "value", "momentum", "investment", "profitability"],
        returns_col="ret",
        size_col="me",
        exch_col="exchcd",
        bins=5,
        nyse_breaks=False,
        min_obs=5,
    )

    for name, res in results.items():
        metrics = res["metrics"]
        print(f"\n=== {name} anomaly ===")
        for key, val in metrics.items():
            if pd.notna(val):
                print(f"{key}: {val:.4f}")
            else:
                print(f"{key}: NaN")

    reg_panel = panel.dropna(
        subset=[
            "ret",
            "size",
            "value",
            "momentum",
            "investment",
            "profitability",
        ]
    )

    res_fmb = fama_macbeth_full(
        reg_panel,
        y="ret",
        xcols=["size", "value", "momentum", "investment", "profitability"],
        time_col="date",
        nw_lags=2,
    )

    print("\n=== Fama–MacBeth regression on all signals ===")
    print("Average betas:")
    print(res_fmb["lambdas"])
    print("\nt-statistics:")
    print(res_fmb["tstat"])


if __name__ == "__main__":
    main()
