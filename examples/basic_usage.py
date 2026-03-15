# ruff: noqa: E402

"""
Basic usage example for the Assaying Anomalies Python library.

This script demonstrates how to:

* generate synthetic CRSP-style data
* compute a size anomaly signal
* run univariate portfolio sorts
* run a Fama–MacBeth regression

The data are randomly generated so the results have no economic meaning.  The
purpose of the example is solely to illustrate the API exposed by the
`aa` package.  Running this script does not require WRDS credentials or
any external datasets.
"""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

from aa.asset_pricing import SortConfig, univariate_sort
from aa.asset_pricing.fama_macbeth import fama_macbeth_full
from aa.signals import compute_size_signal


def main() -> None:
    np.random.seed(0)

    dates = pd.date_range("2020-01-31", periods=12, freq="ME")
    permnos = np.arange(10000, 10005)

    crsp_records: list[dict[str, object]] = []
    for permno in permnos:
        me_series = np.abs(np.random.lognormal(mean=5.0, sigma=0.3, size=len(dates)))
        for date, me in zip(dates, me_series):
            ret = np.random.normal(loc=0.01, scale=0.05)
            crsp_records.append(
                {
                    "date": date,
                    "permno": int(permno),
                    "ret": float(ret),
                    "me": float(me),
                }
            )
    crsp = pd.DataFrame(crsp_records)

    size_signal = compute_size_signal(crsp[["date", "permno", "me"]])

    panel = crsp.merge(size_signal, on=["date", "permno"], how="inner")

    sort_res = univariate_sort(
        returns=panel[["date", "permno", "ret"]],
        signal=panel[["date", "permno", "signal"]],
        size=panel[["date", "permno", "me"]],
        config=SortConfig(n_bins=5, nyse_breaks=False, min_obs=1),
    )
    print("Univariate size sort summary:")
    print(sort_res["summary"])

    panel = panel.rename(columns={"signal": "size"})

    fmb_res = fama_macbeth_full(
        panel,
        y="ret",
        xcols=["size"],
        time_col="date",
        nw_lags=1,
    )

    print("\nFama–MacBeth regression results:")
    print("Average coefficients:\n", fmb_res["lambdas"])
    print("\nt-statistics:\n", fmb_res["tstat"])


if __name__ == "__main__":
    main()
