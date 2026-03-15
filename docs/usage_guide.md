# Usage Guide

This document provides a practical walkthrough of how to use the
**Assaying Anomalies** Python library to compute anomaly signals,
construct portfolios and run cross‑sectional regressions.  The focus is
on demonstrating the high‑level API on synthetic data; for a
production‑scale analysis you would replace the toy inputs with
CRSP/Compustat data.

## Prerequisites

The library depends on Python ≥ 3.9 and standard scientific
packages.  Install the stable release from PyPI with:

```bash
pip install assaying-anomalies
```

If you clone the repository to inspect the code or contribute, install
it in editable mode along with development dependencies:

```bash
git clone https://github.com/Hello-Surya/AssayingAnomalies-Python.git
cd AssayingAnomalies-Python
pip install -e .[dev]
```

## Typical workflow

1. **Prepare a panel** of monthly returns and firm fundamentals with
   columns such as `date`, `permno`, `ret`, `me`, `be`, `at` and
   `op`.
2. **Compute anomaly signals** using the functions in `aa.signals`.  For
   example:

   ```python
   from aa.signals import compute_size_signal, compute_book_to_market_signal
   size = compute_size_signal(crsp_df[["date", "permno", "me"]])
   bm   = compute_book_to_market_signal(
       funda_df[["date", "permno", "be"]],
       crsp_df[["date", "permno", "me"]],
   )
   ```

3. **Perform portfolio sorts** using `aa.asset_pricing.univariate_sort` or
   `aa.asset_pricing.double_sort`.  These functions form equal‑ or
   value‑weighted portfolios and compute high‑minus‑low spreads.
   ```python
   from aa.asset_pricing.univariate import SortConfig, univariate_sort
   cfg = SortConfig(n_bins=5, nyse_breaks=False, min_obs=20)
   res = univariate_sort(
       returns=returns,
       signal=size,
       size=crsp_df[["date", "permno", "me"]],
       exch=None,
       config=cfg,
   )
   summary = res["summary"]  # average returns by bin
   hl      = res["hl"]        # high‑minus‑low time series
   ```

4. **Estimate risk prices** with two‑pass Fama–MacBeth regressions via
   `aa.asset_pricing.fama_macbeth_full` to obtain average betas and
   Newey–West standard errors:
   ```python
   from aa.asset_pricing.fama_macbeth import fama_macbeth_full
   reg_res = fama_macbeth_full(
       panel=panel,
       y="ret",
       xcols=["size", "bm"],
       time_col="date",
       nw_lags=3,
   )
   print(reg_res["average_beta"])
   print(reg_res["se_beta"])
   ```

5. **Evaluate multiple signals** simultaneously using
   `aa.analysis.anomaly_pipeline.evaluate_signals`, which returns
   performance metrics for each signal.

6. **Use the replication scripts** in `scripts/` to orchestrate the
   entire pipeline on your dataset without writing any Python code.

For more detailed explanations and advanced usage, see the full
documentation in `docs/architecture.md`, the Jupyter notebooks in
`notebooks/` and the examples in `examples/`.